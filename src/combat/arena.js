import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

/** A night proving ground: 80 m ring, floodlit pillars, fog and bloom. Units are metres. */
export function createArena(canvas) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.75)); renderer.setSize(innerWidth, innerHeight);
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.1;
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#0d1214'); scene.fog = new THREE.FogExp2('#0d1214', .0062);
  const camera = new THREE.PerspectiveCamera(44, innerWidth / innerHeight, .5, 900);
  const pmrem = new THREE.PMREMGenerator(renderer); const room = new RoomEnvironment();
  scene.environment = pmrem.fromScene(room, .04).texture; scene.environmentIntensity = .35; room.dispose(); pmrem.dispose();
  scene.add(new THREE.HemisphereLight('#b9c9d6', '#1a1f1a', .9));
  const moon = new THREE.DirectionalLight('#dfe9ff', 2.6); moon.position.set(-60, 120, 40); moon.castShadow = true;
  moon.shadow.mapSize.set(2048, 2048); Object.assign(moon.shadow.camera, { left: -90, right: 90, top: 90, bottom: -90, near: 10, far: 300 });
  moon.shadow.bias = -.0004; moon.shadow.normalBias = .3; scene.add(moon);
  const warm = new THREE.DirectionalLight('#ffb27a', 1.1); warm.position.set(70, 40, -50); scene.add(warm);

  // Floor: cracked graphite with a painted ring and radial marks.
  const tex = document.createElement('canvas'); tex.width = tex.height = 1024; const g = tex.getContext('2d');
  g.fillStyle = '#20262a'; g.fillRect(0, 0, 1024, 1024);
  for (let i = 0; i < 6000; i++) { g.fillStyle = `rgba(${40 + Math.random() * 30},${44 + Math.random() * 30},${44 + Math.random() * 30},.5)`; g.fillRect(Math.random() * 1024, Math.random() * 1024, 2 + Math.random() * 6, 2 + Math.random() * 6); }
  g.strokeStyle = 'rgba(120,135,110,.35)'; g.lineWidth = 2;
  for (let i = 0; i <= 16; i++) { g.beginPath(); g.moveTo(i * 64, 0); g.lineTo(i * 64, 1024); g.stroke(); g.beginPath(); g.moveTo(0, i * 64); g.lineTo(1024, i * 64); g.stroke(); }
  const floorTexture = new THREE.CanvasTexture(tex); floorTexture.wrapS = floorTexture.wrapT = THREE.RepeatWrapping; floorTexture.repeat.set(12, 12); floorTexture.colorSpace = THREE.SRGBColorSpace;
  const floor = new THREE.Mesh(new THREE.CircleGeometry(400, 96), new THREE.MeshStandardMaterial({ map: floorTexture, roughness: .93, metalness: .08 }));
  floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; scene.add(floor);
  const ringMaterial = new THREE.MeshBasicMaterial({ color: '#d5f3a5', transparent: true, opacity: .35, side: THREE.DoubleSide, depthWrite: false });
  for (const [inner, outer] of [[78, 78.6], [40, 40.25]]) { const ring = new THREE.Mesh(new THREE.RingGeometry(inner, outer, 160), ringMaterial); ring.rotation.x = -Math.PI / 2; ring.position.y = .06; scene.add(ring); }
  for (let i = 0; i < 72; i++) { const a = i / 72 * Math.PI * 2; const tick = new THREE.Mesh(new THREE.BoxGeometry(.25, .05, i % 6 ? 1.2 : 3.2), ringMaterial); tick.position.set(Math.sin(a) * 76.5, .06, Math.cos(a) * 76.5); tick.rotation.y = a; scene.add(tick); }

  // Perimeter: floodlight pylons and broken wall segments.
  const pylonMaterial = new THREE.MeshStandardMaterial({ color: '#2b3134', roughness: .6, metalness: .55 });
  const lampMaterial = new THREE.MeshStandardMaterial({ color: '#0a0c0c', emissive: '#f4f2d6', emissiveIntensity: 5 });
  const wallMaterial = new THREE.MeshStandardMaterial({ color: '#3a4044', roughness: .85, metalness: .2 });
  for (let i = 0; i < 12; i++) {
    const a = i / 12 * Math.PI * 2, x = Math.sin(a) * 96, z = Math.cos(a) * 96;
    const pylon = new THREE.Mesh(new THREE.CylinderGeometry(1.6, 2.4, 42, 10), pylonMaterial); pylon.position.set(x, 21, z); pylon.castShadow = true; scene.add(pylon);
    const head = new THREE.Mesh(new THREE.BoxGeometry(7, 2.2, 3), lampMaterial); head.position.set(x * .97, 42, z * .97); head.lookAt(0, 30, 0); scene.add(head);
    const light = new THREE.SpotLight('#f7f3dc', 160, 260, .55, .6, 1); light.position.set(x * .96, 41, z * .96); light.target.position.set(x * .25, 0, z * .25); scene.add(light, light.target);
    if (i % 3 !== 1) { const wall = new THREE.Mesh(new THREE.BoxGeometry(34, 10 + (i % 4) * 4, 4), wallMaterial); wall.position.set(Math.sin(a + .13) * 112, wall.geometry.parameters.height / 2, Math.cos(a + .13) * 112); wall.rotation.y = a; wall.castShadow = true; wall.receiveShadow = true; scene.add(wall); }
  }
  // Wrecks and rubble outside the ring for scale.
  const rubble = new THREE.MeshStandardMaterial({ color: '#4b4f4a', roughness: .95 });
  for (let i = 0; i < 40; i++) {
    const a = Math.random() * Math.PI * 2, r = 84 + Math.random() * 40, s = 2 + Math.random() * 6;
    const rock = new THREE.Mesh(new THREE.DodecahedronGeometry(s, 0), rubble); rock.position.set(Math.sin(a) * r, s * .4, Math.cos(a) * r); rock.rotation.set(Math.random(), Math.random(), Math.random()); rock.castShadow = true; scene.add(rock);
  }
  const stars = new THREE.Points(new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute(Array.from({ length: 1200 * 3 }, (_, i) => i % 3 === 1 ? 120 + Math.random() * 500 : (Math.random() - .5) * 1400), 3)), new THREE.PointsMaterial({ color: '#c9d6e6', size: 1.6, sizeAttenuation: true, transparent: true, opacity: .7 }));
  scene.add(stars);

  const composer = new EffectComposer(renderer);
  composer.addPass(new RenderPass(scene, camera));
  composer.addPass(new UnrealBloomPass(new THREE.Vector2(innerWidth, innerHeight), .3, .55, 1.4));
  composer.addPass(new OutputPass());
  function resize() { camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); composer.setSize(innerWidth, innerHeight); }
  addEventListener('resize', resize);
  return { renderer, scene, camera, composer, resize };
}
