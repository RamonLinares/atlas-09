# SERAPH / 03

A dark titanium mecha with silver articulated metal wings, amber lighting, and a large cannon replacing its anatomical right forearm. Created using the agreed character creation prompt, alongside ATLAS and AETHER in the existing viewer.

## Assets and reproduction

- Concept: `assets/seraph-03/concepts/seraph-03.png` (original OpenAI image generation).
- Exact creation prompt: `assets/seraph-03/creation-prompt.txt`.
- Tripo source and retopology: `assets/seraph-03/source/` and `assets/seraph-03/retopo/`.
- Portable Blender project: `blender/SERAPH-03.blend`, with packed textures.
- Animated runtime asset: `public/models/seraph-03.glb`.
- Extracted textures: `public/textures/seraph-03/`.

Rebuild with Blender 5.1:

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/build_seraph.py -- --skip-render
/Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/validate_seraph.py
node scripts/validate_glb.mjs public/models/seraph-03.glb output/seraph-03/gltf-validation.json
npm run build -- --base=/atlas-09/
```

The character is normalized to 20 meters from sole to the highest wingtip in its source pose. Its body is approximately 15 meters tall. The final asset has 28,386 triangles, 15,137 mesh vertices, 22 bones, and two materials. Two zero-area source triangles are removed during intake. Rigid armor is separated at inspected anatomical seams; connected-island checks repair lower wing plates and cannon fragments that overlap other parts in front view; four additional wing bones articulate the wing roots and outer plates. A right hand control exists for skeletal compatibility, but the source has a cannon instead of a right hand. `Muzzle_R` is attached to the cannon's forearm bone.

## Motion

Six baked clips: Sentinel (idle), WingDeploy (activation), Run, KneelFire, Backflip, and Flight. The cannon uses a carried pose while running, and the wings fold behind the shoulders. Firing effects use an amber projectile synchronized with the cannon's 0.64 second recoil interval. Flight adds a lift, hover, and landing sequence. The viewer fits each clip's complete motion envelope to its camera.

Animation is authored locally, without additional provider charges. The existing ATLAS and AETHER model files are preserved.

## Cost and provenance

Tripo image-to-model task `fa47e26c-98f7-4ae5-baec-99f8e93b748b` used model `v3.1-20260211`, standard geometry and texture quality, PBR textures, and a 150,000 face target: 30 credits. Smart retopology task `643b8c72-4326-491e-aa6f-1f029a03ab78` targeted 20,000 faces and consumed another 30 credits. Total: 60 credits, US$0.60 at the checked rate of US$0.01 per credit, within the authorized US$1 cap. See the preserved task receipts and [Tripo's pricing](https://developers.tripo3d.ai/en/pricing).

## Validation and limitations

Validation reports are saved under `output/seraph-03/`; browser captures are under `output/playwright/`. The independent anatomical tests rotate both arms, both thighs, and each wing root, checking that unrelated anatomical regions remain stationary. Motion validation samples between animation keys, verifies rigid triangle edges, loop closure, finite coordinates, and floor clearance. Both UV channels are inspected for invalid coordinates and degenerate faces. Mirrored source leg surfaces provide an independent regression against accidentally binding a leg panel to the cannon. The browser also samples actual skinned vertices through each motion on desktop and mobile, checks camera bounds, and verifies muzzle direction and recoil timing. A 1024 × 768 layout check verifies that the feet remain above the toolbar. The final GLB validator reports zero errors and zero warnings; the Vite production build passes with the existing bundle-size advisory.

This is a realtime prototype made from a generated surface. The wing plates articulate as rigid outer assemblies rather than individually simulated feathers. Armor cuts expose some joint gaps at extreme poses, and the source has baked surface detail rather than fully modeled internal mechanisms. The cannon and wings are not physics simulated. Flight is an authored display animation.
