/**
 * Opponent brain on the lane: closes to its light range, attacks on a
 * cooldown with a visible tell before heavies, backs off after swinging,
 * and blocks or dodges what the player starts after a human-ish delay.
 */
export function createAI(me, target, { aggression = .5, reaction = .4 } = {}) {
  let cooldown = 1.6, heavies = 0, retreat = 0, sawAttackAt = -1, responded = false, pendingHeavy = 0, blockHold = 0;
  const input = { move: 0, dash: false };
  const reach = move => Math.min(40, Math.max(...move.hits.map(h => h.range))) * me.scale + me.profile.radius * .5 + target.profile.radius * .5;
  return {
    input,
    update(dt, distance, now) {
      input.move = 0; input.dash = false;
      if (me.dead || target.dead) return;
      cooldown -= dt;
      if (blockHold > 0) { blockHold -= dt; if (blockHold <= 0) me.stopBlock(); else return; }
      if (target.attack) {
        if (sawAttackAt < 0) { sawAttackAt = now; responded = false; }
        else if (!responded && now - sawAttackAt > reaction) {
          responded = true; const roll = Math.random();
          if (roll < .3 && me.startBlock()) blockHold = .9;
          else if (roll < .5) me.startDodge();
        }
      } else sawAttackAt = -1;
      if (pendingHeavy > 0) { pendingHeavy -= dt; if (pendingHeavy <= 0) { me.startMove('heavy'); heavies++; } return; }
      if (!me.free()) return;
      const light = reach(me.profile.moves.light), heavy = reach(me.profile.moves.heavy);
      if (cooldown <= 0) {
        const wantHeavy = heavies < 1 && Math.random() < .3;
        if (wantHeavy && distance <= heavy) { me.tell = me.profile.moves.heavy.tell || .35; pendingHeavy = me.tell; cooldown = 3.4 + Math.random() * 2 - aggression; retreat = Math.random() < .5 ? .8 : 0; return; }
        if (distance <= light && me.startMove('light')) { heavies = 0; cooldown = 1.8 + Math.random() * 1.6 - aggression; retreat = Math.random() < .5 ? .7 + Math.random() * .5 : 0; return; }
      }
      if (retreat > 0) { retreat -= dt; input.move = -me.facing; return; }
      const preferred = light * (cooldown <= 0 ? .75 : 1.05);
      if (distance > preferred + 2) input.move = me.facing;
      else if (distance < preferred * .6) input.move = -me.facing * .8;
    },
  };
}
