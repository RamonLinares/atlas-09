import * as THREE from 'three';

/** Hit sparks, camera shake, floating damage numbers and synthesized audio. */
export function createFeedback(scene, camera, hud) {
  const sparkMaterial = new THREE.PointsMaterial({ color: '#ffe9b0', size: 1.6, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, sizeAttenuation: true });
  const bursts = []; const numbers = []; let shake = 0; let shakeTime = 0;
  let audio = null;
  function context() {
    if (audio) return audio;
    try { audio = new (window.AudioContext || window.webkitAudioContext)(); } catch { audio = null; }
    return audio;
  }
  function tone({ type = 'square', from = 440, to = 80, duration = .12, gain = .2, noise = false }) {
    const ctx = context(); if (!ctx) return; if (ctx.state === 'suspended') ctx.resume();
    const t = ctx.currentTime; const out = ctx.createGain(); out.gain.setValueAtTime(gain, t); out.gain.exponentialRampToValueAtTime(.001, t + duration); out.connect(ctx.destination);
    if (noise) {
      const buffer = ctx.createBuffer(1, ctx.sampleRate * duration, ctx.sampleRate); const data = buffer.getChannelData(0);
      for (let i = 0; i < data.length; i++) data[i] = (Math.random() * 2 - 1) * (1 - i / data.length);
      const src = ctx.createBufferSource(); src.buffer = buffer; const filter = ctx.createBiquadFilter(); filter.type = 'lowpass'; filter.frequency.setValueAtTime(from, t); filter.frequency.exponentialRampToValueAtTime(to, t + duration);
      src.connect(filter); filter.connect(out); src.start(t); src.stop(t + duration);
    } else {
      const osc = ctx.createOscillator(); osc.type = type; osc.frequency.setValueAtTime(from, t); osc.frequency.exponentialRampToValueAtTime(to, t + duration); osc.connect(out); osc.start(t); osc.stop(t + duration);
    }
  }
  const sounds = {
    light() { tone({ noise: true, from: 3000, to: 200, duration: .14, gain: .35 }); tone({ type: 'sine', from: 160, to: 50, duration: .18, gain: .3 }); },
    heavy() { tone({ noise: true, from: 2400, to: 120, duration: .32, gain: .5 }); tone({ type: 'sine', from: 110, to: 35, duration: .4, gain: .5 }); },
    block() { tone({ type: 'triangle', from: 900, to: 300, duration: .1, gain: .2 }); tone({ noise: true, from: 5000, to: 800, duration: .08, gain: .15 }); },
    shot() { tone({ type: 'sawtooth', from: 1400, to: 200, duration: .07, gain: .12 }); },
    dodge() { tone({ noise: true, from: 1200, to: 300, duration: .25, gain: .12 }); },
    ko() { tone({ type: 'sine', from: 80, to: 25, duration: 1.2, gain: .6 }); tone({ noise: true, from: 1600, to: 60, duration: .9, gain: .5 }); },
  };
  function spark(position, count = 26, color = '#ffe9b0', speed = 18) {
    const geometry = new THREE.BufferGeometry(); const pos = new Float32Array(count * 3); const vel = [];
    for (let i = 0; i < count; i++) { pos.set([position.x, position.y, position.z], i * 3); const d = new THREE.Vector3(Math.random() - .5, Math.random() - .2, Math.random() - .5).normalize().multiplyScalar(speed * (.4 + Math.random())); vel.push(d); }
    geometry.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    const material = sparkMaterial.clone(); material.color.set(color);
    const points = new THREE.Points(geometry, material); scene.add(points); bursts.push({ points, vel, life: .45, age: 0 });
  }
  function number(position, text, color) {
    const el = document.createElement('div'); el.className = 'dmg'; el.textContent = text; el.style.color = color; hud.appendChild(el);
    numbers.push({ el, position: position.clone(), age: 0, life: .9 });
  }
  function impact(position, { heavy = false, blocked = false, ranged = false, damage = 0, color = '#ffe9b0' } = {}) {
    if (blocked) { spark(position, 12, '#9fd8ff', 10); shake = Math.max(shake, .25); sounds.block(); }
    else if (ranged) { spark(position, 10, color, 12); shake = Math.max(shake, .18); sounds.shot(); }
    else { spark(position, heavy ? 48 : 26, color, heavy ? 26 : 18); shake = Math.max(shake, heavy ? 1 : .5); heavy ? sounds.heavy() : sounds.light(); }
    if (damage > 0) number(position, `-${damage}`, blocked ? '#9fd8ff' : heavy ? '#ffb27a' : '#ffffff');
  }
  const offset = new THREE.Vector3();
  function update(dt) {
    shakeTime += dt; const strength = shake * 1.1; shake = Math.max(0, shake - dt * 3);
    offset.set(Math.sin(shakeTime * 71) * strength, Math.cos(shakeTime * 57) * strength * .6, 0);
    for (const b of bursts) { b.age += dt; const p = b.points.geometry.attributes.position; for (let i = 0; i < b.vel.length; i++) { b.vel[i].y -= 40 * dt; p.setXYZ(i, p.getX(i) + b.vel[i].x * dt, p.getY(i) + b.vel[i].y * dt, p.getZ(i) + b.vel[i].z * dt); } p.needsUpdate = true; b.points.material.opacity = 1 - b.age / b.life; }
    for (const b of bursts.splice(0).filter(b => { if (b.age < b.life) return true; scene.remove(b.points); b.points.geometry.dispose(); b.points.material.dispose(); return false; })) bursts.push(b);
    const v = new THREE.Vector3();
    for (const n of numbers) { n.age += dt; v.copy(n.position); v.y += n.age * 9; v.project(camera); n.el.style.transform = `translate(${(v.x * .5 + .5) * innerWidth}px, ${(-v.y * .5 + .5) * innerHeight}px) translate(-50%,-50%) scale(${1 + Math.min(.5, n.age * 3)})`; n.el.style.opacity = String(Math.max(0, 1 - n.age / n.life)); }
    for (const n of numbers.splice(0).filter(n => { if (n.age < n.life) return true; n.el.remove(); return false; })) numbers.push(n);
    return offset;
  }
  function dispose() { for (const b of bursts) { scene.remove(b.points); b.points.geometry.dispose(); } bursts.length = 0; for (const n of numbers) n.el.remove(); numbers.length = 0; }
  return { impact, update, dispose, sounds, spark };
}
