async page => {
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.reload();await page.waitForFunction(()=>window.atlas?.stats.clips?.length===5);
  await page.setViewportSize({width:1440,height:1000});
  const results=[];
  for(const [name,id,duration] of [['AETHER / 02','aether-02',28/30],['ATLAS / 09','atlas-09',34/30]]) {
    await page.getByRole('button',{name,exact:true}).click();
    await page.waitForFunction(id=>window.atlas?.stats.character===id,id);
    await page.getByRole('button',{name:'RUN',exact:true}).click();
    const before=await page.evaluate(()=>atlas.mixer.time);
    await page.evaluate(()=>new Promise(resolve=>{let n=20;function tick(){if(--n<=0)resolve();else requestAnimationFrame(tick)}requestAnimationFrame(tick)}));
    const state=await page.evaluate(()=>({character:atlas.stats.character,clip:atlas.stats.activeClip,duration:atlas.stats.clips.find(c=>c.name==='Run').duration,time:atlas.mixer.time,drawCalls:atlas.renderer.info.render.calls,download:document.querySelector('.download').href}));
    if(Math.abs(state.duration-duration)>.001||state.time<=before+.05||state.drawCalls<1)throw Error(JSON.stringify(state));
    await page.getByRole('button',{name:'Pause animation',exact:true}).click();
    for(const [label,u,x,z] of [['front',.18,0,17],['push',.38,17,0],['recovery',.60,17,0]]) {
      await page.evaluate(({u,duration,x,z})=>{atlas.mixer.setTime(u*duration);atlas.camera.position.set(x,4,z);atlas.controls.target.set(0,3.2,0);atlas.controls.update()},{u,duration,x,z});
      await page.screenshot({path:`output/motion/run-v5-${id}-${label}.png`});
    }
    results.push(state);
  }
  await page.setViewportSize({width:390,height:844});
  await page.getByRole('button',{name:'AETHER / 02',exact:true}).click();
  await page.waitForFunction(()=>atlas.stats.character==='aether-02');
  await page.getByRole('button',{name:'Pause animation',exact:true}).click();
  await page.evaluate(()=>atlas.mixer.setTime(.18*28/30));
  await page.screenshot({path:'output/motion/run-v5-mobile.png'});
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
  if(overflow||errors.length)throw Error(JSON.stringify({overflow,errors}));
  return {results,mobileOverflow:overflow,errors};
}
