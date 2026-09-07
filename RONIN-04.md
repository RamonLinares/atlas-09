# RONIN / 04

An original 16-metre samurai mecha with crimson lacquer armor, an aged-gold crescent helmet, layered skirt plates, a right-hand katana, and a left pulse bracer. RONIN joins ATLAS, AETHER and SERAPH in the same viewer.

## Deliverables

- [Packed Blender project](blender/RONIN-04.blend)
- [Animated GLB](public/models/ronin-04.glb)
- [Original concept](assets/ronin-04/concepts/ronin-04.png)
- [Extracted textures](public/textures/ronin-04/)
- [Blender preview](output/ronin-04/ronin-04-beauty.png)
- [Build script](scripts/build_ronin.py), [authored motions](scripts/ronin_motions.py), and [anatomical validation](scripts/validate_ronin.py)
- [Live RONIN viewer](https://ramonlinares.github.io/atlas-09/?character=ronin-04&motion=BladeSalute&v=8)

The GLB contains six ordinary baked skeletal clips: Sentinel (6 s), BladeSalute / activation (6 s), SwordSlash (4 s), Run (1.33 s), KneelFire (8 s), and Backflip (3.6 s). Muzzle flash and projectiles are viewer effects synchronized with the baked left-arm recoil at 0.48-second intervals. The katana remains held throughout all six clips.

## Provenance and cost

The user's reusable [creation prompt](assets/ronin-04/creation-prompt.txt) authorized autonomous execution and up to US$1 for generation and retopology.

1. OpenAI built-in image generation produced the original reference. Its exact visual prompt is saved in [prompt.txt](assets/ronin-04/concepts/prompt.txt).
2. Tripo image-to-model task `2f5656fc-e857-46ac-85f7-64cf547038cc`: model `v3.1-20260211`, standard geometry and texture, PBR, UVs, 150,000 requested faces, model/texture seeds `9062028`, original-image texture alignment. **30 credits consumed**.
3. Tripo smart retopology task `d544a72e-1082-4fbd-8f88-7183fe80350b`: `v2.0`, requested 20,000 faces with texture preservation. **30 credits consumed**. The delivered source contains 24,466 triangles; the request is a target, not an exact result.
4. Local Blender preparation, rigid rigging, and authored animation incurred no additional provider charges.

**Total Tripo consumption: 60 credits, US$0.60** at the [pricing checked on 6 September 2026](https://developers.tripo3d.ai/en/pricing). The concept uses the built-in image tool; no separate Tripo credits apply to it. Original provider meshes, previews and task receipts are preserved under `assets/ronin-04/source` and `assets/ronin-04/retopo`.

## Preparation and checks

The final mesh has **28,185 triangles**, **15,481 Blender vertices**, **21 bones**, four materials and two UV layers. Base color is 2048²; normal and packed occlusion/roughness/metallic textures are 1024². All image textures are packed into the Blender project and embedded in the GLB.

The source was inspected from the front, side and back before binding. The rig includes separate shoulder, arm, leg, skirt, head and sword controls. Geometry is split at mechanical boundaries and given full rigid weights. The shoulder boundary follows the plate's diagonal edge; the sword pommel behind the wrist follows the grip. A sloping blade boundary avoids attaching boot geometry to the weapon. Compact actuator housings cover joints. The skirt follows each thigh around the hip during running and kneeling.

- Blender validation checks both UV maps for bounds and nonzero face area, one full-weight binding per vertex and per face, independently sampled anatomical domains, finite animation positions, rigid edge lengths, ground contact and loop closure.
- Quarter-frame contact sampling adds small root corrections where interpolated geometry would touch the floor. The run uses boot geometry for support and toe-off; the kneel seats the rear shin armor.
- Per-motion swept bounds provide stable desktop/mobile camera framing for the long sword and the backflip.
- Khronos glTF validator: **0 errors, 0 warnings**. Informational messages concern unused UV/tangent data and an empty control node.
- Actual browser checks exercise all six clips at 1440×1000 and 390×844, character switching, playback, downloads and page overflow. Animated-vertex checks sample ground and camera bounds; muzzle checks verify direction and flash timing.

Reports live in [output/ronin-04](output/ronin-04/); browser screenshots are in `output/playwright/ronin-*`.

## Sword slash and grip repair

SwordSlash now raises a guard, makes a fast diagonal cut with a coordinated torso turn, continues into follow-through, then recovers. The wrist and sword retain their rest relationship throughout the cut rather than aiming the blade by opening the wrist. The source glove and hilt geometry remain intact; three fitted mechanical finger arcs close the grip and are rigidly attached to the right hand.

Validation additionally checks the locked wrist, attached elbow/wrist/sword joints, frame-to-frame rotational continuity, and lateral sword-tip travel. These changes rebuild locally with no additional generation charges. The armor, rig pivots, and shoulder shapes are preserved.

## Reproduce

```sh
blender -b --python scripts/inspect_ronin.py
blender -b --python scripts/build_ronin.py
blender -b --python scripts/validate_ronin.py
node scripts/validate_glb.mjs public/models/ronin-04.glb output/ronin-04/gltf-validation.json
npm run build -- --base=/atlas-09/
```

The build uses the preserved retopology locally. No API key or paid call is required to rebuild the delivered asset or viewer. Open the Blender Action Editor to choose another motion; the project opens in the sword slash guard pose.

## Remaining limitations

This is a realtime mechanical character prototype. The generated armor has irregular topology and baked surface detail; separated rigid sections leave 2,721 boundary edges, so this is not a watertight manufacturing mesh. Joint housings and simplified two-panel skirt articulation support these authored clips, but extreme custom poses can reveal seams or armor overlap. Fingers are fixed around the grip; the sword has no separate draw/sheath animation. There is no physics, gameplay collision rig, facial rig, or LOD chain. The backflip is deliberately stylized for a giant mecha. Browser firing effects are not embedded as particles in the GLB.
