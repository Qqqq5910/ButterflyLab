async(page)=>{
  await page.goto('http://127.0.0.1:5176/');await page.getByRole('button',{name:'Research Mode',exact:true}).click();
  await page.getByRole('heading',{name:'World Studio',exact:true}).waitFor();
  await page.getByRole('tab',{name:'Sensitivity Lab',exact:true}).click();
  await page.getByLabel('Scan values',{exact:true}).fill('0.1,0.2,0.4');
  await page.getByLabel('Discovery seeds',{exact:true}).fill('5');
  await page.getByRole('button',{name:'Run scan',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('#sensitivity .run-status')?.textContent.includes('COMPLETED'),{}, {timeout:120000});
  const scan=await page.evaluate(()=>localStorage.getItem('butterflylab.scan'));
  await page.reload();await page.getByRole('button',{name:'Research Mode',exact:true}).click();
  await page.waitForFunction(id=>document.querySelector('#sensitivity')?.textContent.includes(id),scan);
  return {scan,restored:true};
}
