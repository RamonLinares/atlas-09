import * as THREE from 'three';

/** Visual pulse rounds and contact effects, synchronized to the baked clips. */
export function createMotionFX(scene, model) {
  const group = new THREE.Group(); group.name = 'Motion effects'; scene.add(group);
  const muzzle = model.getObjectByName('Muzzle_R');
  const forearm = model.getObjectByName('forearmR'), hand = model.getObjectByName('handR');
  const forearmPosition = new THREE.Vector3();
  const shotMaterial = new THREE.MeshBasicMaterial({ color: '#9dfaff', transparent: true, blending: THREE.AdditiveBlending, depthWrite: false });
  const shots = Array.from({length: 5}, () => {
    const mesh = new THREE.Mesh(new THREE.CylinderGeometry(.035, .035, 1.15, 8), shotMaterial.clone());
    mesh.visible = false; group.add(mesh); return mesh;
  });
  const flash = new THREE.Mesh(new THREE.IcosahedronGeometry(.18, 1), new THREE.MeshBasicMaterial({color:'#caffff',transparent:true,blending:THREE.AdditiveBlending,depthWrite:false}));
  flash.visible = false; group.add(flash);
  const flashLight = new THREE.PointLight('#79efff', 0, 7); group.add(flashLight);
  const landing = new THREE.Mesh(new THREE.RingGeometry(.85, 1.05, 64), new THREE.MeshBasicMaterial({color:'#c2cba9',transparent:true,opacity:0,side:THREE.DoubleSide,depthWrite:false}));
  landing.rotation.x = -Math.PI/2; landing.position.y=.012; group.add(landing);
  const origin = new THREE.Vector3(), direction = new THREE.Vector3(), rotation = new THREE.Quaternion();
  const up = new THREE.Vector3(0,1,0);
  let renderedShots = 0;
  function update(clip, t) {
    shots.forEach(s => {s.visible=false;}); flash.visible=false; flashLight.intensity=0; landing.material.opacity=0; renderedShots=0;
    if (clip === 'KneelFire' && muzzle && t >= 2.4 && t < 6.35) {
      muzzle.getWorldPosition(origin); muzzle.getWorldQuaternion(rotation);
      if (forearm && hand) {
        forearm.getWorldPosition(forearmPosition); hand.getWorldPosition(direction);
        direction.sub(forearmPosition).normalize();
      } else direction.set(0,0,-1).applyQuaternion(rotation).normalize();
      const lastShot=Math.min(10,Math.floor((t-2.4)/.32));
      for(let j=0;j<shots.length;j++) {
        const index=lastShot-j,age=t-(2.4+index*.32);
        if(index<0||age<0||age>.65)continue;
        const s=shots[j];s.visible=true;s.position.copy(origin).addScaledVector(direction,.45+age*25);s.quaternion.setFromUnitVectors(up,direction);s.material.opacity=1-age/.65;renderedShots++;
      }
      const age=t-(2.4+lastShot*.32);
      if(lastShot>=0&&age>=0&&age<.13) {
        flash.visible=true;flash.position.copy(origin);flash.scale.setScalar(1+age*7);flash.material.opacity=1-age/.13;flashLight.position.copy(origin);flashLight.intensity=12*(1-age/.13);
      }
    }
    if(clip==='Backflip') {
      const age=t-2.88;
      if(age>=0&&age<.6) {landing.scale.setScalar(1+age*5);landing.material.opacity=.35*(1-age/.6);}
    }
    return {muzzleFound:!!muzzle,visibleProjectiles:renderedShots,flash:flash.visible};
  }
  return {group,update,muzzle};
}
