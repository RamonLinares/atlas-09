"""Replace a humanoid's procedural Run with the Quaternius CC0 Jog_Fwd_Loop, retargeted.

Usage: blender -b --python scripts/update_library_run.py -- <ATLAS-09|AETHER-02> [--with-sprint]

Only animation data changes: the mesh, UVs, materials, rig and every other
clip are preserved. `--with-sprint` also bakes Sprint_Loop as `Sprint` for
side-by-side review (it is not exported unless kept deliberately).
"""
import bpy, sys, json, runpy, numpy as np
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'scripts'))
from retarget_library import retarget_motions, MotionSource
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
WITH_SPRINT = '--with-sprint' in argv
ASSET = next((a for a in argv if a in ('ATLAS-09', 'AETHER-02')), 'ATLAS-09'); KEY = ASSET.lower(); PREFIX = ASSET.replace('-', '_')
# Vertical travel scales with leg length (about 8.7x a human for ATLAS, 6.8x
# for AETHER), so the human jog's pelvis bounce and foot lift are damped per
# frame: the 18 m heavy machine more than the 14 m athletic one.
DAMPING = {'ATLAS-09': (.40, .55), 'AETHER-02': (.55, .70)}[ASSET]
OUT = ROOT / 'output/motion'; OUT.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'blender' / f'{ASSET}.blend'))
rig = bpy.data.objects[f'{PREFIX}_RIG']; obj = bpy.data.objects[f'{PREFIX}_Armor']; scene = bpy.context.scene
rig.animation_data.action = None
previous = {a.name: list(a.frame_range) for a in bpy.data.actions}
replace = ['Run', 'Sprint']
for track in list(rig.animation_data.nla_tracks):
    if track.name in replace: rig.animation_data.nla_tracks.remove(track)
for a in list(bpy.data.actions):
    if a.name in replace: bpy.data.actions.remove(a)

src = MotionSource(ROOT / 'assets/animations/quaternius/UAL1_selected.glb')
from mathutils import Matrix, Vector
# Timing, lean and limb swing are kept; only the vertical excursions are
# damped toward the rest heights.
PELVIS_BOUNCE, FOOT_LIFT = DAMPING
def closed_loop(clip, tail=.15):
    """The source jog and sprint loops end a few centimetres from their first
    pose. Ease the final part of the cycle onto the first pose so the baked
    clip repeats without a seam, and damp vertical excursions."""
    duration = src.duration(clip); rest = src.rest
    def damp(pose):
        out = dict(pose)
        for name, k in [('pelvis', PELVIS_BOUNCE), ('foot_l', FOOT_LIFT), ('foot_r', FOOT_LIFT), ('ball_l', FOOT_LIFT), ('ball_r', FOOT_LIFT)]:
            m = pose[name].copy(); r = rest[name].translation.z
            m.translation = Vector((m.translation.x, m.translation.y, r + (m.translation.z - r) * k)); out[name] = m
        return out
    first = damp(src.sample(clip, 0))
    def sampler(t):
        pose = damp(src.sample(clip, min(t, duration))); w = max(0.0, (t / duration - (1 - tail)) / tail); w = w * w * (3 - 2 * w)
        if w <= 0: return pose
        return {name: Matrix.LocRotScale(pose[name].translation.lerp(first[name].translation, w), pose[name].to_quaternion().slerp(first[name].to_quaternion(), w), Vector((1, 1, 1))) for name in pose}
    return duration, sampler
specs = [('Run', *closed_loop('Jog_Fwd_Loop'))]
if WITH_SPRINT: specs.append(('Sprint', *closed_loop('Sprint_Loop')))
report = retarget_motions(rig, obj, motion_specs=specs)
for item in report: item['source_clips'] = ['Jog_Fwd_Loop'] if item['name'] == 'Run' else ['Sprint_Loop']

