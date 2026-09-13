import * as THREE from 'three';
import './style.css';
import { fighters } from './roster.js';
import { Fighter, loadFighterModel } from './fighter.js';
import { createAI } from './ai.js';
import { createArena } from './arena.js';
import * as SkeletonUtils from 'three/addons/utils/SkeletonUtils.js';

const $ = s => document.querySelector(s);
const arena = createArena($('#scene'));
const { scene, camera, composer } = arena;
const base = import.meta.env.BASE_URL;
const ROUND_SECONDS = 99;

// ---------------------------------------------------------------- selection
const picks = [];
const grid = $('#grid');
for (const f of fighters) {
  const card = document.createElement('button'); card.className = 'card'; card.dataset.id = f.id;
  card.innerHTML = `<span class="badge"></span><img src="${base}thumbs/${f.id}.jpg" alt="${f.name}"><div class="meta"><div class="name">${f.name}<span>/ ${f.number}</span></div><div class="style">${f.style}</div></div>`;
  card.addEventListener('click', () => pick(f.id)); grid.appendChild(card);
}
function pick(id) {
  if (picks.length >= 2) picks.length = 0;
  picks.push(id); renderPicks();
}
function renderPicks() {
  for (const card of grid.children) { const i = picks.indexOf(card.dataset.id); card.dataset.slot = i < 0 ? '' : i === 0 ? 'p1' : 'p2'; card.querySelector('.badge').textContent = i < 0 ? '' : i === 0 ? 'PLAYER' : 'AI'; }
  const p1 = fighters.find(f => f.id === picks[0]), p2 = fighters.find(f => f.id === picks[1]);
  $('#slotP1').textContent = p1 ? `${p1.name} / ${p1.number}` : '—'; $('#slotP2').textContent = p2 ? `${p2.name} / ${p2.number}` : '—';
  $('#fight').disabled = picks.length < 2;
}
$('#random').addEventListener('click', () => { picks.length = 0; const pool = fighters.map(f => f.id); while (picks.length < 2) picks.push(pool.splice(Math.floor(Math.random() * pool.length), 1)[0]); renderPicks(); });
$('#clear').addEventListener('click', () => { picks.length = 0; renderPicks(); });
$('#fight').addEventListener('click', () => startMatch(picks[0], picks[1]));
$('#rematch').addEventListener('click', () => startMatch(picks[0], picks[1]));
$('#reselect').addEventListener('click', () => { endMatch(); $('#result').hidden = true; $('#hud').hidden = true; $('#select').hidden = false; });
const params = new URLSearchParams(location.search);
if (fighters.some(f => f.id === params.get('p1')) && fighters.some(f => f.id === params.get('p2'))) { picks.push(params.get('p1'), params.get('p2')); renderPicks(); }
renderPicks();

// ---------------------------------------------------------------- input
const keys = new Set();
const pressed = { light: false, heavy: false, block: false, dodge: false };
addEventListener('keydown', e => {
  if (e.repeat) return; keys.add(e.code);
  if (e.code === 'KeyJ') pressed.light = true; if (e.code === 'KeyK') pressed.heavy = true; if (e.code === 'KeyL') pressed.block = true; if (e.code === 'Space') { pressed.dodge = true; e.preventDefault(); }
  if (e.code === 'Escape' && match) { endMatch(); $('#result').hidden = true; $('#hud').hidden = true; $('#select').hidden = false; }
});
addEventListener('keyup', e => keys.delete(e.code));
const stick = { active: false, x: 0, y: 0, id: null };
const stickEl = $('#stick'), knob = stickEl.querySelector('i');
stickEl.addEventListener('pointerdown', e => { stick.active = true; stick.id = e.pointerId; stickEl.setPointerCapture(e.pointerId); moveStick(e); });
stickEl.addEventListener('pointermove', e => { if (stick.active && e.pointerId === stick.id) moveStick(e); });
for (const type of ['pointerup', 'pointercancel']) stickEl.addEventListener(type, () => { stick.active = false; stick.x = stick.y = 0; knob.style.transform = ''; });
function moveStick(e) { const r = stickEl.getBoundingClientRect(); const dx = (e.clientX - r.left - r.width / 2) / (r.width / 2), dy = (e.clientY - r.top - r.height / 2) / (r.height / 2); const l = Math.hypot(dx, dy) || 1; const k = Math.min(1, l); stick.x = dx / l * k; stick.y = dy / l * k; knob.style.transform = `translate(${stick.x * 34}px,${stick.y * 34}px)`; }
for (const button of document.querySelectorAll('.pad button')) button.addEventListener('pointerdown', e => { e.preventDefault(); pressed[button.dataset.act] = true; });
function readInput() {
  const forward = (keys.has('KeyW') || keys.has('ArrowUp') ? 1 : 0) - (keys.has('KeyS') || keys.has('ArrowDown') ? 1 : 0) - stick.y;
  const strafe = (keys.has('KeyD') || keys.has('ArrowRight') ? 1 : 0) - (keys.has('KeyA') || keys.has('ArrowLeft') ? 1 : 0) + stick.x;
  return { forward: THREE.MathUtils.clamp(forward, -1, 1), strafe: THREE.MathUtils.clamp(strafe, -1, 1) };
}

