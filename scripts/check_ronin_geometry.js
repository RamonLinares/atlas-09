async page => {
 await page.waitForFunction(()=>window.atlas?.stats.character==='ronin-04');
 const reports=[];
 for(const width of [1440,390]){
  await page.setViewportSize({width,height:width===390?844:1000});
  for(const [label,name] of [['IDLE','Sentinel'],['RUN','Run'],['KNEEL & FIRE','KneelFire'],['BACKFLIP','Backflip'],['BLADE SALUTE','BladeSalute'],['SWORD SLASH','SwordSlash'],['PUNCH COMBO','PunchCombo']]){
   await page.getByRole('button',{name:label,exact:true}).click();await page.getByRole('button',{name:'Pause animation',exact:true}).click();
   reports.push(await page.evaluate(({name,width})=>{
    const a=atlas.actions.get(name),duration=a.getClip().duration;
    const meshes=[];atlas.model.traverse(o=>{if(o.isSkinnedMesh)meshes.push(o)});
    let low=Infinity;const min=[Infinity,Infinity],max=[-Infinity,-Infinity];let samples=0;
    for(let t=0;t<=duration+.001;t+=1/12){
     atlas.mixer.setTime(Math.min(t,duration));atlas.model.updateMatrixWorld(true);
     for(const mesh of meshes){mesh.skeleton.update();const v=mesh.position.clone();
      for(let i=0;i<mesh.geometry.attributes.position.count;i++){
       mesh.getVertexPosition(i,v);v.applyMatrix4(mesh.matrixWorld);
       if(!Number.isFinite(v.lengthSq()))throw Error('Non-finite skin');low=Math.min(low,v.y);v.project(atlas.camera);
       min[0]=Math.min(min[0],v.x);min[1]=Math.min(min[1],v.y);max[0]=Math.max(max[0],v.x);max[1]=Math.max(max[1],v.y);
      }
     }samples++;
    }
    if(low<-.005||min.some(v=>v<-.97)||max.some(v=>v>.97))throw Error(JSON.stringify({name,width,low,min,max}));
    return {name,width,samples,lowestWorldY:low,projectedMin:min,projectedMax:max};
   },{name,width}));
  }
 }
 await page.getByRole('button',{name:'KNEEL & FIRE',exact:true}).click();await page.getByRole('button',{name:'Pause animation',exact:true}).click();
 const firing=await page.evaluate(()=>{
  const states=[];
  for(const time of [2.42,2.8,2.90,3.38]){atlas.mixer.setTime(time);atlas.model.updateMatrixWorld(true);states.push({time,...atlas.motionFX.update('KneelFire',time)})}
  const m=atlas.motionFX.muzzle,fore=atlas.model.getObjectByName('forearmL'),hand=atlas.model.getObjectByName('handL');
  const cannonDirection=hand.getWorldPosition(hand.position.clone()).sub(fore.getWorldPosition(fore.position.clone())).normalize();
  const projectileDirection=m.position.clone().set(0,-1,0).applyQuaternion(m.getWorldQuaternion(m.quaternion.clone()));
  const alignment=projectileDirection.dot(cannonDirection);
  if(alignment<.98||!states[0].flash||states[1].flash||!states[2].flash||!states[3].flash)throw Error(JSON.stringify({alignment,states}));
  return {alignment,states};
 });
 return {reports,firing};
}