# Gait checks on the evaluated armor: loop closure, floor contact, support and
# counter-rotation. These replace the procedural-run contact model checks.
feet = {s: [v.index for v in obj.data.vertices if any(g.group == obj.vertex_groups['foot.' + s].index for g in v.groups)] for s in 'LR'}
def sample(frame):
    scene.frame_set(int(frame), subframe=float(frame % 1)); bpy.context.view_layer.update()
    ev = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    v = np.empty(len(m.vertices) * 3, dtype=np.float32); m.vertices.foreach_get('co', v); ev.to_mesh_clear(); return v.reshape((-1, 3))
checks = {}
for item in report:
    rig.animation_data.action = bpy.data.actions[item['name']]; start, end = rig.animation_data.action.frame_range
    first = sample(start); last = sample(end); low = 1e9; support = []; yaw = []; flight = 0
    for f in np.arange(start, end + .01, .5):
        v = sample(f); assert np.isfinite(v).all(); low = min(low, float(v[:, 2].min()))
        per_foot = [float(v[feet[s], 2].min()) for s in 'LR']; support.append(min(per_foot)); flight = max(flight, min(per_foot))
        yaw.append({n: (rig.pose.bones[n].matrix.to_3x3() @ rig.data.bones[n].matrix_local.to_3x3().inverted()).to_euler().z for n in ['pelvis', 'chest']})
    closure = float(np.linalg.norm(first - last, axis=1).max())
    contact_fraction = float(np.mean([s < .05 for s in support]))
    counter = float(max(abs(y['pelvis'] - y['chest']) for y in yaw))
    checks[item['name']] = {'lowest_vertex_m': low, 'loop_error_m': closure, 'frames_with_a_planted_boot_5cm': contact_fraction,
                            'frames_with_a_boot_under_15cm': float(np.mean([s < .15 for s in support])),
                            'max_flight_clearance_m': flight, 'max_pelvis_chest_counter_rotation_rad': counter, 'duration_s': item['duration'],
                            'support_height_per_half_frame_m': [round(x, 3) for x in support]}
    assert low > -.001, (item['name'], 'penetration', low)
    assert closure < .0001, (item['name'], 'closure', closure)
rig.animation_data.action = None
(OUT / f'{KEY}-run-library-bake.json').write_text(json.dumps({'retarget': report, 'checks': checks, 'previous_actions': previous}, indent=2) + '\n')

rig['Motion notes'] = f'Run is the Quaternius / Gonzalo Furnier CC0 Jog_Fwd_Loop retargeted to the rigid armor (in place, {"1.2x heavy" if ASSET == "ATLAS-09" else "original"} timing). KneelFire drops onto the right knee, holds a firing pose, then stands. Backflip uses authored root motion around the pelvis. All controls are baked into ordinary bone keyframes.'
bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); rig.select_set(True)
for o in bpy.context.scene.objects:
    if o.name == 'Muzzle_R': o.select_set(True)
bpy.context.view_layer.objects.active = rig; obj.parent = None
bpy.ops.export_scene.gltf(filepath=str(ROOT / 'public/models' / f'{KEY}.glb'), export_format='GLB', use_selection=True, export_animations=True, export_animation_mode='ACTIONS',
                          export_anim_slide_to_zero=True, export_nla_strips=True, export_skins=True, export_yup=True, export_texcoords=True, export_normals=True, export_tangents=True, export_image_format='AUTO')
runpy.run_path(str(ROOT / 'scripts/fix_export_tangents.py'), init_globals={'ASSET_PATH': ROOT / 'public/models' / f'{KEY}.glb', 'REPORT_PATH': OUT / f'{KEY}-run-tangent-repairs.json'}, run_name='__main__')
obj.parent = rig; rig.animation_data.action = bpy.data.actions['Sentinel']; scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'blender' / f'{ASSET}.blend'))
print('RUN_REPORT', ASSET, json.dumps({'retarget': report, 'checks': checks}))
