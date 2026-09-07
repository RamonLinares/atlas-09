"""Shared local preparation for the classic humanoid mechas (TITAN-06, VANGUARD-07).

A character spec supplies measured anatomy, a rigid section function, bones,
joint housings, hardware and authored motions. Everything here runs on the
preserved Tripo retopology and consumes no provider credits.
"""
import bpy, bmesh, math, json, sys, runpy
import numpy as np
from pathlib import Path
from collections import defaultdict
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[1]


def material(name, color, metallic, roughness, emission=None, strength=0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = color; p.inputs['Metallic'].default_value = metallic; p.inputs['Roughness'].default_value = roughness
    if emission:
        p.inputs['Emission Color'].default_value = emission; p.inputs['Emission Strength'].default_value = strength
    return m


class Hardware:
    """Primitive helpers that bind generated parts rigidly to a bone."""
    def __init__(self, uv_name):
        self.uv_name = uv_name; self.pieces = []; self.empties = []
    def bind(self, o, name, mat):
        o.data.materials.append(mat)
        o.vertex_groups.new(name=name).add(list(range(len(o.data.vertices))), 1, 'REPLACE')
        if o.data.uv_layers: o.data.uv_layers.active.name = self.uv_name
        else: o.data.uv_layers.new(name=self.uv_name)
        for f in o.data.polygons: f.use_smooth = True
        self.pieces.append(o); return o
    def sphere(self, center, radius, name, mat, segments=16):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=8, radius=radius, location=center)
        return self.bind(bpy.context.object, name, mat)
    def cylinder(self, center, radius, length, direction, name, mat, vertices=20):
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=length, location=center)
        o = bpy.context.object; o.rotation_euler = Vector(direction).normalized().to_track_quat('Z', 'Y').to_euler()
        return self.bind(o, name, mat)
    def cone(self, center, radius1, radius2, length, direction, name, mat):
        bpy.ops.mesh.primitive_cone_add(vertices=20, radius1=radius1, radius2=radius2, depth=length, location=center)
        o = bpy.context.object; o.rotation_euler = Vector(direction).normalized().to_track_quat('Z', 'Y').to_euler()
        return self.bind(o, name, mat)
    def box(self, center, size, name, mat, direction=None):
        bpy.ops.mesh.primitive_cube_add(size=1, location=center)
        o = bpy.context.object; o.scale = size
        if direction is not None: o.rotation_euler = Vector(direction).normalized().to_track_quat('Z', 'Y').to_euler()
        return self.bind(o, name, mat)
    def muzzle(self, rig, bone, position, direction, name):
        bpy.ops.object.empty_add(type='ARROWS', location=position)
        e = bpy.context.object; e.name = name
        e.rotation_euler = Vector(direction).normalized().to_track_quat('-Z', 'Y').to_euler()
        bpy.context.view_layer.update(); world = e.matrix_world.copy()
        e.parent = rig; e.parent_type = 'BONE'; e.parent_bone = bone; e.matrix_world = world
        self.empties.append(e); return e


