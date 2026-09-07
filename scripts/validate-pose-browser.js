// Run in the viewer's browser context; exercises real GLB rigs with controlled poses.
async () => {
  const Vector3 = window.atlas.model.position.constructor;
  const report = [];
  const assert = (value, text) => { if (!value) throw new Error(text); };
  window.atlas.webcam.stop();
  function pose(kind) {
    const p = Array.from({length:33}, () => ({x:0,y:0,z:0,visibility:1}));
    const set = (i,x,y,z=0) => Object.assign(p[i],{x,y,z});
    set(11,.22,-.55);set(12,-.22,-.55);set(23,.13,0);set(24,-.13,0);
    set(13,.26,-.28);set(14,-.26,-.28);set(15,.27,-.02);set(16,-.27,-.02);
    set(25,.14,.43);set(26,-.14,.43);set(27,.15,.85);set(28,-.15,.85);
    set(7,.07,-.75);set(8,-.07,-.75);set(0,0,-.75,-.10);
    if(kind==='raised') {set(13,.22,-.86);set(15,.22,-1.14);}
    if(kind==='tpose') {set(13,.52,-.55);set(15,.82,-.55);set(14,-.52,-.55);set(16,-.82,-.55);}
    if(kind==='squat') {set(25,.18,.25,-.3);set(26,-.18,.25,-.3);set(27,.18,.55);set(28,-.18,.55);set(13,.24,-.55,-.3);set(15,.24,-.55,-.6);set(14,-.24,-.55,-.3);set(16,-.24,-.55,-.6);}
    return p;
  }
  for (const id of ['atlas-09','aether-02','seraph-03','ronin-04','scorpio-05']) {
    await window.atlas.loadCharacter(id);
    const {poseRig:rig,model,mixer}=window.atlas;
    // Pause through the actual UI so the render loop cannot overwrite test poses.
    if(document.querySelector('#pause').getAttribute('aria-label')==='Pause animation')document.querySelector('#pause').click();
    mixer.stopAllAction();rig.restore();
    assert(rig.supported,`${id}: unsupported rig`);
    const offsets=[...rig.bones].map(([n,b])=>[n,b.position.clone()]);
    const neutral=[...rig.bones].map(([n,b])=>[n,b.quaternion.clone()]);
    const start=performance.now(), result={id,poses:[]};
    const world=(n)=>rig.bones.get(n).getWorldPosition(new Vector3());
    for(const kind of ['standing','raised','tpose','squat']) {
      rig.restore();assert(rig.accept(pose(kind),false,start),`${id} no pose`);
      for(let i=0;i<80;i++)rig.update(1/60,start);
      for(const [n,v] of offsets)assert(rig.bones.get(n).position.distanceTo(v)<1e-8,`${id} ${n} joint separated`);
      for(const b of rig.bones.values())assert(b.quaternion.toArray().every(Number.isFinite),`${id} invalid rotation`);
      const arm=world('forearm.L').sub(world('upper_arm.L')).normalize();
      if(kind==='raised')assert(arm.y>.97,`${id} raised arm did not raise: ${arm.toArray()}`);
      if(kind==='tpose')assert(arm.x>.97,`${id} T pose did not spread: ${arm.toArray()}`);
      let footMin=Infinity, allMin=Infinity, triangleError=0;
      model.traverse(mesh=>{
        if(!mesh.isSkinnedMesh)return;
        const a=mesh.geometry.attributes, v=new Vector3();
        for(let i=0;i<a.position.count;i++) {
          v.fromBufferAttribute(a.position,i);mesh.applyBoneTransform(i,v).applyMatrix4(mesh.matrixWorld);allMin=Math.min(allMin,v.y);
          if(/^foot[.]?[LR]$/.test(mesh.skeleton.bones[a.skinIndex.getX(i)]?.name))footMin=Math.min(footMin,v.y);
        }
        const idx=mesh.geometry.index;
        for(let j=0;j<idx.count;j+=3*23){
          const aidx=idx.getX(j),bidx=idx.getX(j+1),a0=new Vector3().fromBufferAttribute(a.position,aidx),b0=new Vector3().fromBufferAttribute(a.position,bidx);
          const expected=a0.distanceTo(b0)*model.scale.x;
          const actual=mesh.applyBoneTransform(aidx,a0).applyMatrix4(mesh.matrixWorld).distanceTo(mesh.applyBoneTransform(bidx,b0).applyMatrix4(mesh.matrixWorld));
          triangleError=Math.max(triangleError,Math.abs(actual-expected));
        }
      });
      assert(Math.abs(footMin)<.001,`${id} feet not grounded: ${footMin}`);
      assert(triangleError<.001,`${id} armor stretch: ${triangleError}`);
      result.poses.push({kind,arm:arm.toArray(),footMin,allMin,triangleError});
    }
    rig.restore();rig.accept(pose('raised'),true,start);for(let i=0;i<80;i++)rig.update(1/60,start);
    assert(world('forearm.R').sub(world('upper_arm.R')).normalize().y>.97,`${id} mirror side incorrect`);
    rig.accept([],true,start);for(let i=0;i<180;i++)rig.update(1/60,start+1000);
    for(const [n,q] of neutral)assert(rig.bones.get(n).quaternion.angleTo(q)<.001,`${id} ${n} did not recover after tracking loss`);
    result.lossRecovered=true;rig.restore();window.atlas.setClip('Sentinel');report.push(result);
  }
  await window.atlas.loadCharacter('seraph-03');
  return report;
}
