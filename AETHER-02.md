# AETHER / 02

A second frame in the FORGE character lab: a stylized, athletic humanoid mecha with streamlined white steel, opaque smoked-glass chest and visor panels, graphite actuators, and restrained ice-blue indicators. Its physical design height is 14 metres.

## Deliverables

- Editable Blender source: [blender/AETHER-02.blend](blender/AETHER-02.blend)
- Portable animated model: [public/models/aether-02.glb](public/models/aether-02.glb)
- Concept: [assets/aether-02/concepts/aether-02.png](assets/aether-02/concepts/aether-02.png)
- Exact concept prompt: [prompt.txt](assets/aether-02/concepts/prompt.txt)
- Blender render: [aether-02-beauty.png](output/aether-02/aether-02-beauty.png)
- Reproducible build: [scripts/build_aether.py](scripts/build_aether.py)
- Rig and motion validation: [scripts/validate_aether.py](scripts/validate_aether.py)

The browser's character selector preserves access to ATLAS. `/?character=aether-02&motion=Run` opens AETHER running. The model includes Sentinel (idle), Awaken, Run, KneelFire and Backflip. A compact wrist emitter supports the firing animation; pulse rounds and muzzle flash are synchronized in Three.js.

## Provenance and cost

Created 2026-09-06 using the user's saved character-creation prompt, which authorizes up to US$1 for provider operations including premium processing. The request was to add this character to the existing project, so it shares the existing private repository.

The original reference was generated using OpenAI's built-in image-generation tool. The image, downloaded Tripo source and retopology remain preserved under `assets/aether-02/`. Credential probe: `TRIPO_API_KEY=SET`; no credential is included in source or browser code.

| Operation | Task ID | Estimated credits | Consumed credits |
| --- | --- | --- | --- |
| Textured image-to-3D | `72fc944e-e523-4f53-868b-e6f38d051c8a` | 30 | 30 |
| Smart retopology v2.0 | `71b9da3c-c71e-4861-b892-5ab03bf38e6d` | 30 | 30 |

**Total: 60 credits / US$0.60.** Current prices were checked against [Tripo's pricing page](https://developers.tripo3d.ai/en/pricing). Smart retopology was chosen within the saved prompt's explicit premium-processing authorization; basic decimation would have cost 10 credits instead of 30. Rigging, materials, animation, cleanup, rendering and export were performed locally without further provider charges.

Generation used `v3.1-20260211`, standard geometry and texture quality, PBR, original-image texture alignment, 150,000 face target, and model/texture seeds `9062026`. Retopology used `v2.0`, 18,000 target triangles and texture baking; its adaptive output contained 21,022 triangles. The final character has 24,310 triangles after adding compact joint housings and the wrist emitter.

## Rig, materials and validation

The 18-bone rig has paired shoulder/arm/hand and thigh/shin/foot chains, plus root, pelvis, chest and head. Every vertex has exactly one weight of 1, and every triangle belongs to a single bone. Rigid plates therefore retain their shapes. Limb boundaries and joint positions were established from front and side inspection renders. The independent isolation test caught a hand-boundary error during development; the boundary was corrected before delivery.

The new model uses five materials, packed textures, and two UV channels. The opaque-glass material has alpha 1, transmission 0 and roughness 0.32. It reflects studio lighting without showing through to the interior. Normal maps and source texture detail are preserved. Four shared texture maps supply base color, ORM, normals and derived emission.

Validation evidence:

- [Asset inventory](output/aether-02/asset-report.json): geometry, material names, texture dimensions, rig and clip inventory.
- [Blender checks](output/aether-02/blender-validation.json): 3,310 leg vertices and 1,330 arm vertices tested independently, with zero displacement of the unrelated limb region. All five clips are sampled for finite positions, rigid edge lengths, ground penetration and loop closure.
- [glTF validator](output/aether-02/gltf-validation.json): zero errors and zero warnings. Informational messages concern unused UV/tangent attributes and the intentional muzzle socket.
- [Browser checks](output/aether-02/browser-validation.json): both run phases, kneeling fire, backflip, repeated character switches and a 390×844 phone viewport. No page errors or horizontal overflow. Repeated swaps retain one skeleton helper and one effect group; reported geometry/texture counts remain stable across the same character.
- Screenshots in `output/aether-02/`: desktop idle/action poses and mobile run/backflip.

The production build passes. The existing Three.js bundle-size advisory remains. Browser checks are desktop and emulated-phone observations, not certification on physical mobile hardware.

## Limitations

This is a realtime presentation/prototype asset. Generated topology and baked surface detail remain softer than hand-modeled production armor. Rigid joints have open cut boundaries (1,378 boundary edges) with compact housings covering their interiors; arbitrary extreme poses can still reveal gaps or intersections. Motion uses authored analytic two-bone IK during baking and portable FK keyframes at runtime. No interactive IK controls, individual finger animation, collision rig, LOD chain or physics controller are included.

## Rebuild locally

```sh
blender -b --python scripts/build_aether.py
blender -b --python scripts/validate_aether.py
node scripts/validate_glb.mjs public/models/aether-02.glb output/aether-02/gltf-validation.json
npm run build
```

The existing downloaded retopology is the build input. Rebuilding does not call Tripo or require an API key. The shared motion library accepts a body-proportion profile; its original defaults remain the ATLAS values.

## Head alignment and chest lighting correction

The generated mesh originally faced about 35 degrees to its left in the rest pose. `build_aether.py` now rotates only the head armor around the neck joint by -35 degrees before export. This changes the Blender source and downloadable GLB, so the correction applies to rest and all five clips. Rigid weights, UVs and animation tracks remain valid.

The viewer now uses a per-character reactor-light intensity. AETHER uses zero extra point-light intensity, removing the cyan hotspot cast onto its torso by ATLAS’s fixed reactor light. Its textured emission details and studio lighting remain active. ATLAS retains its original reactor illumination. A model revision query refreshes previously cached AETHER downloads.

Verification: Blender rig/UV/isolation and all five motion checks pass; GLB validation reports zero errors and warnings; production build passes. Browser checks confirm a forward-facing head in rest, idle and run, zero extra reactor-light intensity on AETHER, and 2.52 intensity on ATLAS at the default 84% slider value after switching. No browser errors. Visual evidence: `output/playwright/aether-front-before.png`, `aether-front-after.png`, `aether-fixed-IDLE.png` and `aether-fixed-RUN.png`.
