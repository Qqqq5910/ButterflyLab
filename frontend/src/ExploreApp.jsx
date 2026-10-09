import React,{useState,useEffect,lazy,Suspense,useRef} from 'react';
import {Activity,ArrowRight,Play,Pause,Share2,RotateCcw,Download} from 'lucide-react';
import Network from './Network.jsx';
import {MODE,TemplateInterpreter,restoreShare,shareURL,narrative} from './explore-core.mjs';
const Research=lazy(()=>import('./ResearchApp.jsx'));
const MetricPlot=lazy(()=>import('./MetricPlot.jsx'));
const interpreter=new TemplateInterpreter();
const cache=new Map();
const STATIC=MODE==='PUBLIC_STATIC_DEMO';
async function json(path,options) {
  const response=await fetch(path,options);if(!response.ok)throw new Error(`Unable to load (${response.status}). Retry or run locally.`);return response.json();
}
async function checked(meta) {
  if(cache.has(meta.file))return cache.get(meta.file);
  const promise=(async()=>{
    const response=await fetch(import.meta.env.BASE_URL+'demo/'+meta.file);
    if(!response.ok)throw new Error('Replay file unavailable. Please retry.');
    const data=await response.arrayBuffer();
    const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',data)),b=>b.toString(16).padStart(2,'0')).join('');
    const gzip=new Uint8Array(data)[0]===31&&new Uint8Array(data)[1]===139;
    if(digest!==(gzip?meta.sha256:meta.raw_sha256))throw new Error('Replay checksum mismatch. Reload before continuing.');
    const stream=new Blob([data]).stream();
    const raw=gzip?stream.pipeThrough(new DecompressionStream('gzip')):stream;
    return JSON.parse(await new Response(raw).text());
  })();cache.set(meta.file,promise);try{return await promise;}catch(e){cache.delete(meta.file);throw e;}
}
export default function App() {
  const [mode,setMode]=useState('explore'),[scenarios,setScenarios]=useState([]),[env,setEnv]=useState(null);
  const [question,setQuestion]=useState('What if information transmission probability doubles?'),[intent,setIntent]=useState(null);
  const [result,setResult]=useState(null),[record,setRecord]=useState(null),[trajectory,setTrajectory]=useState(null);
  const [seed,setSeed]=useState(42),[round,setRound]=useState(0),[playing,setPlaying]=useState(false),[speed,setSpeed]=useState(1),[diff,setDiff]=useState(true);
  const [busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState(''),[hero,setHero]=useState(null);
  const restore=useRef(null),runToken=useRef(0);
  const act=async fn=>{setError('');setBusy(true);try{await fn();}catch(e){setError(e.message);}finally{setBusy(false);}};
  const loadCatalog=()=>act(async()=>{
    const data=await json(STATIC?import.meta.env.BASE_URL+'demo/manifest.json':'/api/explore/scenarios');
    setScenarios(data.scenarios);setEnv(data.environment);
    restore.current=restoreShare(location.search,data.scenarios);
    if(STATIC)setHero(await checked(data.scenarios[0].preview));
    else setHero(await json('/api/world/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data.scenarios[0].world)}));
  });
  useEffect(()=>{loadCatalog();},[]);
  useEffect(()=>{if(!restore.current||!scenarios.length)return;const saved=restore.current;restore.current=null;const picked=select(saved.scenario);open(picked,saved.seed,saved.round);},[scenarios]);
  const select=s=>{const parsed=interpreter.interpret(s.question,scenarios);setQuestion(s.question);setIntent(parsed);setError(parsed.error||'');return parsed;};
  const parse=()=>{const parsed=interpreter.interpret(question,scenarios);setIntent(parsed.error?null:parsed);setError(parsed.error||'');};
  const open=(chosen=intent,newSeed=42,newRound=0)=>act(async()=>{
    if(!chosen||chosen.error)return;
    if(STATIC&&!chosen.exact)throw new Error('This exact configuration is not precomputed. Choose a preset below or use Local Research for live simulation. 不会用其他结果替代。');
    ++runToken.current;setPlaying(false);setTrajectory(null);setResult(null);setNotice('');
    if(STATIC){const data=await checked(chosen.scenario.summary);setRecord(null);setResult(data);}
    else {const data=await json('/api/explore/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(chosen.request)});setRecord(data);setResult({...data.result,scenario:{...chosen.scenario,id:chosen.scenario_id,change:chosen.change}});setEnv(data.configuration.environment);}
    setSeed(newSeed);setRound(newRound);
    setTimeout(()=>document.getElementById('parallel')?.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'}),60);
  });
  const block=Math.floor(round/10)*10;
  useEffect(()=>{
    if(!result)return;let alive=true;setTrajectory(null);
    const token=runToken.current;
    (async()=>{
      if(STATIC)return checked(result.trajectory_files[String(seed)]);
      const parts=await Promise.all(['baseline','variant'].map(branch=>json(`/api/experiments/${record.experiment_id}/trajectory?seed=${seed}&branch=${branch}&start=${block}&end=${Math.min(result.configuration.world.rounds,block+9)}`)));
      return {baseline:parts[0],variant:parts[1]};
    })().then(data=>{if(alive&&token===runToken.current)setTrajectory(data);}).catch(e=>{if(alive)setError(e.message);});
    return()=>{alive=false;};
  },[result,seed,STATIC?0:block]);
  const total=result?.configuration.world.rounds||50;
  const frame=branch=>{
    const snap=trajectory?.[branch].snapshots.find(s=>s.round===round);
    return snap?{...snap,config:result.configuration.world}:null;
  };
  const a=frame('baseline'),b=frame('variant');
  useEffect(()=>{if(!playing||!a||!b)return;const timer=setInterval(()=>setRound(r=>{if(r>=total){setPlaying(false);return total;}return r+1;}),400/speed);return()=>clearInterval(timer);},[playing,speed,total,!!a,!!b]);
  const share=()=>act(async()=>{const url=shareURL(location.href,result.scenario.id,seed,round);history.replaceState(null,'',url);try{await navigator.clipboard.writeText(url);setNotice('Share link copied.');}catch{setNotice(url);}});
  const metric=result?.scenario.metric||'coverage',index=result?.seeds.indexOf(seed)||0;
  const seriesA=result?.baseline[index].series||[],seriesB=result?.variant[index].series||[];
  const differences=diff&&a&&b?a.agents.filter((node,i)=>['informed','action','resource','opinion'].some(k=>node[k]!==b.agents[i][k])).map(node=>node.id):[];
  const activeNode=result?.selected_nodes[String(seed)]?.agent??result?.configuration.intervention?.agent;
  const download=()=>{const blob=new Blob([JSON.stringify(result,null,2)],{type:'application/json'});const link=document.createElement('a');link.href=URL.createObjectURL(blob);link.download='butterflylab-explore-summary.json';link.click();setTimeout(()=>URL.revokeObjectURL(link.href),1000);};
  return <><div className="mode-bar"><a className="explore-brand" href={import.meta.env.BASE_URL}><Activity size={23}/> ButterflyLab</a><div><button aria-pressed={mode==='explore'} onClick={()=>setMode('explore')}>Explore Mode</button><button aria-pressed={mode==='research'} onClick={()=>setMode('research')}>Research Mode</button><a href="https://github.com/Qqqq5910/ButterflyLab">GitHub <ArrowRight size={14}/></a></div></div>
    {mode==='research'?(STATIC?<div className="research-download"><h1>Research on your own machine.</h1><p>The complete research console runs locally: World Studio, saved experiments, sensitivity scans, Rule / Mock / optional Real decisions and exact reproduction.</p><p>The public demo has no Python backend. Download the repository and run the free launcher.</p><code>powershell -ExecutionPolicy Bypass -File scripts/free-demo.ps1</code><p><a href="https://github.com/Qqqq5910/ButterflyLab#run-locally">Open local setup instructions</a></p><button onClick={()=>setMode('explore')}>Return to Explore</button></div>:<Suspense fallback={<p>Loading Research Mode…</p>}><Research Network={Network}/></Suspense>):<main className="explore">
      <section className="explore-hero"><div className="hero-copy"><h1>Change One Thing.<br/><span>Watch Two Worlds Diverge.</span></h1><p className="hero-chinese">只改变一件事，看看两个世界会走向哪里。</p><p>Explore how small changes shape the evolution of artificial societies.</p><form onSubmit={e=>{e.preventDefault();parse();}}><label htmlFor="question">What would you change? / 你想改变什么？</label><textarea id="question" value={question} onChange={e=>setQuestion(e.target.value)} maxLength={300}/><button className="explore-primary" disabled={busy||!scenarios.length}>Explore a World <ArrowRight size={18}/></button></form><p className="free-note">No API Key Required · Synthetic Simulation<br/>{STATIC?'Interactive Replay of Real Simulations':'Local Research · Live Rule Simulation'}</p></div><div className="hero-world"><Network world={hero}/><div>50 agents · shared initial network · five paired seeds</div></div></section>
      {error&&<div role="alert" className="explore-error">{error} <button onClick={()=>result?setResult({...result}):loadCatalog()}>Retry loading</button></div>}
      <section className="scenario-list" aria-label="Example questions">{scenarios.map(s=><button key={s.id} onClick={()=>select(s)}><h2>{s.title}</h2><p>{s.question}</p><span>{s.question_zh}</span><ArrowRight size={18}/></button>)}</section>
      {intent&&!intent.error&&<section className="confirmation"><h2>One change. Two matched worlds.</h2><p>{intent.change}</p><div className="conditions"><div><strong>World A</strong><p>{intent.request.variant_world?`${Object.keys(intent.request.world).find(k=>intent.request.world[k]!==intent.request.variant_world[k])}: ${intent.request.world[Object.keys(intent.request.world).find(k=>intent.request.world[k]!==intent.request.variant_world[k])]}`:'No local intervention'}</p></div><div><strong>World B</strong><p>{intent.request.variant_world?intent.change:`${intent.request.intervention.kind} ${intent.request.intervention.magnitude}; ${intent.request.centrality?'initial-degree selected node':`agent index ${intent.request.intervention.agent}`}`}</p></div></div><p>{intent.note}</p><p>50 agents · seeds {intent.request.seeds.join(', ')} · same initial agents and ties</p>{STATIC&&!intent.exact?<p role="status">No exact precomputed replay. Choose one of the presets or run locally.</p>:<button className="explore-primary" onClick={()=>open()} disabled={busy}>{busy?'Preparing real results…':'Explore Parallel Worlds'} <ArrowRight size={18}/></button>}</section>}
      {result&&<section id="parallel" className="parallel"><div className="explore-section-head"><div><h2>{result.scenario.title}</h2><p>{result.scenario.change}</p></div><div className="explore-actions"><button disabled={!intent?.exact} onClick={share}><Share2 size={16}/> Share Experiment</button><button onClick={download}><Download size={16}/> Summary</button></div></div>
        <div className="parallel-worlds">{['baseline','variant'].map((branch,i)=><div className="parallel-world" key={branch}><div className="world-label"><strong>World {i?'B':'A'}</strong><span>{i?'Changed condition':'Baseline'} · seed {seed} · round {round}</span></div><Network world={i?b:a} transmissions={trajectory?.[branch].transmission_paths?.filter(p=>p.round===round)||[]} highlight={!!i&&activeNode!=null} interventionAgent={activeNode} differences={differences} detailKey={`${seed}:${round}`}/></div>)}</div>
        <div className="playback"><button aria-label={playing?'Pause':'Play'} onClick={()=>{if(round===total)setRound(0);setPlaying(!playing);}} disabled={!trajectory}>{playing?<Pause size={18}/>:<Play size={18}/>}</button><button aria-label="Restart" onClick={()=>{setPlaying(false);setRound(0);}}><RotateCcw size={18}/></button><label>Speed <select value={speed} onChange={e=>setSpeed(Number(e.target.value))}><option value={.5}>0.5×</option><option value={1}>1×</option><option value={2}>2×</option></select></label><label>Seed <select value={seed} onChange={e=>{setPlaying(false);setSeed(Number(e.target.value));}}>{result.seeds.map(s=><option key={s}>{s}</option>)}</select></label><label><input type="checkbox" checked={diff} onChange={e=>setDiff(e.target.checked)}/> Highlight differences</label><b>Round {round} / {total}</b></div><input className="explore-seek" aria-label="Simulation round" type="range" min={0} max={total} value={round} onChange={e=>{setPlaying(false);setRound(Number(e.target.value));}}/>
        <p className="network-key">Mint: cooperating · Coral: competing · Blue outline: informed · Blue edges: transmissions this round · Amber ring: changed state between worlds</p>
        <div className="outcome"><h2>What happened?</h2><p>{narrative(result.summary,metric)}</p><p>The displayed network is seed {seed}, selected by you; it does not replace the five-seed result. Initial degree selection is performed before simulation, never chosen by outcome.</p></div>
        <Suspense fallback={<p>Loading metric plots…</p>}><div className="explore-plots">{[metric,...(metric==='coverage'?['mean_trust']:['resource_mean'])].map(m=><MetricPlot key={m} a={seriesA} b={seriesB} metric={m} round={round} definition={result.metric_definitions[m]}/>)}</div></Suspense>
        <div className="round-values"><span>At round {round}: A {seriesA[round]?.[metric].toFixed(4)} / B {seriesB[round]?.[metric].toFixed(4)} / B−A {((seriesB[round]?.[metric]||0)-(seriesA[round]?.[metric]||0)).toFixed(4)}</span><span>Final selected seed: A {seriesA[total]?.[metric].toFixed(4)} / B {seriesB[total]?.[metric].toFixed(4)}</span></div>
        <details className="research-details"><summary>Research Details · configurations, seeds, uncertainty and engine</summary><p>Engine {result.engine_version} · template interpreter (no LLM) · paired bootstrap, 2,000 resamples. Five seeds provide descriptive uncertainty; no significance or real-world causality claim.</p><p>Mean B−A {result.summary[metric].mean.toFixed(4)} · SD {result.summary[metric].std?.toFixed(4)} · descriptive 95% bootstrap interval [{result.summary[metric].ci95?.map(v=>v.toFixed(4)).join(', ')}]</p><div className="table-scroll"><table><thead><tr><th>Seed</th><th>A final</th><th>B final</th><th>B−A</th><th>Selected node</th></tr></thead><tbody>{result.paired.map(p=><tr key={p.seed}><td>{p.seed}</td><td>{p.baseline[metric].toFixed(4)}</td><td>{p.intervention[metric].toFixed(4)}</td><td>{p.delta[metric].toFixed(4)}</td><td>{result.selected_nodes[String(p.seed)]?JSON.stringify(result.selected_nodes[String(p.seed)]):'—'}</td></tr>)}</tbody></table></div><p>{result.metric_definitions[metric].formula} · {result.metric_definitions[metric].note}</p><pre>{JSON.stringify({configuration:result.configuration,engine:result.engine_version,environment:env},null,2)}</pre><h3>Recorded events · round {round}</h3>{['baseline','variant'].map(branch=><div key={branch}><strong>{branch}</strong><ul>{trajectory?.[branch].events?.filter(e=>e.round===round).slice(0,8).map((e,i)=><li key={i}>{e.type}: {e.detail}</li>)}</ul></div>)}{record&&<p>Saved locally as {record.experiment_id}. Open it in Research Mode → Experiments to export or reproduce.</p>}</details>
      </section>}
      {notice&&<p role="status" className="explore-notice">{notice}</p>}<footer><p>Artificial societies, measured honestly. Different outcomes are possible; a small change may have no visible effect.</p><a href="https://github.com/Qqqq5910/ButterflyLab">Explore the source and reproduce these worlds <ArrowRight size={16}/></a></footer>
    </main>}</>;
}