def build(spec):
    name = spec['id']; prefix = spec['prefix']; H = spec['height']
    OUT = ROOT / 'output' / name; TEX = ROOT / 'public/textures' / name
    OUT.mkdir(parents=True, exist_ok=True); TEX.mkdir(parents=True, exist_ok=True)
    uv_name = f'{prefix}_Surface'
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    source = next((ROOT / 'assets' / name / 'retopo').glob('*model*.glb'))
    bpy.ops.import_scene.gltf(filepath=str(source))
    obj = next(o for o in bpy.context.scene.objects if o.type == 'MESH'); obj.name = f'{spec["blender_name"]}_Armor'
    for o in list(bpy.context.scene.objects):
        if o is not obj and o.type != 'MESH': bpy.data.objects.remove(o)
    # Blender's glTF import is Z-up; the source faces +Y, our rigs face -Y.
    coords = [Matrix.Rotation(-math.pi / 2, 4, 'Z') @ (obj.matrix_world @ v.co) for v in obj.data.vertices]
    lo = min(p.z for p in coords); scale = H / (max(p.z for p in coords) - lo)
    shift = Vector(spec.get('shift', (0, 0, 0)))
    for v, p in zip(obj.data.vertices, coords): v.co = (p - Vector((0, 0, lo))) * scale + shift
    obj.matrix_world = Matrix.Identity(4)
    bpy.context.view_layer.objects.active = obj; obj.select_set(True)
    mesh = obj.data; intake_triangles = sum(len(f.vertices) - 2 for f in mesh.polygons)
    bm = bmesh.new(); bm.from_mesh(mesh)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=.00006)
    zero = [f for f in bm.faces if f.calc_area() < 1e-7]
    bmesh.ops.delete(bm, geom=zero, context='FACES_ONLY')
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh); bm.free(); mesh.update()

    mesh.uv_layers.active.name = uv_name
    mat = mesh.materials[0]; mat.name = spec['material_name']; mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'); base = None; textures = []
    for n in list(mat.node_tree.nodes):
        if n.type != 'TEX_IMAGE' or not n.image: continue
        im = n.image
        semantic = 'BaseColor' if any(l.to_socket == bsdf.inputs['Base Color'] for l in n.outputs['Color'].links) else ('Normal' if 'normal' in im.name.lower() else 'ORM')
        if semantic == 'BaseColor': base = im
        ext = 'jpg' if im.packed_file and bytes(im.packed_file.data[:2]) == b'\xff\xd8' else 'png'
        im.filepath_raw = str(TEX / f'{prefix}_{semantic}.{ext}'); im.file_format = 'JPEG' if ext == 'jpg' else 'PNG'
        im.save(); im.pack()
        textures.append({'semantic': semantic, 'size': list(im.size), 'file': str(Path(im.filepath_raw).relative_to(ROOT))})
        uv = mat.node_tree.nodes.new('ShaderNodeUVMap'); uv.uv_map = uv_name
        mat.node_tree.links.new(uv.outputs['UV'], n.inputs['Vector'])
    bsdf.inputs['Coat Weight'].default_value = spec.get('coat', .25); bsdf.inputs['Coat Roughness'].default_value = .22

    if base and spec.get('emission_mask'):
        w, h = base.size; px = np.empty(w * h * 4, dtype=np.float32); base.pixels.foreach_get(px); px = px.reshape((-1, 4))
        mask = np.clip(spec['emission_mask'](px), 0, 1)
        out = np.zeros_like(px); out[:, :3] = mask[:, None] * np.array(spec['emission_color']); out[:, 3] = 1
        em = bpy.data.images.new(f'{prefix}_Emission', width=w, height=h); em.pixels.foreach_set(out.ravel())
        em.filepath_raw = str(TEX / f'{prefix}_Emission.png'); em.file_format = 'PNG'; em.save(); em.pack()
        en = mat.node_tree.nodes.new('ShaderNodeTexImage'); en.image = em
        uv = mat.node_tree.nodes.new('ShaderNodeUVMap'); uv.uv_map = uv_name
        mat.node_tree.links.new(uv.outputs['UV'], en.inputs['Vector']); mat.node_tree.links.new(en.outputs['Color'], bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = spec.get('emission_strength', 3.5)
        textures.append({'semantic': 'Emission', 'size': [w, h], 'file': str(Path(em.filepath_raw).relative_to(ROOT)), 'emissive_texels': int((mask > .5).sum())})

    # Rigid sections from measured anatomy. Every vertex is duplicated per
    # section so no face straddles two bones.
    section = spec['section']
    labels = {f.index: section(f.center) for f in mesh.polygons}
    parts = defaultdict(list)
    for fi, label in labels.items():
        if label != 'discard': parts[label].append(fi)
    old = mesh; verts = []; faces = []; uvs = []; weights = defaultdict(list)
    for label, indices in parts.items():
        remap = {}
        for fi in indices:
            f = old.polygons[fi]; face = []
            for li, vi in zip(f.loop_indices, f.vertices):
                if vi not in remap:
                    remap[vi] = len(verts); verts.append(tuple(old.vertices[vi].co)); weights[label].append(remap[vi])
                face.append(remap[vi]); uvs.append(tuple(old.uv_layers[uv_name].data[li].uv))
            faces.append(face)
    mesh = bpy.data.meshes.new(f'{prefix}_RigidArmor'); mesh.from_pydata(verts, [], faces); mesh.update(); obj.data = mesh
    mesh.materials.append(mat)
    uv = mesh.uv_layers.new(name=uv_name)
    for i, co in enumerate(uvs): uv.data[i].uv = co
    for f in mesh.polygons: f.material_index = 0; f.use_smooth = True
    group_of = spec.get('group_of', lambda label: label)
    for label, indices in weights.items():
        driver = group_of(label)
        (obj.vertex_groups.get(driver) or obj.vertex_groups.new(name=driver)).add(indices, 1, 'REPLACE')
    section_report = {label: len(indices) for label, indices in parts.items()}

    bpy.ops.object.armature_add(enter_editmode=True); rig = bpy.context.object
    rig.name = f'{spec["blender_name"]}_RIG'; rig.show_in_front = True
    eb = rig.data.edit_bones; eb.remove(eb[0])
    for bone_name, head, tail, parent, deform in spec['bones']:
        b = eb.new(bone_name); b.head = head; b.tail = tail; b.use_deform = deform
        if parent: b.parent = eb[parent]
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.parent = rig; mod = obj.modifiers.new('Rigid mechanical skin', 'ARMATURE'); mod.object = rig
    for b in rig.pose.bones: b.rotation_mode = 'XYZ'
    missing = [g.name for g in obj.vertex_groups if g.name not in rig.data.bones]
    assert not missing, f'Vertex groups without bones: {missing}'

    hw = Hardware(uv_name)
    hardware_report = spec['hardware'](hw, rig, obj)
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
    for o in hw.pieces: o.select_set(True)
    bpy.context.view_layer.objects.active = obj; bpy.ops.object.join()
    bm = bmesh.new(); bm.from_mesh(obj.data); bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3]); bm.to_mesh(obj.data); bm.free(); obj.data.update()
    mesh = obj.data
    mesh.uv_layers.new(name=f'{prefix}_Lightmap'); mesh.uv_layers.active_index = 1
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=.008, area_weight=.3, scale_to_bounds=True)
    bpy.ops.object.mode_set(mode='OBJECT'); mesh.uv_layers.active_index = 0; mesh.uv_layers[uv_name].active_render = True

    scene = bpy.context.scene; scene.render.fps = 30; rig.animation_data_create()
    motion_report = spec['motions'](rig, obj)
    (OUT / 'bake-report.json').write_text(json.dumps(motion_report, indent=2))

    rig['README'] = spec['readme']
    for pb in rig.pose.bones: pb.rotation_euler = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)
    scene.frame_set(1); scene.frame_start = 1; scene.frame_end = 181
    bm = bmesh.new(); bm.from_mesh(mesh); boundary = sum(e.is_boundary for e in bm.edges); bm.free()
    report = {'source': str(source.relative_to(ROOT)), 'height_m': H, 'source_triangles': intake_triangles, 'vertices': len(mesh.vertices),
              'triangles': sum(len(f.vertices) - 2 for f in mesh.polygons), 'bones': len(rig.data.bones), 'materials': [m.name for m in mesh.materials],
              'boundary_edges': boundary, 'textures': textures, 'sections': section_report, 'hardware': hardware_report,
              'animations': [{'name': a.name, 'frames': list(a.frame_range)} for a in bpy.data.actions]}
    (OUT / 'asset-report.json').write_text(json.dumps(report, indent=2))

    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); rig.select_set(True)
    for e in hw.empties: e.select_set(True)
    bpy.context.view_layer.objects.active = rig; obj.parent = None
    glb = ROOT / 'public/models' / f'{name}.glb'
    bpy.ops.export_scene.gltf(filepath=str(glb), export_format='GLB', use_selection=True, export_animations=True, export_animation_mode='ACTIONS',
                              export_anim_slide_to_zero=True, export_nla_strips=True, export_skins=True, export_yup=True, export_texcoords=True,
                              export_normals=True, export_tangents=True, export_image_format='AUTO')
    runpy.run_path(str(ROOT / 'scripts/fix_export_tangents.py'), init_globals={'ASSET_PATH': glb, 'REPORT_PATH': OUT / 'tangent-repairs.json'}, run_name='__main__')
    obj.parent = rig

    stage = bpy.data.collections.new('STUDIO — excluded from GLB'); scene.collection.children.link(stage)
    def to_stage(o):
        for c in list(o.users_collection): c.objects.unlink(o)
        stage.objects.link(o)
    def aim(o): o.rotation_euler = (Vector((0, 0, H * .5)) - o.location).to_track_quat('-Z', 'Y').to_euler()
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = spec.get('world', (.12, .14, .16, 1)); scene.world.node_tree.nodes['Background'].inputs[1].default_value = .5
    bpy.ops.mesh.primitive_plane_add(size=2000, location=(0, 0, -.045)); floor = bpy.context.object; floor.name = 'Studio floor'; to_stage(floor)
    floor.data.materials.append(material('Studio graphite', (.05, .065, .075, 1), .15, .8))
    for pos, power, color in spec.get('lights', [((8, -14, 24), 3200, (.9, .95, 1)), ((-10, -8, 15), 2200, (1, .95, .85)), ((8, 10, 22), 3600, (.7, .85, 1))]):
        bpy.ops.object.light_add(type='AREA', location=pos); l = bpy.context.object
        l.data.energy = power; l.data.color = color; l.data.shape = 'DISK'; l.data.size = 8; aim(l); to_stage(l)
    bpy.ops.object.camera_add(location=(16, -32, 14)); cam = bpy.context.object; aim(cam)
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = H + 8; cam.data.clip_end = 2000; scene.camera = cam; to_stage(cam)
    scene.render.engine = 'CYCLES'; scene.cycles.samples = 16; scene.cycles.use_denoising = True
    scene.render.resolution_x = 1000; scene.render.resolution_y = 1000; scene.render.resolution_percentage = 100; scene.view_settings.view_transform = 'AgX'
    bpy.ops.object.select_all(action='DESELECT'); rig.select_set(True); bpy.context.view_layer.objects.active = rig
    rig.animation_data.action = bpy.data.actions[spec['beauty_clip'][0]]; scene.frame_set(spec['beauty_clip'][1])
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'blender' / f'{spec["blender_name"]}.blend'))
    scene.render.filepath = str(OUT / f'{name}-beauty.png')
    if '--skip-render' not in sys.argv: bpy.ops.render.render(write_still=True)
    print('ASSET_REPORT', json.dumps({k: v for k, v in report.items() if k not in ('sections', 'hardware')}))
    return report


