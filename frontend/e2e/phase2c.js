async(page)=>{
  const root='D:/Projects/ButterflyLab/output/playwright/';
  const requests=[];page.on('request',r=>{if(r.url().includes(':8001/api/experiments'))requests.push(r.url())});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.evaluate(()=>{localStorage.removeItem('butterflylab.scan');localStorage.setItem('butterflylab.experiment','1e651584-0eec-4d25-b7f5-5f5d18e94a55')});
  await page.reload();
  await page.waitForFunction(()=>document.querySelectorAll('#worlds .node').length===100&&document.querySelectorAll('.metric-chart .recharts-line-curve').length===14,{}, {timeout:120000});
  await page.getByLabel('Timeline round',{exact:true}).fill('25');
  await page.waitForFunction(()=>document.querySelectorAll('#worlds .node').length===100);
  await page.getByLabel('Displayed seed',{exact:true}).selectOption('1');
  await page.waitForFunction(()=>document.querySelectorAll('#worlds .node').length===100);
  if(requests.some(u=>/experiments\/[a-f0-9-]+$/.test(u)))throw new Error('Full trajectory request during browsing');
  const lazyRequests=requests.filter(u=>u.includes('/trajectory'));
  if(!lazyRequests.some(u=>u.includes('start=20')))throw new Error('Missing lazy interval');
  await page.getByRole('button',{name:'Create world',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('.aside-bottom').textContent.includes('social-1.0.0'));
  await page.getByRole('tab',{name:'Sensitivity Lab',exact:true}).click();
  await page.getByLabel('Scan values',{exact:true}).fill('0,0.1,1');
  await page.getByLabel('Discovery seeds',{exact:true}).fill('5');
  await page.getByRole('button',{name:'Run scan',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('#sensitivity .run-status').textContent.includes('COMPLETED'),{}, {timeout:180000});
  const sensitivity=await page.evaluate(()=>localStorage.getItem('butterflylab.scan'));
  if(await page.locator('.lab-response .recharts-line-curve').count()!==2)throw new Error('Response curves missing');
  await page.getByRole('tab',{name:'Criticality Explorer',exact:true}).click();
  await page.getByLabel('Independent seeds',{exact:true}).fill('5');
  await page.getByLabel('Agent scales',{exact:true}).fill('30,50');
  await page.getByRole('button',{name:'Run scan',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('#sensitivity .run-status').textContent.includes('COMPLETED'),{}, {timeout:180000});
  const critical=await page.evaluate(()=>localStorage.getItem('butterflylab.scan'));
  if(critical===sensitivity)throw new Error('New scan not created');
  if(!(await page.locator('#sensitivity').innerText()).includes('stable across independent'))throw new Error('Independent validation missing');
  await page.reload();
  await page.waitForFunction(id=>document.querySelector('#sensitivity').textContent.includes(id),critical);
  await page.getByLabel('Saved scans',{exact:true}).selectOption(sensitivity);
  await page.waitForFunction(id=>document.querySelector('#sensitivity').textContent.includes(id),sensitivity);
  const lightDownload=page.waitForEvent('download');await page.locator('#sensitivity').getByRole('link',{name:'Summary JSON',exact:true}).click();await(await lightDownload).saveAs(root+'phase2c-scan-summary.json');
  const archiveDownload=page.waitForEvent('download',{timeout:180000});await page.locator('#sensitivity').getByRole('button',{name:'Full archive',exact:true}).click();await(await archiveDownload).saveAs(root+'phase2c-scan.zip');
  for(const [label,width,height] of [['desktop',1440,1000],['mobile',390,844]]){
    await page.setViewportSize({width,height});await page.locator('#sensitivity').scrollIntoViewIfNeeded();await page.screenshot({path:root+`phase2c-${label}.png`});
    if(!await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth))throw new Error('Viewport overflow');
  }
  await page.setViewportSize({width:1440,height:1000});
  return {sensitivity,critical,lazyRequests,errors};
}
