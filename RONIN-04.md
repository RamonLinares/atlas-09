# RONIN / 04

**Free for commercial and noncommercial use under [CC0 1.0](ASSET-LICENSE.md). No attribution or permission required.**

An original 16-metre samurai mecha with crimson lacquer armor, an aged-gold crescent helmet, layered skirt plates, a right-hand katana, and a left pulse bracer. RONIN joins ATLAS, AETHER and SERAPH in the same viewer.

## Deliverables

- [Packed Blender project](blender/RONIN-04.blend)
- [Animated GLB](public/models/ronin-04.glb)
- [Original concept](assets/ronin-04/concepts/ronin-04.png)
- [Extracted textures](public/textures/ronin-04/)
- [Blender preview](output/ronin-04/ronin-04-beauty.png)
- [Build script](scripts/build_ronin.py), [authored motions](scripts/ronin_motions.py), and [anatomical validation](scripts/validate_ronin.py)
- [Live RONIN viewer](https://ramonlinares.github.io/atlas-09/?character=ronin-04&motion=SwordSlash&v=24)

The GLB contains twelve ordinary baked skeletal clips. The original seven are: Sentinel (6 s), BladeSalute / activation (6 s), SwordSlash (2.33 s), Run (1.33 s), KneelFire (8 s), Backflip (3.6 s), and PunchCombo (12 s). Muzzle flash and projectiles are viewer effects synchronized with the baked left-arm recoil at 0.48-second intervals. PunchCombo places the katana on two magnetic back mounts, releases it for a jab–cross–hook sequence and recovery, retrieves it, and returns to the initial stance. The katana remains held in every other clip. Added clips are SwordCombo (three source strikes), SwordBlock, HitChest, HitHead, and Knockback. Knockback plays once and holds the fallen pose.

## Provenance and cost

The user's reusable [creation prompt](assets/ronin-04/creation-prompt.txt) authorized autonomous execution and up to US$1 for generation and retopology.

1. OpenAI built-in image generation produced the original reference. Its exact visual prompt is saved in [prompt.txt](assets/ronin-04/concepts/prompt.txt).
2. Tripo image-to-model task `2f5656fc-e857-46ac-85f7-64cf547038cc`: model `v3.1-20260211`, standard geometry and texture, PBR, UVs, 150,000 requested faces, model/texture seeds `9062028`, original-image texture alignment. **30 credits consumed**.
3. Tripo smart retopology task `d544a72e-1082-4fbd-8f88-7183fe80350b`: `v2.0`, requested 20,000 faces with texture preservation. **30 credits consumed**. The delivered source contains 24,466 triangles; the request is a target, not an exact result.
4. Local Blender preparation, rigid rigging, and authored animation incurred no additional provider charges.

**Total Tripo consumption: 60 credits, US$0.60** at the [pricing checked on 6 September 2026](https://developers.tripo3d.ai/en/pricing). The concept uses the built-in image tool; no separate Tripo credits apply to it. Original provider meshes, previews and task receipts are preserved under `assets/ronin-04/source` and `assets/ronin-04/retopo`.

## Preparation and checks

The final mesh has **31,533 triangles**, **17,252 Blender vertices**, **21 bones**, four materials and two UV layers. Base color is 2048²; normal and packed occlusion/roughness/metallic textures are 1024². All image textures are packed into the Blender project and embedded in the GLB.

The source was inspected from the front, side and back before binding. The rig includes separate shoulder, arm, leg, skirt, head and sword controls. Geometry is split at mechanical boundaries and given full rigid weights. Both shoulder protectors are rigidly weighted to their corresponding upper-arm bones, so they move with the arms. The shoulder boundary follows the plate's diagonal edge; the sword pommel behind the wrist follows the grip. A sloping blade boundary avoids attaching boot geometry to the weapon. Compact actuator housings cover joints. The skirt follows each thigh around the hip during running and kneeling.

- Blender validation checks both UV maps for bounds and nonzero face area, one full-weight binding per vertex and per face, independently sampled anatomical domains, finite animation positions, rigid edge lengths, ground contact and loop closure.
- Quarter-frame contact sampling adds small root corrections where interpolated geometry would touch the floor. The run uses boot geometry for support and toe-off; the kneel seats the rear shin armor.
- Per-motion swept bounds provide stable desktop/mobile camera framing for the long sword and the backflip.
- Khronos glTF validator: **0 errors, 0 warnings**. Informational messages concern unused UV/tangent data and an empty control node.
- Actual browser checks exercise all seven clips at 1440×1000 and 390×844, character switching, playback, downloads and page overflow. Animated-vertex checks sample ground and camera bounds; muzzle checks verify direction and flash timing.

Reports live in [output/ronin-04](output/ronin-04/); browser screenshots are in `output/playwright/ronin-*`.

## Sword slash and grip repair

SwordSlash now uses the Quaternius Sword_Regular_B strike and recovery: a full-body wind-up, fast diagonal cut, hip and shoulder rotation, weight transfer through both legs, and a controlled return to guard. The attack keeps its source timing; the recovery is shortened to 85% of its original duration. The wrist and sword retain their rest relationship throughout the cut rather than aiming the blade by opening the wrist. The katana blade is rotated 180° around its length so its single sharpened edge leads the forward cut. The blade base is also aligned with the measured handle centerline through the guard, removing the angular kink between grip and blade. Its separate blade component retains the original UVs and curvature. The generated glove and hilt originally shared fused surfaces. Clean armored palms, thumbs and mechanical fingers now form both fists; the wrapped handle, gold guard and pommel are independent weapon geometry so the whole katana can leave the hand. The original textured blade is preserved.

Validation additionally checks the locked wrist, attached elbow/wrist/sword joints, frame-to-frame rotational continuity, and lateral sword-tip travel. These changes rebuild locally with no additional generation charges. The armor, rig pivots, and shoulder shapes are preserved.

## Punch combo and magnetic docking

The 12-second PunchCombo uses a clear placement, a short magnetic docking pause, the same Quaternius jab, cross, hook, and recovery used by ATLAS and AETHER, retargeted to Ronin with full-body movement, and an over-shoulder retrieval. The combat section preserves AETHER’s original 3.9-second timing; the full stow/combat/retrieval clip remains 12 seconds. The shared CC0 motion sources and licenses are preserved in `assets/animations/quaternius`. Two illuminated back mounts have fitted support brackets embedded in the chest armor. Both mounts stay above the waist and move with the chest. The hand lifts in front of the body and passes over the right shoulder along an elbow-guided path; forearm pronation carries the grip while wrist bending remains below 30 degrees. Retrieval reverses that reach. The mounts keep the blade behind the torso while both arms strike. Sword motion is baked into skeletal tracks, including subframe compensation during docking. Validation checks arm joints, held-weapon contact, dock drift, foot contact, fist travel, and rotational continuity.

The additional combat set is reproduced with `scripts/add_combat_motions.py --character RONIN-04` after the base build. The animation-only GLB merge upgrades SwordSlash and preserves the other existing clips, including the corrected magnetic mounts and placement/retrieval. See `output/motion/ronin-04-combat-bake.json` for durations and sources.

## Reproduce

```sh
blender -b --python scripts/inspect_ronin.py
blender -b --python scripts/build_ronin.py
blender -b --python scripts/validate_ronin.py
blender -b --python scripts/add_combat_motions.py -- --character RONIN-04
blender -b --python scripts/validate_combat_motions.py -- --character RONIN-04
blender -b --python scripts/validate_ronin_slash.py
blender -b --python scripts/validate_ronin_sword_clearance.py -- --clip SwordSlash
node scripts/validate_glb.mjs public/models/ronin-04.glb output/ronin-04/gltf-validation.json
npm run build -- --base=/atlas-09/
```

The build uses the preserved retopology locally. No API key or paid call is required to rebuild the delivered asset or viewer. Open the Blender Action Editor to choose another motion; the project opens in the sword slash guard pose.

## Remaining limitations

This is a realtime mechanical character prototype. The generated armor has irregular topology and baked surface detail; separated rigid sections leave 2,773 boundary edges, so this is not a watertight manufacturing mesh. Joint housings and simplified two-panel skirt articulation support these authored clips, but extreme custom poses can reveal seams or armor overlap. The hands use rigid mechanical finger shapes. Magnetic stow and retrieval are baked into PunchCombo; there is no scabbard or magnetic physics simulation. There is no physics, gameplay collision rig, facial rig, or LOD chain. The backflip is deliberately stylized for a giant mecha. Browser firing effects are not embedded as particles in the GLB.

The final SwordCombo strike is reauthored as an outward diagonal on Ronin’s right side, followed by a raised recovery. The blade stays outside the left leg’s silhouette throughout the final sweep. `scripts/validate_ronin_sword_clearance.py` checks the actual blade and both legs, including skirt plates, at 240 samples per second.