// ---------------------------------------------------------------- match
let match = null;
window.combat = { get match() { return match; }, fighters, start: startMatch, camera };
async function startMatch(p1, p2) {
  endMatch(); $('#result').hidden = true; $('#select').hidden = true; $('#loading').hidden = false;
  const profiles = [fighters.find(f => f.id === p1), fighters.find(f => f.id === p2)];
  $('#loadingText').textContent = `ASSEMBLING ${profiles[0].name} AND ${profiles[1].name}`;
  const [g1, g2] = await Promise.all(profiles.map(loadFighterModel));
  const player = new Fighter(profiles[0], cloneGltf(g1), scene);
  const enemy = new Fighter(profiles[1], cloneGltf(g2), scene);
  player.root.position.set(-1, 0, -26); enemy.root.position.set(1, 0, 26);
  player.root.rotation.y = 0; enemy.root.rotation.y = Math.PI;
  const ai = createAI(enemy, player, { aggression: .5, reaction: .42 });
  match = { player, enemy, ai, time: 0, clock: ROUND_SECONDS, over: false, started: false, countdown: 2.6, combo: 0, comboTimer: 0 };
  $('#nameP1').textContent = `${profiles[0].name} / ${profiles[0].number}`; $('#nameP2').textContent = `${profiles[1].name} / ${profiles[1].number}`;
  document.documentElement.style.setProperty('--p1', profiles[0].accent); document.documentElement.style.setProperty('--p2', profiles[1].accent);
  updateBars(); $('#loading').hidden = true; $('#hud').hidden = false; $('#status').textContent = `${profiles[0].style}  vs  ${profiles[1].style}`;
  banner('READY', 'FIGHT WHEN THE RING LIGHTS UP');
  const url = new URL(location.href); url.searchParams.set('p1', p1); url.searchParams.set('p2', p2); history.replaceState(null, '', url);
  camera.position.set(-1, 22, -70); camera.lookAt(0, 10, 0);
}
function cloneGltf(gltf) {
  // A fresh skinned scene graph per fighter so mirror matches and rematches
  // never share bones; materials are cloned so hit flashes stay per fighter.
  const scene = SkeletonUtils.clone(gltf.scene);
  scene.traverse(o => { if (o.isMesh) o.material = Array.isArray(o.material) ? o.material.map(m => m.clone()) : o.material.clone(); });
  return { scene, animations: gltf.animations };
}
function endMatch() {
  if (!match) return; match.player.dispose(); match.enemy.dispose(); match = null;
}
function banner(text, sub = '') { const b = $('#banner'); b.innerHTML = `${text}${sub ? `<small>${sub}</small>` : ''}`; b.classList.add('show'); clearTimeout(banner.t); banner.t = setTimeout(() => b.classList.remove('show'), 1400); }
function updateBars() {
  if (!match) return;
  $('#fillP1').style.transform = `scaleX(${match.player.health / 100})`; $('#fillP2').style.transform = `scaleX(${match.enemy.health / 100})`;
  setTimeout(() => { if (!match) return; $('#ghostP1').style.transform = `scaleX(${match.player.health / 100})`; $('#ghostP2').style.transform = `scaleX(${match.enemy.health / 100})`; }, 300);
  $('#timer').textContent = String(Math.ceil(match.clock)).padStart(2, '0');
}
function finish(winner) {
  match.over = true; const player = winner === match.player;
  $('#resultTitle').textContent = player ? 'VICTORY' : 'DEFEAT';
  $('#resultTitle').style.color = player ? 'var(--p1)' : 'var(--p2)';
  $('#resultText').textContent = `${winner.profile.name} wins · ${Math.round(match.player.stats.landed)} damage dealt, ${Math.round(match.player.stats.taken)} taken · ${Math.round(ROUND_SECONDS - match.clock)} s`;
  setTimeout(() => { $('#result').hidden = false; }, 2200);
}

