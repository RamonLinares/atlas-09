import * as THREE from 'three';

/**
 * Opponent brain: closes distance, picks attacks by reach, keeps a cooldown,
 * strafes while waiting and sometimes dodges or blocks incoming attacks.
 */
export function createAI(me, target, { aggression = .55, reaction = .28 } = {}) {
  let cooldown = 2.0, strafeDir = 1, strafeTimer = 0, sawAttackAt = -1, responded = false, heavies = 0, reposition = 0, repositionDir = 0;
  const input = { forward: 0, strafe: 0 };
  // Ranged windows reach 70 m in the rules, but the brain only commits to a
  // shot from closer, so the fight keeps moving instead of sniping.
  const reach = spec => Math.min(46, Math.max(...spec.hits.map(h => h.range))) + me.profile.radius + target.profile.radius * .5;
  const lightReach = () => reach(me.profile.light);
  const heavyReach = () => reach(me.profile.heavy);
  return {
    input,
    update(dt, distance, now) {
      input.forward = 0; input.strafe = 0;
      if (me.dead || target.dead) return;
      cooldown -= dt; strafeTimer -= dt;
      if (strafeTimer <= 0) { strafeDir = Math.random() < .5 ? -1 : 1; strafeTimer = 1.2 + Math.random() * 1.8; }
      // React to an incoming attack once, after a human-ish delay.
      if (target.attack) {
        if (sawAttackAt < 0) { sawAttackAt = now; responded = false; }
        else if (!responded && now - sawAttackAt > reaction) {
          responded = true; const roll = Math.random();
          if (roll < .3 && me.profile.block) me.startBlock();
          else if (roll < .55) me.startDodge(new THREE.Vector3(target.root.position.x - me.root.position.x, 0, target.root.position.z - me.root.position.z).normalize().negate());
        }
      } else sawAttackAt = -1;
      if (!me.canAct()) return;
      const light = lightReach(), heavy = heavyReach();
      if (cooldown <= 0) {
        // Never more than one heavy in a row; lights are the bread and butter.
        const wantHeavy = heavies < 1 && Math.random() < .3;
        const swing = kind => {
          if (!me.startAttack(kind)) return false;
          heavies = kind === 'heavy' ? heavies + 1 : 0;
          cooldown = (kind === 'heavy' ? 3.6 + Math.random() * 2.2 : 2.2 + Math.random() * 1.8) - aggression;
          // After a swing, sometimes step off the line instead of standing still.
          if (Math.random() < .5) { reposition = 1 + Math.random(); repositionDir = Math.random() < .5 ? -1 : 1; }
          return true;
        };
        if (wantHeavy && distance <= heavy && swing('heavy')) return;
        if (distance <= light && swing('light')) return;
        if (distance <= heavy && heavies < 1 && swing('heavy')) return;
      }
      if (reposition > 0) { reposition -= dt; input.strafe = repositionDir; input.forward = -.35; return; }
      // Close to the light-attack range, then circle while the cooldown runs;
      // creep in when ready so the next swing is not thrown from too far.
      const preferred = light * (cooldown <= 0 ? .7 : .9);
      if (distance > preferred) input.forward = 1;
      else if (distance < preferred * .5) input.forward = -.7;
      else { input.strafe = strafeDir * .85; input.forward = cooldown <= 0 ? .3 : 0; }
    },
  };
}
