import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { createMotionFX } from '../motion-fx.js';

const loader = new GLTFLoader();
const cache = new Map();

export function loadFighterModel(profile) {
  if (!cache.has(profile.id)) cache.set(profile.id, loader.loadAsync(profile.model));
  return cache.get(profile.id);
}

/**
 * One mecha in the arena: baked-clip playback, locomotion, attacks with timed
 * hit windows, blocks, dodges, hit reactions and death. Facing is +Z.
 */
export class Fighter {
  constructor(profile, gltf, scene, { flip = false } = {}) {
    this.profile = profile; this.scene = scene;
    this.model = gltf.scene; this.flip = flip;
    const box = new THREE.Box3().setFromObject(this.model);
    this.height = box.getSize(new THREE.Vector3()).y;
    this.model.position.set(-(box.min.x + box.max.x) / 2, -box.min.y, -(box.min.z + box.max.z) / 2);
    this.root = new THREE.Group(); this.root.add(this.model); scene.add(this.root);
    this.model.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; o.frustumCulled = false; } });
    this.materials = [];
    this.model.traverse(o => { if (o.isMesh) for (const m of Array.isArray(o.material) ? o.material : [o.material]) this.materials.push(m); });
    this.mixer = new THREE.AnimationMixer(this.model);
    this.actions = new Map(gltf.animations.map(c => [c.name, this.mixer.clipAction(c)]));
    this.fx = createMotionFX(scene, this.model, profile.effects);
    this.health = 100; this.state = 'idle'; this.current = null; this.currentName = null;
    this.attack = null; this.blocking = null; this.dead = false; this.flinch = 0; this.flash = 0;
    this.velocity = new THREE.Vector3(); this.pushback = new THREE.Vector3(); this.timers = { hitLock: 0, action: 0 };
    this.stats = { landed: 0, taken: 0 };
    this.mixer.addEventListener('finished', e => this.onFinished(e.action));
    this.play('Sentinel');
  }
  get position() { return this.root.position; }
  play(name, { once = false, fade = .18, start = 0, timeScale = 1 } = {}) {
    const action = this.actions.get(name); if (!action) return null;
    if (this.current && this.current !== action) this.current.fadeOut(fade);
    action.reset().setLoop(once ? THREE.LoopOnce : THREE.LoopRepeat, once ? 1 : Infinity);
    action.clampWhenFinished = once; action.time = start; action.timeScale = timeScale;
    action.setEffectiveWeight(1).fadeIn(this.current === action ? 0 : fade).play();
    this.current = action; this.currentName = name; return action;
  }
  onFinished(action) {
    if (this.dead) return;
    if (this.attack && action === this.attack.action) this.endAttack();
    else if (this.state === 'dodge' || this.state === 'hit' || this.state === 'block') this.idle();
  }
  idle() { this.state = 'idle'; this.attack = null; this.blocking = null; this.play('Sentinel'); }
  endAttack() { this.attack = null; this.state = 'idle'; this.play('Sentinel'); }
  canAct() { return !this.dead && (this.state === 'idle' || this.state === 'move'); }
  startAttack(kind) {
    if (!this.canAct()) return false;
    const spec = this.profile[kind]; if (!spec || !this.actions.has(spec.clip)) return false;
    const action = this.play(spec.clip, { once: true, start: spec.start || 0, timeScale: spec.timeScale || 1 });
    this.attack = { kind, spec, action, fired: new Set(), end: spec.end ?? action.getClip().duration };
    this.state = 'attack'; return true;
  }
  startBlock() {
    const spec = this.profile.block; if (!spec || !this.canAct()) return false;
    const action = this.play(spec.clip, { once: true }); this.blocking = { spec, action }; this.state = 'block'; return true;
  }
  startDodge(direction) {
    if (!this.canAct() || !this.actions.has(this.profile.dodge)) return false;
    this.play(this.profile.dodge, { once: true }); this.state = 'dodge'; this.dodgeDirection = direction.clone(); return true;
  }
  /** Damage arriving from `attacker`. Returns the damage actually applied. */
  receive(damage, attacker, heavy, stagger = true) {
    if (this.dead) return 0;
    if (this.state === 'dodge') {
      const t = this.current.time / this.current.getClip().duration; if (t > .15 && t < .8) return 0;
    }
    if (this.blocking) {
      const { spec, action } = this.blocking;
      if (action.time >= spec.t0 && action.time <= spec.t1) { damage = Math.round(damage * (1 - spec.reduce)); this.flash = .3; }
    }
    this.health = Math.max(0, this.health - damage); this.stats.taken += damage;
    const away = this.root.position.clone().sub(attacker.root.position).setY(0).normalize();
    this.pushback.copy(away).multiplyScalar(!stagger ? 1.5 : heavy ? 9 : 4); this.flash = .35;
    if (this.health <= 0) { this.die(); return damage; }
    // Ranged rounds and beams chip without staggering; attacks have super
    // armor against light melee hits; heavy melee hits always interrupt.
    if (!stagger) return damage;
    if (this.state === 'attack' && !heavy) return damage;
    const clip = heavy && this.profile.hitHeavy ? this.profile.hitHeavy : this.profile.hit;
    this.attack = null; this.blocking = null;
    if (clip && this.actions.has(clip)) { this.state = 'hit'; this.play(clip, { once: true, timeScale: 1.3 }); }
    else { this.state = 'hit'; this.flinch = heavy ? .5 : .3; this.timers.hitLock = this.flinch; }
    return damage;
  }
  die() {
    this.dead = true; this.state = 'dead'; this.attack = null; this.blocking = null;
    const clip = this.profile.death;
    if (clip !== 'topple' && this.actions.has(clip)) this.play(clip, { once: true, fade: .12 });
    else { this.play('Sentinel', { fade: .3 }); this.topple = 0; }
  }
  /** Facing target on the ground plane; strafe/advance input in local terms. */
  update(dt, opponent, input) {
    const toOpponent = opponent.root.position.clone().sub(this.root.position).setY(0);
    const distance = toOpponent.length(); toOpponent.normalize();
    if (!this.dead) {
      const yaw = Math.atan2(toOpponent.x, toOpponent.z);
      let current = this.root.rotation.y; let delta = yaw - current;
      delta = Math.atan2(Math.sin(delta), Math.cos(delta)); this.root.rotation.y = current + delta * Math.min(1, dt * 8);
    }
    if (this.state === 'hit' && this.flinch > 0) {
      this.timers.hitLock -= dt;
      if (this.timers.hitLock <= 0) { this.flinch = 0; this.idle(); }
    }
    const right = new THREE.Vector3(toOpponent.z, 0, -toOpponent.x);
    const wanted = new THREE.Vector3();
    if (input && (this.state === 'idle' || this.state === 'move')) {
      wanted.addScaledVector(toOpponent, input.forward).addScaledVector(right, input.strafe);
      if (wanted.lengthSq() > 1) wanted.normalize();
      const moving = wanted.lengthSq() > .01;
      if (moving && this.state !== 'move') { this.state = 'move'; this.play('Run', { fade: .22 }); }
      if (!moving && this.state === 'move') { this.idle(); }
      if (moving) { this.current.timeScale = .85 + .35 * wanted.length(); }
    }
    this.velocity.lerp(wanted.multiplyScalar(this.profile.speed), Math.min(1, dt * 9));
    this.root.position.addScaledVector(this.velocity, dt);
    if (this.state === 'dodge') {
      const t = this.current.time / this.current.getClip().duration;
      if (t > .18 && t < .8) this.root.position.addScaledVector(this.dodgeDirection, dt * 18 * Math.sin((t - .18) / .62 * Math.PI));
    }
    this.root.position.addScaledVector(this.pushback, dt); this.pushback.multiplyScalar(Math.max(0, 1 - dt * 7));
    if (this.topple !== undefined && this.dead) {
      this.topple = Math.min(1, this.topple + dt / 1.3); const k = this.topple * this.topple * (3 - 2 * this.topple);
      this.model.rotation.x = -k * Math.PI * .47; this.model.position.y = -k * this.height * .02;
    }
    const radius = 78 - this.profile.radius; const flat = this.root.position.clone().setY(0);
    if (flat.length() > radius) { flat.setLength(radius); this.root.position.x = flat.x; this.root.position.z = flat.z; }
    this.mixer.update(dt);
    if (this.attack && this.current.time >= this.attack.end) this.endAttack();
    this.flash = Math.max(0, this.flash - dt);
    for (const m of this.materials) if (m.emissive) { m.emissiveIntensity = (m.userData.base ??= m.emissiveIntensity || 1) * (1 + this.flash * 3); }
    this.model.updateMatrixWorld(true);
    this.fx.update(this.attack ? this.attack.spec.clip : this.currentName, this.current?.time ?? 0);
    return distance;
  }
  /** Hit windows that land this frame against `opponent`. */
  resolveHits(opponent, distance, facingDot) {
    if (!this.attack) return [];
    const landed = []; const t = this.attack.action.time;
    this.attack.spec.hits.forEach((hit, i) => {
      if (this.attack.fired.has(i) || t < hit.t0 || t > hit.t1) return;
      if (t > hit.t0 && t <= hit.t1) {
        const inArc = hit.kind === 'radial' || facingDot >= Math.cos(THREE.MathUtils.degToRad(hit.arc / 2));
        const reach = hit.range + this.profile.radius * .5 + opponent.profile.radius;
        if (distance <= reach && inArc) { this.attack.fired.add(i); landed.push(hit); }
      }
    });
    return landed;
  }
  dispose() {
    this.scene.remove(this.root); this.fx.dispose(); this.mixer.stopAllAction(); this.mixer.uncacheRoot(this.model);
    for (const m of this.materials) m.dispose();
  }
}
