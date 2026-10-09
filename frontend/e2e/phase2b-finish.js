async (page) => {
  const root = 'D:/Projects/ButterflyLab/output/playwright/';
  await page.evaluate(() => {
    localStorage.setItem('butterflylab.experiment', '1e651584-0eec-4d25-b7f5-5f5d18e94a55');
    localStorage.setItem('butterflylab.study', '09136de5-b525-4e93-bf45-cd14a563e81c');
  });
  await page.reload();
  await page.waitForFunction(() => document.querySelectorAll('.metric-chart .recharts-line-curve').length === 14 && document.querySelectorAll('#observatory tbody tr').length === 30, {}, {timeout:120000});
  await page.getByLabel('Saved world', {exact:true}).selectOption('7dea3c40-8b27-4c7d-a86a-549825046df2');
  await page.waitForFunction(() => document.querySelectorAll('#studio .node').length === 50);
  await page.getByLabel('Saved study', {exact:true}).selectOption('09136de5-b525-4e93-bf45-cd14a563e81c');
  if (!(await page.locator('#studies').innerText()).includes('Saved result: 5 paired seeds')) throw new Error('Saved sample provenance missing');
  await page.getByLabel('Effect distribution cell').selectOption('3');
  if (!(await page.getByLabel('Effect distribution cell').inputValue() === '3')) throw new Error('Cell selector failed');
  if (!(await page.getByTestId('selected-study-cell').innerText()).includes('incentive = 0.6')) throw new Error('Full selected cell label missing');
  if (await page.locator('#studies .recharts-bar-rectangle').count() !== 5) throw new Error('Cell seed distribution missing');
  const resource = page.locator('.metric-chart').filter({has:page.getByRole('heading', {name:'Mean Resources',exact:true})});
  for (const [label,width,height] of [['desktop',1440,1000],['mobile',390,844]]) {
    await page.setViewportSize({width,height});
    await page.waitForFunction(() => [...document.querySelectorAll('.recharts-wrapper')].every(e=>e.getBoundingClientRect().right<=innerWidth));
    await page.evaluate(()=>window.scrollTo(0,0));
    await page.screenshot({path:root+`phase2b-${label}-top.png`});
    await page.locator('#observatory').scrollIntoViewIfNeeded();
    await page.screenshot({path:root+`phase2b-${label}-charts.png`});
    await resource.screenshot({path:root+`phase2b-${label}-resources.png`});
    const ticks = await resource.locator('.recharts-yAxis .recharts-cartesian-axis-tick-value').allTextContents();
    if (ticks.some(t=>t.length>7)) throw new Error('Unbounded tick precision');
    await page.locator('#studies').screenshot({path:root+`phase2b-grid-${label}.png`});
    await page.screenshot({path:root+`phase2b-${label}.png`,fullPage:true});
    if (!await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)) throw new Error('Page overflow');
  }
  await page.setViewportSize({width:1440,height:1000});
  await page.evaluate(()=>window.scrollTo(0,0));
  return {restoredSocialSeeds:30,savedStudySeeds:5,cell:3,viewports:[1440,390],realCurves:14};
}
