async (page) => {
  const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.reload();
  await page.waitForFunction(()=>window.atlas?.stats.character==='aether-02');
  await page.setViewportSize({width:1440,height:1000});
  const results=[];
  for(const [clip,label,t] of [['Sentinel','IDLE',0],['Run','RUN',.27],['Run','RUN',.97],['KneelFire','KNEEL & FIRE',3.37],['Backflip','BACKFLIP',1.79]]) {
    await page.getByRole('button',{name:label,exact:true}).click();
    await page.getByRole('button',{name:'Pause animation',exact:true}).click();
    await page.evaluate(t=>{atlas.mixer.setTime(t);atlas.model.updateMatrixWorld(true);},t);
    await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
    const stats=await page.evaluate(()=>({...atlas.stats,memory:{...atlas.renderer.info.memory},effects:atlas.scene.children.filter(o=>o.name==='Motion effects').length}));
    await page.screenshot({path:`output/aether-02/${clip}-${t}.png`,scale:'css'});
    results.push(stats);
  }
  // Swap in both directions with a live clip; only one character/effect set remains.
  for(const [name,id] of [['ATLAS / 09','atlas-09'],['AETHER / 02','aether-02'],['ATLAS / 09','atlas-09'],['AETHER / 02','aether-02']]) {
    await page.getByRole('button',{name,exact:true}).click();
    await page.waitForFunction(id=>atlas.stats.character===id,id);
    await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
    results.push(await page.evaluate(()=>({character:atlas.stats.character,memory:{...atlas.renderer.info.memory},effects:atlas.scene.children.filter(o=>o.name==='Motion effects').length,download:document.querySelector('.download').getAttribute('href'),skeletons:atlas.scene.children.filter(o=>o.isSkeletonHelper).length})));
  }
  await page.setViewportSize({width:390,height:844});
  await page.getByRole('button',{name:'RUN',exact:true}).click();
  await page.getByRole('button',{name:'Pause animation',exact:true}).click();
  await page.evaluate(()=>atlas.mixer.setTime(.27));
  await page.screenshot({path:'output/aether-02/mobile-run.png',scale:'css'});
  results.push(await page.evaluate(()=>({mobile:true,overflow:document.documentElement.scrollWidth>innerWidth,canvas:[document.querySelector('canvas').clientWidth,document.querySelector('canvas').clientHeight]})));
  await page.getByRole('button',{name:'BACKFLIP',exact:true}).click();
  await page.getByRole('button',{name:'Pause animation',exact:true}).click();
  await page.evaluate(()=>atlas.mixer.setTime(1.79));
  await page.screenshot({path:'output/aether-02/mobile-backflip.png',scale:'css'});
  await page.setViewportSize({width:1440,height:1000});
  await page.getByRole('button',{name:'IDLE',exact:true}).click();
  if(errors.length)throw Error(errors.join('\n'));
  if(results.some(r=>r.effects!==undefined&&r.effects!==1))throw Error('Leaked effects after swap');
  if(results.some(r=>r.overflow))throw Error('Mobile overflow');
  return {results,errors};
}
