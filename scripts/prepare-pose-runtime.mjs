import { mkdir, copyFile, readdir } from 'node:fs/promises';
const source = new URL('../node_modules/@mediapipe/tasks-vision/', import.meta.url);
const target = new URL('../public/tracking/runtime/', import.meta.url);
await mkdir(new URL('wasm/', target), { recursive: true });
await copyFile(new URL('vision_bundle.js', source), new URL('vision_bundle.js', target));
for (const name of await readdir(new URL('wasm/', source))) {
  if (/\.(js|wasm)$/.test(name)) await copyFile(new URL(`wasm/${name}`, source), new URL(`wasm/${name}`, target));
}
