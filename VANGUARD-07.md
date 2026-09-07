# VANGUARD / 07

**Free for commercial and noncommercial use under [CC0 1.0](ASSET-LICENSE.md). No attribution or permission required.**

An original 18-metre classic real-robot military mecha: white satin armor with a cobalt chest block, red lower torso and skirt plates, small yellow accents, dark inner-frame actuators, a golden V antenna, green camera eyes, a slim backpack with two vernier nozzles, a beam rifle in the right hand and an armored shield on the left forearm. VANGUARD joins ATLAS, AETHER, SERAPH, RONIN, SCORPIO and TITAN in the same interactive studio viewer.

## Deliverables

- [Packed Blender project](blender/VANGUARD_07.blend)
- [Animated GLB](public/models/vanguard-07.glb)
- [Original concept](assets/vanguard-07/concepts/vanguard-07.png)
- [Extracted textures](public/textures/vanguard-07/)
- [Blender beauty render](output/vanguard-07/vanguard-07-beauty.png)
- [Anatomy](scripts/vanguard_anatomy.py), [build script](scripts/build_vanguard.py), [authored motions](scripts/vanguard_motions.py), shared [preparation module](scripts/classic_mecha.py) and [validation](scripts/validate_classic.py)
- [Live studio viewer](https://ramonlinares.github.io/atlas-09/?character=vanguard-07&motion=RifleBurst)

The GLB contains seven baked skeletal actions: Sentinel idle (6 s), RifleBurst (3.2 s), ShieldGuard (3 s), BoostJump (3.6 s), Run (1.07 s), KneelFire (8 s) and Backflip (3.6 s). The viewer adds beam-rifle rounds during the standing burst and the kneeling burst, and two vernier flames during the boost jump.

## Movements

- **Rifle Burst** — the torso turns the rifle side forward, the right arm brings the rifle to shoulder height, the shield arm rises beside it as a forward guard, six shots at 0.2-second intervals kick the rifle and torso, then the frame lowers.
- **Shield Guard** — the left forearm crosses the chest so the shield covers the torso and head, the body turns behind it and drops lower, the rifle arm swings back out of the way, an impact at 1.4 s pushes the frame back, then it recovers.
- **Boost Jump** — crouch, vernier launch to 6.5 m with the legs trailing and the arms spread, a hovering bob, descent, landing compression and stand. Root motion is vertical only so the clip loops in place.
- **Run** — shared-library in-place cycle with the rifle carried across the front and the shield arm swinging less.
- **Kneel & Fire** — drops onto the folded rear leg, the rifle aims forward for the burst with recoil, the left arm stays bent with the hand forward at knee height and the shield outboard, then stands.
- **Backflip** — crouch, launch, full backward rotation, landing absorb, rifle kept clear of the legs.
- **Idle** — breathing, head turn and small arm settling.

Skirt plates are separate bones that follow each thigh from the shared hip pivot, as on RONIN, so running and the front kneeling leg do not push the thighs through the armor; a thigh that folds backward under the hip lets its plates hang instead.

## Provenance and cost

The user's reusable [creation prompt](assets/vanguard-07/creation-prompt.txt) authorized autonomous execution and up to US$1 for generation and retopology.

1. The reference image was generated with Google's Gemini image API through the local `threejs-image-generator` tooling (no OpenAI image credential was available in this environment). The first draft stood with its arms at its sides and the rifle against the leg; an in-place edit did not widen the pose, so the prompt was strengthened and regenerated. All three images are kept in [assets/vanguard-07/concepts](assets/vanguard-07/concepts/); the final prompt is [prompt.txt](assets/vanguard-07/concepts/prompt.txt).
2. Tripo image-to-model task `c36254b3-0811-47f0-8fd3-6098d3292b28`: model `v3.1-20260211`, standard geometry and texture, PBR, UVs, 150,000 requested faces, model/texture seeds `9072027`, original-image texture alignment. **30 credits consumed**.
3. Tripo smart retopology task `6769b5d3-cf8f-4613-a0f7-7070589641a6`: `P-v2.0-20251225`, requested 20,000 faces with baked textures. **30 credits consumed**. The delivered source contains 23,578 triangles.
4. Local Blender preparation, rigid rigging, hardware and authored animation incurred no additional provider charges.

**Total Tripo consumption: 60 credits, US$0.60** at US$0.01 per credit, within the US$1.00 budget (account balance 1090 → 970 across both new characters). Provider meshes, previews and task receipts are preserved under `assets/vanguard-07/source/` and `assets/vanguard-07/retopo/`.

## Preparation and checks

The source arrived 0.52 m right of centre and 0.3 m behind; the build recentres it before sectioning. Sections: head, chest (including the backpack and verniers), pelvis (with the rear skirt), per-side skirt plates, thigh, shin, foot, upper arm (with the shoulder armor), forearm, hand, plus the rifle (its own bone under the right hand, carrying the muzzle) and the shield (bound to the left forearm along its measured inner edge). Everything is 100% rigid. Graphite joint housings close the rotating seams; hardware adds vernier nozzle rings with emissive throats and a beam emitter at the rifle muzzle. Green emission is extracted from the camera eyes and sensors in the base colour texture.

- Rigid binding, UV bounds and zero-area faces, and independent domain isolation (head, each arm including rifle and shield, legs) are asserted by `validate_classic.py`.
- Every clip is checked for loop closure, connected joints, no bone translation other than the root, bounded frame-to-frame angular change, rigid edge lengths and ground contact. The kneel checks the front boot and the rear leg on the floor; RifleBurst must bring the rifle more than 3 m forward and ShieldGuard the shield forearm more than 1.5 m forward with both boots planted; BoostJump must lift the boots more than 4 m.
- Quarter-frame contact sampling adds root corrections so interpolated geometry never dips under the floor.
- Per-motion swept bounds in `src/vanguard-motion-bounds.json` frame the rifle, shield and jump apex on desktop and mobile.
- Khronos glTF validator results (`gltf-validation.json`, 0 errors, 0 warnings), Blender validation (`blender-validation.json`), review frame sheets (`motion/sheet-*.png`) and the interactive browser verification record (`browser-validation.json`) are in `output/vanguard-07/`. `scripts/check_classic.js` is the reproducible Playwright routine for the browser pass.

## Reproduce

```sh
blender -b --python scripts/inspect_classic.py -- vanguard-07 18
blender -b --python scripts/build_vanguard.py
blender -b --python scripts/validate_classic.py -- vanguard-07
blender -b --python scripts/render_classic_frames.py -- VANGUARD_07 vanguard-07
node scripts/validate_glb.mjs public/models/vanguard-07.glb output/vanguard-07/gltf-validation.json
npm run build -- --base=/atlas-09/
```

Rebuilding runs entirely locally from the preserved retopology and consumes 0 credits.

## Remaining limitations

This is a realtime presentation asset. The retopologized armor is not watertight and separated rigid sections leave boundary edges. The rifle and hand are one rigid unit; the rifle cannot be holstered or handed over. The shield is fixed to the forearm at its generated angle and does not swivel. Hands do not open. The boost jump is a display motion with no physics or ground scorch. Firing and vernier effects are rendered in Three.js rather than baked into the GLB. There is no gameplay collision capsule or ragdoll rig. The design deliberately evokes the classic real-robot archetype without reproducing any specific franchise machine; it is an original generated model.
