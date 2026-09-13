import * as THREE from 'three';

/**
 * Opponent brain: closes distance, picks attacks by reach, keeps a cooldown,
 * strafes while waiting and sometimes dodges or blocks incoming attacks.
 */
export function createAI(me, target, { aggression = .55, reaction = .28 } = {}) {
  let cooldown = 2.0, strafeDir = 1, strafeTimer = 0, sawAttackAt = -1, responded = false;
  const input = { forward: 0, strafe: 0 };
  const lightReach = () => Math.max(...me.profile.light.hits.map(h => h.range)) + me.profile.radius + target.profile.radius * .5;
  const heavyReach = () => Math.max(...me.profile.heavy.hits.map(h => h.range)) + me.profile.radius + target.profile.radius * .5;
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
      const ranged = me.profile.light.hits[0].kind === 'ranged' || me.profile.heavy.hits[0].kind === 'ranged';
      if (cooldown <= 0) {
        const wantHeavy = Math.random() < .35;
        if (wantHeavy && distance <= heavy && me.startAttack('heavy')) { cooldown = 3.6 + Math.random() * 2.2 - aggression; return; }
        if (distance <= light && me.startAttack('light')) { cooldown = 2.4 + Math.random() * 1.8 - aggression; return; }
        if (!wantHeavy && distance <= heavy && me.startAttack('heavy')) { cooldown = 3.8 + Math.random() * 2.2 - aggression; return; }
      }
      // Ranged frames keep their distance; melee frames close in, then circle.
      const preferred = ranged ? Math.min(light, heavy) * .8 : light * .85;
      if (distance > preferred) input.forward = 1;
      else if (distance < preferred * .55) input.forward = -.7;
      else input.strafe = strafeDir * .8;
    },
  };
}
