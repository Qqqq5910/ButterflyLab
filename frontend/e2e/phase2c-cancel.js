async(page)=>{
  await page.getByRole('button',{name:'Create world',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('.aside-bottom').textContent.includes('social-1.0.0'));
  await page.getByRole('tab',{name:'Sensitivity Lab',exact:true}).click();
  await page.getByLabel('Discovery seeds',{exact:true}).fill('100');
  await page.getByLabel('Scan values',{exact:true}).fill('0,0.1,0.2,0.4,0.7,1');
  await page.getByRole('button',{name:'Run scan',exact:true}).click();
  await page.waitForFunction(()=>{const s=document.querySelector('#sensitivity .run-status').textContent;return s.includes('RUNNING')&&!s.includes('/ 0 of')},{},{timeout:60000});
  const id=await page.evaluate(()=>localStorage.getItem('butterflylab.scan'));
  await page.getByRole('button',{name:'Cancel scan',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('#sensitivity .run-status').textContent.includes('CANCELLED'),{},{timeout:30000});
  const api=async()=>await(await page.request.get('http://127.0.0.1:8001/api/labs/'+id)).json();
  const stopped=await api();
  if(!(stopped.result.partial_cell?.completed_seeds.length||stopped.result.cells.length))throw new Error('No completed results preserved');
  await page.reload();
  await page.waitForFunction(id=>document.querySelector('#sensitivity').textContent.includes(id)&&document.querySelector('#sensitivity .run-status').textContent.includes('CANCELLED'),id);
  const restored=await api();
  if(stopped.task.completed!==restored.task.completed)throw new Error('Calculation continued after cancellation');
  const child=stopped.result.partial_cell?.experiment_id||stopped.result.cells[0].experiment_id;
  const data=await(await page.request.get('http://127.0.0.1:8001/api/experiments/'+child+'/summary')).json();
  if(stopped.result.partial_cell&&(!data.result.incomplete||data.experiment_status!=='cancelled'))throw new Error('Partial experiment mislabeled');
  await page.evaluate(()=>performance.clearResourceTimings());
  await page.locator('#experiments tr').filter({hasText:'1e651584-0eec-4d25-b7f5-5f5d18e94a55'}).getByRole('button').first().click();
  await page.waitForFunction(()=>document.querySelectorAll('#worlds .node').length===100);
  const performanceData=await page.evaluate(()=>({requests:performance.getEntriesByType('resource').filter(r=>r.name.includes('/api/experiments/1e651584')).map(r=>({url:r.name,bytes:r.encodedBodySize,decodedBytes:r.decodedBodySize,transferBytes:r.transferSize,durationMs:r.duration})),jsHeap:performance.memory?{used:performance.memory.usedJSHeapSize,limit:performance.memory.jsHeapSizeLimit}:null}));
  for(const [label,width,height] of [['desktop',1440,1000],['mobile',390,844]]){await page.setViewportSize({width,height});await page.screenshot({path:`D:/Projects/ButterflyLab/.impeccable/review/${label}.png`,fullPage:true});}
  return {id,state:restored.state,completed:restored.task.completed,partial:restored.result.partial_cell,performanceData};
}
