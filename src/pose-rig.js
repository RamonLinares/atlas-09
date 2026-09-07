import * as THREE from 'three';
const identity = new THREE.Quaternion();
const clamp = THREE.MathUtils.clamp;

// Rest orientations are captured before the animation mixer touches the rig.
// Only rotations change below the root: armor weights and joint offsets stay intact.
export function createPoseRig(model) {
  const bones = new Map(), rest = new Map(), soles = [];
  const origin = model.position.clone();
  model.updateMatrixWorld(true);
  model.traverse(b => {
    if (!b.isBone) return;
    const name = b.name.replace(/(upper_arm|forearm|hand|thigh|shin|foot)([LR])$/, '$1.$2');
    bones.set(name, b);
    rest.set(name, { position: b.position.clone(), quaternion: b.quaternion.clone(), scale: b.scale.clone(), world: b.getWorldQuaternion(new THREE.Quaternion()) });
  });
  const links = [];
  for (const side of ['L', 'R']) for (const [name, child, start, end] of [
    ['upper_arm', 'forearm', 11, 13], ['forearm', 'hand', 13, 15],
    ['thigh', 'shin', 23, 25], ['shin', 'foot', 25, 27],
  ]) {
    const bone = bones.get(`${name}.${side}`), tip = bones.get(`${child}.${side}`);
    if (!bone || !tip) continue;
    links.push({ bone, name: `${name}.${side}`, side, start, end, direction: tip.getWorldPosition(new THREE.Vector3()).sub(bone.getWorldPosition(new THREE.Vector3())).normalize() });
  }
  model.traverse(mesh => {
    if (!mesh.isSkinnedMesh) return;
    const indices = mesh.geometry.attributes.skinIndex, weights = mesh.geometry.attributes.skinWeight;
    for (let i = 0; i < indices.count; i++) {
      if ([0, 1, 2, 3].some(k => weights.getComponent(i, k) > .5 && /^foot[.]?[LR]$/.test(mesh.skeleton.bones[indices.getComponent(i, k)]?.name))) soles.push([mesh, i]);
    }
  });
  let targets = new Map(), lastSeen = -Infinity, trackingMode = null;
  function restore() {
    for (const [name, b] of bones) { const r = rest.get(name); b.position.copy(r.position); b.quaternion.copy(r.quaternion); b.scale.copy(r.scale); }
    model.position.copy(origin); targets.clear(); lastSeen = -Infinity; trackingMode = null; model.updateMatrixWorld(true);
  }
  function accept(world, mirror, now, landmarks) {
    trackingMode = null;
    if (!world || world.length < 33) return false;
    const index = i => mirror && i >= 11 && i <= 32 ? (i % 2 ? i + 1 : i - 1) : i;
    const point = i => { const p = world[index(i)]; return new THREE.Vector3((mirror ? -1 : 1) * p.x, -p.y, -p.z); };
    const visible = i => {
      const p = world[index(i)], image = landmarks?.[index(i)];
      return p && (p.visibility ?? 1) > .55 && [p.x, p.y, p.z].every(Number.isFinite)
        && (!landmarks || image && (image.visibility ?? 1) > .55 && image.x >= 0 && image.x <= 1 && image.y >= 0 && image.y <= 1);
    };
    if (![11, 12].every(visible)) return false;
    const hipsVisible = [23, 24].every(visible);
    const fullBody = [23, 24, 25, 26, 27, 28].every(visible);
    const next = new Map();
    // A shoulder line supplies roll and turn even when the hips are off camera.
    // Never steer the legs with inferred, out-of-frame landmarks.
    const up = hipsVisible
      ? point(11).add(point(12)).sub(point(23)).sub(point(24)).normalize()
      : new THREE.Vector3(0, 1, 0);
    function torso(name, left, right, amount) {
      const x = point(left).sub(point(right)).normalize();
      const z = new THREE.Vector3().crossVectors(x, up).normalize();
      if (z.lengthSq() < .5) return;
      const y = new THREE.Vector3().crossVectors(z, x).normalize();
      const q = new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(x, y, z));
      // Bound unreliable monocular flips while retaining lean and turning.
      const angle = q.angleTo(identity);
      if (angle > 1.2) q.slerp(identity, 1 - 1.2 / angle);
      if (rest.has(name)) next.set(name, identity.clone().slerp(q, amount).multiply(rest.get(name).world));
    }
    if (fullBody) torso('pelvis', 23, 24, .65);
    torso('chest', 11, 12, 1);
    for (const link of links) {
      if (!fullBody && link.start >= 23) continue;
      const offset = link.side === 'R' ? 1 : 0;
      if (![link.start + offset, link.end + offset].every(visible)) continue;
      const direction = point(link.end + offset).sub(point(link.start + offset));
      if (direction.lengthSq() < .0025) continue;
      next.set(link.name, new THREE.Quaternion().setFromUnitVectors(link.direction, direction.normalize()).multiply(rest.get(link.name).world));
    }
    if (rest.has('head') && [0, 7, 8].every(visible)) {
      const face = point(0).sub(point(7).add(point(8)).multiplyScalar(.5)).normalize();
      const yaw = clamp(Math.atan2(face.x, face.z), -.8, .8);
      const pitch = clamp(-Math.atan2(face.y, Math.hypot(face.x, face.z)), -.45, .45);
      const q = new THREE.Quaternion().setFromEuler(new THREE.Euler(pitch, yaw, 0, 'YXZ'));
      next.set('head', q.multiply(rest.get('head').world));
    }
    targets = next; lastSeen = now; trackingMode = fullBody ? 'full' : 'upper'; return true;
  }
  function update(dt, now) {
    const stale = now - lastSeen > 650;
    const alpha = 1 - Math.exp(-dt * (stale ? 4 : 13));
    // Parent-first traversal converts desired world directions into local joints.
    model.traverse(b => {
      if (!b.isBone) return;
      const name = b.name.replace(/(upper_arm|forearm|hand|thigh|shin|foot)([LR])$/, '$1.$2');
      const target = !stale && targets.get(name);
      if (target) {
        const local = b.parent.getWorldQuaternion(new THREE.Quaternion()).invert().multiply(target);
        b.quaternion.slerp(local, alpha);
      } else b.quaternion.slerp(rest.get(name).quaternion, alpha);
      b.updateWorldMatrix(false, false);
    });
    model.position.y = origin.y; model.updateMatrixWorld(true);
    let floor = Infinity;
    const v = new THREE.Vector3();
    for (const [mesh, i] of soles) {
      v.fromBufferAttribute(mesh.geometry.attributes.position, i);
      mesh.applyBoneTransform(i, v).applyMatrix4(mesh.matrixWorld); floor = Math.min(floor, v.y);
    }
    if (Number.isFinite(floor)) model.position.y -= floor;
    model.updateMatrixWorld(true);
  }
  return { accept, update, restore, bones, get trackingMode() { return trackingMode; }, get supported() { return links.length === 8; } };
}
