import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { createMotionFX } from './motion-fx.js';
import { characters } from './characters.js';
import './style.css';

const $ = (s) => document.querySelector(s);
const renderer = new THREE.WebGLRenderer({ canvas: $('#scene'), antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.75));
renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.18;
renderer.info.autoReset = false;
const scene = new THREE.Scene();
scene.background = new THREE.Color('#181e1e');
scene.fog = new THREE.FogExp2('#181e1e', 0.035);
const camera = new THREE.PerspectiveCamera(33, innerWidth / innerHeight, 0.1, 150);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.minDistance = 7;
controls.maxDistance = 42;
controls.maxPolarAngle = Math.PI * 0.51;
controls.minPolarAngle = 0.2;
controls.autoRotateSpeed = 0.55;
controls.enablePan = true;
const pmrem = new THREE.PMREMGenerator(renderer);
const room = new RoomEnvironment();
const env = pmrem.fromScene(room, 0.025);
scene.environment = env.texture;
scene.environmentIntensity = 0.45;
room.dispose(); pmrem.dispose();
scene.add(new THREE.HemisphereLight('#dfe6de', '#303926', 1.3));
const key = new THREE.DirectionalLight('#fff2d9', 4.5);
key.position.set(-5, 10, 6); key.castShadow = true;
key.shadow.mapSize.set(2048, 2048);
Object.assign(key.shadow.camera, { left: -7, right: 7, top: 10, bottom: -6, near: 0.1, far: 35 });
key.shadow.normalBias = 0.03; key.shadow.bias = -0.0002;
scene.add(key);
const rim = new THREE.DirectionalLight('#a3cad2', 3.2); rim.position.set(5, 7, -4); scene.add(rim);
const fill = new THREE.DirectionalLight('#d7e1b8', 0.8); fill.position.set(4, 3, 5); scene.add(fill);
const floor = new THREE.Mesh(new THREE.PlaneGeometry(200, 200), new THREE.MeshStandardMaterial({ color: '#29312c', roughness: 0.92, metalness: 0.1 }));
floor.rotation.x = -Math.PI / 2; floor.position.y = -0.025; floor.receiveShadow = true; scene.add(floor);
const pad = new THREE.Mesh(new THREE.CylinderGeometry(3.4, 3.5, 0.12, 96), new THREE.MeshStandardMaterial({ color: '#303830', roughness: 0.79, metalness: 0.5 }));
pad.position.y = -0.07; pad.receiveShadow = true; scene.add(pad);
const ringMaterial = new THREE.MeshBasicMaterial({ color: '#899778', transparent: true, opacity: 0.2, side: THREE.DoubleSide, depthWrite: false });
for (const r of [3.18, 3.27]) {
  const ring = new THREE.Mesh(new THREE.RingGeometry(r, r + 0.008, 128), ringMaterial);
  ring.rotation.x = -Math.PI / 2; ring.position.y = 0.002; scene.add(ring);
}
for (let i = 0; i < 48; i++) {
  const a = i / 48 * Math.PI * 2;
  const tick = new THREE.Mesh(new THREE.BoxGeometry(0.012, 0.003, i % 4 ? 0.04 : 0.12), ringMaterial);
  tick.position.set(Math.sin(a) * 3.11, 0.003, Math.cos(a) * 3.11); tick.rotation.y = a; scene.add(tick);
}
const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
const bloom = new UnrealBloomPass(new THREE.Vector2(innerWidth, innerHeight), 0.24, 0.5, 1.6);
composer.addPass(bloom); composer.addPass(new OutputPass());
const hero = new THREE.Group(); scene.add(hero);
let model, mixer, skeleton, activeAction, paused = false, clipName = 'Sentinel';
let motionFX;
const actions = new Map(), materials = new Set(), emitters = [];
const powerLight = new THREE.PointLight('#63f4ff', 0, 3, 2); scene.add(powerLight);
let time = 0, power = 0.84;
function resetCamera() {
  const mobile = innerWidth < 701;
  if (clipName === 'Backflip') {
    camera.position.set(mobile ? 13 : 11, mobile ? 10 : 9, mobile ? 31 : 24);
    controls.target.set(0, mobile ? 5.4 : 4.6, 0);
  } else if (clipName === 'KneelFire') {
    camera.position.set(mobile ? 11 : 9, mobile ? 7.2 : 6.7, mobile ? 27 : 18.5);
    controls.target.set(mobile ? 0 : -0.35, mobile ? 3.35 : 2.65, 0);
  } else {
    camera.position.set(mobile ? 11 : 8.7, mobile ? 7.2 : 5.8, mobile ? 27 : 15.8);
    controls.target.set(mobile ? 0 : -0.35, mobile ? 4 : 3.05, 0);
  }
  controls.update();
}
resetCamera();
function setClip(name) {
  const previous = clipName;
  clipName = name;
  if (name === 'Rest' && ['Backflip','KneelFire'].includes(previous)) resetCamera();
  document.querySelectorAll('[data-clip]').forEach(b => b.classList.toggle('active', b.dataset.clip === name));
  if (!mixer) return;
  if (name === 'Rest') { mixer.stopAllAction(); model.traverse(o => { if (o.isSkinnedMesh) o.pose(); }); activeAction = null; return; }
  const next = actions.get(name);
  if (!next) return;
  // Reset completed fades and root transforms before a large-motion clip.
  mixer.stopAllAction();
  next.reset().setEffectiveWeight(1).setEffectiveTimeScale(1).play(); activeAction = next;
  if (['Backflip','KneelFire'].includes(previous) || ['Backflip','KneelFire'].includes(name)) resetCamera();
  paused = false; $('#pause').textContent = 'Ⅱ'; $('#pause').setAttribute('aria-label','Pause animation');
}
let activeCharacter = null, loadSequence = 0;
function disposeModel(root) {
  const geometries = new Set(), mats = new Set(), textures = new Set(), skeletons = new Set();
  root?.traverse(o => {
    if (o.geometry) geometries.add(o.geometry);
    if (o.skeleton) skeletons.add(o.skeleton);
    for (const mat of o.material ? (Array.isArray(o.material) ? o.material : [o.material]) : []) mats.add(mat);
  });
  mats.forEach(m => { Object.values(m).forEach(v => { if (v?.isTexture) textures.add(v); }); m.dispose(); });
  textures.forEach(t => t.dispose()); geometries.forEach(g => g.dispose()); skeletons.forEach(s => s.dispose());
}
function showCharacterInfo(id) {
  const c = characters[id];
  document.title = `${c.name} / ${c.number} — FORGE Asset Lab`;
  document.body.dataset.character = id;
  document.documentElement.style.setProperty('--acid', c.accent);
  $('#scene').setAttribute('aria-label', `Interactive 3D model of ${c.name}, ${c.className.toLowerCase()}`);
  $('.intro .eyebrow').innerHTML = `<span class="dot"></span> ${c.className}`;
  $('.intro h1').innerHTML = `${c.name}<span>/ ${c.number}</span>`;
  $('.tagline').innerHTML = c.tagline.join('<br>');
  $('.description').innerHTML = c.description.join('<br>');
  $('.inspector dl dd').innerHTML = `${c.height} <small>m</small>`;
  $('.wear').textContent = c.condition;
  $('.view-caption').innerHTML = `<span class="cross">+</span><span>MODEL ${c.study}<br><b>${c.caption}</b></span>`;
  $('.edition b').textContent = `${c.study}—26`;
  $('.download').href = c.model;
  $('#conceptDialog img').src = c.concept; $('#conceptDialog img').alt = c.conceptAlt;
  $('#conceptDialog h2').textContent = c.conceptTitle;
  document.querySelectorAll('[data-character]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.character === id)));
}
async function loadCharacter(id) {
  if (!characters[id]) return;
  if (id === activeCharacter) { ++loadSequence; $('#loading').style.display = 'none'; return; }
  const sequence = ++loadSequence, character = characters[id];
  $('#loading').innerHTML = `<div class="load-ring"></div><span>ASSEMBLING ${character.name}</span><small id="loadingProgress">Loading geometry & materials</small>`;
  $('#loading').style.display = 'flex';
  try {
  const gltf = await new GLTFLoader().loadAsync(character.model, event => {
    if (sequence === loadSequence && event.total) $('#loadingProgress').textContent = `${Math.round(event.loaded / event.total * 100)}% · Loading geometry & materials`;
  });
  if (sequence !== loadSequence) { disposeModel(gltf.scene); return; }
  const requestedMotion = activeCharacter ? clipName : new URLSearchParams(location.search).get('motion');
  mixer?.stopAllAction();
  if (model) { mixer?.uncacheRoot(model); hero.remove(model); disposeModel(model); }
  if (skeleton) { scene.remove(skeleton); skeleton.dispose(); }
  motionFX?.dispose(); actions.clear(); materials.clear(); emitters.length = 0;
  activeCharacter = id;
  model = gltf.scene;
  const box = new THREE.Box3().setFromObject(model);
  const size = box.getSize(new THREE.Vector3());
  const scale = 6.5 / size.y;
  model.scale.setScalar(scale);
  const center = box.getCenter(new THREE.Vector3());
  model.position.set(-center.x * scale, -box.min.y * scale, -center.z * scale);
  hero.add(model);
  motionFX = createMotionFX(scene, model);
  let triangles = 0, boneCount = 0;
  model.traverse(o => {
    if (o.isBone) boneCount++;
    if (!o.isMesh) return;
    o.castShadow = true; o.receiveShadow = true; o.frustumCulled = false;
    triangles += (o.geometry.index ? o.geometry.index.count : o.geometry.attributes.position.count) / 3;
    for (const mat of Array.isArray(o.material) ? o.material : [o.material]) {
      materials.add(mat);
      mat.wireframe = $('#wireframe').getAttribute('aria-checked') === 'true';
      if (mat.map) mat.map.anisotropy = Math.min(renderer.capabilities.getMaxAnisotropy(), 8);
      if (mat.name.toLowerCase().includes('reactor') || mat.name.toLowerCase().includes('emission')) {
        emitters.push({ mat, intensity: mat.emissiveIntensity || 1 });
      }
    }
  });
  skeleton = new THREE.SkeletonHelper(model); skeleton.visible = $('#skeleton').getAttribute('aria-checked') === 'true';
  skeleton.material.depthTest = false; skeleton.material.transparent = true; skeleton.renderOrder = 100; scene.add(skeleton);
  mixer = new THREE.AnimationMixer(model);
  gltf.animations.forEach(clip => actions.set(clip.name, mixer.clipAction(clip)));
  $('#triangles').textContent = Math.round(triangles).toLocaleString(); $('#bones').textContent = boneCount;
  $('#loading').style.display = 'none';
  showCharacterInfo(id);
  setClip(requestedMotion === 'Rest' || actions.has(requestedMotion) ? requestedMotion : 'Sentinel'); resetCamera();
  const url = new URL(location.href); url.searchParams.set('character', id); history.replaceState(null, '', url);
  window.atlas = { model, scene, camera, controls, renderer, mixer, actions, skeleton, setClip, motionFX, loadCharacter, stats: { character: id, triangles, boneCount, materials: materials.size, clips: gltf.animations.map(c => ({name:c.name, duration:c.duration, tracks:c.tracks.length})) } };
  } catch (error) {
    if (sequence !== loadSequence) return;
    console.error(error); $('#loading').innerHTML = '<span>MODEL COULD NOT LOAD</span><small>Choose another frame or refresh to retry.</small>';
  }
}
const requestedCharacter = new URLSearchParams(location.search).get('character');
loadCharacter(characters[requestedCharacter] ? requestedCharacter : 'atlas-09');
document.querySelectorAll('[data-character]').forEach(button => button.addEventListener('click', () => loadCharacter(button.dataset.character)));
function toggle(id, fn) { $(id).addEventListener('click', e => { const b = e.currentTarget, enabled = b.getAttribute('aria-checked') !== 'true'; b.setAttribute('aria-checked', String(enabled)); fn(enabled); }); }
toggle('#wireframe', on => materials.forEach(m => { m.wireframe = on; }));
toggle('#skeleton', on => { if (skeleton) skeleton.visible = on; });
toggle('#rotate', on => { controls.autoRotate = on; });
$('#power').addEventListener('input', e => { power = Number(e.target.value) / 100; $('#powerReading').innerHTML = `${e.target.value}<small>%</small>`; $('.status').innerHTML = `<span class="dot"></span> ${power > 0 ? 'CORE ONLINE' : 'CORE STANDBY'}`; });
document.querySelectorAll('[data-clip]').forEach(button => button.addEventListener('click', () => setClip(button.dataset.clip)));
$('#pause').addEventListener('click', () => { paused = !paused; $('#pause').textContent = paused ? '▷' : 'Ⅱ'; $('#pause').setAttribute('aria-label', paused ? 'Play animation' : 'Pause animation'); });
$('#reset').addEventListener('click', resetCamera);
$('#conceptButton').addEventListener('click', () => $('#conceptDialog').showModal());
$('#closeConcept').addEventListener('click', () => $('#conceptDialog').close());
$('#conceptDialog').addEventListener('click', e => { if (e.target === $('#conceptDialog')) { const r = e.target.getBoundingClientRect(); if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) e.target.close(); } });
let last = performance.now(), frameCount = 0, sampleStart = last;
renderer.setAnimationLoop(now => {
  const dt = Math.min((now - last) / 1000, 0.05); last = now; time += dt;
  if (mixer && !paused) mixer.update(dt);
  if (motionFX) {
    model.updateMatrixWorld(true);
    const fx=motionFX.update(clipName,activeAction?.time ?? 0);
    if(window.atlas) {window.atlas.stats.motionFX=fx;window.atlas.stats.activeClip=clipName;window.atlas.stats.clipTime=activeAction?.time ?? 0;}
  }
  emitters.forEach(({ mat, intensity }) => { mat.emissiveIntensity = intensity * power * (1 + Math.sin(time * 2.3) * 0.06); });
  powerLight.intensity = power * (characters[activeCharacter]?.reactorLightIntensity ?? 0); powerLight.position.set(0, 4.35, 0.8);
  controls.update(); renderer.info.reset(); composer.render();
  frameCount++;
  if (now - sampleStart > 1500) { const fps = Math.round(frameCount * 1000 / (now - sampleStart)); $('#renderStatus').textContent = `${fps} FPS / REALTIME PBR`; if (window.atlas) Object.assign(window.atlas.stats, { fps, drawCalls: renderer.info.render.calls, renderedTriangles: renderer.info.render.triangles, textureCount: renderer.info.memory.textures }); frameCount = 0; sampleStart = now; }
});
let wasMobile = innerWidth < 701;
window.addEventListener('resize', () => { camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); composer.setSize(innerWidth, innerHeight); const mobile = innerWidth < 701; if (mobile !== wasMobile) resetCamera(); wasMobile = mobile; });
