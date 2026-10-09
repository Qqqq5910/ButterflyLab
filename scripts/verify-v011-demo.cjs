async(page)=>{
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.setViewportSize({width:1440,height:1000});
  await page.goto('http://127.0.0.1:5176/');
  await page.getByRole('button',{name:'Run Demo',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('.run-status')?.textContent.includes('completed'),{}, {timeout:120000});
  await page.getByLabel('INTERVENTION',{exact:true}).selectOption('information');
  await page.locator('#agent').fill('1');await page.locator('#magnitude').fill('1');
  const old=await page.evaluate(()=>localStorage.getItem('butterflylab.experiment'));
  await page.getByRole('button',{name:'Run A/B experiment',exact:true}).click();
  await page.waitForFunction(id=>localStorage.getItem('butterflylab.experiment')!==id,old);
  await page.waitForFunction(()=>document.querySelector('.run-status')?.textContent.includes('completed'),{}, {timeout:120000});
  const eid=await page.evaluate(()=>localStorage.getItem('butterflylab.experiment'));
  await page.reload();
  await page.waitForFunction(()=>document.querySelector('.run-status')?.textContent.includes('completed'));
  if(await page.evaluate(()=>localStorage.getItem('butterflylab.experiment'))!==eid)throw Error('Refresh recovery failed');
  const downloadPromise=page.waitForEvent('download');
  await page.getByRole('link',{name:'Summary JSON',exact:true}).first().click();
  const download=await downloadPromise;
  await download.saveAs('output/release/v011-demo-summary.json');
  const reproduction=await (await page.request.post(`http://127.0.0.1:5176/api/experiments/${eid}/reproduce`)).json();
  const summary=await (await page.request.get(`http://127.0.0.1:5176/api/experiments/${eid}/summary`)).json();
  const status=await (await page.request.get('http://127.0.0.1:5176/api/llm/status')).json();
  if(!reproduction.identical||status.real_ready||errors.length)throw Error('Verification failed');
  await page.locator('#worlds').screenshot({path:'output/release/v011-ab.png'});
  return {eid,reproduction,seeds:summary.random_seeds,real_ready:status.real_ready,errors,download:download.suggestedFilename()};
}
