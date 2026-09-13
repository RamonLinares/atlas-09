"""Replace a mecha's procedural Run with the Quaternius CC0 Jog_Fwd_Loop, retargeted.

Usage: blender -b --python scripts/update_library_run.py -- <CHARACTER> [--with-sprint]

CHARACTER is one of ATLAS-09, AETHER-02, SERAPH-03, RONIN-04, SCORPIO-05,
TITAN-06, VANGUARD-07 (or `all`). Only animation data changes: the mesh, UVs,
materials, rig and every other clip are preserved. Each character keeps its
own carried equipment during the run (SERAPH's cannon and folded wings,
RONIN's katana and skirt, SCORPIO's claws and tail, VANGUARD's rifle and
skirt) through a pose adjuster applied after the humanoid retarget.
`--with-sprint` also bakes Sprint_Loop as `Sprint` for side-by-side review.
"""
import bpy, sys, json, math, runpy, numpy as np
from pathlib import Path
from mathutils import Matrix, Vector, Quaternion
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'scripts'))
from retarget_library import retarget_motions, MotionSource
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
WITH_SPRINT = '--with-sprint' in argv

# Vertical travel scales with leg length (about 8.7x a human for ATLAS), so
# the human jog's pelvis bounce and foot lift are damped per frame: heavier,
# taller machines more than the athletic ones. `timescale` slows the cycle
# for mass; `adjust` names the equipment pass run after every retargeted pose.
CONFIG = {
    'ATLAS-09':    dict(blend='ATLAS-09',    damping=(.40, .55), timescale=1.20),
    'AETHER-02':   dict(blend='AETHER-02',   damping=(.45, .60), timescale=1.00),
    'SERAPH-03':   dict(blend='SERAPH-03',   damping=(.38, .55), timescale=1.20, adjust='seraph'),
    'RONIN-04':    dict(blend='RONIN-04',    damping=(.42, .58), timescale=1.10, adjust='ronin', force_sampling=False, post=['normalize', 'dock']),
    'SCORPIO-05':  dict(blend='SCORPIO-05',  damping=(.40, .55), timescale=1.15, adjust='scorpio'),
    'TITAN-06':    dict(blend='TITAN_06',    damping=(.38, .52), timescale=1.25),
    'VANGUARD-07': dict(blend='VANGUARD_07', damping=(.40, .55), timescale=1.15, adjust='vanguard'),
}
ASSETS = list(CONFIG) if 'all' in argv else [a for a in argv if a in CONFIG] or ['ATLAS-09']
OUT = ROOT / 'output/motion'; OUT.mkdir(parents=True, exist_ok=True)
src = MotionSource(ROOT / 'assets/animations/quaternius/UAL1_selected.glb')


def update(): bpy.context.view_layer.update()


