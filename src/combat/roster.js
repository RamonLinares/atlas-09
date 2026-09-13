import { characters } from '../characters.js';

/**
 * Combat profiles built on the baked clips each mecha already ships with.
 * Times are clip seconds. A hit window lands once per activation when the
 * opponent is inside `range` metres and within `arc` degrees of the facing.
 * `kind: 'ranged'` windows are the viewer's synchronized rounds and beams and
 * never stagger; only melee hits of 14+ damage or a heavy melee attack do.
 * `radial` ignores facing (ground shock).
 */
const shots = (start, end, interval, damage, range = 70, arc = 22) => {
  const list = [];
  for (let t = start; t < end - 1e-6; t += interval) list.push({ t0: t, t1: t + interval * .8, damage, range, arc, kind: 'ranged' });
  return list;
};

export const roster = {
  'atlas-09': {
    style: 'BRAWLER · PULSE CANNON', speed: 11, radius: 4.2,
    light: { clip: 'PunchCombo', end: 3.9, hits: [{ t0: .45, t1: .8, damage: 7, range: 9.5, arc: 50 }, { t0: 1.45, t1: 1.85, damage: 7, range: 9.5, arc: 50 }, { t0: 2.65, t1: 3.15, damage: 12, range: 10.5, arc: 60 }] },
    heavy: { clip: 'KneelFire', start: 1.3, end: 6.6, timeScale: 1.5, hits: shots(2.4, 5.8, .48, 3) },
    dodge: 'Backflip', hit: 'HitChest', hitHeavy: 'HitHead', death: 'Collapse',
  },
  'aether-02': {
    style: 'STRIKER · WRIST EMITTER', speed: 15, radius: 3.4,
    light: { clip: 'PunchCombo', end: 3.3, hits: [{ t0: .4, t1: .7, damage: 6, range: 8, arc: 50 }, { t0: 1.25, t1: 1.6, damage: 6, range: 8, arc: 50 }, { t0: 2.2, t1: 2.65, damage: 11, range: 9, arc: 60 }] },
    heavy: { clip: 'KneelFire', start: 1.3, end: 6.6, timeScale: 1.5, hits: shots(2.4, 5.8, .48, 3) },
    dodge: 'Backflip', hit: 'HitChest', hitHeavy: 'HitHead', death: 'Collapse',
  },
  'seraph-03': {
    style: 'GUNNER · CANNON ARM', speed: 12, radius: 4.2,
    light: { clip: 'KneelFire', start: 1.3, end: 6.6, timeScale: 1.6, hits: shots(2.4, 5.8, .64, 4) },
    heavy: { clip: 'WingDeploy', end: 4.2, timeScale: 1.4, hits: [{ t0: 1.9, t1: 2.7, damage: 20, range: 13, arc: 80 }] },
    dodge: 'Backflip', hit: 'HitChest', hitHeavy: 'HitHead', death: 'Knockback',
  },
  'ronin-04': {
    style: 'DUELIST · KATANA', speed: 13, radius: 3.6,
    light: { clip: 'SwordSlash', hits: [{ t0: .8, t1: 1.2, damage: 14, range: 12, arc: 70 }] },
    heavy: { clip: 'SwordCombo', hits: [{ t0: .55, t1: .95, damage: 9, range: 12, arc: 70 }, { t0: 1.85, t1: 2.25, damage: 9, range: 12, arc: 70 }, { t0: 3.25, t1: 3.75, damage: 15, range: 13, arc: 80 }] },
    block: { clip: 'SwordBlock', t0: .35, t1: 2.0, reduce: .8 },
    dodge: 'Backflip', hit: 'HitChest', hitHeavy: 'HitHead', death: 'Knockback',
  },
  'scorpio-05': {
    style: 'PREDATOR · STINGER', speed: 12, radius: 4.6,
    light: { clip: 'ClawSlash', hits: [{ t0: .85, t1: 1.25, damage: 10, range: 12, arc: 60 }, { t0: 2.35, t1: 2.8, damage: 10, range: 12, arc: 60 }] },
    heavy: { clip: 'StingerStrike', end: 5.0, timeScale: 1.25, hits: [{ t0: 1.85, t1: 2.45, damage: 26, range: 15, arc: 50 }] },
    dodge: 'Backflip', death: 'topple',
  },
  'titan-06': {
    style: 'SUPER ROBOT · ROCKET FIST', speed: 10, radius: 4.8,
    light: { clip: 'RocketPunch', hits: [{ t0: 1.15, t1: 1.9, damage: 22, range: 22, arc: 30 }] },
    heavy: { clip: 'ChestBeam', hits: shots(1.28, 2.88, .2, 2, 70, 16) },
    dodge: 'Backflip', death: 'topple',
  },
  'vanguard-07': {
    style: 'TROOPER · BEAM RIFLE', speed: 14, radius: 3.6,
    light: { clip: 'RifleBurst', hits: shots(1.0, 2.0, .2, 3) },
    heavy: { clip: 'BoostJump', hits: [{ t0: 2.95, t1: 3.25, damage: 20, range: 13, arc: 360, kind: 'radial' }] },
    block: { clip: 'ShieldGuard', t0: .5, t1: 2.3, reduce: .85 },
    dodge: 'Backflip', death: 'topple',
  },
};

export const fighters = Object.keys(roster).map(id => ({ id, ...characters[id], ...roster[id] }));
