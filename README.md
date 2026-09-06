# FORGE — Character Lab

Five original mecha characters, reconstructed and retopologized with Tripo, prepared and rigged in Blender, and exported into an interactive Three.js studio.

| Character | Design | Blender source | Animated model |
| --- | --- | --- | --- |
| ATLAS / 09 | Battle-worn 18-metre heavy mecha with olive armor | [ATLAS-09.blend](blender/ATLAS-09.blend) | [atlas-09.glb](public/models/atlas-09.glb) |
| AETHER / 02 | Athletic 14-metre mecha with streamlined white steel and opaque smoked glass | [AETHER-02.blend](blender/AETHER-02.blend) | [aether-02.glb](public/models/aether-02.glb) |
| SERAPH / 03 | Titanium mecha with metal wings, 20-metre wingtip height, and a heavy right cannon arm | [SERAPH-03.blend](blender/SERAPH-03.blend) | [seraph-03.glb](public/models/seraph-03.glb) |
| RONIN / 04 | 16-metre samurai mecha with crimson armor, gold crescent helmet and katana | [RONIN-04.blend](blender/RONIN-04.blend) | [ronin-04.glb](public/models/ronin-04.glb) |
| SCORPIO / 05 | 17-metre scorpion predator mecha with hydraulic pincer claws and plasma stinger tail | [SCORPIO-05.blend](blender/SCORPIO-05.blend) | [scorpio-05.glb](public/models/scorpio-05.glb) |

Use **SELECT FRAME** to change characters. Each has its own concept, model download, descriptive information, materials, rig and baked clips. ATLAS and AETHER have seven motions; SERAPH, RONIN, and SCORPIO have six motions each, including specialized combat attacks (wing deployment/flight, blade salute/slash, and stinger strike/pincer strike). The viewer releases the previous character's graphics resources when switching. Body heights are normalized for inspection, with SERAPH and SCORPIO framed for their respective wing and stinger envelopes; their physical design heights remain embedded in the source assets.

