import * as THREE from 'three';
import './style.css';
import { fighters } from './roster.js';
import { Fighter, loadFighterModel } from './fighter.js';
import { createAI } from './ai.js';
import { createArena } from './arena.js';
import { createFeedback } from './feedback.js';
import * as SkeletonUtils from 'three/addons/utils/SkeletonUtils.js';

const $ = s => document.querySelector(s);
const arena = createArena($('#scene'));
const { scene, camera, composer } = arena;
const feedback = createFeedback(scene, camera, $('#hud'));
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
function pick(id) { if (picks.length >= 2) picks.length = 0; picks.push(id); renderPicks(); }
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
function toSelect() { endMatch(); $('#result').hidden = true; $('#hud').hidden = true; $('#select').hidden = false; }
$('#reselect').addEventListener('click', toSelect);
const params = new URLSearchParams(location.search);
if (fighters.some(f => f.id === params.get('p1')) && fighters.some(f => f.id === params.get('p2'))) picks.push(params.get('p1'), params.get('p2'));
renderPicks();

// ---------------------------------------------------------------- input
const keys = new Set();
const pressed = { light: false, heavy: false, dodge: false, dash: false };
let touchMove = 0, touchBlock = false, lastTap = { code: '', at: 0 };
const isLeft = c => c === 'KeyA' || c === 'ArrowLeft', isRight = c => c === 'KeyD' || c === 'ArrowRight';
addEventListener('keydown', e => {
  if (e.repeat) return; keys.add(e.code);
  if (isLeft(e.code) || isRight(e.code)) { const now = performance.now(); if (lastTap.code === e.code && now - lastTap.at < 260) pressed.dash = true; lastTap = { code: e.code, at: now }; }
  if (e.code === 'KeyJ') pressed.light = true; if (e.code === 'KeyK') pressed.heavy = true;
  if (e.code === 'Space') { pressed.dodge = true; e.preventDefault(); }
  if (e.code === 'Escape' && match) toSelect();
});
addEventListener('keyup', e => keys.delete(e.code));
for (const button of document.querySelectorAll('.touch .move button')) {
  const dir = Number(button.dataset.move);
  button.addEventListener('pointerdown', e => { e.preventDefault(); touchMove = dir; button.setPointerCapture(e.pointerId); });
  for (const type of ['pointerup', 'pointercancel']) button.addEventListener(type, () => { if (touchMove === dir) touchMove = 0; });
}
for (const button of document.querySelectorAll('.pad button')) {
  button.addEventListener('pointerdown', e => { e.preventDefault(); if (button.dataset.act === 'block') touchBlock = true; else pressed[button.dataset.act] = true; });
  for (const type of ['pointerup', 'pointercancel']) button.addEventListener(type, () => { if (button.dataset.act === 'block') touchBlock = false; });
}
function readInput() {
  const move = (keys.has('KeyD') || keys.has('ArrowRight') ? 1 : 0) - (keys.has('KeyA') || keys.has('ArrowLeft') ? 1 : 0) + touchMove;
  return { move: THREE.MathUtils.clamp(move, -1, 1), dash: pressed.dash, block: keys.has('KeyS') || keys.has('ArrowDown') || touchBlock };
}

// ---------------------------------------------------------------- match
let match = null;
window.combat = { get match() { return match; }, fighters, start: startMatch, camera, step: dt => frame(dt, false) };
async function startMatch(p1, p2) {
  endMatch(); $('#result').hidden = true; $('#select').hidden = true; $('#loading').hidden = false;
  const profiles = [fighters.find(f => f.id === p1), fighters.find(f => f.id === p2)];
  $('#loadingText').textContent = `ASSEMBLING ${profiles[0].name} AND ${profiles[1].name}`;
  const [g1, g2] = await Promise.all(profiles.map(loadFighterModel));
  const player = new Fighter(profiles[0], cloneGltf(g1), scene);
  const enemy = new Fighter(profiles[1], cloneGltf(g2), scene);
  player.x = -18; enemy.x = 18; player.root.rotation.y = Math.PI / 2; enemy.root.rotation.y = -Math.PI / 2;
  const ai = createAI(enemy, player, { aggression: .5, reaction: .4 });
  match = { player, enemy, ai, time: 0, clock: ROUND_SECONDS, over: false, started: false, countdown: 2.2, combo: 0, comboTimer: 0 };
  $('#nameP1').textContent = `${profiles[0].name} / ${profiles[0].number}`; $('#nameP2').textContent = `${profiles[1].name} / ${profiles[1].number}`;
  document.documentElement.style.setProperty('--p1', profiles[0].accent); document.documentElement.style.setProperty('--p2', profiles[1].accent);
  updateBars(); $('#loading').hidden = true; $('#hud').hidden = false; $('#status').textContent = `${profiles[0].style}  vs  ${profiles[1].style}`;
  banner('READY');
  const url = new URL(location.href); url.searchParams.set('p1', p1); url.searchParams.set('p2', p2); history.replaceState(null, '', url);
  camera.position.set(0, 14, 90); camera.lookAt(0, 9, 0);
}
function cloneGltf(gltf) {
  // A fresh skinned scene graph per fighter so mirror matches and rematches
  // never share bones; materials are cloned so hit flashes stay per fighter.
  const scene = SkeletonUtils.clone(gltf.scene);
  scene.traverse(o => { if (o.isMesh) o.material = Array.isArray(o.material) ? o.material.map(m => m.clone()) : o.material.clone(); });
  return { scene, animations: gltf.animations };
}
function endMatch() { if (!match) return; match.player.dispose(); match.enemy.dispose(); feedback.dispose(); match = null; }
function banner(text, sub = '') { const b = $('#banner'); b.innerHTML = `${text}${sub ? `<small>${sub}</small>` : ''}`; b.classList.add('show'); clearTimeout(banner.t); banner.t = setTimeout(() => b.classList.remove('show'), 1100); }
function updateBars() {
  if (!match) return;
  $('#fillP1').style.transform = `scaleX(${match.player.health / 100})`; $('#fillP2').style.transform = `scaleX(${match.enemy.health / 100})`;
  setTimeout(() => { if (!match) return; $('#ghostP1').style.transform = `scaleX(${match.player.health / 100})`; $('#ghostP2').style.transform = `scaleX(${match.enemy.health / 100})`; }, 300);
  $('#timer').textContent = String(Math.ceil(match.clock)).padStart(2, '0');
}
function finish(winner) {
  match.over = true; const player = winner === match.player; feedback.sounds.ko(); banner('K.O.');
  $('#resultTitle').textContent = player ? 'VICTORY' : 'DEFEAT';
  $('#resultTitle').style.color = player ? 'var(--p1)' : 'var(--p2)';
  $('#resultText').textContent = `${winner.profile.name} wins · ${Math.round(match.player.stats.landed)} damage dealt, ${Math.round(match.player.stats.taken)} taken · ${Math.round(ROUND_SECONDS - match.clock)} s`;
  setTimeout(() => { $('#result').hidden = false; }, 2200);
}

