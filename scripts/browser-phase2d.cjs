async (page) => {
  await page.setViewportSize({width:1440,height:1000});
  await page.locator('#llm-society').getByRole('tab',{name:'Mock LLM',exact:true}).click();
  await page.locator('#llm-society').scrollIntoViewIfNeeded();
  await page.screenshot({path:'.impeccable/review/phase2d/desktop.png',fullPage:true});
  await page.locator('#llm-society').screenshot({path:'docs/assets/llm-society.png'});
  await page.setViewportSize({width:390,height:844});
  await page.locator('#llm-society').scrollIntoViewIfNeeded();
  await page.screenshot({path:'.impeccable/review/phase2d/mobile.png',fullPage:true});
  if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)) throw Error('Mobile document overflow');
  const downloadPromise=page.waitForEvent('download');
  await page.locator('#llm-society').getByRole('link',{name:'Pilot JSON',exact:true}).click();
  const download=await downloadPromise;
  await download.saveAs('output/research/browser-pilot.json');
  const data=await page.evaluate(async()=>{
    const id=localStorage.getItem('butterflylab.pilot');
    return (await fetch('/api/experiments/'+id+'/light-export')).json();
  });
  if(data.result.pilot.mode!=='mock'||data.result.paired.length!==5)throw Error('Invalid saved export');
}
