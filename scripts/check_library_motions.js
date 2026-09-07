async page => {
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:5175/?character=aether-02');await page.waitForFunction(()=>window.atlas?.stats.character==='aether-02');
 await page.setViewportSize({width:1440,height:1000});
 const results=[];
 for(const [name,id,scale] of [['AETHER / 02','aether-02',1],['ATLAS / 09','atlas-09',1.2]]) {
  await page.getByRole('button',{name,exact:true}).click();await page.waitForFunction(id=>atlas.stats.character===id,id);
  const motions=[];
  for(const [label,clip,time] of [['WALK','Walk',.35],['PUNCH COMBO','PunchCombo',.43],['COLLAPSE','Collapse',2.4]]) {
   await page.getByRole('button',{name:label,exact:true}).click();
   const before=await page.evaluate(()=>atlas.mixer.time);
   await page.evaluate(()=>new Promise(resolve=>{let n=12;function tick(){if(--n<=0)resolve();else requestAnimationFrame(tick)}requestAnimationFrame(tick)}));
   const advanced=await page.evaluate(()=>atlas.mixer.time);if(advanced<=before)throw Error('Animation did not play');
   await page.getByRole('button',{name:'Pause animation',exact:true}).click();
   await page.evaluate(t=>atlas.mixer.setTime(t),time*scale);
   await page.screenshot({path:`output/playwright/library-v6-${id}-${clip}.png`});
   motions.push(await page.evaluate(()=>({clip:atlas.stats.activeClip,time:atlas.stats.clipTime,drawCalls:atlas.renderer.info.render.calls})));
  }
  const held=await page.evaluate(()=>{const action=atlas.actions.get('Collapse');atlas.mixer.setTime(10);const t1=action.time;atlas.mixer.update(1);return {t1,t2:action.time,paused:action.paused,duration:action.getClip().duration}});
  if(!held.paused||held.t1!==held.t2||held.t1!==held.duration)throw Error('Collapse failed to hold');
  await page.getByRole('button',{name:'COLLAPSE',exact:true}).click();
  const replay=await page.evaluate(()=>atlas.actions.get('Collapse').time);if(replay>=.5)throw Error('Collapse did not restart');
  await page.getByRole('button',{name:'RUN',exact:true}).click();
  await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(resolve)));
  const state=await page.evaluate(()=>({character:atlas.stats.character,clips:atlas.stats.clips.map(c=>c.name),runDuration:atlas.actions.get('Run').getClip().duration,active:atlas.stats.activeClip,download:document.querySelector('.download').href}));
  if(state.active!=='Run'||state.clips.includes('Awaken')||state.clips.length!==(id==='atlas-09'?10:11))throw Error('Wrong clip inventory');
  results.push({state,motions,held,replay});
 }
 await page.setViewportSize({width:390,height:844});
 await page.getByRole('button',{name:'AETHER / 02',exact:true}).click();await page.waitForFunction(()=>atlas.stats.character==='aether-02');
 for(const label of ['PUNCH COMBO','WALK','COLLAPSE']) {
  await page.getByRole('button',{name:label,exact:true}).click();await page.getByRole('button',{name:'Pause animation',exact:true}).click();
  await page.evaluate(t=>atlas.mixer.setTime(t),label==='COLLAPSE'?2.4:.43);
  await page.screenshot({path:`output/playwright/library-v6-mobile-${label.toLowerCase().replace(' ','-')}.png`});
 }
 const layout=await page.evaluate(()=>({overflow:document.documentElement.scrollWidth>innerWidth,buttons:[...document.querySelectorAll('[data-clip]')].map(b=>({label:b.textContent,rect:b.getBoundingClientRect().toJSON()}))}));
 if(layout.overflow||layout.buttons.some(b=>b.rect.left<0||b.rect.right>390||b.rect.bottom>844)||errors.length)throw Error(JSON.stringify({layout,errors}));
 return {results,layout,errors};
}
