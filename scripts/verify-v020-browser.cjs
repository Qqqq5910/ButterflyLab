async(page)=>{
  const base=page.url().startsWith('https://qqqq5910.github.io/')?'https://qqqq5910.github.io/ButterflyLab/':'http://127.0.0.1:5180/ButterflyLab/';
  const errors=[],requests=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>requests.push(r.url()));
  await page.setViewportSize({width:1440,height:1000});
  const start=Date.now();await page.goto(base);
  await page.waitForFunction(()=>document.querySelectorAll('.hero-world .node').length===50);
  const firstWorldMs=Date.now()-start;
  await page.getByRole('button').filter({has:page.getByRole('heading',{name:'The Information Ripple',exact:true})}).click();
  await page.getByRole('button',{name:'Explore Parallel Worlds',exact:true}).click();
  await page.waitForFunction(()=>document.querySelectorAll('.parallel-world .node').length===100);
  const parallelMs=Date.now()-start;
  await page.getByRole('button',{name:'Play',exact:true}).click();
  await page.waitForFunction(()=>Number(document.querySelector('.explore-seek').value)>1);
  await page.getByRole('button',{name:'Pause',exact:true}).click();
  const paused=await page.getByRole('slider',{name:'Simulation round'}).inputValue();
  await page.waitForTimeout(650);
  if(await page.getByRole('slider',{name:'Simulation round'}).inputValue()!==paused)throw Error('Pause failed');
  await page.getByRole('slider',{name:'Simulation round'}).fill('17');
  await page.waitForFunction(()=>document.querySelectorAll('.world-label').length===2 && [...document.querySelectorAll('.world-label')].every(e=>e.textContent.includes('round 17')));
  await page.locator('.parallel-world .node').first().click();
  await page.locator('.agent-pop').first().waitFor();
  await page.locator('.research-details summary').click();
  if(!(await page.locator('.outcome').textContent()).includes('37.20 percentage points'))throw Error('Narrative mismatch');
  await page.getByRole('button',{name:'Share Experiment',exact:true}).click();
  const shared=page.url();const other=await page.context().newPage();await other.goto(shared);
  await other.waitForFunction(()=>document.querySelector('.explore-seek')?.value==='17' && document.querySelectorAll('.parallel-world .node').length===100);
  await other.reload();await other.waitForFunction(()=>document.querySelector('.explore-seek')?.value==='17');await other.close();
  const captures=[];
  for(const width of [1440,1024,390]){
    await page.setViewportSize({width,height:1000});await page.evaluate(()=>window.scrollTo(0,0));await page.waitForTimeout(150);
    if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Horizontal overflow at '+width);
    const target=width===1440?'.impeccable/review/desktop.png':width===390?'.impeccable/review/mobile.png':'.impeccable/review/tablet.png';
    await page.screenshot({path:target,fullPage:true});captures.push(target);
  }
  await page.emulateMedia({reducedMotion:'reduce'});
  await page.getByRole('slider',{name:'Simulation round'}).fill('50');
  await page.waitForFunction(()=>document.querySelectorAll('.parallel-world .node').length===100);
  await page.getByRole('button',{name:'Research Mode',exact:true}).click();
  await page.getByRole('heading',{name:'Research on your own machine.'}).waitFor();
  const bad=requests.filter(url=>/\/api\/|localhost|127\.0\.0\.1:(?!5180)/.test(url));
  if(bad.length||errors.length)throw Error(JSON.stringify({errors,bad}));
  return {firstWorldMs,parallelMs,shared,captures,errors,backendRequests:bad.length,resources:await page.evaluate(()=>performance.getEntriesByType('resource').map(r=>({name:r.name.split('/').pop(),transfer:r.transferSize,duration:r.duration}))),reducedMotion:true};
}
