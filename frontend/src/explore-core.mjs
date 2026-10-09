// Replaceable structured interpreter. No provider or remote calls are made here.
export const MODE = import.meta.env?.VITE_APP_MODE || 'LOCAL_RESEARCH';
export const numbers = text => (text.match(/-?\d*\.?\d+/g) || []).map(Number);
export class TemplateInterpreter {
  interpret(text, scenarios) {
    const q = text.trim().toLowerCase();
    const values = numbers(q);
    let id, field;
    if (/传播|transmission|spread|diffus/.test(q)) { id='information'; field='transmission'; }
    else if (/激励|incentive/.test(q)) { id='cooperation'; field='incentive'; }
    else if (/连接最多|most connected|influential/.test(q)) id='influential';
    else if (/资源|resource/.test(q)) id='resource';
    else return {error:'这个问题目前还不能直接模拟。Try information probability, the most connected node, or cooperation incentives.'};
    const scenario=scenarios.find(s=>s.id===(id==='resource'?'information':id));
    if (!scenario) return {error:'Scenarios are still loading. Please retry.'};
    const request={experiment_name:scenario.title,world:{...scenario.world},variant_world:scenario.variant_world?{...scenario.variant_world}:null,intervention:scenario.intervention?{...scenario.intervention}:null,seeds:[...scenario.seeds],centrality:id==='influential'};
    let change=scenario.change;
    if (field) {
      let a,b;
      if (values.length===2) [a,b]=values;
      else if (/一倍|double|twice/.test(q) && !values.length) {a=request.world[field];b=a*2;}
      else if (!values.length && id==='cooperation') {a=.3;b=.6;}
      else return {error:'Specify two values, e.g. transmission from 0.1 to 0.2. Only supported templates are interpreted.'};
      if (!Number.isFinite(a)||!Number.isFinite(b)||a<0||a>1||b<0||b>1||a===b) return {error:'The two distinct probabilities/incentives must be in [0,1]. 参数必须合法且不同。'};
      request.world[field]=a;request.variant_world={...request.world,[field]:b};request.intervention=null;
      change=`Global ${field}: ${a} → ${b}`;
    } else if (id==='resource') {
      if(values.length!==1 || !/减少|reduce|decreas|lose|loss/.test(q)) return {error:'Supported resource template: an agent loses 1 resource unit. Specify one loss in (0,50].'};
      const loss=Math.abs(values[0]);
      if(!loss||loss>50) return {error:'Resource loss must be in (0,50].'};
      request.variant_world=null;request.intervention={kind:'resource',agent:1,magnitude:-loss};request.centrality=false;
      change=`Local resource removal: A02 −${loss} units at round 0`;
    }
    const exact=id!=='resource' && JSON.stringify(request.world)===JSON.stringify(scenario.world) && JSON.stringify(request.variant_world)===JSON.stringify(scenario.variant_world);
    return {scenario_id:id,scenario,request,change,exact,intervention_id:'default',note:field==='transmission'?'Transmission is a per-edge probability multiplier, not guaranteed propagation speed. Effective probability also uses trust, edge strength and susceptibility.':'Only the declared rule or local state is changed. Shared initial states and paired seeds.'};
  }
}
export function restoreShare(search, scenarios) {
  const p=new URLSearchParams(search),allowed=['scenario_id','intervention_id','seed','round'];
  if ([...p.keys()].some(k=>!allowed.includes(k)) || allowed.some(k=>p.getAll(k).length>1)) return null;
  const scenario=scenarios.find(s=>s.id===p.get('scenario_id'));
  if(!scenario || p.get('intervention_id')!=='default')return null;
  const seed=Number(p.get('seed')),round=Number(p.get('round'));
  if(!p.has('seed')||!p.has('round')||!scenario.seeds.includes(seed)||!Number.isInteger(round)||round<0||round>scenario.world.rounds)return null;
  return {scenario,seed,round};
}
export function shareURL(base,scenario,seed,round) {
  const url=new URL(base);url.hash='';url.search='';
  url.search=new URLSearchParams({scenario_id:scenario,intervention_id:'default',seed:String(seed),round:String(round)}).toString();return url.href;
}
export function narrative(summary,metric) {
  const s=summary[metric];
  const unit=metric==='resource_mean'?'units':'percentage points';
  const scale=unit==='units'?1:100;
  return `Across ${s.n} paired seeds, World A ends at ${(s.baseline_mean*scale).toFixed(2)} and World B at ${(s.intervention_mean*scale).toFixed(2)}. Mean B−A: ${(s.mean*scale).toFixed(2)} ${unit}. ${Math.abs(s.mean)<1e-12?'No final mean difference was observed.':'This is an observed synthetic simulation difference.'}`;
}