# ---------------------------------------------------------------- posing kit

class PoseKit:
    """Small authoring toolkit over pose bones: smooth curves, aiming and IK."""
    def __init__(self, rig, obj):
        self.rig = rig; self.obj = obj; self.bones = rig.pose.bones; self.scene = bpy.context.scene
    def update(self): bpy.context.view_layer.update()
    def neutral(self):
        for b in self.bones:
            if b.rotation_mode != 'QUATERNION': b.rotation_mode = 'XYZ'
            b.rotation_euler = (0, 0, 0); b.rotation_quaternion = (1, 0, 0, 0); b.location = (0, 0, 0); b.scale = (1, 1, 1)
        self.update()
    @staticmethod
    def smooth(x):
        x = max(0., min(1., float(x))); return x * x * (3 - 2 * x)
    @staticmethod
    def blend_direction(a, b, t):
        """Spherical blend of two directions; a plain lerp collapses near opposite vectors and flips the aim."""
        a = Vector(a).normalized(); b = Vector(b).normalized(); t = max(0., min(1., float(t)))
        if a.dot(b) < -.9995:
            side = a.cross(Vector((0, 0, 1))) if abs(a.z) < .9 else a.cross(Vector((1, 0, 0)))
            b = (b + side.normalized() * .05).normalized()
        return a.slerp(b, t).normalized()
    @classmethod
    def curve(cls, u, keys):
        if u <= keys[0][0]: return keys[0][1]
        for (ta, a), (tb, b) in zip(keys, keys[1:]):
            if u <= tb:
                t = cls.smooth((u - ta) / (tb - ta)); return a * (1 - t) + b * t
        return keys[-1][1]
    def rest_axis(self, name):
        b = self.bones[name].bone; return (b.tail_local - b.head_local).normalized()
    def aim(self, name, direction, roll=0):
        b = self.bones[name]
        q = self.rest_axis(name).rotation_difference(Vector(direction).normalized()) @ b.bone.matrix_local.to_quaternion()
        m = Matrix.Translation(b.head) @ q.to_matrix().to_4x4()
        if roll: m = m @ Matrix.Rotation(roll, 4, 'Y')
        b.matrix = m; self.update()
    def aim_stable(self, name, direction, up=(0, 0, 1)):
        """Aim with a full basis (direction plus a projected up hint) so the roll
        stays continuous while the direction sweeps past the rest antipode."""
        def basis(d):
            d = Vector(d).normalized(); u = Vector(up) - d * d.dot(Vector(up))
            if u.length < 1e-4: u = Vector((1, 0, 0)) - d * d.x
            u.normalize(); m = Matrix.Identity(3); m.col[1] = d; m.col[2] = u; m.col[0] = d.cross(u); return m
        b = self.bones[name]
        r = basis(direction) @ basis(self.rest_axis(name)).inverted()
        b.matrix = Matrix.Translation(b.head) @ (r @ b.bone.matrix_local.to_3x3()).to_4x4(); self.update()
    def world_rotation(self, name, pitch, roll=0, yaw=0):
        b = self.bones[name]
        r = Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(roll, 4, 'Y') @ Matrix.Rotation(pitch, 4, 'X')
        b.matrix = Matrix.Translation(b.head) @ r @ b.bone.matrix_local.to_quaternion().to_matrix().to_4x4(); self.update()
    def frame_of(self, name):
        b = self.bones[name]; return b.matrix.to_3x3() @ b.bone.matrix_local.to_3x3().inverted()
    def two_bone(self, upper, lower, target, pole, tip=None):
        """Analytic IK: aim `upper` and `lower` so the lower bone's tail reaches target."""
        u = self.bones[upper]; l = self.bones[lower]; h = u.head.copy(); a = Vector(target); v = a - h
        l1 = u.bone.length; l2 = l.bone.length
        dist = min(l1 + l2 - .003, max(abs(l1 - l2) + .003, v.length)); axis = v.normalized()
        p = Vector(pole); p -= axis * p.dot(axis)
        if p.length < .001: p = Vector((0, 0, -1))
        p.normalize(); along = (l1 * l1 - l2 * l2 + dist * dist) / (2 * dist)
        k = h + axis * along + p * math.sqrt(max(0, l1 * l1 - along * along))
        self.aim(upper, k - h); self.aim(lower, a - self.bones[lower].head)
        if tip: self.aim(tip, self.rest_axis(tip))
    def lowest_vertex(self, indices=None):
        ev = self.obj.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        pts = np.empty(len(m.vertices) * 3, dtype=np.float32); m.vertices.foreach_get('co', pts); pts = pts.reshape((-1, 3))
        low = float(pts[:, 2].min()) if indices is None else float(pts[indices, 2].min()); ev.to_mesh_clear(); return low
    def group_indices(self, name):
        g = self.obj.vertex_groups[name].index
        return np.array([v.index for v in self.obj.data.vertices if any(x.group == g for x in v.groups)])
    def lift_root(self, amount):
        r = self.bones['root']; r.matrix = Matrix.Translation((0, 0, amount)) @ r.matrix; self.update()


