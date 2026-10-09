import React, { useEffect, useState } from 'react';
import { Play, Square, RotateCw, Download, ExternalLink } from 'lucide-react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

import { API } from './api';
const f=v=>Number(v||0).toFixed(4);
export default function LLMSociety({request,post,Network,onOpen,onSaved}) {
  const [mode,setMode]=useState('rule'),[count,setCount]=useState(5),[enabled,setEnabled]=useState(false);
  const [status,setStatus]=useState(null),[record,setRecord]=useState(null),[history,setHistory]=useState([]);
  const [error,setError]=useState(''),[busy,setBusy]=useState(false),[seedIndex,setSeedIndex]=useState(0),[round,setRound]=useState(8);
  const [frames,setFrames]=useState(null),[replay,setReplay]=useState('');
  const running=record?.experiment_status==='running';
  const refresh=async()=>{
    const [s,h]=await Promise.all([request('/llm/status'),request('/experiments')]);
    setStatus(s);setHistory(h.experiments.filter(r=>r.kind==='llm-pilot'));
  };
  const adopt=r=>{setRecord(r);setSeedIndex(0);setReplay('');localStorage.setItem('butterflylab.pilot',r.experiment_id)};
  useEffect(()=>{let alive=true; (async()=>{
    try{await refresh();const id=localStorage.getItem('butterflylab.pilot');if(id){const r=await request(`/experiments/${id}/summary`);if(alive)adopt(r)}}
    catch(e){if(alive)setError(e.message)}
  })();return()=>{alive=false}},[]);
  useEffect(()=>{
    if(!running)return;
    let alive=true;const timer=setInterval(async()=>{
      try{const r=await request(`/experiments/${record.experiment_id}/summary`);if(alive){setRecord(r);await refresh();if(r.experiment_status!=='running')onSaved()}}
      catch(e){if(alive)setError(e.message)}
    },700);return()=>{alive=false;clearInterval(timer)};
  },[record?.experiment_id,running]);
  const data=record?.result,a=data?.baseline?.[seedIndex],b=data?.variant?.[seedIndex];
  useEffect(()=>{
    let alive=true;setFrames(null);
    if(a)Promise.all(['baseline','variant'].map(branch=>request(`/experiments/${record.experiment_id}/trajectory?seed=${a.seed}&branch=${branch}&start=0&end=8&view=network`)))
      .then(([a,b])=>{if(alive)setFrames({a:a.snapshots,b:b.snapshots})}).catch(e=>{if(alive)setError(e.message)});
    return()=>{alive=false};
  },[record?.experiment_id,a?.seed]);
  const perform=async(fn)=>{setBusy(true);setError('');try{await fn()}catch(e){setError(e.message)}finally{setBusy(false)}};
  const usage=status?.usage,cfg=status?.configuration;
  const estimate=cfg?.price_verified?24*count*(1500*cfg.input_cny_per_million+256*cfg.output_cny_per_million)/1e6:null;
  const curve=a?.series.map((p,i)=>({round:p.round,Rule:p.coverage,Hybrid:b.series[i].coverage}))||[];
  const recordedMode=data?.pilot?.mode||record?.configuration?.pilot?.mode;
  return <section id="llm-society" className="llm-society">
    <div className="section-heading"><h2>LLM Society</h2><span className="seed">{record?.experiment_id||'Information Cascade'}</span></div>
    {error&&<p role="alert" className="error-banner">{error}</p>}
    <div className="lab-tabs" role="tablist" aria-label="LLM mode">{[['rule','Rule Only'],['mock','Mock LLM'],['real','Real LLM']].map(([id,label])=><button key={id} role="tab" aria-selected={mode===id} disabled={running} onClick={()=>{setMode(id);setEnabled(false)}}>{label}</button>)}</div>
    <div className="toolbar">
      <div className="field"><label htmlFor="pilot-seeds">Paired seeds</label><select id="pilot-seeds" value={count} disabled={running} onChange={e=>setCount(Number(e.target.value))}><option value="1">1 / pre-experiment</option><option value="5">5 / exploratory</option></select></div>
      <div className="field"><label htmlFor="pilot-history">Saved LLM comparisons</label><select id="pilot-history" value={record?.experiment_id||''} disabled={running||busy} onChange={e=>perform(async()=>adopt(await request(`/experiments/${e.target.value}/summary`)))}><option value="" disabled>Select experiment</option>{history.map(r=><option key={r.experiment_id} value={r.experiment_id}>{r.experiment_name} / {r.experiment_status}</option>)}</select></div>
      {mode==='real'&&<label className="pilot-consent"><input type="checkbox" checked={enabled} disabled={!status?.real_ready||running} onChange={e=>setEnabled(e.target.checked)}/>Enable paid API calls</label>}
      <button className="run" disabled={busy||running||!status||(mode==='real'&&(!enabled||!status?.real_ready))} onClick={()=>perform(async()=>{adopt(await request('/llm/pilots',post({mode,seed_count:count,enable_real:enabled,experiment_name:`Information Cascade / ${mode} / ${count} seeds`})));await refresh()})}><Play size={15}/>Run comparison</button>
      {running&&<button className="export" onClick={()=>perform(()=>request(`/experiments/${record.experiment_id}/cancel`,post({})))}><Square size={15}/>Stop experiment</button>}
    </div>
    <dl className="pilot-facts">
      <div><dt>Scenario</dt><dd>50 agents / small-world / 8 rounds</dd></div><div><dt>Hybrid selection</dt><dd>3 highest initial degree / ID tie-break</dd></div>
      <div><dt>Model</dt><dd>{cfg?.model||'gpt-5.6-luna'}</dd></div><div><dt>Paid requests</dt><dd>{mode==='real'?24*count:0} expected / {usage?.calls||0} used / 125 limit</dd></div>
      <div><dt>Price</dt><dd>{cfg?.price_verified?'Account rate verified':'价格未验证 / Price unverified'}</dd></div>
      <div><dt>Budget (CNY)</dt><dd>{f(usage?.cost_cny)} accounted / {f(status?.remaining_cny)} remaining / 10 cap</dd></div>
      <div><dt>Estimated run (CNY)</dt><dd>{mode==='real'?(estimate===null?'unavailable':f(estimate)):'0 / free'}</dd></div>
      <div><dt>Real API</dt><dd>{status?.real_ready?'Ready':usage?.input_target_exceeded?'Blocked: provider input exceeded target':'Disabled or price unverified'}</dd></div>
      <div><dt>Tokens / all paid calls</dt><dd>{usage?.input_tokens||0} input / {usage?.output_tokens||0} output / {usage?.reasoning_tokens||0} reasoning</dd></div>
      <div><dt>Provider outcome</dt><dd>{usage?.successes||0} accepted / {usage?.failures||0} rejected</dd></div>
    </dl>
    <p className="metric-note">Costs are software estimates or conservative reservations, not a provider billing cap. Recorded results: {recordedMode||'none'}; Mock is free and does not constitute real LLM evidence.</p>
    {record&&<div className="run-status" role="status">{record.task?.state||record.experiment_status} / {record.progress_completed||0} of {record.progress_total||count*8} hybrid rounds {record.error&&`/ ${record.error}`}</div>}
    {data&&<>
      <div className="toolbar"><div className="field"><label htmlFor="pilot-seed">Pilot displayed seed</label><select id="pilot-seed" value={seedIndex} onChange={e=>setSeedIndex(Number(e.target.value))}>{data.seeds.map((s,i)=><option key={s} value={i}>{s}</option>)}</select></div>
        <div className="field"><label htmlFor="pilot-round">Pilot timeline round</label><input id="pilot-round" type="range" min="0" max="8" value={round} onChange={e=>setRound(Number(e.target.value))}/><span>{round}</span></div>
        <button className="export" onClick={()=>perform(async()=>setReplay((await request(`/llm/pilots/${record.experiment_id}/replay`,post({}))).identical?'Recorded replay: identical states, events and metrics':'Replay mismatch'))}><RotateCw size={15}/>Recorded Replay</button>
        <button className="export" onClick={()=>onOpen(record.experiment_id)}><ExternalLink size={15}/>Open in Observatory</button>
        <a className="export" href={`${API}/experiments/${record.experiment_id}/light-export`} download><Download size={15}/>Pilot JSON</a>
        {replay&&<span role="status">{replay}</span>}
      </div>
      <div className="world-grid pilot-worlds">{[['a','A / Rule baseline'],['b',`B / ${recordedMode==='real'?'Live LLM recording':recordedMode==='mock'?'Mock hybrid':'Rule control'}`]].map(([branch,title])=><div className="panel world-panel" key={branch}><div className="panel-head"><h3>{title}</h3></div><Network world={frames?.[branch]?.[round]?{...frames[branch][round],config:record.world_config}:null} detailKey={`${record.experiment_id}:${a.seed}:${branch}:${round}`} loadAgent={async id=>(await request(`/experiments/${record.experiment_id}/trajectory?seed=${a.seed}&branch=${branch==='a'?'baseline':'variant'}&start=${round}&end=${round}&agent=${id}`)).snapshots[0]?.agents[0]}/></div>)}</div>
      <div className="metric-chart pilot-curve"><h3>Information coverage / seed {a.seed}</h3><ResponsiveContainer width="100%" height={280}><LineChart data={curve} margin={{top:15,right:18,bottom:22,left:12}}><CartesianGrid stroke="#354244" strokeDasharray="3 3"/><XAxis dataKey="round" tick={{fill:'#a0aca6'}} label={{value:'Simulation round',position:'insideBottom',offset:-14,fill:'#a0aca6'}}/><YAxis domain={[0,1]} tick={{fill:'#a0aca6'}} tickFormatter={v=>`${Math.round(v*100)}%`}/><Tooltip formatter={v=>`${(v*100).toFixed(1)}%`}/><Legend verticalAlign="top"/><Line dataKey="Rule" name="A / Rule" stroke="#a9ddc6" dot={false} isAnimationActive={false}/><Line dataKey="Hybrid" name="B / Hybrid" stroke="#de8877" dot={false} isAnimationActive={false}/></LineChart></ResponsiveContainer></div>
      <div className="table-scroll"><table><thead><tr><th>Seed</th><th>Selected Agents</th><th>Rule coverage</th><th>Hybrid coverage</th><th>Paired difference</th><th>Accepted / fallback</th><th>Replay</th></tr></thead><tbody>{data.paired.map((p,i)=><tr key={p.seed}><td>{p.seed}</td><td>{data.pilot.pairs[i].agents.map(id=>`A${String(id+1).padStart(2,'0')}`).join(', ')}</td><td>{f(p.baseline.coverage)}</td><td>{f(p.intervention.coverage)}</td><td>{f(p.delta.coverage)}</td><td>{data.pilot.pairs[i].accepted} / {data.pilot.pairs[i].fallbacks}</td><td>{data.pilot.pairs[i].recorded_replay_identical?'Identical':'Mismatch'}</td></tr>)}</tbody></table></div>
      <p className="notice">{data.pilot.conclusion} Direction consistency: {f(data.pilot.direction_consistency)}. Descriptive 95% interval: {data.summary.coverage.ci95?.map(f).join(' to ')||'unavailable'}.{data.incomplete?' Incomplete experiment.':''}</p>
    </>}
  </section>;
}
