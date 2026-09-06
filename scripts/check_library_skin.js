async page => {
 const results=[];
 for(const [label,id] of [['AETHER / 02','aether-02'],['ATLAS / 09','atlas-09']]) {
  await page.getByRole('button',{name:label,exact:true}).click();await page.waitForFunction(id=>atlas.stats.character===id,id);
  results.push(await page.evaluate(()=>{
   const meshes=[];atlas.model.traverse(o=>{if(o.isSkinnedMesh)meshes.push(o)});const v=atlas.controls.target.clone(),clips=[];
   for(const name of ['Walk','PunchCombo','Collapse']) {
    atlas.setClip(name);document.querySelector('#pause').click();const duration=atlas.actions.get(name).getClip().duration;let lowest=Infinity,worstTime=0,samples=0;
    for(let t=0;t<=duration+1e-6;t+=1/60){atlas.mixer.setTime(t);atlas.model.updateMatrixWorld(true);for(const m of meshes)m.skeleton.update();let min=Infinity;
     for(const m of meshes)for(let i=0;i<m.geometry.attributes.position.count;i++){m.getVertexPosition(i,v);v.applyMatrix4(m.matrixWorld);if(!Number.isFinite(v.y))throw Error('Nonfinite skinned vertex');min=Math.min(min,v.y)}
     if(min<lowest){lowest=min;worstTime=t}samples++;
    }
    clips.push({name,samples,lowestWorldY:lowest,worstTime});
   }
   return {asset:atlas.stats.character,clips};
  }));
 }
 if(results.some(r=>r.clips.some(c=>c.lowestWorldY<-.005)))throw Error(JSON.stringify(results));
 return results;
}
