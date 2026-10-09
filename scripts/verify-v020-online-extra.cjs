async(page)=>{
  const context=await page.context().browser().newContext({viewport:{width:1440,height:1000}});
  const fresh=await context.newPage();const requests=[],errors=[];fresh.on('request',r=>requests.push(r.url()));fresh.on('pageerror',e=>errors.push(e.message));
  const base='https://qqqq5910.github.io/ButterflyLab/';const start=Date.now();await fresh.goto(base);
  await fresh.waitForFunction(()=>document.querySelectorAll('.hero-world .node').length===50);
  const firstWorldMs=Date.now()-start;
  await fresh.getByRole('button').filter({has:fresh.getByRole('heading',{name:'The Information Ripple',exact:true})}).click();
  await fresh.getByRole('button',{name:'Explore Parallel Worlds',exact:true}).click();
  await fresh.waitForFunction(()=>document.querySelectorAll('.parallel-world .node').length===100);
  const parallelMs=Date.now()-start;
  const initialResources=await fresh.evaluate(()=>performance.getEntriesByType('resource').map(r=>({name:r.name.split('/').pop(),transfer:r.transferSize,duration:r.duration})));
  for(const [title,expected] of [['The Influential Node','24.00 percentage points'],['The Cooperation Dilemma','73.60 percentage points']]){
    await fresh.getByRole('button').filter({has:fresh.getByRole('heading',{name:title,exact:true})}).click();
    await fresh.getByRole('button',{name:'Explore Parallel Worlds',exact:true}).click();
    await fresh.waitForFunction(()=>document.querySelectorAll('.parallel-world .node').length===100);
    if(!(await fresh.locator('.outcome').textContent()).includes(expected))throw Error('Actual scenario result mismatch');
    await fresh.locator('.playback select').nth(1).selectOption('46');
    await fresh.waitForFunction(()=>document.querySelectorAll('.parallel-world .node').length===100);
  }
  await fresh.getByRole('textbox').fill('transmission from 0.2 to 0.3');await fresh.getByRole('button',{name:'Explore a World',exact:true}).click();
  if(await fresh.getByRole('button',{name:'Explore Parallel Worlds',exact:true}).count())throw Error('Custom configuration silently matched');
  await fresh.goto(base+'?scenario_id=information&intervention_id=default&seed=42&round=999&url=https://example.org');
  await fresh.waitForFunction(()=>document.querySelectorAll('.hero-world .node').length===50);
  if(await fresh.locator('#parallel').count())throw Error('Invalid URL restored');
  if(requests.some(r=>/\/api\/|localhost|127\.0\.0\.1/.test(r))||errors.length)throw Error(JSON.stringify({errors,requests}));
  const resources=await fresh.evaluate(()=>performance.getEntriesByType('resource').map(r=>({name:r.name.split('/').pop(),transfer:r.transferSize,duration:r.duration})));
  await context.close();return {coldFirstWorldMs:firstWorldMs,coldJourneyToParallelMs:parallelMs,otherScenarios:true,seed42And46Verified:true,customRejected:true,invalidShareRejected:true,errors,initialResources,resources};
}
