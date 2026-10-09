"""SQLite experiment metadata and run artifacts, with versioned migrations."""
import json, os, sqlite3, uuid
from pathlib import Path
from datetime import datetime, timezone
from contextlib import contextmanager
from .simulation import ENGINE_VERSION
from .social_config import engine_for

def now(): return datetime.now(timezone.utc).isoformat()

class Store:
    def __init__(self,path=None):
        self.path=Path(path or os.environ.get('BUTTERFLYLAB_DB',Path(__file__).resolve().parent.parent/'data'/'experiments.sqlite3'))
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.migrate()
        from .trajectories import Trajectories
        self.trajectories=Trajectories(self.path.parent/(self.path.stem+'-trajectories'))
    @contextmanager
    def connect(self):
        con=sqlite3.connect(self.path,timeout=30); con.row_factory=sqlite3.Row
        con.execute('PRAGMA foreign_keys=ON')
        try:
            with con:
                yield con
        finally:
            con.close()
    def migrate(self):
        with self.connect() as con:
            version=con.execute('PRAGMA user_version').fetchone()[0]
            if version>1: raise RuntimeError('Database schema is newer than this engine.')
            if version<1:
                con.executescript('''
                CREATE TABLE IF NOT EXISTS experiments (
                  experiment_id TEXT PRIMARY KEY, experiment_name TEXT NOT NULL,
                  created_at TEXT NOT NULL, updated_at TEXT NOT NULL, engine_version TEXT NOT NULL,
                  world_config TEXT NOT NULL, baseline_config TEXT NOT NULL, intervention_config TEXT,
                  random_seeds TEXT NOT NULL, experiment_status TEXT NOT NULL,
                  experiment_summary TEXT NOT NULL, configuration TEXT NOT NULL, kind TEXT NOT NULL,
                  progress_completed INTEGER NOT NULL DEFAULT 0, progress_total INTEGER NOT NULL DEFAULT 0,
                  error TEXT);
                CREATE TABLE IF NOT EXISTS artifacts (
                  experiment_id TEXT PRIMARY KEY REFERENCES experiments(experiment_id) ON DELETE CASCADE,
                  metric_results TEXT NOT NULL, payload TEXT NOT NULL);
                PRAGMA user_version=1;
                ''')
    def create(self,configuration,kind='comparison'):
        eid=str(uuid.uuid4()); stamp=now(); world=configuration['world']
        with self.connect() as con:
            con.execute('INSERT INTO experiments (experiment_id,experiment_name,created_at,updated_at,engine_version,world_config,baseline_config,intervention_config,random_seeds,experiment_status,experiment_summary,configuration,kind) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
              (eid,configuration['experiment_name'],stamp,stamp,engine_for(world),json.dumps(world),json.dumps({'world':world,'intervention':None}),json.dumps(configuration.get('intervention')),json.dumps(configuration['seeds']),'running','{}',json.dumps(configuration),kind))
        return eid
    def progress(self,eid,completed,total):
        with self.connect() as con: con.execute('UPDATE experiments SET progress_completed=?,progress_total=?,updated_at=? WHERE experiment_id=?',(completed,total,now(),eid))
    def finish(self,eid,payload):
        data=payload.get('validation',payload)
        compact=self.trajectories.save(eid,payload)
        with self.connect() as con:
            metrics={'paired':data['paired'],'summary':data['summary'],
                     'time_series':[{'seed':s,'baseline':a['series'],'intervention':b['series']} for s,a,b in zip(data['seeds'],data['baseline'],data['variant'])]}
            con.execute('INSERT INTO artifacts VALUES (?,?,?)',(eid,json.dumps(metrics,allow_nan=False),json.dumps({'trajectory_format':1},allow_nan=False)))
            con.execute("UPDATE experiments SET experiment_status='completed',experiment_summary=?,updated_at=? WHERE experiment_id=?",(json.dumps(data['summary']),now(),eid))
            con.execute('UPDATE experiments SET intervention_config=? WHERE experiment_id=?',(json.dumps(data['configuration']['intervention']),eid))
    def fail(self,eid,error):
        with self.connect() as con: con.execute("UPDATE experiments SET experiment_status='failed',error=?,updated_at=? WHERE experiment_id=?",(str(error),now(),eid))
    def recover(self):
        with self.connect() as con: con.execute("UPDATE experiments SET experiment_status='failed',error='Server stopped before completion; rerun this configuration.',updated_at=? WHERE experiment_status='running'",(now(),))
    def decode(self,row):
        if row is None: raise KeyError('Experiment not found')
        result=dict(row)
        for key in ['world_config','baseline_config','intervention_config','random_seeds','experiment_summary','configuration']:
            result[key]=json.loads(result[key])
        return result
    def list(self):
        with self.connect() as con: return [self.decode(r) for r in con.execute('SELECT * FROM experiments ORDER BY created_at DESC')]
    def get(self,eid):
        with self.connect() as con:
            result=self.decode(con.execute('SELECT * FROM experiments WHERE experiment_id=?',(eid,)).fetchone())
            row=con.execute('SELECT metric_results,payload FROM artifacts WHERE experiment_id=?',(eid,)).fetchone()
            result['metric_results']=json.loads(row[0]) if row else None
            result['result']=json.loads(row[1]) if row else None
            if result['result']=={'trajectory_format':1}:result['result']=self.trajectories.restore(eid)
            return result
    def summary(self,eid):
        with self.connect() as con:
            record=self.decode(con.execute('SELECT * FROM experiments WHERE experiment_id=?',(eid,)).fetchone())
        if not self.trajectories.exists(eid):
            full=self.get(eid)
            if not full['result']:return full
            self.trajectories.save(eid,full['result'])
        record['result']=self.trajectories.summary(eid)
        record['metric_results']=None
        record['trajectory_format']=1
        return record
    def rename(self,eid,name):
        with self.connect() as con:
            if not con.execute('UPDATE experiments SET experiment_name=?,updated_at=? WHERE experiment_id=?',(name,now(),eid)).rowcount: raise KeyError('Experiment not found')
        return self.get(eid)
    def delete(self,eid):
        with self.connect() as con:
            row=con.execute('SELECT experiment_status FROM experiments WHERE experiment_id=?',(eid,)).fetchone()
            if row is None: raise KeyError('Experiment not found')
            if row[0]=='running': raise ValueError('Wait for the running experiment before deleting it.')
            con.execute('DELETE FROM experiments WHERE experiment_id=?',(eid,))
