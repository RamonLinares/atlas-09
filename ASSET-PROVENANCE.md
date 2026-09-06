# ATLAS / 09 — asset provenance

Created 2026-09-06 for the request: a giant mecha robot that has seen better days but still keeps its power. No Higgsfield or Seedance used.

## Concept

OpenAI built-in image generation, stylized-concept mode. Saved to `assets/concepts/atlas-09.png`. The exact prompt is in `assets/concepts/prompt.txt`.

## Tripo

Credential probe: `TRIPO_API_KEY=SET`. No secret is stored in the application.

The user explicitly chose “Use smart retopology — about $0.60 total.” No other paid postprocessing or premium generation options were used.

| Step | Task | Estimate | Consumed |
| --- | --- | ---: | ---: |
| Image to model | `e5192c06-e783-49b4-a2c1-1b25441ecbc7` | 30 credits | 30 credits |
| Smart retopology | `e7b54117-37cf-494b-a3ce-d7d3ead2920c` | 30 credits | 30 credits |

Total consumed: **60 credits ($0.60)**.

Generation settings: `v3.1-20260211`, standard geometry and texture quality, PBR and UV export enabled, original-image texture alignment, 150,000 face target, model and texture seeds 9042026. No orientation override, multiview, autofix, or automatic part generation.

Retopology: `v2.0`, 18,000 triangle target, baked textures enabled, triangle output. `--approve-premium` was used only after the user's explicit selection. Provider targets are adaptive; measured output counts are in `output/asset-report.json`.

Original task metadata and downloaded source files are retained under `assets/source` and `assets/retopo`. Provider download links in task JSON are temporary and are not used at runtime.

## Blender

Blender 5.1.2. Reproducible preparation script: `scripts/build_mecha.py`. The Blender file contains the actual character, PBR maps, named rigid skin groups, armature, animations, UVs and a rendering stage. The exported character is the same mesh and rig, excluding the studio stage.

Local work: orientation/scale normalization, UV-seam-safe vertex welding, rigid joint ownership segmentation, a second packed UV channel, emissive data derived from cyan texture elements, FK armature, Sentinel and Awaken animation clips, embedded PBR textures, GLB export, Blender render and audit.

## Three.js

### Motion expansion

Added locally at the user's request: Run, KneelFire and Backflip. No additional provider calls or credits. `scripts/motion_library.py` adds joint housings and an integrated pulse cannon, solves leg targets with analytic two-bone IK, performs a contact pass and bakes rotations/translations into the existing rig. `src/motion-fx.js` supplies clip-synchronized pulse rounds, muzzle flash and a landing ring in the browser. The same five skeletal clips are in Blender and the exported GLB. Original deliverables are preserved in `blender/versions/`.

The browser loads the Blender-exported GLB with GLTFLoader and plays the embedded clips with AnimationMixer. The model is normalized to 6.5 display units in the studio viewer; the downloadable GLB and Blender source preserve 18-metre physical height. The viewer adds its own lighting, studio floor, bloom and inspection controls. No generation credentials or live provider calls are included in the client.

Reference documentation: [Tripo image generation](https://developers.tripo3d.ai/en/docs/generation-image-to-model/h), [Tripo pricing](https://developers.tripo3d.ai/en/pricing), [Three.js](https://threejs.org/docs/).

The run refinement is also local: no provider calls or additional credits. `motion_library.py` now authors foot contact, rolling, recovery and body counter-rotation using character-specific timing. Both Blender sources and GLBs include it.
