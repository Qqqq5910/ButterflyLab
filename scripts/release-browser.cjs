async(page)=>{
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.setViewportSize({width:1440,height:1000});
  await page.goto('http://127.0.0.1:5174/');
  await page.getByLabel('Scenario',{exact:true}).selectOption('cascade');
  await page.getByRole('button',{name:'Create world',exact:true}).click();
  await page.getByLabel('PAIRED SEEDS / 1-100').fill('5');
  await page.getByLabel('EXPERIMENT NAME').fill('v0.1.0 free cascade acceptance');
  const run=async(name)=>{
    const old=await page.evaluate(()=>localStorage.getItem('butterflylab.experiment'));
    await page.getByRole('button',{name,exact:true}).click();
    await page.waitForFunction(id=>localStorage.getItem('butterflylab.experiment')!==id,old);
    await page.waitForFunction(()=>document.querySelector('.run-status')?.textContent.includes('completed'),{}, {timeout:120000});
  };
  await run('Run baseline');
  await page.getByLabel('INTERVENTION',{exact:true}).selectOption('information');
  await page.locator('#magnitude').fill('1');
  await run('Run A/B experiment');
  const id=await page.evaluate(()=>localStorage.getItem('butterflylab.experiment'));
  await page.getByRole('button',{name:'Save experiment',exact:true}).click();
  await page.reload();
  await page.waitForFunction(()=>document.querySelectorAll('#worlds .node').length===100,{}, {timeout:120000});
  await page.locator('#studio').screenshot({path:'docs/assets/world-studio.png'});
  await page.locator('#worlds').screenshot({path:'docs/assets/parallel-worlds.png'});
  await page.locator('#observatory').screenshot({path:'docs/assets/observatory.png'});
  await page.locator('#worlds').scrollIntoViewIfNeeded();
  await page.screenshot({path:'docs/assets/hero.png'});
  await page.getByRole('button',{name:'Reproduce',exact:true}).click();
  await page.getByRole('status').filter({hasText:'Exact reproduction verified'}).waitFor({timeout:120000});
  const d=page.waitForEvent('download');
  await page.getByRole('link',{name:'Summary JSON',exact:true}).first().click();
  await(await d).saveAs('output/release/acceptance-summary.json');
  await page.getByRole('tab',{name:'Sensitivity Lab',exact:true}).click();
  await page.getByLabel('Scan values',{exact:true}).fill('0.1,0.2,0.4');
  await page.getByLabel('Discovery seeds',{exact:true}).fill('5');
  await page.getByRole('button',{name:'Run scan',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('#sensitivity .run-status')?.textContent.includes('COMPLETED'),{}, {timeout:180000});
  await page.locator('#sensitivity').screenshot({path:'docs/assets/sensitivity.png'});
  const scan=await page.evaluate(()=>localStorage.getItem('butterflylab.scan'));
  await page.reload();
  await page.waitForFunction(id=>document.querySelector('#sensitivity')?.textContent.includes(id),scan);
  await page.getByRole('tab',{name:'Mock LLM',exact:true}).click();
  await page.locator('#llm-society').screenshot({path:'docs/assets/llm-society.png'});
  for(const width of [1440,390]){
    await page.setViewportSize({width,height:width===390?844:1000});
    await page.mouse.move(0,0);
    await page.waitForTimeout(1000);
    if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Viewport overflow');
    await page.screenshot({path:'output/release/browser-'+width+'.png',fullPage:true});
  }
  if(errors.length)throw Error(errors.join('\n'));
  return {id,scan,errors};
}
