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
 * One mecha on the lane. Position is a scalar `x` along world X; the fighter
 * always faces its opponent (+X is rotation.y = +90 degrees). Moves are short
 * cuts of the baked clips with cancel points; blocks hold a clip frame; the
 * dodge is the backflip with invulnerable frames.
 */
export class Fighter {
  constructor(profile, gltf, scene) {
    this.profile = profile; this.scene = scene; this.model = gltf.scene;
    const box = new THREE.Box3().setFromObject(this.model);
    this.height = box.getSize(new THREE.Vector3()).y; this.scale = this.height / 18;
    this.model.position.set(-(box.min.x + box.max.x) / 2, -box.min.y, -(box.min.z + box.max.z) / 2);
    this.root = new THREE.Group(); this.root.add(this.model); scene.add(this.root);
    this.materials = [];
    this.model.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; o.frustumCulled = false; for (const m of Array.isArray(o.material) ? o.material : [o.material]) this.materials.push(m); } });
    this.mixer = new THREE.AnimationMixer(this.model);
    this.actions = new Map(gltf.animations.map(c => [c.name, this.mixer.clipAction(c)]));
    this.fx = createMotionFX(scene, this.model, profile.effects);
    this.health = 100; this.state = 'idle'; this.current = null; this.currentName = null;
    this.attack = null; this.queued = null; this.blocking = false; this.dead = false; this.flash = 0;
    this.x = 0; this.facing = 1; this.vx = 0; this.push = 0; this.hitstop = 0; this.stagger = 0; this.tell = 0; this.dash = 0; this.dashDir = 0;
    this.stats = { landed: 0, taken: 0 }; this.lean = 0;
    this.mixer.addEventListener('finished', e => this.onFinished(e.action));
    this.play('Sentinel');
  }
  get speed() { return 22 * this.profile.speed * this.scale; }
  play(name, { once = false, fade = .12, start = 0, timeScale = 1 } = {}) {
    const action = this.actions.get(name); if (!action) return null;
    if (this.current && this.current !== action) this.current.fadeOut(fade);
    action.reset().setLoop(once ? THREE.LoopOnce : THREE.LoopRepeat, once ? 1 : Infinity);
    action.clampWhenFinished = once; action.time = start; action.timeScale = timeScale; action.paused = false;
    action.setEffectiveWeight(1).fadeIn(this.current === action ? 0 : fade).play();
    this.current = action; this.currentName = name; return action;
  }
  onFinished(action) {
    if (this.dead) return;
    if (this.attack && action === this.attack.action) this.endAttack();
    else if (this.state === 'dodge' || this.state === 'hit') this.idle();
  }
  idle() { this.state = 'idle'; this.attack = null; this.queued = null; this.blocking = false; this.play('Sentinel', { fade: .16 }); }
  endAttack() { this.attack = null; this.queued = null; this.state = 'idle'; this.play('Sentinel', { fade: .16 }); }
  free() { return !this.dead && (this.state === 'idle' || this.state === 'move' || this.state === 'block'); }
  cancellable() { return this.state === 'attack' && !!this.attack && this.attack.action.time >= this.attack.move.cancel; }
  /** Start (or queue) a move by name; chained presses continue combos. */
  startMove(name) {
    if (this.dead) return false;
    const move = this.profile.moves[name]; if (!move || !this.actions.has(move.clip)) return false;
    if (this.state === 'attack' && this.attack) {
      const next = this.attack.move.chain;
      if (next && next.startsWith(name)) { this.queued = next; return true; }
      if (!this.cancellable()) return false;
    } else if (!this.free()) return false;
    this.begin(move);
    return true;
  }
  begin(move) {
    const continuing = this.attack && this.attack.move.clip === move.clip && Math.abs(this.attack.action.time - move.start) < .3;
    const action = continuing ? this.attack.action : this.play(move.clip, { once: true, start: move.start, timeScale: move.timeScale || 1, fade: .08 });
    if (continuing) action.timeScale = move.timeScale || 1;
    this.attack = { move, action, fired: new Set() }; this.queued = null; this.state = 'attack'; this.blocking = false;
  }
  startBlock() {
    if (!(this.free() || this.cancellable())) return false;
    if (this.state === 'block') return true;
    this.state = 'block'; this.attack = null; this.blocking = true;
    const spec = this.profile.block;
    if (spec && this.actions.has(spec.clip)) { const a = this.play(spec.clip, { once: true, fade: .1 }); a.time = spec.hold; a.paused = true; }
    else this.play('Sentinel', { fade: .1 });
    return true;
  }
  stopBlock() { if (this.state === 'block') this.idle(); }
  startDodge() {
    if (!(this.free() || this.cancellable()) || !this.actions.has(this.profile.dodge)) return false;
    this.attack = null; this.blocking = false; this.state = 'dodge'; this.play(this.profile.dodge, { once: true, timeScale: 1.7, fade: .08 }); return true;
  }
  /** Damage from `attacker`; returns what was applied, -1 when dodged, or a negative-zero-like 0 when blocked fully. */
  receive(hit, attacker) {
    if (this.dead) return { damage: 0 };
    let damage = hit.damage; const heavy = !!hit.stagger;
    if (this.state === 'dodge') { const t = this.current.time / this.current.getClip().duration; if (t > .12 && t < .82) return { dodged: true, damage: 0 }; }
    if (this.blocking) {
      const reduce = this.profile.block ? this.profile.block.reduce : .6;
      damage = Math.max(1, Math.round(damage * (1 - reduce))); this.flash = .25; this.push = attacker.facing * 4;
      this.health = Math.max(0, this.health - damage); this.stats.taken += damage; if (this.health <= 0) this.die();
      return { blocked: true, damage };
    }
    this.health = Math.max(0, this.health - damage); this.stats.taken += damage; this.flash = .35;
    this.push = attacker.facing * (heavy ? 14 : hit.kind === 'ranged' ? 2 : 6);
    if (this.health <= 0) { this.die(); return { damage, killed: true, heavy }; }
    if (hit.kind === 'ranged' || (this.state === 'attack' && !heavy)) return { damage, heavy };
    this.attack = null; this.queued = null; this.blocking = false; this.state = 'hit';
    const clip = heavy && this.profile.hitHeavy ? this.profile.hitHeavy : this.profile.hit;
    if (clip && this.actions.has(clip)) this.play(clip, { once: true, timeScale: heavy ? 1.4 : 1.8, fade: .06 });
    else { this.play('Sentinel', { fade: .06 }); this.stagger = heavy ? .45 : .25; }
    return { damage, heavy };
  }
  die() {
    this.dead = true; this.state = 'dead'; this.attack = null; this.blocking = false;
    const clip = this.profile.death;
    if (clip !== 'topple' && this.actions.has(clip)) this.play(clip, { once: true, fade: .1 });
    else { this.play('Sentinel', { fade: .3 }); this.topple = 0; }
  }
  /** `input.move` is -1..1 along X, `input.dash` a one-shot burst request. */
  update(dt, opponent, input) {
    this.facing = opponent.x >= this.x ? 1 : -1;
    const sim = this.hitstop > 0 ? 0 : dt; this.hitstop = Math.max(0, this.hitstop - dt);
    if (this.stagger > 0) { this.stagger -= sim; if (this.stagger <= 0 && this.state === 'hit') this.idle(); }
    if (this.tell > 0) this.tell -= sim;
    let wanted = 0;
    const mobile = !this.dead && (this.state === 'idle' || this.state === 'move' || this.cancellable());
    if (input && mobile) {
      wanted = THREE.MathUtils.clamp(input.move, -1, 1);
      if (input.dash && wanted) { this.dash = .22; this.dashDir = Math.sign(wanted); }
      const moving = Math.abs(wanted) > .05;
      if (moving && this.state !== 'move') { this.attack = null; this.queued = null; this.state = 'move'; this.play('Run', { fade: .1 }); }
      if (!moving && this.state === 'move') this.idle();
      if (moving) { const forward = Math.sign(wanted) === this.facing; this.current.timeScale = (forward ? 1.35 : -1.1) * this.profile.speed; this.lean = THREE.MathUtils.lerp(this.lean, forward ? .12 : -.06, sim * 8); }
    }
    if (this.state !== 'move') this.lean = THREE.MathUtils.lerp(this.lean, 0, sim * 8);
    const target = wanted * this.speed + (this.dash > 0 ? this.dashDir * this.speed * 2.2 : 0);
    if (this.dash > 0) this.dash -= sim;
    this.vx = THREE.MathUtils.lerp(this.vx, target, Math.min(1, sim * 18));
    this.x += this.vx * sim;
    if (this.state === 'dodge') { const t = this.current.time / this.current.getClip().duration; if (t > .15 && t < .8) this.x -= this.facing * sim * 30 * this.scale * Math.sin((t - .15) / .65 * Math.PI); }
    this.x += this.push * sim; this.push *= Math.max(0, 1 - sim * 8);
    const limit = 62 * this.scale; this.x = THREE.MathUtils.clamp(this.x, -limit, limit);
    if (this.topple !== undefined && this.dead) { this.topple = Math.min(1, this.topple + dt / 1.2); const k = this.topple * this.topple * (3 - 2 * this.topple); this.model.rotation.x = -k * Math.PI * .47; }
    this.root.position.set(this.x, 0, 0);
    const yaw = this.facing * Math.PI / 2; let d = yaw - this.root.rotation.y; d = Math.atan2(Math.sin(d), Math.cos(d));
    this.root.rotation.y += d * Math.min(1, dt * 10);
    if (this.topple === undefined) this.model.rotation.x = this.lean;
    this.mixer.update(sim);
    if (this.attack) {
      const t = this.attack.action.time; const hits = this.attack.move.hits;
      if (this.queued && t >= hits[hits.length - 1].t1) this.begin(this.profile.moves[this.queued]);
      else if (t >= this.attack.move.end) this.endAttack();
    }
    this.flash = Math.max(0, this.flash - dt);
    const glow = 1 + this.flash * 3 + (this.tell > 0 ? 2.5 : 0);
    for (const m of this.materials) if (m.emissive) m.emissiveIntensity = (m.userData.base ??= m.emissiveIntensity || 1) * glow;
    this.model.updateMatrixWorld(true);
    this.fx.update(this.attack ? this.attack.move.clip : this.currentName, this.current?.time ?? 0);
  }
  /** Hit windows landing this frame against `opponent` at lane `distance`. */
  resolveHits(opponent, distance) {
    if (!this.attack) return [];
    const landed = []; const t = this.attack.action.time; const { move } = this.attack;
    move.hits.forEach((hit, i) => {
      if (this.attack.fired.has(i) || t < hit.t0 || t > hit.t1) return;
      const reach = hit.range * this.scale + this.profile.radius * .5 + opponent.profile.radius * .5;
      if (distance <= reach) { this.attack.fired.add(i); landed.push(hit); }
    });
    return landed;
  }
  dispose() {
    this.scene.remove(this.root); this.fx.dispose(); this.mixer.stopAllAction(); this.mixer.uncacheRoot(this.model);
    for (const m of this.materials) m.dispose();
  }
}
