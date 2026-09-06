# SCORPIO / 05

An original 17-metre scorpion predator mecha with blackened ceramic chitin armor, weathered desert bronze plating, dual hydraulic pincer claws, an eleven-link dorsal tail plus articulated stinger, an integrated plasma stinger rail-cannon, and vivid venom-green reactor emission. SCORPIO joins ATLAS, AETHER, SERAPH, and RONIN in the same interactive studio viewer.

## Deliverables

- [Packed Blender project](blender/SCORPIO-05.blend)
- [Animated GLB](public/models/scorpio-05.glb)
- [Original concept](assets/scorpio-05/concepts/scorpio-05.png)
- [Extracted textures](public/textures/scorpio-05/)
- [Blender beauty render](output/scorpio-05/scorpio-05-beauty.png)
- [Build script](scripts/build_scorpio.py), [authored motions](scripts/scorpio_motions.py), and [anatomical validation](scripts/validate_scorpio.py)
- [Live studio viewer](https://ramonlinares.github.io/atlas-09/?character=scorpio-05&motion=StingerStrike)

The GLB contains six baked skeletal actions: Sentinel idle (6 s), StingerStrike activation (6 s), ClawSlash attack (4 s), Run (1.4 s), KneelFire (8 s), and Backflip (3.6 s). Venom-plasma muzzle flash and projectile bursts in Three.js are synchronized to the baked stinger recoil at 0.48-second intervals.

## Provenance and cost

The user's reusable [creation prompt](assets/scorpio-05/creation-prompt.txt) authorized autonomous execution and up to US$1 for generation and retopology.

1. OpenAI built-in image generation produced the original reference. Its exact visual prompt is saved in [prompt.txt](assets/scorpio-05/concepts/prompt.txt).
2. Tripo image-to-model task `e17c2621-00d0-4110-bd7f-5fdc38771e94`: model `v3.1-20260211`, standard geometry and texture, PBR, UVs, 150,000 requested faces, model/texture seeds `9062028`, original-image texture alignment. **30 credits consumed**.
3. Tripo smart retopology task `09644c4a-ec3f-45cb-be11-91056907e615`: `v2.0`, requested 20,000 faces with texture preservation. **30 credits consumed**. The delivered source contains 24,393 triangles.
4. Local Blender preparation, rigid mechanical rigging, hardware addition, and authored animations incurred no additional provider charges.

**Total Tripo consumption: 60 credits, US$0.60** at the standard pricing of US$0.01 per credit, well within the US$1.00 budget. Original provider meshes, previews, and task receipts are preserved under `assets/scorpio-05/source/` and `assets/scorpio-05/retopo/`.

## Preparation and checks

The final mesh has **30,445 triangles**, **16,522 Blender vertices**, **30 bones**, four materials, and two UV layers (`Scorpio_Surface` and `Scorpio_Lightmap`). Base color and synthesized venom-green emission maps are 2048²; normal and packed occlusion/roughness/metallic textures are 1024². All textures are packed into the Blender project and embedded in the GLB.

The source was inspected from the front, side, and back before binding. The rig includes separate head, chest, pelvis, shoulder, upper arm, forearm, hand/pincer claw, thigh, shin, foot, and an anatomically measured tail chain (`tail_01` through `tail_11`, plus `stinger`). Geometry is split at mechanical boundaries and given full 100% rigid weights (one bone weight per vertex and per face). Graphite actuator joint housings close visual gaps under the articulated armor, and an integrated plasma muzzle empty (`Muzzle_Stinger`) is parented to the stinger bone.

- Blender validation checks both UV maps for 0 out-of-bounds coordinates and 0 zero-area faces, strict 1.0 single-group rigid binding, independent anatomical domain isolation (moving arms, legs, or tail causes zero unintended displacement in other domains), finite vertex positions, ground clearance, and loop closure.
- Quarter-frame contact sampling adds root corrections where interpolated geometry would touch the floor during rapid kneeling.
- Per-motion swept bounds provide stable desktop/mobile camera framing for the long stinger tail and backflip.
- Khronos glTF validator: **0 errors, 0 warnings**.
- Actual browser checks exercise all six clips at 1440×1000 and 390×844, character switching between all 5 characters, playback, downloads, and page layout overflow.

Reports live in `output/scorpio-05/`; browser screenshots are in `output/playwright/scorpio-*`.

## Movement repair

The previous attack clips had endpoint jumps of 2.48 m (StingerStrike) and 4.14 m (ClawSlash). The five-link tail rig missed the visible couplings, the stinger translated away from its parent, the knee pivots sat above the actual joints, and the firing socket used the wrong axis.

The repair follows the visible tail joints, places the knees and ankles at their actual hinges, binds the complete knee shields to the thighs, and separates the front head from the torso. Attack poses use continuous curves with matching endpoints. Claws carry forward without inheriting leftover wrist rotations. Kneeling seats the armor and re-solves the front boot; recoil rotates the attached stinger and fires along its barrel. All six clips are regenerated locally; no new generation credits were used.

Validation now asserts loop closure, connected-joint continuity, absence of non-root translations, and bounded frame-to-frame angular changes, planted front-boot and rear-knee contact, in addition to the existing geometry and UV checks. The old validator reported endpoint errors but did not reject them. Baseline reports and screenshots are retained under `output/scorpio-05/before/`.

## Reproduce

```sh
blender -b --python scripts/inspect_scorpio.py
blender -b --python scripts/build_scorpio.py
blender -b --python scripts/validate_scorpio.py
node scripts/validate_glb.mjs public/models/scorpio-05.glb output/scorpio-05/gltf-validation.json
npm run build -- --base=/atlas-09/
```

Rebuilding runs entirely locally using the preserved retopology and consumes 0 credits.

## Remaining limitations

This is a realtime mechanical character prototype. The generated chitin armor has baked surface detail and separated rigid sections leaving 2,651 boundary edges; it is not a watertight manufacturing mesh. Each pincer is one rigid unit; the jaws do not open independently. There is no gameplay physics collision capsule or ragdoll rig. The backflip is deliberately stylized for an agile heavy mecha. Firing particle effects are rendered in Three.js rather than baked as point particles inside the GLB container.
