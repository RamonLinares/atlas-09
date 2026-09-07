# TITAN / 06

**Free for commercial and noncommercial use under [CC0 1.0](ASSET-LICENSE.md). No attribution or permission required.**

An original 19-metre classic super-robot mecha in the heroic 1970s silhouette: deep royal blue lacquered armor over graphite actuators, a crimson chest plate with a golden V crest, twin swept golden horns, dome pauldrons, cylindrical forearm gauntlets that launch as rocket fists, and a chest-mounted beam lens. TITAN joins ATLAS, AETHER, SERAPH, RONIN and SCORPIO in the same interactive studio viewer.

## Deliverables

- [Packed Blender project](blender/TITAN_06.blend)
- [Animated GLB](public/models/titan-06.glb)
- [Original concept](assets/titan-06/concepts/titan-06.png)
- [Extracted textures](public/textures/titan-06/)
- [Blender beauty render](output/titan-06/titan-06-beauty.png)
- [Anatomy](scripts/titan_anatomy.py), [build script](scripts/build_titan.py), [authored motions](scripts/titan_motions.py), shared [preparation module](scripts/classic_mecha.py) and [validation](scripts/validate_classic.py)
- [Live studio viewer](https://ramonlinares.github.io/atlas-09/?character=titan-06&motion=RocketPunch)

The GLB contains six baked skeletal actions: Sentinel idle (6 s), RocketPunch (3.5 s), ChestBeam (4 s), Run (1.2 s), KneelFire (8 s) and Backflip (3.6 s). The rocket fist is real geometry: the right gauntlet bone translates 9.5 m along its own axis, exposing a thruster nozzle recessed in the elbow, then returns. The viewer adds a thruster flame during the launch, a chest beam with bloom while the lens fires, and knuckle-blaster rounds during the kneeling burst.

## Movements

- **Rocket Punch** — fighting stance, right arm cocked back with a torso twist, driven forward, gauntlet launched and recovered, relax. The left fist holds a guard throughout; both boots stay planted.
- **Chest Beam** — arms swing wide and back, legs brace lower and wider, the chest thrusts forward while the beam fires from the crest lens with a slight recoil shiver, then the frame relaxes.
- **Run** — heavy in-place cycle from the shared motion library with wide, slower footfalls and swinging fists clear of the hips.
- **Kneel & Fire** — drops until the folded rear leg rests on the floor, lines the right arm up on the target for a knuckle-blaster burst while the left arm stays bent with the fist forward, then stands. The rear leg is seated by its own contact pass so the front boot stays planted.
- **Backflip** — crouch, launch, full backward rotation around the pelvis, landing absorb.
- **Idle** — subtle breathing, head scan and pauldron sway.

## Provenance and cost

The user's reusable [creation prompt](assets/titan-06/creation-prompt.txt) authorized autonomous execution and up to US$1 for generation and retopology.

1. The reference image was generated with Google's Gemini image API through the local `threejs-image-generator` tooling (no OpenAI image credential was available in this environment). The exact prompt is saved in [prompt.txt](assets/titan-06/concepts/prompt.txt).
2. Tripo image-to-model task `7bb91975-e08f-4c99-87ae-432a642690aa`: model `v3.1-20260211`, standard geometry and texture, PBR, UVs, 150,000 requested faces, model/texture seeds `9072026`, original-image texture alignment. **30 credits consumed** (account balance 1090 → 1060).
3. Tripo smart retopology task `0379bea6-ab60-4230-8a03-4c88de362974`: `P-v2.0-20251225`, requested 20,000 faces with baked textures. **30 credits consumed**. The delivered source contains 23,427 triangles.
4. Local Blender preparation, rigid mechanical rigging, hardware and authored animation incurred no additional provider charges.

**Total Tripo consumption: 60 credits, US$0.60** at US$0.01 per credit, within the US$1.00 budget. Provider meshes, previews and task receipts are preserved under `assets/titan-06/source/` and `assets/titan-06/retopo/`.

## Preparation and checks

The source was normalized to 19 m, inspected from the front, side and back, and measured in per-height vertex bands before sectioning (`scripts/inspect_classic.py`, reports in `output/titan-06/`). Geometry is split at mechanical boundaries and given 100% rigid weights: head, chest, pelvis, and per side upper arm (including the whole pauldron, assigned by an ellipsoid rather than a flat cut), forearm (the gauntlet), hand, thigh (including the knee plate that hangs over the shin), shin and boot. Graphite joint housings close the rotating seams; additional hardware adds rocket nozzles, knuckle blasters, the chest lens and two emissive eye lenses, because the generated texture paints the eyes in the same dull gold as the trim and no colour mask could separate them.

- Rigid binding, UV bounds and zero-area faces, and independent domain isolation (head, each arm, legs) are asserted by `validate_classic.py`.
- Every clip is checked for loop closure, connected joints, absence of unintended bone translation (only the right forearm translates, and only in RocketPunch), bounded frame-to-frame angular change, rigid edge lengths, and ground contact. The kneel checks the front boot and the rear leg on the floor; RocketPunch must reach more than 8 m forward and ChestBeam must spread the fists more than 2 m beyond rest, with both boots planted.
- Quarter-frame contact sampling adds root corrections so interpolated geometry never dips under the floor.
- Per-motion swept bounds in `src/titan-motion-bounds.json` frame the launched fist and the beam stance on desktop and mobile.
- Khronos glTF validator results (`gltf-validation.json`, 0 errors, 0 warnings), Blender validation (`blender-validation.json`), review frame sheets (`motion/sheet-*.png`) and the interactive browser verification record (`browser-validation.json`) are in `output/titan-06/`. `scripts/check_classic.js` is the reproducible Playwright routine for the browser pass.

## Reproduce

```sh
blender -b --python scripts/inspect_classic.py -- titan-06 19
blender -b --python scripts/build_titan.py
blender -b --python scripts/validate_classic.py -- titan-06
blender -b --python scripts/render_classic_frames.py -- TITAN_06 titan-06
node scripts/validate_glb.mjs public/models/titan-06.glb output/titan-06/gltf-validation.json
npm run build -- --base=/atlas-09/
```

Rebuilding runs entirely locally from the preserved retopology and consumes 0 credits.

## Remaining limitations

This is a realtime presentation asset. The retopologized armor is not watertight and separated rigid sections leave boundary edges; the pauldrons ride the upper arms as single rigid domes, so extreme arm raises can push a pauldron into the collar. The rocket fist has no trailing cable or recovery physics; it flies and returns along its axis. Eyes are separate emissive lenses rather than texture emission. Firing, beam and thruster effects are rendered in Three.js rather than baked into the GLB. There is no gameplay collision capsule or ragdoll rig.