Direct links can select a character and motion, for example `/?character=scorpio-05&motion=StingerStrike`. Open the [live viewer](https://ramonlinares.github.io/atlas-09/) or go directly to [SCORPIO](https://ramonlinares.github.io/atlas-09/?character=scorpio-05). GitHub Actions builds and publishes the viewer on every push to `main`. The Pages build uses `npm run build -- --base=/atlas-09/` so models, concept images and downloads resolve under the repository path.

The added characters' full provenance, checks and limitations are in [AETHER-02.md](AETHER-02.md), [SERAPH-03.md](SERAPH-03.md), [RONIN-04.md](RONIN-04.md), and [SCORPIO-05.md](SCORPIO-05.md). The remaining original asset notes below describe ATLAS unless stated otherwise.

## Open the result

- Blender source: `blender/ATLAS-09.blend`
- Portable animated character: `public/models/atlas-09.glb`
- Blender beauty render: `output/atlas-09-beauty.png`
- Original concept: `assets/concepts/atlas-09.png`
- Production assessment: `PRODUCTION-READINESS.md`
- Prompts, provider tasks, settings and cost: `ASSET-PROVENANCE.md`

The `.blend` includes packed textures, two UV layers, a named 18-bone FK rig, rigid weights, seven animation actions, and a studio stage. Press Play on the Blender timeline for Sentinel; select Run, KneelFire, Backflip, Walk, PunchCombo or Collapse in the Action Editor for the other motions. The same character and clips are embedded in the GLB. Blender's studio floor, lights and camera are excluded from that character export.

## Run the Three.js viewer

```sh
npm install
npm run dev
```

Open the localhost address printed by Vite. In this session the server is at `http://127.0.0.1:5175` because two lower ports were already occupied.

Drag to orbit, scroll/pinch to zoom, and choose **Idle**, **Run**, **Kneel & Fire**, **Backflip**, **Punch Combo**, **Walk**, or **Collapse**. The pulse cannon's muzzle flash and projectiles are added in Three.js and synchronized to the firing clip. The backflip camera pulls back to keep the jump visible. Wireframe, skeleton and turntable remain available. The core-intensity slider changes emissive output. Get Model downloads the complete animated GLB. Concept opens the original reference.

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
blender -b --python scripts/build_scorpio.py
blender -b --python scripts/validate_scorpio.py
node scripts/validate_glb.mjs public/models/scorpio-05.glb output/scorpio-05/gltf-validation.json
```

The preparation script reads the already downloaded Tripo retopology in `assets/retopo`, so rebuilding is local and uses no provider credits. It recreates the mesh, unwrap, rig, clips, textures, GLB, Blender file, beauty render, and audit data. It also repairs a rare zero tangent at a split vertex using the local triangle's UV differential.

`scripts/browser_checks.js` is a Playwright CLI inspection routine. The executed results are in `output/browser-validation.json`; screenshots are in `output/playwright/`. Blender geometry and animation checks are in `output/blender-validation.json`.

## Asset conventions

- Physical height: 18 metres. Blender is Z-up / -Y-forward; the GLB is Y-up / +Z-forward.
- Viewer: a display wrapper scales the character to 6.5 studio units.
- UV0 / `Atlas_Surface`: baked base color, metal/roughness, normal and derived emission.
- UV1 / `Atlas_Lightmap`: additional packed Blender unwrap, available for future baking.
- Four materials, one Blender mesh (four glTF primitives), 17 rigid sections, 18 bones. The extra geometry consists of joint housings and an integrated pulse cannon.
- Sentinel: 6-second idle loop. Awaken and the unanimated Rest button have been replaced by distinct library motions.
- Walk: 1.33 seconds on AETHER, 1.60 seconds on ATLAS.
- PunchCombo: jab, cross, hook and recovery, 3.90 seconds on AETHER and 4.70 seconds on ATLAS.
- Collapse: backward fall followed by a held pose, 3.0 seconds on AETHER and 3.60 seconds on ATLAS. It plays once; click Collapse again to replay.
- Run: 1.13-second ATLAS cycle and 0.93-second AETHER cycle, with narrower foot placement, heel settling, toe push-off, early heel recovery and opposing hip/shoulder rotation. KneelFire: 8-second drop/fire/stand sequence. Backflip: 3.6-second crouch/jump/full backward rotation/landing sequence.
- New poses use an analytic two-bone IK solver during baking; the exported clips use ordinary bone transforms and require no runtime IK library.
- Rig uses `.L` / `.R` suffixes in Blender. Three.js sanitizes dots in node names when loading; use the loaded bone names when extending the viewer.

This is a realtime prototype and presentation asset. Read the production assessment before using it for demanding animation, close-up film shots or mobile production.

## Refined run cycles

The run now uses contact and recovery phases instead of broad oval foot paths. Foot spacing is approximately the hip-joint spacing (previously much wider), with compact elbow motion and a small torso counter-rotation. Boot geometry determines ground height and the forefoot pivot. ATLAS has longer support and less flight; AETHER has a faster cadence and more pronounced heel recovery. Baked Run keys use linear interpolation to prevent planted-foot overshoot. All exported clips start at zero, eliminating the previous initial hold.

The Blender and GLB downloads include the updated motion. Other clips retain their sampled poses. `scripts/validate_run.py` measures contact, placement, rolling, coordination and flight from the actual baked armor; [run validation](output/motion/run-validation.json) and [browser verification](output/motion/run-browser-validation.json) record the results. Existing rig, head and thigh isolation checks also pass.

## Imported motion library

Walk, PunchCombo and Collapse are adapted from Quaternius / Gonzalo Furnier’s CC0 Universal Animation Libraries. The free Standard packs supplied all six source clips; no payment, account or cloud animation service was needed. See [motion provenance and rebuild instructions](assets/animations/quaternius/README.md). The existing Idle, Run, KneelFire and Backflip clips are retained.
