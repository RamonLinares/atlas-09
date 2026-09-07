async page => {
 const errors=[];page.on('pageerror',e=>errors.push(e.message));const reports=[],playback=[];
 const characters=[['atlas-09',10,['HitChest','HitHead','Knockback']],['aether-02',11,['HitChest','HitHead','Knockback','DodgeRoll']],['seraph-03',9,['HitChest','HitHead','Knockback']],['ronin-04',12,['HitChest','HitHead','Knockback','SwordCombo','SwordBlock']]];
 for(const [id,count,clips] of characters){
  await page.goto(`http://127.0.0.1:5175/?character=${id}`);await page.waitForFunction(id=>window.atlas?.stats.character===id,id);
  if(await page.locator('[data-clip]').count()!==count)throw Error(`${id}: missing controls`);
  for(const width of [1440,390]){
   await page.setViewportSize({width,height:width===390?844:1000});
   for(const name of clips){
    await page.locator(`[data-clip="${name}"]`).click();await page.getByRole('button',{name:'Pause animation',exact:true}).click();
    reports.push(await page.evaluate(({name,width})=>{
     const a=atlas.actions.get(name),duration=a.getClip().duration,meshes=[];atlas.model.traverse(o=>{if(o.isSkinnedMesh)meshes.push(o)});
     let minY=Infinity,maxRollGap=0,minX=Infinity,maxX=-Infinity,minScreenY=Infinity,maxScreenY=-Infinity,samples=0;
     for(let t=0;t<=duration+.001;t+=1/15){
      atlas.mixer.setTime(Math.min(t,duration));atlas.model.updateMatrixWorld(true);let floor=Infinity;
      for(const mesh of meshes){
       mesh.skeleton.update();const v=mesh.position.clone();
       for(let i=0;i<mesh.geometry.attributes.position.count;i++){
        mesh.getVertexPosition(i,v);v.applyMatrix4(mesh.matrixWorld);if(!Number.isFinite(v.lengthSq()))throw Error('Non-finite skin');floor=Math.min(floor,v.y);v.project(atlas.camera);
        minX=Math.min(minX,v.x);maxX=Math.max(maxX,v.x);minScreenY=Math.min(minScreenY,v.y);maxScreenY=Math.max(maxScreenY,v.y);
       }
      }
      minY=Math.min(minY,floor);if(name==='DodgeRoll'&&t>.6&&t<1.95)maxRollGap=Math.max(maxRollGap,floor);samples++;
     }
     const toolbar=document.querySelector('.toolbar').getBoundingClientRect(),inspector=document.querySelector('.inspector').getBoundingClientRect();
     const overflow=document.documentElement.scrollWidth>innerWidth;
     if(minY<-.008||minX<-.97||maxX>.97||minScreenY<-.96||maxScreenY>.97||overflow)throw Error(JSON.stringify({id:atlas.stats.character,name,width,minY,minX,maxX,minScreenY,maxScreenY,overflow}));
     if(name==='DodgeRoll'&&maxRollGap>.04)throw Error(`Roll floats ${maxRollGap}`);
     if(width===390&&inspector.bottom>toolbar.top-5)throw Error('Inspection controls overlap animations');
     return {character:atlas.stats.character,name,width,samples,minY,maxRollGap,projectedBounds:[minX,minScreenY,maxX,maxScreenY],overflow};
    },{name,width}));
    await page.evaluate(({name})=>atlas.mixer.setTime(name==='Knockback'?atlas.actions.get(name).getClip().duration:name==='DodgeRoll'?1.05:name==='SwordCombo'?1.25:.65),{name});
    await page.screenshot({path:`output/playwright/combat-${id}-${width}-${name}.png`});
   }
  }
  await page.setViewportSize({width:1440,height:1000});
  for(const name of clips){
   await page.locator(`[data-clip="${name}"]`).click();
   playback.push(await page.evaluate(name=>new Promise((resolve,reject)=>{
    const a=atlas.actions.get(name),duration=a.getClip().duration;let frames=0,last=a.time,end=false;
    const timeout=setTimeout(()=>reject(Error(`${name} playback did not finish`)),(duration+5)*1000);
    function next(){frames++;if(a.time>duration-.1)end=true;
     if(end&&(name==='Knockback'?a.paused:a.time<last)){clearTimeout(timeout);resolve({character:atlas.stats.character,name,frames,completed:true,held:name==='Knockback'});return}
     last=a.time;requestAnimationFrame(next);
    }requestAnimationFrame(next);
   }),name));
  }
 }
 if(errors.length)throw Error(JSON.stringify(errors));return {reports,playback,errors};
}
