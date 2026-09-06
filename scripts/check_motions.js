async (page) => {
  await page.reload();
  await page.waitForFunction(()=>window.atlas?.actions.has('Backflip'));
  const results=[];
  for(const [clip,label,t] of [['Run','RUN',.27],['KneelFire','KNEEL & FIRE',3.37],['Backflip','BACKFLIP',1.79]]) {
    await page.getByRole('button',{name:label,exact:true}).click();
    await page.getByRole('button',{name:'Pause animation',exact:true}).click();
    const stats=await page.evaluate(({clip,t})=>{
      const a=atlas,action=a.actions.get(clip);a.mixer.setTime(t);a.model.updateMatrixWorld(true);
      const min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity];let finite=true;
      a.model.traverse(o=>{if(!o.isSkinnedMesh)return;o.skeleton.update();const v=o.position.clone();for(let i=0;i<o.geometry.attributes.position.count;i+=19){o.getVertexPosition(i,v);v.applyMatrix4(o.matrixWorld);for(let j=0;j<3;j++){const n=v.getComponent(j);finite=finite&&Number.isFinite(n);min[j]=Math.min(min[j],n);max[j]=Math.max(max[j],n);}}});
      const knee=a.model.getObjectByName('shinR');const kneePos=knee.position.clone();knee.getWorldPosition(kneePos);
      const muzzle=a.motionFX.muzzle;const p=muzzle.position.clone();muzzle.getWorldPosition(p);
      return {clip,time:action.time,finite,min,max,rightKnee:kneePos.toArray(),muzzle:p.toArray(),tracks:action.getClip().tracks.length};
    },{clip,t});
    await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
    stats.fx=await page.evaluate(()=>atlas.stats.motionFX);
    await page.screenshot({path:`output/motion/${clip}.png`,scale:'css'});
    if(!stats.finite)throw new Error(`${clip} produced non-finite positions`);
    results.push(stats);
  }
  await page.getByRole('button',{name:'IDLE',exact:true}).click();
  return results;
}
