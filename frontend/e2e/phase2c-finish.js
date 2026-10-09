async(page)=>{
  await page.setViewportSize({width:1440,height:1000});
  const root='D:/Projects/ButterflyLab/';
  await page.evaluate(()=>localStorage.setItem('butterflylab.experiment','1e651584-0eec-4d25-b7f5-5f5d18e94a55'));
  await page.reload();
  await page.waitForFunction(()=>document.querySelectorAll('#worlds .node').length===100&&document.querySelectorAll('.metric-chart .recharts-line-curve').length===14,{}, {timeout:120000});
  if(await page.getByRole('alert').count())throw new Error('Unsettled error banner');
  await page.getByLabel('Saved scans',{exact:true}).selectOption('8fef8714-fc85-4d4c-8798-be755ae73125');
  await page.waitForFunction(()=>document.querySelector('#sensitivity').textContent.includes('8fef8714'));
  await page.locator('aside nav a[href="#criticality"]').click();
  if(await page.getByRole('tab',{name:'Criticality Explorer',exact:true}).getAttribute('aria-selected')!=='true')throw new Error('Navigation did not select mode');
  for(const [label,width,height] of [['desktop',1440,1000],['mobile',390,844]]){
    await page.setViewportSize({width,height});await page.mouse.move(0,0);await page.screenshot({path:root+`.impeccable/review/${label}.png`,fullPage:true});
    await page.locator('.lab-response').scrollIntoViewIfNeeded();await page.mouse.move(0,0);await page.screenshot({path:root+`output/playwright/phase2c-critical-${label}.png`});
    if(!await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth))throw new Error('Overflow');
  }
  await page.setViewportSize({width:1440,height:1000});
  const id='1e651584-0eec-4d25-b7f5-5f5d18e94a55';const measurements=[];
  for(const tail of ['/summary','/trajectory?seed=42&branch=baseline&start=0&end=9&view=network','/trajectory?seed=42&branch=variant&start=0&end=9&view=network']){
    const start=Date.now();const r=await page.request.get('http://127.0.0.1:8001/api/experiments/'+id+tail);
    const body=await r.body();measurements.push({tail,seconds:(Date.now()-start)/1000,decodedBytes:body.length,compressedBytes:Number(r.headers()['content-length'])||null,encoding:r.headers()['content-encoding']||null});
  }
  const old=await page.request.get('http://127.0.0.1:8001/api/experiments/3f87a501-0313-4c1b-9d37-57a1f8b24357/summary');
  if(old.status()!==200||(await old.json()).engine_version!=='0.2.0')throw new Error('Legacy unavailable');
  const replay=await page.request.post('http://127.0.0.1:8001/api/experiments/96838a37-fd89-4153-861a-174793aaf84e/reproduce');
  if(!(await replay.json()).identical)throw new Error('Reproduction mismatch');
  return {measurements,legacyAccessible:true,reproductionIdentical:true};
}
