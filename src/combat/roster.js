import { characters } from '../characters.js';

/**
 * Side-view brawler move sets cut from the baked clips each mecha ships with.
 *
 * A move plays its clip from `start` at `timeScale`, lands its `hits` (clip
 * seconds) when the opponent is within `range` metres, can be cancelled into
 * movement, block or dodge once the clip passes `cancel`, and ends at `end`.
 * `chain` names the move that a repeated press continues into once the hit
 * window has passed; chained moves on the same clip keep playing seamlessly.
 * `kind: 'ranged'` hits are the viewer's synchronized rounds and beams and
 * chip without staggering; `radial` hits ignore facing.
 */
const shots = (start, end, interval, damage, range = 60) => {
  const list = [];
  for (let t = start; t < end - 1e-6; t += interval) list.push({ t0: t, t1: t + interval * .8, damage, range, kind: 'ranged' });
  return list;
};

export const roster = {
  'atlas-09': {
    style: 'BRAWLER · PULSE CANNON', speed: 1.15, radius: 4.2,
    moves: {
      light: { clip: 'PunchCombo', start: .1, timeScale: 1.9, hits: [{ t0: .45, t1: .85, damage: 6, range: 10 }], cancel: .9, end: 1.05, chain: 'light2' },
      light2: { clip: 'PunchCombo', start: 1.05, timeScale: 1.9, hits: [{ t0: 1.45, t1: 1.85, damage: 6, range: 10 }], cancel: 1.9, end: 2.1, chain: 'light3' },
      light3: { clip: 'PunchCombo', start: 2.1, timeScale: 1.7, hits: [{ t0: 2.65, t1: 3.15, damage: 12, range: 11, stagger: true }], cancel: 3.3, end: 3.8 },
      heavy: { clip: 'KneelFire', start: 1.9, timeScale: 2.1, hits: shots(2.4, 5.8, .48, 3), cancel: 5.9, end: 6.3, tell: .35 },
    },
    dodge: 'Backflip', hit: 'HitChest', hitHeavy: 'HitHead', death: 'Collapse',
  },
  'aether-02': {
    style: 'STRIKER · WRIST EMITTER', speed: 1.45, radius: 3.4,
    moves: {
      light: { clip: 'PunchCombo', start: .05, timeScale: 1.8, hits: [{ t0: .4, t1: .7, damage: 5, range: 8.5 }], cancel: .75, end: .9, chain: 'light2' },
      light2: { clip: 'PunchCombo', start: .9, timeScale: 1.8, hits: [{ t0: 1.25, t1: 1.6, damage: 5, range: 8.5 }], cancel: 1.65, end: 1.8, chain: 'light3' },
      light3: { clip: 'PunchCombo', start: 1.8, timeScale: 1.6, hits: [{ t0: 2.2, t1: 2.65, damage: 11, range: 9.5, stagger: true }], cancel: 2.8, end: 3.3 },
      heavy: { clip: 'KneelFire', start: 1.9, timeScale: 2.1, hits: shots(2.4, 5.8, .48, 3), cancel: 5.9, end: 6.3, tell: .3 },
    },
    dodge: 'Backflip', hit: 'HitChest', hitHeavy: 'HitHead', death: 'Collapse',
  },
  'seraph-03': {
    style: 'GUNNER · CANNON ARM', speed: 1.2, radius: 4.2,
    moves: {
      light: { clip: 'KneelFire', start: 1.9, timeScale: 2.2, hits: shots(2.4, 5.8, .64, 4), cancel: 5.9, end: 6.3 },
      heavy: { clip: 'WingDeploy', start: 1.0, timeScale: 1.8, hits: [{ t0: 1.9, t1: 2.7, damage: 20, range: 13, stagger: true }], cancel: 2.9, end: 3.6, tell: .4 },
    },
    dodge: 'Backflip', hit: 'HitChest', hitHeavy: 'HitHead', death: 'Knockback',
  },
  'ronin-04': {
    style: 'DUELIST · KATANA', speed: 1.35, radius: 3.6,
    moves: {
      light: { clip: 'SwordSlash', start: .3, timeScale: 1.7, hits: [{ t0: .8, t1: 1.2, damage: 12, range: 12 }], cancel: 1.3, end: 1.8 },
      heavy: { clip: 'SwordCombo', start: .1, timeScale: 1.5, hits: [{ t0: .55, t1: .95, damage: 8, range: 12 }], cancel: 1.1, end: 1.35, chain: 'heavy2', tell: .3 },
      heavy2: { clip: 'SwordCombo', start: 1.35, timeScale: 1.5, hits: [{ t0: 1.85, t1: 2.25, damage: 8, range: 12 }], cancel: 2.35, end: 2.75, chain: 'heavy3' },
      heavy3: { clip: 'SwordCombo', start: 2.75, timeScale: 1.5, hits: [{ t0: 3.25, t1: 3.75, damage: 15, range: 13, stagger: true }], cancel: 3.9, end: 4.4 },
    },
    block: { clip: 'SwordBlock', hold: 1.0, reduce: .8 },
    dodge: 'Backflip', hit: 'HitChest', hitHeavy: 'HitHead', death: 'Knockback',
  },
  'scorpio-05': {
    style: 'PREDATOR · STINGER', speed: 1.2, radius: 4.6,
    moves: {
      light: { clip: 'ClawSlash', start: .4, timeScale: 1.7, hits: [{ t0: .85, t1: 1.25, damage: 9, range: 12 }], cancel: 1.35, end: 1.7, chain: 'light2' },
      light2: { clip: 'ClawSlash', start: 1.7, timeScale: 1.7, hits: [{ t0: 2.35, t1: 2.8, damage: 10, range: 12, stagger: true }], cancel: 2.9, end: 3.4 },
      heavy: { clip: 'StingerStrike', start: 1.1, timeScale: 1.9, hits: [{ t0: 1.85, t1: 2.45, damage: 24, range: 15, stagger: true }], cancel: 2.6, end: 3.4, tell: .45 },
    },
    dodge: 'Backflip', death: 'topple',
  },
  'titan-06': {
    style: 'SUPER ROBOT · ROCKET FIST', speed: 1.0, radius: 4.8,
    moves: {
      light: { clip: 'RocketPunch', start: .55, timeScale: 1.7, hits: [{ t0: 1.15, t1: 1.9, damage: 18, range: 22, stagger: true }], cancel: 2.0, end: 3.1 },
      heavy: { clip: 'ChestBeam', start: .6, timeScale: 1.5, hits: shots(1.28, 2.88, .2, 2), cancel: 2.95, end: 3.3, tell: .45 },
    },
    dodge: 'Backflip', death: 'topple',
  },
  'vanguard-07': {
    style: 'TROOPER · BEAM RIFLE', speed: 1.4, radius: 3.6,
    moves: {
      light: { clip: 'RifleBurst', start: .55, timeScale: 1.7, hits: shots(1.0, 2.0, .2, 3), cancel: 2.05, end: 2.5 },
      heavy: { clip: 'BoostJump', start: .2, timeScale: 1.5, hits: [{ t0: 2.95, t1: 3.25, damage: 20, range: 13, kind: 'radial', stagger: true }], cancel: 3.3, end: 3.5, tell: .3 },
    },
    block: { clip: 'ShieldGuard', hold: 1.1, reduce: .85 },
    dodge: 'Backflip', death: 'topple',
  },
};

export const fighters = Object.keys(roster).map(id => ({ id, ...characters[id], ...roster[id] }));
