# FORGE — Character Lab

Two original mecha characters, reconstructed and retopologized with Tripo, prepared and rigged in Blender, and exported into an interactive Three.js studio.

| Character | Design | Blender source | Animated model |
| --- | --- | --- | --- |
| ATLAS / 09 | Battle-worn 18-metre heavy mecha with olive armor | [ATLAS-09.blend](blender/ATLAS-09.blend) | [atlas-09.glb](public/models/atlas-09.glb) |
| AETHER / 02 | Athletic 14-metre mecha with streamlined white steel and opaque smoked glass | [AETHER-02.blend](blender/AETHER-02.blend) | [aether-02.glb](public/models/aether-02.glb) |

Use **SELECT FRAME** to change characters. Each has its own concept, model download, descriptive information, materials, rig and five clips. The viewer releases the previous character's graphics resources when switching. Both are normalized to the same display height for inspection; their physical design heights remain embedded in the source assets.

Direct links can select a character and motion, for example `/?character=aether-02&motion=Run`. Open the [live viewer](https://ramonlinares.github.io/atlas-09/) or go directly to [AETHER](https://ramonlinares.github.io/atlas-09/?character=aether-02). GitHub Actions builds and publishes the viewer on every push to `main`. The Pages build uses `npm run build -- --base=/atlas-09/` so models, concept images and downloads resolve under the repository path.

AETHER's full provenance, checks and limitations are in [AETHER-02.md](AETHER-02.md). The remaining original asset notes below describe ATLAS unless stated otherwise.

## Open the result

- Blender source: `blender/ATLAS-09.blend`
- Portable animated character: `public/models/atlas-09.glb`
- Blender beauty render: `output/atlas-09-beauty.png`
- Original concept: `assets/concepts/atlas-09.png`
- Production assessment: `PRODUCTION-READINESS.md`
- Prompts, provider tasks, settings and cost: `ASSET-PROVENANCE.md`

The `.blend` includes packed textures, two UV layers, a named 18-bone FK rig, rigid weights, five animation actions, and a studio stage. Press Play on the Blender timeline for Sentinel; select Run, KneelFire, Backflip or Awaken in the Action Editor for the other motions. The same character and clips are embedded in the GLB. Blender's studio floor, lights and camera are excluded from that character export.

## Run the Three.js viewer

```sh
npm install
npm run dev
```

Open the localhost address printed by Vite. In this session the server is at `http://127.0.0.1:5175` because two lower ports were already occupied.

Drag to orbit, scroll/pinch to zoom, and choose **Idle**, **Run**, **Kneel & Fire**, **Backflip**, **Awaken**, or **Rest**. The pulse cannon's muzzle flash and projectiles are added in Three.js and synchronized to the firing clip. The backflip camera pulls back to keep the jump visible. Wireframe, skeleton and turntable remain available. The core-intensity slider changes emissive output. Get Model downloads the complete animated GLB. Concept opens the original reference.

The viewer uses local model assets. Fonts load from Google Fonts with local fallbacks. WebGL2 is required. No Tripo or image-generation key is needed to view or rebuild the application.

## Build and verify

```sh
npm run build
npm run preview
npm run validate:asset
```

The production bundle is `dist/`. `gltf-validator` is a development dependency; its detailed output is saved to `output/gltf-validation.json`.

To reproduce local asset preparation with Blender installed:

```sh
blender -b --python scripts/build_mecha.py
blender -b --python scripts/validate_scene.py
blender -b --python scripts/build_aether.py
blender -b --python scripts/validate_aether.py
npm run validate:asset
node scripts/validate_glb.mjs public/models/aether-02.glb output/aether-02/gltf-validation.json
```

The preparation script reads the already downloaded Tripo retopology in `assets/retopo`, so rebuilding is local and uses no provider credits. It recreates the mesh, unwrap, rig, clips, textures, GLB, Blender file, beauty render, and audit data. It also repairs a rare zero tangent at a split vertex using the local triangle's UV differential.

`scripts/browser_checks.js` is a Playwright CLI inspection routine. The executed results are in `output/browser-validation.json`; screenshots are in `output/playwright/`. Blender geometry and animation checks are in `output/blender-validation.json`.

## Asset conventions

- Physical height: 18 metres. Blender is Z-up / -Y-forward; the GLB is Y-up / +Z-forward.
- Viewer: a display wrapper scales the character to 6.5 studio units.
- UV0 / `Atlas_Surface`: baked base color, metal/roughness, normal and derived emission.
- UV1 / `Atlas_Lightmap`: additional packed Blender unwrap, available for future baking.
- Four materials, one Blender mesh (four glTF primitives), 17 rigid sections, 18 bones. The extra geometry consists of joint housings and an integrated pulse cannon.
- Sentinel: approximately 6 seconds. Awaken: approximately 5 seconds. Both loop in place.
- Run: 1.4-second in-place cycle with alternating contacts and flight phases. KneelFire: 8-second drop/fire/stand sequence. Backflip: 3.6-second crouch/jump/full backward rotation/landing sequence.
- New poses use an analytic two-bone IK solver during baking; the exported clips use ordinary bone transforms and require no runtime IK library.
- Rig uses `.L` / `.R` suffixes in Blender. Three.js sanitizes dots in node names when loading; use the loaded bone names when extending the viewer.

This is a realtime prototype and presentation asset. Read the production assessment before using it for demanding animation, close-up film shots or mobile production.
