async(page)=>{
  await page.goto('https://github.com/Qqqq5910/ButterflyLab');
  await page.waitForSelector('article');
  await page.waitForTimeout(2000);
  const checks=[];
  for(const width of [1440,390]){
    await page.setViewportSize({width,height:width===390?844:1000});
    const demo=page.locator('article animated-image').first();
    await demo.scrollIntoViewIfNeeded();
    await page.waitForFunction(()=>[...document.querySelectorAll('article img')].every(i=>i.complete&&i.naturalWidth>0),{}, {timeout:60000});
    await page.waitForTimeout(2200);
    await demo.screenshot({path:`output/release/github-gif-${width}-a.png`});
    await page.waitForTimeout(4000);
    await demo.screenshot({path:`output/release/github-gif-${width}-b.png`});
    checks.push(await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,images:[...document.querySelectorAll('article img')].map(i=>({src:i.src,width:i.naturalWidth,complete:i.complete}))})));
  }
  await page.goto('https://github.com/Qqqq5910/ButterflyLab/blob/main/README.zh-CN.md');
  await page.getByText('真实规则研究',{exact:true}).first().waitFor({timeout:60000});
  const chinese=await page.locator('img[src*="butterflylab-demo.gif"]').count();
  return {checks,chinese};
}
