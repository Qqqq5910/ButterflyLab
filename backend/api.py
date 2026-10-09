from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import Field
from .models import StrictModel, WorldConfig, Intervention
from .simulation import initial_world, simulate, search_interventions, ENGINE_VERSION
from .research import RunRequest, SearchRequest, comparison, discover, paired_result
from .jobs import Jobs
from .exploration import ExplorationRequest,LabStore,explore,replay_cell,PARAMETERS,ALGORITHM_VERSION
from .storage import Store
from .social_config import SocialConfig, engine_for, preset
from .world_store import WorldStore
from .studies import StudyRequest,study
from .environment import environment
from .decisions import ProviderConfig,DecisionProvider
from .social import simulate_social
from .llm import Ledger,settings
from .pilot import PilotRequest,configuration as pilot_configuration,run_pilot,replay_result

class NameRequest(StrictModel):
    experiment_name:str=Field(min_length=1,max_length=120)
class SimRequest(StrictModel):
    seed:int=Field(42,ge=0,le=2147483647)
    rounds:int=Field(50,ge=5,le=100)
    intervention:Intervention|None=None
class WorldRequest(StrictModel):
    name:str=Field('Untitled world',min_length=1,max_length=120)
    configuration:SocialConfig=Field(default_factory=SocialConfig)
    parent_id:str|None=None
class DecisionRun(StrictModel):
    world:SocialConfig=Field(default_factory=lambda:SocialConfig(decision_mode='mock'))
    provider:ProviderConfig=Field(default_factory=ProviderConfig)
    seed:int=Field(42,ge=0,le=2147483647)