def make_adjuster(kind, rig, context):
    """Equipment poses for the run, expressed with world matrices so they are
    valid in the retargeter's quaternion rotation mode."""
    bones = rig.pose.bones
    def rest_axis(name):
        b = bones[name].bone; return (b.tail_local - b.head_local).normalized()
    def aim(name, direction):
        b = bones[name]; q = rest_axis(name).rotation_difference(Vector(direction).normalized()) @ b.bone.matrix_local.to_quaternion()
        b.matrix = Matrix.Translation(b.head) @ q.to_matrix().to_4x4(); update()
    def local_rotation(name, matrix3):
        b = bones[name]; b.rotation_quaternion = matrix3.to_quaternion(); b.location = (0, 0, 0)
    def follow_thigh(side, clamp_backward):
        thigh = bones['thigh.' + side]; b = bones['skirt.' + side]
        delta = (thigh.matrix.to_3x3() @ thigh.bone.matrix_local.to_3x3().inverted()).to_quaternion()
        if clamp_backward:
            pelvis_frame = bones['pelvis'].matrix.to_3x3() @ bones['pelvis'].bone.matrix_local.to_3x3().inverted()
            local_dir = pelvis_frame.inverted() @ (thigh.tail - thigh.head).normalized()
            backward = max(0.0, (rest_axis('thigh.' + side).y - local_dir.y) / .5)
            delta = Quaternion((1, 0, 0, 0)).slerp(delta, max(0.0, 1.0 - min(1.0, backward)))
        b.matrix = Matrix.Translation(b.head) @ delta.to_matrix().to_4x4() @ b.bone.matrix_local.to_quaternion().to_matrix().to_4x4()
    def held(hand_name, tool_name, direction):
        hand = bones[hand_name]; tool = bones[tool_name].bone
        q = (tool.tail_local - tool.head_local).rotation_difference(Vector(direction).normalized()) @ hand.bone.matrix_local.to_quaternion()
        hand.matrix = Matrix.Translation(hand.head) @ q.to_matrix().to_4x4(); update()

    if kind == 'seraph':
        def wings(fold, fan):
            for sign, side in [(1, 'L'), (-1, 'R')]:
                for part, angle, axis in [('wing_root', sign * fold, Vector((0, 0, 1))), ('wing_outer', sign * fan, Vector((0, 1, 0)))]:
                    b = bones[part + '.' + side]; local = b.bone.matrix_local.to_3x3().inverted() @ axis
                    local_rotation(part + '.' + side, Matrix.Rotation(angle, 3, local))
            update()
        def adjust():
            # The long cannon is carried forward; a human forearm swing would
            # sweep the barrel through the floor and the knees.
            aim('upper_arm.R', Vector((-.28, -.18, -1)))
            aim('forearm.R', Vector((-.14, -1, -.05 + .04 * math.sin(context['u'] * math.tau))))
            wings(math.radians(72), .06)
        return adjust
    if kind == 'ronin':
        def adjust():
            aim('upper_arm.R', Vector((-.35, .12, -1))); aim('forearm.R', Vector((-.22, -1, .05)))
            held('hand.R', 'sword.R', Vector((-.55, .15, 1)))
            for side in 'LR': follow_thigh(side, clamp_backward=False)
            update()
        return adjust
    if kind == 'scorpio':
        from scorpio_anatomy import TAIL_NAMES
        tail_pitch = [.05, .04, .035, .03, .02, 0, -.01, -.02, -.03, -.04, -.05]
        def carry(phase):
            frame = bones['chest'].matrix.to_3x3() @ bones['chest'].bone.matrix_local.to_3x3().inverted()
            for sign, side in [(1, 'L'), (-1, 'R')]:
                sway = .08 * sign * math.sin(phase * math.tau)
                for part, target in [('upper_arm', Vector((sign * .30, -.23 + sway, -1))), ('forearm', Vector((sign * .28, -1, .10 - sway))), ('hand', Vector((sign * .30, -1, -.04)))]:
                    name = part + '.' + side
                    orientation = frame @ (rest_axis(name).rotation_difference(target.normalized()) @ bones[name].bone.matrix_local.to_quaternion()).to_matrix()
                    bones[name].matrix = Matrix.Translation(bones[name].head) @ orientation.to_4x4(); update()
        def tail_pose(amount, sway, phase):
            for i, name in enumerate(TAIL_NAMES):
                r = bones[name].bone.matrix_local.to_3x3()
                yaw = sway * math.sin(phase + i * .35) / (1 + i * .15)
                local_rotation(name, r.inverted() @ Matrix.Rotation(tail_pitch[i] * amount, 3, 'X') @ Matrix.Rotation(yaw, 3, 'Z') @ r)
            update()
        def adjust():
            u = context['u']; carry(u); tail_pose(-.12 + .025 * math.sin(u * math.tau), .004, u * math.tau)
        return adjust
    if kind == 'vanguard':
        def adjust():
            # Rifle carried across the front; the shield arm keeps the jog swing.
            aim('upper_arm.R', Vector((-.32, -.12, -.94))); aim('forearm.R', Vector((-.08, -1, -.12)))
            held('hand.R', 'rifle.R', Vector((-.1, -.85, -.55)))
            for side in 'LR': follow_thigh(side, clamp_backward=True)
            update()
        return adjust
    return None