// ---------------------------------------------------------------- loop
const clock = new THREE.Clock();
const cameraTarget = new THREE.Vector3(), cameraGoal = new THREE.Vector3(), impactPoint = new THREE.Vector3();
arena.renderer.setAnimationLoop(() => frame(Math.min(clock.getDelta(), .05)));
function frame(dt, render = true) {
  if (!match) { camera.position.lerp(new THREE.Vector3(Math.sin(performance.now() * .0001) * 90, 30, Math.cos(performance.now() * .0001) * 90), .02); camera.lookAt(0, 8, 0); if (render) composer.render(); return; }
  const { player, enemy, ai } = match;
  if (!match.started) { match.countdown -= dt; if (match.countdown <= 0) { match.started = true; banner('FIGHT'); } }
  const live = match.started && !match.over;
  const input = live ? readInput() : { move: 0, dash: false, block: false };
  if (live && !player.dead) {
    if (input.block) player.startBlock(); else player.stopBlock();
    if (pressed.light) player.startMove('light'); if (pressed.heavy) player.startMove('heavy');
    if (pressed.dodge && player.startDodge()) feedback.sounds.dodge();
  }
  pressed.light = pressed.heavy = pressed.dodge = false;
  const distance = Math.abs(player.x - enemy.x);
  if (live) { match.time += dt; match.clock = Math.max(0, match.clock - dt); ai.update(dt, distance, match.time); }
  player.update(dt, enemy, live ? input : null); enemy.update(dt, player, live ? ai.input : null);
  pressed.dash = false;
  // Keep the two hulls apart on the lane.
  const minGap = (player.profile.radius + enemy.profile.radius) * .9; const gap = Math.abs(player.x - enemy.x);
  if (gap < minGap) { const push = (minGap - gap) / 2; const dir = Math.sign(enemy.x - player.x) || 1; player.x -= push * dir; enemy.x += push * dir; }
  // Hit resolution with feedback.
  for (const [a, b] of [[player, enemy], [enemy, player]]) {
    for (const hit of a.resolveHits(b, distance)) {
      const scaled = a === enemy ? { ...hit, damage: Math.max(1, Math.round(hit.damage * .85)) } : hit;
      const result = b.receive(scaled, a); a.stats.landed += result.damage;
      impactPoint.set(THREE.MathUtils.lerp(a.x, b.x, .62), b.height * (hit.kind === 'ranged' ? .55 : .5), 0);
      if (result.dodged) { feedback.spark(impactPoint, 6, '#9fd8ff', 6); continue; }
      feedback.impact(impactPoint, { heavy: !!hit.stagger, blocked: !!result.blocked, ranged: hit.kind === 'ranged', damage: result.damage, color: a.profile.accent });
      if (hit.kind !== 'ranged') { const stop = hit.stagger ? .14 : .07; a.hitstop = Math.max(a.hitstop, stop); b.hitstop = Math.max(b.hitstop, stop); }
      if (result.damage > 0 && a === player && !result.blocked) { match.combo++; match.comboTimer = 1.4; if (match.combo >= 3) banner(`${match.combo} HITS`); }
      updateBars();
    }
  }
  match.comboTimer -= dt; if (match.comboTimer <= 0) match.combo = 0;
  if (live) {
    if (enemy.dead) finish(player); else if (player.dead) finish(enemy);
    else if (match.clock <= 0) finish(player.health >= enemy.health ? player : enemy);
  }
  // Fixed side view that frames both fighters: pulls back as they separate.
  const scale = Math.max(player.scale, enemy.scale);
  const mid = (player.x + enemy.x) / 2, sep = Math.abs(player.x - enemy.x);
  const depth = THREE.MathUtils.clamp(sep * 1.05 + 36 * scale, 48 * scale, 150);
  cameraGoal.set(mid, 12 * scale + depth * .14, depth);
  cameraTarget.set(mid, 8.5 * scale, 0);
  camera.position.lerp(cameraGoal, Math.min(1, dt * 4)); camera.lookAt(cameraTarget);
  const shake = feedback.update(dt); camera.position.add(shake);
  if (render) composer.render();
}