def create_app(db_path=None):
    store=Store(db_path)
    worlds=WorldStore(store.path.with_name('worlds.sqlite3'))
    runtime=environment()
    jobs=Jobs(store.path.with_name(store.path.stem+'-jobs.sqlite3'))
    labs=LabStore(store.path.with_name(store.path.stem+'-labs.sqlite3'))
    ledger=Ledger(store.path.with_name('llm-budget.sqlite3'))
    @asynccontextmanager
    async def lifespan(app):
        store.recover()
        jobs.recover();labs.recover()
        try:
            yield
        finally:
            jobs.shutdown()
    app=FastAPI(title='ButterflyLab API',version=ENGINE_VERSION,lifespan=lifespan)
    app.state.store=store
    app.state.jobs=jobs
    app.state.labs=labs
    app.state.ledger=ledger
    app.add_middleware(GZipMiddleware,minimum_size=1000,compresslevel=1)
    app.add_middleware(CORSMiddleware,allow_origins=['http://127.0.0.1:5173','http://localhost:5173'],allow_methods=['*'],allow_headers=['*'])
    def get_record(eid):
        try: return store.get(eid)
        except KeyError as error: raise HTTPException(404,str(error)) from error
    def execute(eid,req,search=False,cancel=None,queued=False):
        aa=[];bb=[];candidates=[]
        try:
            if queued:raise InterruptedError('Cancelled while queued')
            def progress(done,total):
                store.progress(eid,done,total);jobs.progress(eid,done,total)
            pair=lambda s,a,b:(aa.append(a),bb.append(b))
            result=discover(req,progress,cancel=cancel,on_pair=pair,on_candidate=candidates.append) if search else comparison(req,progress,cancel=cancel,on_pair=pair)
            store.finish(eid,result)
        except InterruptedError:
            if aa or candidates:
                if search:
                    seedlist=req.evaluation_seeds[:len(aa)]
                    action=bb[0]['intervention'] if bb else None
                    validation=paired_result(RunRequest(experiment_name=req.experiment_name,world=req.world,seeds=seedlist,intervention=action),aa,bb) if aa else {'configuration':{'intervention':None},'seeds':[],'baseline':[],'variant':[],'paired':[],'summary':{}}
                    result={'configuration':req.model_dump(),'results':candidates,'validation':validation,'incomplete':True,'selection_note':'Cancelled search; only completed candidates and validation pairs retained.'}
                else:result=paired_result(req.model_copy(update={'seeds':req.seeds[:len(aa)]}),aa,bb)
                result['incomplete']=True;result['requested_seeds']=req.seeds;store.finish(eid,result)
            with store.connect() as con:con.execute("UPDATE experiments SET experiment_status='cancelled',error='Incomplete: task cancelled or runtime budget exhausted' WHERE experiment_id=?",(eid,))
            raise
        except Exception as error:
            store.fail(eid,error);raise
    def enqueue(eid,req,search,budget):
        total=(req.max_experiments+1)*len(req.seeds)+2*len(req.evaluation_seeds) if search else len(req.seeds)
        try:jobs.submit(eid,total,budget,lambda cancel,queued:execute(eid,req,search,cancel,queued))
        except ValueError as error:
            store.fail(eid,error);raise HTTPException(429,str(error)) from error
    @app.get('/api/health')
    def health(): return {'status':'ok','mode':'deterministic','schema_version':1}
    @app.get('/api/environment')
    def env(): return runtime
    @app.get('/api/scenarios')
    def scenarios(): return {'fragile':preset('fragile'),'cascade':preset('cascade')}
    @app.post('/api/world/preview')
    def preview(req:SocialConfig): return initial_world(req.initial_seed,req)
    @app.post('/api/worlds',status_code=201)
    def save_world(req:WorldRequest):
        try:return worlds.save(req.name,req.configuration.model_dump(),req.parent_id)
        except KeyError as e:raise HTTPException(404,str(e)) from e
    @app.get('/api/worlds')
    def list_worlds():return {'worlds':[r|({'task':jobs.get(r['world_id'])} if jobs.get(r['world_id']) else {}) for r in worlds.list()]}
    @app.get('/api/worlds/{wid}')
    def get_world(wid:str):
        try:return worlds.get(wid)|({'task':jobs.get(wid)} if jobs.get(wid) else {})
        except KeyError as e:raise HTTPException(404,str(e)) from e
    @app.post('/api/studies')
    def run_study(req:StudyRequest):
        result=study(req)
        # Study artifacts have their own immutable catalog; keep experiment schema/Phase 2A contract.
        saved=worlds.save(req.experiment_name,{'study_request':req.model_dump(),'result':result,'environment':runtime})
        return saved
    @app.post('/api/studies/jobs',status_code=202)
    def study_job(req:StudyRequest,max_seconds:int=Query(600,ge=1,le=3600)):
        saved=worlds.save(req.experiment_name,{'study_request':req.model_dump(),'result':None,'environment':runtime,'state':'QUEUED'})
        eid=saved['world_id'];total=(1 if req.kind=='ablation' else len(req.values)*len(req.second_values))*len(req.seeds)
        config=dict(saved['configuration'])
        def persist(result,state,error=None):
            import json
            config.update(result=result,state=state,error=error)
            with worlds.connect() as con:con.execute('UPDATE worlds SET configuration=? WHERE world_id=?',(json.dumps(config),eid))
        def work(cancel,queued):
            partial=None
            def retain(result):
                nonlocal partial
                partial=result;persist(result,'RUNNING')
            try:
                if queued:raise InterruptedError()
                persist(None,'RUNNING')
                result=study(req,lambda done,total:jobs.progress(eid,done,total),cancel,retain)
                persist(result,'COMPLETED')
            except InterruptedError:persist(partial,'CANCELLED');raise
            except Exception as error:persist(partial,'FAILED',str(error));raise
        try:jobs.submit(eid,total,max_seconds,work)
        except ValueError as error:persist(None,'FAILED',str(error));raise HTTPException(429,str(error)) from error
        return worlds.get(eid)|{'task':jobs.get(eid)}
    @app.post('/api/decisions/demo')
    def decisions_demo(req:DecisionRun):
        if req.world.decision_mode=='external':
            raise HTTPException(422,'Use explicitly enabled, budgeted /api/llm/pilots for real API requests')
        else:provider=DecisionProvider('mock',req.provider)
        run=simulate_social(req.seed,req.world,provider=provider)
        replay=simulate_social(req.seed,req.world,tape=run['decisions'])
        equal=all(run[k]==replay[k] for k in ['snapshots','series','events','decisions','transmission_paths'])
        result={'run':run,'replay_identical':equal,'provider_configuration':req.provider.model_dump(),
                'note':'Recorded decision replay; this does not claim fresh model calls reproduce outputs.'}
        saved=worlds.save('Decision tape / '+req.world.decision_mode,{'decision_demo':result,'environment':runtime})
        return result|{'world_id':saved['world_id']}
    @app.get('/api/llm/status')
    def llm_status():
        cfg=settings();usage=ledger.totals()
        return {'configuration':cfg,'usage':usage,'remaining_cny':max(0,10-usage['cost_cny']),
                'real_ready':cfg['enabled'] and cfg['price_verified'] and not usage['input_target_exceeded'],
                'note':'Software estimate/reservation is not a provider-enforced billing cap.'}
    @app.post('/api/llm/pilots',status_code=202)
    def create_pilot(req:PilotRequest):
        cfg=settings();usage=ledger.totals()
        if req.mode=='real':
            if not req.enable_real or not cfg['enabled']:raise HTTPException(422,'Real API must be explicitly enabled in browser and server')
            if not cfg['price_verified']:raise HTTPException(422,'Account price unverified; bulk paid experiment blocked')
            if usage['input_target_exceeded']:raise HTTPException(422,'Provider-reported input exceeded target; paid requests blocked pending operator review')
            expected=24*req.seed_count
            cost=expected*(1500*cfg['input_cny_per_million']+256*cfg['output_cny_per_million'])/1e6
            if usage['calls']+expected>125 or usage['cost_cny']+cost>10:raise HTTPException(422,'Preflight global pilot budget insufficient')
        config=pilot_configuration(req);eid=store.create(config,'llm-pilot');partial=None
        def retain(data):
            nonlocal partial
            partial=data
        def work(cancel,queued):
            try:
                if queued:raise InterruptedError('Cancelled while queued')
                def progress(done,total):store.progress(eid,done,total);jobs.progress(eid,done,total)
                data=run_pilot(req,ledger,eid,cancel,progress,retain);store.finish(eid,data)
            except InterruptedError:
                if partial:store.finish(eid,partial)
                with store.connect() as con:con.execute("UPDATE experiments SET experiment_status='cancelled',error='Incomplete pilot: cancelled' WHERE experiment_id=?",(eid,))
                raise
            except Exception as error:
                if partial:store.finish(eid,partial)
                store.fail(eid,error);raise
        try:jobs.submit(eid,req.seed_count*8,1800,work)
        except ValueError as error:store.fail(eid,error);raise HTTPException(429,str(error)) from error
        return store.summary(eid)
    @app.post('/api/llm/pilots/{eid}/replay')
    def pilot_replay(eid:str):
        record=get_record(eid)
        if record['kind']!='llm-pilot' or not record['result']:raise HTTPException(422,'Completed pilot trajectory required')
        if record['engine_version']!=engine_for(record['world_config']):raise HTTPException(409,'Engine version differs')
        recorded_env=record['configuration'].get('environment')
        if recorded_env and recorded_env['fingerprint']!=runtime['fingerprint']:raise HTTPException(409,'Dependency environment differs')
        try:return replay_result(record['result'])
        except ValueError as error:raise HTTPException(422,str(error)) from error
    @app.get('/api/world')
    def world(seed:int=Query(42,ge=0,le=2147483647)): return initial_world(seed)
    @app.post('/api/experiment')
    def experiment(req:RunRequest):
        if getattr(req.world,'decision_mode','rule')=='external':raise HTTPException(422,'External model calls require explicit decisions/demo provider configuration.')
        try: return comparison(req)
        except ValueError as error: raise HTTPException(422,str(error)) from error
    @app.post('/api/experiments',status_code=202)
    def create_experiment(req:RunRequest,light:bool=False,max_seconds:int=Query(600,ge=1,le=3600)):
        if getattr(req.world,'decision_mode','rule')=='external':raise HTTPException(422,'External model calls use explicit decisions/demo only; recorded tape replay is distinct from resampling.')
        eid=store.create(req.model_dump()|({'environment':runtime} if engine_for(req.world)!='0.2.0' else {}))
        enqueue(eid,req,False,max_seconds)
        return store.summary(eid) if light else get_record(eid)
    @app.post('/api/search/jobs',status_code=202)
    def create_search(req:SearchRequest,light:bool=False,max_seconds:int=Query(600,ge=1,le=3600)):
        if getattr(req.world,'decision_mode','rule')=='external':raise HTTPException(422,'External calls unsupported in search')
        eid=store.create(req.model_dump()|({'environment':runtime} if engine_for(req.world)!='0.2.0' else {}),'search')
        enqueue(eid,req,True,max_seconds)
        return store.summary(eid) if light else get_record(eid)
    @app.get('/api/experiments')
    def experiments(): return {'experiments':store.list()}
    @app.get('/api/experiments/{eid}')
    def get_experiment(eid:str): return JSONResponse(get_record(eid))
    @app.get('/api/experiments/{eid}/summary')
    def summary(eid:str):
        try:return store.summary(eid)|{'task':jobs.get(eid)}
        except KeyError as e:raise HTTPException(404,str(e)) from e
    @app.get('/api/experiments/{eid}/trajectory')
    def trajectory(eid:str,seed:int,branch:str=Query('baseline',pattern='^(baseline|variant)$'),start:int=Query(0,ge=0,le=100),end:int=Query(9,ge=0,le=100),agent:str|None=None,view:str=Query('full',pattern='^(full|network)$')):
        if end<start or end-start>19:raise HTTPException(422,'Interval must contain at most 20 rounds')
        try:
            store.summary(eid)
            data=store.trajectories.interval(eid,seed,branch,start,end,agent)
            if view=='network':
                for frame in data.get('snapshots',[]):
                    for a in frame['agents']:a.pop('memory',None)
            return data
        except KeyError as e:raise HTTPException(404,str(e)) from e
    @app.post('/api/experiments/{eid}/cancel')
    def cancel_experiment(eid:str):
        try:return jobs.cancel(eid)
        except KeyError as e:raise HTTPException(404,str(e)) from e
    @app.get('/api/experiments/{eid}/light-export')
    def light_export(eid:str):
        record=summary(eid)
        return JSONResponse(record,headers={'Content-Disposition':f'attachment; filename="butterflylab-{eid}-summary.json"'})
    @app.post('/api/experiments/{eid}/archive',status_code=202)
    def archive_start(eid:str):
        record=summary(eid)
        if not record['result']:raise HTTPException(409,'No completed trajectory available')
        import uuid
        aid=str(uuid.uuid4())
        try:jobs.submit(aid,1,3600,lambda cancel,queued:store.trajectories.archive(eid,record) if not cancel() else None)
        except ValueError as e:raise HTTPException(429,str(e)) from e
        return {'job_id':aid,'download_url':f'/api/experiments/{eid}/archive-download?job_id={aid}'}
    @app.get('/api/jobs/{jid}')
    def job_status(jid:str):
        result=jobs.get(jid)
        if not result:raise HTTPException(404,'Task not found')
        return result
    @app.get('/api/experiments/{eid}/archive-download')
    def archive_download(eid:str,job_id:str):
        state=job_status(job_id)
        if state['state']!='COMPLETED':raise HTTPException(409,'Archive not ready')
        path=store.trajectories.folder(eid)/'archive.zip'
        if not path.exists():raise HTTPException(404,'Archive not found')
        return FileResponse(path,media_type='application/zip',filename=f'butterflylab-{eid}.zip')
    @app.get('/api/experiments/{eid}/export')
    def export_experiment(eid:str):
        record=get_record(eid)
        return JSONResponse(record,headers={'Content-Disposition':f'attachment; filename="butterflylab-{record["experiment_id"]}.json"'})
    @app.post('/api/experiments/{eid}/reproduce')
    def reproduce(eid:str):
        record=get_record(eid)
        if record['experiment_status']!='completed': raise HTTPException(409,'Only completed experiments can be reproduced.')
        if record['engine_version']!=engine_for(record['world_config']): raise HTTPException(409,'Engine version differs; exact replay cannot be guaranteed.')
        config=dict(record['configuration']);recorded_env=config.pop('environment',None)
        if recorded_env and recorded_env['fingerprint']!=runtime['fingerprint']:raise HTTPException(409,'Dependency environment differs; exact recomputation rejected.')
        if record['kind']=='llm-pilot':return replay_result(record['result'])|{'engine_version':record['engine_version']}
        result=replay_cell(record['configuration']) if record['kind']=='scan_cell' else discover(SearchRequest(**config)) if record['kind']=='search' else comparison(RunRequest(**config))
        return {'identical':result==record['result'],'engine_version':record['engine_version'],
                'compared':'All configurations, trajectories, snapshots, logs, metrics and summaries; metadata timestamps excluded.'}
    @app.patch('/api/experiments/{eid}')
    def save(eid:str,req:NameRequest,light:bool=False):
        try:
            if light:
                with store.connect() as con:
                    if not con.execute('UPDATE experiments SET experiment_name=? WHERE experiment_id=?',(req.experiment_name,eid)).rowcount:raise KeyError('Experiment not found')
                return store.summary(eid)
            return store.rename(eid,req.experiment_name)
        except KeyError as error: raise HTTPException(404,str(error)) from error
    @app.delete('/api/experiments/{eid}')
    def delete(eid:str):
        try: store.delete(eid)
        except KeyError as error: raise HTTPException(404,str(error)) from error
        except ValueError as error: raise HTTPException(409,str(error)) from error
        return {'deleted':eid}
    @app.get('/api/search')
    def legacy_search(max_experiments:int=Query(12,ge=1,le=24)):
        return {'results':search_interventions(max_experiments)}
    @app.post('/api/simulate')
    def simulate_route(req:SimRequest):
        try: return simulate(req.seed,WorldConfig(rounds=req.rounds),req.intervention)
        except (ValueError,IndexError) as error: raise HTTPException(422,str(error)) from error
    @app.get('/api/labs/parameters')
    def parameters():
        return {'algorithm_version':ALGORITHM_VERSION,'parameters':{p:{'description':p,'range':({'trust_speed':[0,.5],'incentive':[0,1],'transmission':[0,1],'opinion_speed':[0,1],'magnitude':[-50,50],'centrality':[0,1],'degree':[2,98]})[p]} for p in PARAMETERS}}
    @app.post('/api/labs',status_code=202)
    def create_lab(req:ExplorationRequest):
        eid=labs.create(req)
        total=2*len(req.values)*(len(req.second_values) if req.second_parameter else 1)*len(req.seeds)
        if req.mode=='criticality':total+=2*req.refinement_points*len(req.seeds)+4*len(req.validation_seeds)*len(req.scales)*len(req.topologies)
        if req.mode=='robustness':total+=2*len(req.values)*len(req.validation_seeds)
        def work(cancel,queued):
            if queued:labs.save(eid,labs.get(eid)['result'],'CANCELLED');raise InterruptedError()
            explore(req,eid,labs,store,cancel,lambda done:jobs.progress(eid,done,total))
        try:jobs.submit(eid,total,req.max_seconds,work)
        except ValueError as e:
            labs.save(eid,labs.get(eid)['result'],'FAILED',str(e));raise HTTPException(429,str(e)) from e
        return labs.get(eid)|{'task':jobs.get(eid)}
    @app.get('/api/labs')
    def list_labs():return {'labs':labs.list()}
    @app.get('/api/labs/{eid}')
    def get_lab(eid:str):
        try:return labs.get(eid)|{'task':jobs.get(eid)}
        except KeyError as e:raise HTTPException(404,str(e)) from e
    @app.post('/api/labs/{eid}/cancel')
    def cancel_lab(eid:str):return cancel_experiment(eid)
    @app.get('/api/labs/{eid}/export')
    def export_lab(eid:str):return JSONResponse(get_lab(eid),headers={'Content-Disposition':f'attachment; filename="scan-{eid}.json"'})
    @app.post('/api/labs/{eid}/archive',status_code=202)
    def archive_lab(eid:str):
        record=get_lab(eid)
        if record['state'] not in ('COMPLETED','CANCELLED'):raise HTTPException(409,'Wait for scan to stop')
        import uuid,zipfile,json
        aid=str(uuid.uuid4());path=store.trajectories.root/(eid+'-scan.zip')
        def work(cancel,queued):
            with zipfile.ZipFile(path.with_suffix('.tmp'),'w',compression=zipfile.ZIP_STORED) as output:
                output.writestr('scan.json',json.dumps(record))
                cells=list(record['result']['cells'])
                for v in record['result']['validation']:cells.extend(v.get('cells',[v]))
                partial=record['result'].get('partial_cell')
                if partial and partial['completed_seeds']:cells.append(partial)
                for i,c in enumerate(cells):
                    if cancel():raise InterruptedError()
                    cid=c['experiment_id'];child=store.summary(cid)
                    output.write(store.trajectories.archive(cid,child),cid+'.zip');jobs.progress(aid,i+1,len(cells))
            path.with_suffix('.tmp').replace(path)
        try:jobs.submit(aid,1,3600,work)
        except ValueError as e:raise HTTPException(429,str(e)) from e
        return {'job_id':aid,'download_url':f'/api/labs/{eid}/archive-download?job_id={aid}'}
    @app.get('/api/labs/{eid}/archive-download')
    def download_lab(eid:str,job_id:str):
        if job_status(job_id)['state']!='COMPLETED':raise HTTPException(409,'Archive not ready')
        path=store.trajectories.root/(eid+'-scan.zip')
        if not path.exists():raise HTTPException(404,'Archive not found')
        return FileResponse(path,media_type='application/zip',filename=f'scan-{eid}.zip')
    return app

app=create_app()
