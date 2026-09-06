# ATLAS / 09 — production-readiness assessment

**Verdict: ready for a realtime presentation or controlled prototype using the supplied motions. Further modeling and rigging are needed for unrestricted character animation or close-up film production.**

Assessed 2026-09-06 in Blender 5.1.2 and the Three.js viewer. This is an assessment of the delivered files, not a claim that AI generation alone produced a finished studio character.

## What is delivered

| Area | Result | Assessment |
| --- | --- | --- |
| Design | Original battered olive mecha, exposed mechanics, cyan reactor | Strong, coherent silhouette. The reconstruction softens some of the concept's fine mechanical detail. |
| Geometry | 26,519 triangles; 14,256 Blender vertices | 82.0% fewer triangles than the 147,462-triangle source. Suitable for one browser hero. GLB duplicates vertices at UV/normal/tangent boundaries. |
| Materials | Four materials (armor, housings, collars, cannon glow); base color 2048², ORM 1024², normal 1024², emission 2048² | Packed and portable. Emission is derived from cyan surface elements. Source base-color and normal JPEG formats are preserved. |
| UVs | Baked surface UV0 plus newly generated packed lightmap UV1 | Both have zero out-of-bounds or zero-area UV faces. Full overlap and texel-density certification has not been performed. |
| Rig | 18 bones, 17 rigid sections, paired limb chains | All vertices have exactly one weight of 1. Every triangle belongs entirely to one bone, so armor does not rubberize. |
| Animation | Five clips: Sentinel, Awaken, Run, KneelFire, Backflip; 54 exported tracks each | Loop closure error stays below 0.000004 metres. Supplied poses have been checked in Blender and Three.js. |
| Export | Self-contained GLB, 6,710,980 bytes | Khronos glTF validator: **0 errors, 0 warnings**. Informational items concern unused UV/tangent attributes and the intentionally empty muzzle socket. |
| Blender source | Packed `.blend`, 4,644,554 bytes | Actual character, rig, animations, UVs, textures, camera and studio lighting. Default timeline plays Sentinel. |
| Browser | Approximately 56–60 FPS observed, 1440×1000 desktop viewport | Final recorded sample: 60 FPS. This is an observation on this Mac, not a benchmark guarantee. |
| Responsive layout | 390×844 phone viewport checked | No horizontal overflow; model and inspection controls remain visible. This is desktop browser emulation, not a physical-device certification. |

The expanded studio reports about 126 draw calls at idle. The character uses one Blender mesh, four glTF primitives, four materials and four image maps; pulse effects add transient draws. Approximately 60 FPS was observed after offline rendering finished.

## Motion expansion

Added locally with no additional provider credits: a 1.4-second run, an 8-second kneel/fire/stand sequence, and a 3.6-second backward somersault. Joint housings cover opened articulations. The front boot is planted while the rear armored knee/shin pad rests on the floor. Muzzle flash, pulse rounds and a landing ring are Three.js effects synchronized to the exported motion.

New evidence: `output/motion/browser-check.json`, `output/motion/bake-report.json`, and the Run/KneelFire/Backflip screenshots in `output/motion/`.

## Validation evidence

- `output/gltf-validation.json`: structural export validation.
- `output/blender-validation.json`: packed textures, rigid weights, paired chains and sampled deformation.
- `output/browser-validation.json`: skinned vertex motion, controls, download response and responsive layout.
- `output/asset-report.json`: geometry, UV and rig inventory.
- `output/playwright/desktop-final.png`, `mobile-final.png`, `awaken.png`, `wireframe.png`, `skeleton.png`: visual checks.
- `output/atlas-09-beauty.png`: Blender render of the same character.

Blender deformation checks sample every third frame of all five clips. Maximum change in rigid edge length stayed below 0.000006 metres. Loop endpoints matched within 0.000004 metres. The run includes a 0.42-metre flight phase. The browser sampled 2,327 skinned vertices: all were finite and the activation pose moved vertices by up to approximately 1.12 metres in model space.

The viewer controls were exercised through the rendered UI: animation switching, pause/play, rest pose, camera reset, wireframe, skeleton, turntable, reactor intensity, concept dialog and GLB download. Browser console checks found zero errors and zero warnings after the final fixes. The Vite production build passes; it retains an advisory about the size of the single Three.js bundle.

## Corrections made during review

1. Normalized the provider's forward axis and set a physical 18-metre height in Blender.
2. Replaced soft skinning with rigid ownership per mechanical section.
3. Moved the shoulder boundary below the visible armor to prevent a cut across the plate during activation.
4. Preserved original texture file formats, reducing unnecessary PNG inflation.
5. Exported explicit tangents and a root-level skinned mesh for interchange compatibility.
6. Repaired one zero-length exported tangent using its triangle's UV differential. This fixed a rendering failure visible with bloom during animation. The repair changes tangent data only.
7. Adjusted the phone camera and moved the inspection controls beneath the model.
8. Corrected the lower-arm assignment boundary: disconnected outer-thigh strips had been assigned to the forearm and hand bones on both sides. The boundary now falls in the real gap between thigh and arm geometry. An anatomical isolation check covers 244 thigh-panel faces / 170 vertices: zero displacement when only arms rotate, and all move when their thigh bones rotate. Running, kneeling fire and backflip poses were reviewed again in the production browser.

## Remaining production work

The automatic retopology is triangulated and lacks a hand-authored subdivision cage. The rigid sections have **1,892 open boundary edges** at their cuts, plus one additional non-manifold edge. The current geometry is neither watertight nor suitable for printing. For large joint rotations, model closed individual armor pieces, joint interiors and cable connections, then rebind and stress-test those parts.

The rig exports FK keys with approximate mechanical pivots. The added run, kneeling-fire and backflip poses were authored using analytic two-bone IK and a ground-contact pass, then baked. It has no interactive IK handles, finger articulation, constraint-based pistons or collision avoidance. The supplied clips do not establish that arbitrary combat or locomotion animation will work.

Fine surface detail is partly texture-baked; hero close-ups reveal softened edges and incomplete mechanical construction. A film asset needs a high-resolution modeling pass, higher-resolution texture work, a deliberate UV/texel-density plan and shot-specific review.

For a shipping game, add collision proxies, distance-based LODs, texture compression and target-device performance tests.

## Cost

Tripo generation: 30 credits. User-approved smart retopology: 30 credits. **Total: 60 credits ($0.60).** All later mesh preparation, UV work, rigging, animation, rendering and export were local. See `ASSET-PROVENANCE.md` for task IDs, settings and the exact concept prompt.
