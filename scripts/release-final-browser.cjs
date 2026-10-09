async(page)=>{
  await page.setViewportSize({width:1440,height:1000});
  await page.goto('http://127.0.0.1:5174/');
  await page.getByRole('button',{name:'Run Demo',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('.run-status')?.textContent.includes('completed'),{}, {timeout:120000});
  await page.getByRole('tab',{name:'Mock LLM',exact:true}).click();
  const old=await page.evaluate(()=>localStorage.getItem('butterflylab.pilot'));
  await page.getByRole('button',{name:'Run comparison',exact:true}).click();
  await page.waitForFunction(id=>localStorage.getItem('butterflylab.pilot')!==id,old);
  await page.waitForFunction(()=>document.querySelector('#llm-society .run-status')?.textContent.includes('COMPLETED'),{}, {timeout:120000});
  await page.getByRole('button',{name:'Recorded Replay',exact:true}).click();
  await page.getByRole('status').filter({hasText:'Recorded replay: identical states, events and metrics'}).waitFor();
  await page.locator('#llm-society').screenshot({path:'docs/assets/llm-society.png'});
  const legacy=await page.request.get('http://127.0.0.1:5174/api/experiments/5e5cab8e-43f7-4a38-9e98-163d26609fca/summary');
  if(!legacy.ok())throw Error('Legacy retrieval failed');
  const replay=await page.request.post('http://127.0.0.1:5174/api/experiments/5e5cab8e-43f7-4a38-9e98-163d26609fca/reproduce');
  const legacyReplay=await replay.json();if(!legacyReplay.identical)throw Error('Legacy replay failed');
  const checks=[];
  for(const width of [1440,390]){
    await page.setViewportSize({width,height:width===390?844:1000});await page.mouse.move(0,0);await page.waitForTimeout(1000);
    const scroll=await page.evaluate(()=>document.documentElement.scrollWidth);
    checks.push({width,scroll});if(scroll>width)throw Error('Viewport overflow '+width+' / '+scroll);
    await page.screenshot({path:'output/release/browser-'+width+'.png',fullPage:true});
  }
  return {checks,legacyReplay,pilot:await page.evaluate(()=>localStorage.getItem('butterflylab.pilot'))};
}
