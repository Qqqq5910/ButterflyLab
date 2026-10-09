async(page)=>{
  await page.setViewportSize({width:1280,height:800});await page.goto('https://qqqq5910.github.io/ButterflyLab/');
  await page.waitForFunction(()=>document.querySelectorAll('.hero-world .node').length===50);
  let frame=0;const capture=async n=>{for(let i=0;i<n;i++){await page.mouse.move(0,0);await page.screenshot({path:`output/playwright/explore/frame-${String(frame++).padStart(4,'0')}.png`});await page.waitForTimeout(100);}};
  await capture(12);
  await page.getByRole('button',{name:'Explore a World',exact:true}).click();await page.locator('.confirmation').scrollIntoViewIfNeeded();await capture(12);
  await page.getByRole('button',{name:'Explore Parallel Worlds',exact:true}).click();await page.waitForFunction(()=>document.querySelectorAll('.parallel-world .node').length===100);
  await page.locator('.parallel-worlds').scrollIntoViewIfNeeded();await capture(12);
  await page.locator('.playback select').first().selectOption('2');await page.getByRole('button',{name:'Play',exact:true}).click();await capture(60);
  if(await page.getByRole('button',{name:'Pause',exact:true}).count())await page.getByRole('button',{name:'Pause',exact:true}).click();
  await page.getByRole('slider',{name:'Simulation round'}).fill('50');await page.locator('.outcome').scrollIntoViewIfNeeded();await capture(24);
  return {frames:frame,scenario:'information',seed:42,actualRuleReplay:true};
}
