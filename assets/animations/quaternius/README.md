# Quaternius motion sources

The free Standard downloads were obtained from the official pages on 2026-09-06:

- [Universal Animation Library 1](https://quaternius.itch.io/universal-animation-library): Walk_Loop, Punch_Jab, Punch_Cross, Death01.
- [Universal Animation Library 2](https://quaternius.itch.io/universal-animation-library-2): Melee_Hook, Melee_Hook_Rec.

Creators: Quaternius and Gonzalo Furnier. License: CC0-1.0; original license texts accompany the subsets. All source motions used here are in the free Standard packs. No paid Source/Pro content was used. `provenance.json` records original and subset hashes.

`UAL1_selected.glb` and `UAL2_selected.glb` preserve the source skeleton and selected animation channels. Mannequin meshes, textures and unrelated actions are omitted. These are source motion data; the viewer downloads the retargeted mecha GLBs instead.

## Rebuild

Run `scripts/update_library_motions.py` with Blender to replace animation data in the existing saved assets while preserving their geometry and UVs. Both full character builders also call `retarget_library.retarget_motions`.

To recreate the source subsets, download the Standard packs from the pages above, place their Unreal-Godot `UAL1_Standard.glb` and `UAL2_Standard.glb` files here, and run `python3 scripts/prepare_animation_sources.py`. Full downloads are ignored by Git.

The retargeter uses a human T-pose reference to calibrate the mecha A-pose, source body rotations and proportions scaled by leg length. It solves planted feet against actual boot geometry, adds elbow clearance and corrects ground contact. Jab → cross → hook → recovery are joined with short guard-pose blends. Collapse retains the source backward fall, adds a final hold and plays once in the viewer. ATLAS uses a 1.2 duration multiplier.

The existing hands are rigid and have no independently animated fingers, so the transferred punch motion uses their existing mechanical grip. As with the original animation set, extreme torso and shoulder rotations can expose the prototype's open armor joints; this is not a hand-authored deformation rig or ragdoll.
