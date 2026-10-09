async (page) => {
  await page.getByLabel('Saved world',{exact:true}).selectOption('7dea3c40-8b27-4c7d-a86a-549825046df2');
  await page.waitForFunction(()=>document.querySelectorAll('#studio .node').length===50);
  await page.setViewportSize({width:1440,height:1000});
  await page.evaluate(()=>window.scrollTo(0,0));
  await page.screenshot({path:'D:/Projects/ButterflyLab/output/playwright/phase2b-desktop-top.png'});
  await page.setViewportSize({width:390,height:844});
  await page.evaluate(()=>window.scrollTo(0,0));
  await page.screenshot({path:'D:/Projects/ButterflyLab/output/playwright/phase2b-mobile-top.png'});
  await page.setViewportSize({width:1440,height:1000});
  return {settledPreviewAgents:50};
}