def bake_clips(kit, clips, report, bounds_path, linear=True):
    """Sample authored poses into keyframes, then ground and bound every clip.

    clips: list of (name, frames, pose_fn(u)). Every bone's rotation and
    location are keyed per frame; root lift corrections cover interpolated
    subframes so nothing dips under the floor between keys.
    """
    rig = kit.rig; obj = kit.obj; scene = kit.scene; bones = kit.bones
    for name, frames, fn in clips:
        rig.animation_data.action = None; previous = {}
        for frame in range(1, frames + 1):
            fn((frame - 1) / (frames - 1)); kit.update()
            for b in bones:
                if b.name in previous: b.rotation_euler = b.rotation_euler.to_quaternion().to_euler('XYZ', previous[b.name])
                previous[b.name] = b.rotation_euler.copy()
                b.keyframe_insert('rotation_euler', frame=frame, group=b.name); b.keyframe_insert('location', frame=frame, group=b.name)
        a = rig.animation_data.action; a.name = name; a.use_fake_user = True; rig.animation_data.action = None
        track = rig.animation_data.nla_tracks.new(); track.name = name; track.strips.new(name, 1, a); track.mute = True
        report.append({'name': name, 'frames': frames, 'duration': (frames - 1) / 30})
    # Euler keys hit gimbal lock on deeply bent legs (the shin twists past
    # 90 degrees when kneeling), which corrupts interpolation between keys in
    # Blender while the exported glTF interpolates quaternions. Re-key every
    # clip as sign-continuous quaternions so both behave identically and the
    # ground pass below measures what the viewer will actually show.
    for item in report:
        a = bpy.data.actions[item['name']]; rig.animation_data.action = a
        # Each clip is still Euler-keyed: the bones must evaluate in XYZ mode
        # while its curves are read, whatever the previous clip switched them to.
        for b in bones: b.rotation_mode = 'XYZ'
        rotations = {b.name: [] for b in bones}
        for frame in range(1, item['frames'] + 1):
            scene.frame_set(frame); kit.update()
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
        item['rotation_keys'] = 'quaternion'
    root_up = bones['root'].bone.matrix_local.to_3x3().inverted() @ Vector((0, 0, 1)); bounds = {}
    for item in report:
        a = bpy.data.actions[item['name']]; rig.animation_data.action = a
        if linear:
            for layer in a.layers:
                for strip in layer.strips:
                    for bag in strip.channelbags:
                        for c in bag.fcurves:
                            for k in c.keyframe_points: k.interpolation = 'LINEAR'
        lifts = [0.0] * item['frames']
        for i in range(item['frames'] - 1):
            for f in [0, .25, .5, .75, 1]:
                scene.frame_set(i + 1, subframe=f); kit.update(); low = kit.lowest_vertex()
                if low < 0: lifts[i] = max(lifts[i], -low + .003); lifts[i + 1] = max(lifts[i + 1], -low + .003)
        lifts[0] = lifts[-1] = max(lifts[0], lifts[-1])
        for layer in a.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for c in bag.fcurves:
                        if c.data_path == 'pose.bones["root"].location':
                            for k in c.keyframe_points: k.co.y += lifts[round(k.co.x) - 1] * root_up[c.array_index]
        low = Vector((1e9, 1e9, 1e9)); high = -low
        for frame in range(1, item['frames'] + 1):
            scene.frame_set(frame); kit.update()
            ev = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
            coords = np.empty(len(m.vertices) * 3, dtype=np.float32); m.vertices.foreach_get('co', coords); coords = coords.reshape((-1, 3))
            lo = coords.min(axis=0); hi = coords.max(axis=0); ev.to_mesh_clear()
            for axis in range(3): low[axis] = min(low[axis], float(lo[axis])); high[axis] = max(high[axis], float(hi[axis]))
        bounds[item['name']] = {'min': [round(float(v), 3) for v in low], 'max': [round(float(v), 3) for v in high],
                                'center': [round(float(v), 3) for v in (low + high) / 2], 'size': [round(float(v), 3) for v in (high - low)],
                                'interpolation_lift_m': round(float(max(lifts)), 4)}
        item['interpolation_lift_m'] = round(float(max(lifts)), 4)
        item['interpolation_lift_frame'] = int(np.argmax(lifts)) + 1
    Path(bounds_path).write_text(json.dumps(bounds, indent=2))
    rig.animation_data.action = None; kit.neutral()
    return bounds
