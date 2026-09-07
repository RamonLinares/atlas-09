async page => {
 await page.goto('http://127.0.0.1:5175/?character=ronin-04&motion=PunchCombo');
 await page.waitForFunction(()=>window.atlas?.stats.character==='ronin-04'&&atlas.stats.activeClip==='PunchCombo');
 await page.getByRole('button',{name:'Pause animation',exact:true}).click();
 const result=await page.evaluate(()=>{
  const sword=atlas.model.getObjectByName('swordR'),chest=atlas.model.getObjectByName('chest');
  if(!sword||!chest)throw Error('Missing sword or chest');
  let reference,maxDockDrift=0,maxSwordStep=0,previous;
  for(let t=3.5;t<=8.4;t+=1/120){
   atlas.mixer.setTime(t);atlas.model.updateMatrixWorld(true);
   const relative=chest.matrixWorld.clone().invert().multiply(sword.matrixWorld).elements;
   reference??=relative.slice();maxDockDrift=Math.max(maxDockDrift,...relative.map((v,i)=>Math.abs(v-reference[i])));
  }
  for(let t=0;t<=12;t+=1/120){
   atlas.mixer.setTime(t);atlas.model.updateMatrixWorld(true);const p=sword.getWorldPosition(sword.position.clone());
   if(previous&&(t<3.5||t>8.4))maxSwordStep=Math.max(maxSwordStep,p.distanceTo(previous));previous=p;
  }
  if(maxDockDrift>.008||maxSwordStep>.15)throw Error(JSON.stringify({maxDockDrift,maxSwordStep}));
  return {maxDockDrift,maxSwordStep,duration:atlas.actions.get('PunchCombo').getClip().duration};
 });
 await page.setViewportSize({width:1440,height:1000});
 for(const [tag,t] of [['carry',1.8],['dock',2.4],['jab',4.3],['cross',5.2],['hook',6.1],['retrieve',9.4],['ready',11.99]]){
  await page.evaluate(t=>atlas.mixer.setTime(t),t);await page.screenshot({path:`output/playwright/ronin-combo-${tag}.png`});
 }
 await page.getByRole('button',{name:'PUNCH COMBO',exact:true}).click();
 const playback=await page.evaluate(()=>new Promise((resolve,reject)=>{
  const action=atlas.actions.get('PunchCombo');let previous=action.time,frames=0,reachedEnd=false;
  const timeout=setTimeout(()=>reject(Error('Combo failed to complete a real-time playback loop')),30000);
  function inspect(){
   frames++;const time=action.time;if(time>11.8)reachedEnd=true;
   if(reachedEnd&&time<previous){clearTimeout(timeout);resolve({renderedFrames:frames,completedLoop:true});return}
   previous=time;requestAnimationFrame(inspect);
  }requestAnimationFrame(inspect);
 }));
 return {...result,playback};
}
