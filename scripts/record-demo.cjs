async(page)=>{
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.setViewportSize({width:1280,height:720});
  await page.goto('http://127.0.0.1:5174/');
  let frame=0;
  const capture=async(n)=>{for(let i=0;i<n;i++){
    await page.mouse.move(0,0);
    await page.screenshot({path:`output/playwright/demo/frame-${String(frame++).padStart(4,'0')}.png`});
    await page.waitForTimeout(100);
  }};
  await page.getByLabel('Scenario',{exact:true}).selectOption('cascade');
  await page.getByRole('button',{name:'Create world',exact:true}).click();
  await page.getByLabel('PAIRED SEEDS / 1-100').fill('5');
  await page.getByLabel('EXPERIMENT NAME').fill('Information Cascade / Rule / five seeds');
  await page.locator('.studio-preview').scrollIntoViewIfNeeded();
  await capture(12);
  await page.getByRole('button',{name:'Run baseline',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('.run-status')?.textContent.includes('completed'),{}, {timeout:120000});
  const worldView=async()=>page.evaluate(()=>scrollTo(0,document.querySelector('#worlds').getBoundingClientRect().top+scrollY-55));
  await worldView();await capture(12);
  await page.getByRole('button',{name:'Play or pause',exact:true}).click();
  await worldView();await capture(42);
  await page.getByLabel('INTERVENTION',{exact:true}).selectOption('information');
  await page.locator('#agent').fill('1');await page.locator('#magnitude').fill('1');
  await page.locator('#kind').scrollIntoViewIfNeeded();await capture(12);
  const old=await page.evaluate(()=>localStorage.getItem('butterflylab.experiment'));
  await page.getByRole('button',{name:'Run A/B experiment',exact:true}).click();
  await page.waitForFunction(id=>localStorage.getItem('butterflylab.experiment')!==id,old);
  await page.waitForFunction(()=>document.querySelector('.run-status')?.textContent.includes('completed'),{}, {timeout:120000});
  await page.getByRole('button',{name:'Play or pause',exact:true}).click();
  await worldView();await capture(42);
  const chart=page.locator('.metric-chart').filter({has:page.getByRole('heading',{name:'Information Coverage',exact:true})});
  await chart.scrollIntoViewIfNeeded();await capture(24);
  const result={frames:frame,experiment:await page.evaluate(()=>localStorage.getItem('butterflylab.experiment')),errors};
  if(errors.length)throw Error(errors.join('\n'));
  return result;
}