// ---------------------------------------------------------------- loop
const clock = new THREE.Clock();
const cameraTarget = new THREE.Vector3(), cameraGoal = new THREE.Vector3();
arena.renderer.setAnimationLoop(() => frame(Math.min(clock.getDelta(), .05)));
window.combat.step = dt => frame(dt, false);
function frame(dt, render = true) {
  if (!match) { camera.position.lerp(new THREE.Vector3(Math.sin(performance.now() * .0001) * 90, 30, Math.cos(performance.now() * .0001) * 90), .02); camera.lookAt(0, 8, 0); if (render) composer.render(); return; }
  const { player, enemy, ai } = match;
  if (!match.started) { match.countdown -= dt; if (match.countdown <= 0) { match.started = true; banner('FIGHT'); } }
  const input = match.started && !match.over ? readInput() : { forward: 0, strafe: 0 };
  // Strafe follows the camera's right so A/D always mean screen left/right.
  input.cameraRight = new THREE.Vector3(1, 0, 0).applyQuaternion(camera.quaternion).setY(0).normalize();
  if (match.started && !match.over && !player.dead) {
    if (pressed.light) player.startAttack('light'); if (pressed.heavy) player.startAttack('heavy'); if (pressed.block) player.startBlock();
    if (pressed.dodge) player.startDodge(enemy.root.position.clone().sub(player.root.position).setY(0).normalize().negate());
  }
  pressed.light = pressed.heavy = pressed.block = pressed.dodge = false;
  const distance = player.root.position.distanceTo(enemy.root.position);
  if (match.started && !match.over) { match.time += dt; match.clock = Math.max(0, match.clock - dt); ai.update(dt, distance, match.time); }
  player.update(dt, enemy, input); enemy.update(dt, player, match.started && !match.over ? ai.input : null);
  // Keep the two hulls apart.
  const between = enemy.root.position.clone().sub(player.root.position).setY(0); const minGap = player.profile.radius + enemy.profile.radius;
  if (between.length() < minGap) { const push = between.clone().normalize().multiplyScalar((minGap - between.length()) / 2); player.root.position.sub(push); enemy.root.position.add(push); }
  // Hit resolution.
  for (const [a, b] of [[player, enemy], [enemy, player]]) {
    const dir = b.root.position.clone().sub(a.root.position).setY(0).normalize();
    const facing = new THREE.Vector3(0, 0, 1).applyQuaternion(a.root.quaternion).dot(dir);
    for (const hit of a.resolveHits(b, distance, facing)) {
      const ranged = hit.kind === 'ranged';
      const heavy = !ranged && (hit.damage >= 14 || a.attack?.kind === 'heavy');
      // The AI reads inputs perfectly, so its blows land a little softer.
      const applied = b.receive(a === enemy ? Math.max(1, Math.round(hit.damage * .8)) : hit.damage, a, heavy, !ranged); a.stats.landed += applied;
      if (applied > 0 && a === player) { match.combo++; match.comboTimer = 1.2; if (match.combo >= 3) banner(`${match.combo} HITS`); }
      updateBars();
    }
  }
  match.comboTimer -= dt; if (match.comboTimer <= 0) match.combo = 0;
  if (!match.over && match.started) {
    if (enemy.dead) finish(player); else if (player.dead) finish(enemy);
    else if (match.clock <= 0) finish(player.health >= enemy.health ? player : enemy);
  }
  // Camera: over the player's shoulder, framing both fighters.
  const back = player.root.position.clone().sub(enemy.root.position).setY(0).normalize();
  // Three-quarter view swung about 55 degrees round the player's right, so
  // both hulls read side by side at melee range instead of overlapping.
  const span = THREE.MathUtils.clamp(distance, 16, 90);
  const scale = Math.max(player.height, enemy.height) / 18;
  const azimuth = new THREE.Vector3(back.x * Math.cos(.96) - back.z * Math.sin(.96), 0, back.x * Math.sin(.96) + back.z * Math.cos(.96));
  cameraGoal.lerpVectors(player.root.position, enemy.root.position, .35).addScaledVector(azimuth, (44 + span * .75) * scale).setY((24 + span * .22) * scale);
  cameraTarget.lerpVectors(player.root.position, enemy.root.position, .45).add(new THREE.Vector3(0, 6 * scale, 0));
  camera.position.lerp(cameraGoal, Math.min(1, dt * 3.2)); camera.lookAt(cameraTarget);
  if (render) composer.render();
}
