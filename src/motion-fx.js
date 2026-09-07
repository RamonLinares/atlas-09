import * as THREE from 'three';

/** Visual pulse rounds, beams, thruster flames and contact effects, synchronized to the baked clips. */
export function createMotionFX(scene, model, options = {}) {
  const group = new THREE.Group(); group.name = 'Motion effects'; scene.add(group);
  const muzzle = model.getObjectByName(options.muzzleName || 'Muzzle_R');
  const forearm = model.getObjectByName(options.forearmName || 'forearmR'), hand = model.getObjectByName(options.handName || 'handR');
  const forearmPosition = new THREE.Vector3();
  const shotMaterial = new THREE.MeshBasicMaterial({ color: options.color || '#9dfaff', transparent: true, blending: THREE.AdditiveBlending, depthWrite: false });
  const shots = Array.from({length: 5}, () => {
    const mesh = new THREE.Mesh(new THREE.CylinderGeometry(options.radius || .035, options.radius || .035, options.length || 1.15, 8), shotMaterial.clone());
    mesh.visible = false; group.add(mesh); return mesh;
  });
  const flash = new THREE.Mesh(new THREE.IcosahedronGeometry(options.flashRadius || .18, 1), new THREE.MeshBasicMaterial({color:options.flashColor || '#caffff',transparent:true,blending:THREE.AdditiveBlending,depthWrite:false}));
  flash.visible = false; group.add(flash);
  const flashLight = new THREE.PointLight(options.color || '#79efff', 0, 7); group.add(flashLight);
  const landing = new THREE.Mesh(new THREE.RingGeometry(.85, 1.05, 64), new THREE.MeshBasicMaterial({color:'#c2cba9',transparent:true,opacity:0,side:THREE.DoubleSide,depthWrite:false}));
  landing.rotation.x = -Math.PI/2; landing.position.y=.012; group.add(landing);
  const origin = new THREE.Vector3(), direction = new THREE.Vector3(), rotation = new THREE.Quaternion();
  const up = new THREE.Vector3(0,1,0);
  // Firing windows: the classic kneel-and-fire burst plus any per-character events.
  const events = options.events || [];
  const shotWindows = [{ clip: 'KneelFire', start: 2.4, last: 5.8, interval: options.interval || .32, muzzle }]
    .concat(events.filter(e => e.type === 'shots').map(e => ({ clip: e.clip, start: e.start, last: e.end, interval: e.interval || .2, muzzle: model.getObjectByName(e.muzzle) || muzzle })));
  const beams = events.filter(e => e.type === 'beam').map(e => {
    const length = e.length || 30, radius = e.radius || .22;
    const mesh = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius * 1.15, length, 16, 1, true), new THREE.MeshBasicMaterial({ color: e.color || options.color || '#ffd27a', transparent: true, opacity: .85, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide }));
    const core = new THREE.Mesh(new THREE.CylinderGeometry(radius * .4, radius * .5, length, 8, 1, true), new THREE.MeshBasicMaterial({ color: '#ffffff', transparent: true, opacity: .9, blending: THREE.AdditiveBlending, depthWrite: false }));
    const bloom = new THREE.Mesh(new THREE.IcosahedronGeometry(radius * 3.2, 2), new THREE.MeshBasicMaterial({ color: e.flashColor || '#fff2c8', transparent: true, blending: THREE.AdditiveBlending, depthWrite: false }));
    const light = new THREE.PointLight(e.color || '#ffd27a', 0, 14);
    mesh.visible = core.visible = bloom.visible = false; group.add(mesh, core, bloom, light);
    return { ...e, length, radius, mesh, core, bloom, light, node: model.getObjectByName(e.muzzle) };
  });
  const flames = events.filter(e => e.type === 'flame').flatMap(e => (e.muzzles || [e.muzzle]).map(name => {
    const length = e.length || 2.4, radius = e.radius || .3;
    const mesh = new THREE.Mesh(new THREE.ConeGeometry(radius, length, 12, 1, true), new THREE.MeshBasicMaterial({ color: e.color || '#ffb060', transparent: true, opacity: .8, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide }));
    const core = new THREE.Mesh(new THREE.ConeGeometry(radius * .45, length * .6, 8, 1, true), new THREE.MeshBasicMaterial({ color: e.coreColor || '#fff4d6', transparent: true, opacity: .95, blending: THREE.AdditiveBlending, depthWrite: false }));
    const light = new THREE.PointLight(e.color || '#ffb060', 0, 9);
    mesh.visible = core.visible = false; group.add(mesh, core, light);
    return { ...e, length, radius, mesh, core, light, node: model.getObjectByName(name) };
  }));
  let renderedShots = 0;
  function aimFrom(node) {
    node.getWorldPosition(origin); node.getWorldQuaternion(rotation);
    direction.fromArray(options.muzzleAxis || [0,0,-1]).applyQuaternion(rotation).normalize();
  }
  function update(clip, t) {
    shots.forEach(s => {s.visible=false;}); flash.visible=false; flashLight.intensity=0; landing.material.opacity=0; renderedShots=0;
    let beamOn = false, flameOn = false;
    for (const w of shotWindows) {
      if (clip !== w.clip || !w.muzzle || t < w.start || t >= w.last + .55) continue;
      w.muzzle.getWorldPosition(origin); w.muzzle.getWorldQuaternion(rotation);
      if (forearm && hand && !options.useMuzzleDirection && w.muzzle === muzzle) {
        forearm.getWorldPosition(forearmPosition); hand.getWorldPosition(direction);
        direction.sub(forearmPosition).normalize();
      } else direction.fromArray(options.muzzleAxis || [0,0,-1]).applyQuaternion(rotation).normalize();
      const lastShot=Math.min(Math.floor((w.last-w.start)/w.interval),Math.floor((t-w.start)/w.interval));
      for(let j=0;j<shots.length;j++) {
        const index=lastShot-j,age=t-(w.start+index*w.interval);
        if(index<0||age<0||age>.65)continue;
        const s=shots[j];s.visible=true;s.position.copy(origin).addScaledVector(direction,.45+age*25);s.quaternion.setFromUnitVectors(up,direction);s.material.opacity=1-age/.65;renderedShots++;
      }
      const age=t-(w.start+lastShot*w.interval);
      if(lastShot>=0&&age>=0&&age<.13) {
        flash.visible=true;flash.position.copy(origin);flash.scale.setScalar(1+age*7);flash.material.opacity=1-age/.13;flashLight.position.copy(origin);flashLight.intensity=12*(1-age/.13);
      }
    }
    for (const b of beams) {
      const on = clip === b.clip && b.node && t >= b.start && t < b.end;
      b.mesh.visible = b.core.visible = b.bloom.visible = on; b.light.intensity = 0;
      if (!on) continue;
      beamOn = true; aimFrom(b.node);
      const age = t - b.start, fade = Math.min(1, age / .12) * Math.min(1, (b.end - t) / .2);
      const pulse = 1 + .12 * Math.sin(t * 55);
      b.mesh.position.copy(origin).addScaledVector(direction, b.length / 2); b.mesh.quaternion.setFromUnitVectors(up, direction);
      b.mesh.scale.set(pulse * fade, 1, pulse * fade); b.mesh.material.opacity = .85 * fade;
      b.core.position.copy(b.mesh.position); b.core.quaternion.copy(b.mesh.quaternion); b.core.scale.set(fade, 1, fade);
      b.bloom.position.copy(origin); b.bloom.scale.setScalar(fade * (1 + .25 * Math.sin(t * 40))); b.bloom.material.opacity = .9 * fade;
      b.light.position.copy(origin).addScaledVector(direction, .8); b.light.intensity = 30 * fade;
    }
    for (const f of flames) {
      const on = clip === f.clip && f.node && t >= f.start && t < f.end;
      f.mesh.visible = f.core.visible = on; f.light.intensity = 0;
      if (!on) continue;
      flameOn = true; aimFrom(f.node);
      const age = t - f.start, fade = Math.min(1, age / .15) * Math.min(1, (f.end - t) / .25);
      const flicker = fade * (.85 + .15 * Math.sin(t * 70 + f.length) * Math.sin(t * 23));
      f.mesh.position.copy(origin).addScaledVector(direction, f.length / 2 * flicker); f.mesh.quaternion.setFromUnitVectors(up, direction.clone().negate());
      f.mesh.scale.set(flicker, flicker, flicker); f.mesh.material.opacity = .8 * fade;
      f.core.position.copy(origin).addScaledVector(direction, f.length * .3 * flicker); f.core.quaternion.copy(f.mesh.quaternion); f.core.scale.setScalar(flicker);
      f.light.position.copy(origin).addScaledVector(direction, .6); f.light.intensity = 10 * flicker;
    }
    if(clip==='Backflip') {
      const age=t-2.88;
      if(age>=0&&age<.6) {landing.scale.setScalar(1+age*5);landing.material.opacity=.35*(1-age/.6);}
    }
    return {muzzleFound:!!muzzle,visibleProjectiles:renderedShots,flash:flash.visible,beam:beamOn,flame:flameOn};
  }
  function dispose() {
    scene.remove(group);
    group.traverse(o => { o.geometry?.dispose(); o.material?.dispose(); });
    shotMaterial.dispose();
  }
  return {group,update,muzzle,dispose};
}