def run_character(ASSET):
    cfg = CONFIG[ASSET]; KEY = ASSET.lower()
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'blender' / f'{cfg["blend"]}.blend'))
    scene = bpy.context.scene
    rig = next(o for o in scene.objects if o.type == 'ARMATURE'); obj = next(o for o in scene.objects if o.type == 'MESH' and 'Armor' in o.name)
    muzzles = [o for o in scene.objects if o.type == 'EMPTY' and o.name.startswith('Muzzle')]
    rig.animation_data.action = None
    previous = {a.name: list(a.frame_range) for a in bpy.data.actions}
    replace = ['Run', 'Sprint']
    for track in list(rig.animation_data.nla_tracks):
        if track.name in replace: rig.animation_data.nla_tracks.remove(track)
    for a in list(bpy.data.actions):
        if a.name in replace: bpy.data.actions.remove(a)

    # Timing, lean and limb swing are kept; only the vertical excursions are
    # damped toward the rest heights.
    PELVIS_BOUNCE, FOOT_LIFT = cfg['damping']; context = {'u': 0.0}
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
            context['u'] = min(t, duration) / duration
            pose = damp(src.sample(clip, min(t, duration))); w = max(0.0, (t / duration - (1 - tail)) / tail); w = w * w * (3 - 2 * w)
            if w <= 0: return pose
            return {name: Matrix.LocRotScale(pose[name].translation.lerp(first[name].translation, w), pose[name].to_quaternion().slerp(first[name].to_quaternion(), w), Vector((1, 1, 1))) for name in pose}
        return duration, sampler
    specs = [('Run', *closed_loop('Jog_Fwd_Loop'))]
    if WITH_SPRINT: specs.append(('Sprint', *closed_loop('Sprint_Loop')))
    # Detect the rig's keying convention from the clips that stay, not from
    # the bones' current mode (a previous bad export could have left it wrong).
    curves = [c for a in bpy.data.actions for layer in a.layers for strip in layer.strips for bag in strip.channelbags for c in bag.fcurves]
    target_mode = 'QUATERNION' if any(c.data_path.endswith('rotation_quaternion') for c in curves) else 'XYZ'
    report = retarget_motions(rig, obj, motion_specs=specs, timescale_override=cfg['timescale'], pose_adjust=make_adjuster(cfg.get('adjust'), rig, context))
    for item in report: item['source_clips'] = ['Jog_Fwd_Loop'] if item['name'] == 'Run' else ['Sprint_Loop']; item['timescale'] = cfg['timescale']; item['damping'] = cfg['damping']
    # The retargeter leaves every bone in XYZ Euler mode with Euler-keyed
    # clips. The classic frames (TITAN, VANGUARD) key every clip as
    # quaternions and their bones must stay in QUATERNION mode, otherwise the
    # other clips evaluate as static and export frozen. Re-key the new clips
    # to match and restore the rig's original mode.
    bones = rig.pose.bones
    if target_mode == 'QUATERNION':
        for item in report:
            a = bpy.data.actions[item['name']]; rig.animation_data.action = a
            for b in bones: b.rotation_mode = 'XYZ'
            rotations = {b.name: [] for b in bones}
            for frame in range(1, item['frames'] + 1):
                scene.frame_set(frame); update()
                for b in bones:
                    q = b.rotation_euler.to_quaternion()
                    if rotations[b.name] and q.dot(rotations[b.name][-1]) < 0: q.negate()
                    rotations[b.name].append(q)
            for layer in a.layers:
                for strip in layer.strips:
                    for bag in strip.channelbags:
                        for c in [c for c in bag.fcurves if c.data_path.endswith('rotation_euler')]: bag.fcurves.remove(c)
            for b in bones: b.rotation_mode = 'QUATERNION'
            for i, frame in enumerate(range(1, item['frames'] + 1)):
                for b in bones:
                    b.rotation_quaternion = rotations[b.name][i]; b.keyframe_insert('rotation_quaternion', frame=frame, group=b.name)
            for layer in a.layers:
                for strip in layer.strips:
                    for bag in strip.channelbags:
                        for c in bag.fcurves:
                            for k in c.keyframe_points: k.interpolation = 'LINEAR'
            item['rotation_keys'] = 'quaternion'
        rig.animation_data.action = None
    for b in bones: b.rotation_mode = target_mode; b.rotation_euler = (0, 0, 0); b.rotation_quaternion = (1, 0, 0, 0); b.location = (0, 0, 0)
    update()

    # Gait checks on the evaluated armor: loop closure, floor contact, support
    # and counter-rotation. These replace the procedural-run contact model checks.
    feet = {s: [v.index for v in obj.data.vertices if any(g.group == obj.vertex_groups['foot.' + s].index for g in v.groups)] for s in 'LR'}
    def sample(frame):
        scene.frame_set(int(frame), subframe=float(frame % 1)); update()
        ev = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        v = np.empty(len(m.vertices) * 3, dtype=np.float32); m.vertices.foreach_get('co', v); ev.to_mesh_clear(); return v.reshape((-1, 3))
    checks = {}; bounds = {}
    for item in report:
        rig.animation_data.action = bpy.data.actions[item['name']]; start, end = rig.animation_data.action.frame_range
        first = sample(start); last = sample(end); low = 1e9; support = []; yaw = []; flight = 0
        lo = np.full(3, 1e9); hi = np.full(3, -1e9)
        for f in np.arange(start, end + .01, .5):
            v = sample(f); assert np.isfinite(v).all(); low = min(low, float(v[:, 2].min())); lo = np.minimum(lo, v.min(axis=0)); hi = np.maximum(hi, v.max(axis=0))
            per_foot = [float(v[feet[s], 2].min()) for s in 'LR']; support.append(min(per_foot)); flight = max(flight, min(per_foot))
            yaw.append({n: (rig.pose.bones[n].matrix.to_3x3() @ rig.data.bones[n].matrix_local.to_3x3().inverted()).to_euler().z for n in ['pelvis', 'chest']})
        closure = float(np.linalg.norm(first - last, axis=1).max())
        contact_fraction = float(np.mean([s < .05 for s in support]))
        counter = float(max(abs(y['pelvis'] - y['chest']) for y in yaw))
        checks[item['name']] = {'lowest_vertex_m': low, 'loop_error_m': closure, 'frames_with_a_planted_boot_5cm': contact_fraction,
                                'frames_with_a_boot_under_15cm': float(np.mean([s < .15 for s in support])),
                                'max_flight_clearance_m': flight, 'max_pelvis_chest_counter_rotation_rad': counter, 'duration_s': item['duration'],
                                'support_height_per_half_frame_m': [round(x, 3) for x in support]}
        bounds[item['name']] = {'min': [round(float(x), 3) for x in lo], 'max': [round(float(x), 3) for x in hi],
                                'center': [round(float(x), 3) for x in (lo + hi) / 2], 'size': [round(float(x), 3) for x in hi - lo],
                                'interpolation_lift_m': round(float(item.get('max_interpolation_contact_lift_m', 0)), 4)}
        assert low > -.001, (item['name'], 'penetration', low)
        assert closure < .0001, (item['name'], 'closure', closure)
    rig.animation_data.action = None

    # The lab frames each clip from its offline motion envelope; keep the
    # character's bounds file in whichever shape it already uses.
    bounds_path = ROOT / 'src' / f'{KEY.split("-")[0]}-motion-bounds.json'
    if bounds_path.exists():
        existing = json.loads(bounds_path.read_text())
        for name, box in bounds.items():
            keys = existing.get(name, {'min': None, 'max': None}).keys(); existing[name] = {k: box[k] for k in box if k in keys or k in ('min', 'max')}
        bounds_path.write_text(json.dumps(existing, indent=2) + ('\n' if bounds_path.read_text().endswith('\n') else ''))
    asset_report = next((p for p in [ROOT / 'output' / KEY / 'asset-report.json', ROOT / 'output/asset-report.json' if ASSET == 'ATLAS-09' else None] if p and p.exists()), None)
    if asset_report:
        metadata = json.loads(asset_report.read_text()); metadata['animations'] = [{'name': a.name, 'frames': list(a.frame_range)} for a in bpy.data.actions]
        asset_report.write_text(json.dumps(metadata, indent=2) + '\n')
    (OUT / f'{KEY}-run-library-bake.json').write_text(json.dumps({'retarget': report, 'checks': checks, 'bounds': bounds, 'previous_actions': previous}, indent=2) + '\n')

    notes = rig.get('Motion notes', '')
    tail = notes.split('.', 1)[1].strip() if notes.startswith('Run is in-place.') else notes.split('timing).', 1)[1].strip() if notes.startswith('Run is the Quaternius') else notes
    rig['Motion notes'] = f'Run is the Quaternius / Gonzalo Furnier CC0 Jog_Fwd_Loop retargeted to the rigid armor (in place, {cfg["timescale"]:g}x timing). ' + tail
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); rig.select_set(True)
    for o in muzzles: o.select_set(True)
    bpy.context.view_layer.objects.active = rig; obj.parent = None
    glb = ROOT / 'public/models' / f'{KEY}.glb'
    export = dict(filepath=str(glb), export_format='GLB', use_selection=True, export_animations=True, export_animation_mode='ACTIONS',
                  export_anim_slide_to_zero=True, export_nla_strips=True, export_skins=True, export_yup=True, export_texcoords=True, export_normals=True, export_tangents=True, export_image_format='AUTO')
    if 'force_sampling' in cfg: export['export_force_sampling'] = cfg['force_sampling']
    bpy.ops.export_scene.gltf(**export)
    runpy.run_path(str(ROOT / 'scripts/fix_export_tangents.py'), init_globals={'ASSET_PATH': glb, 'REPORT_PATH': OUT / f'{KEY}-run-tangent-repairs.json'}, run_name='__main__')
    for step in cfg.get('post', []):
        if step == 'normalize': runpy.run_path(str(ROOT / 'scripts/normalize_animation_times.py'), init_globals={'ASSET_PATH': glb, 'REPORT_PATH': ROOT / 'output' / KEY / 'animation-time-normalization.json'}, run_name='__main__')
        if step == 'dock': runpy.run_path(str(ROOT / 'scripts/bake_gltf_magnetic_dock.py'), run_name='__main__')
    obj.parent = rig; rig.animation_data.action = bpy.data.actions['Sentinel']; scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'blender' / f'{cfg["blend"]}.blend'))
    print('RUN_REPORT', ASSET, json.dumps({'retarget': report, 'checks': {k: {kk: vv for kk, vv in v.items() if kk != 'support_height_per_half_frame_m'} for k, v in checks.items()}, 'bounds': bounds}), flush=True)


for asset in ASSETS: run_character(asset)
