"""Add independent, rigid feather hinges and a folded-to-open wing deployment."""
import bpy,bmesh,json,math,sys,runpy
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from seraph_feathers import articulate_feathers
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/SERAPH-03.blend'))
scene=bpy.context.scene;rig=bpy.data.objects['SERAPH_03_RIG'];obj=bpy.data.objects['SERAPH_03_Armor'];rig.animation_data.action=None
for b in rig.pose.bones:b.rotation_euler=(0,0,0);b.location=(0,0,0)
bpy.context.view_layer.update();specs=articulate_feathers(obj,rig)
OUT=ROOT/'output/seraph-03';OUT.mkdir(exist_ok=True)
def update():bpy.context.view_layer.update()
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def set_roots(amount):
    for side,sign in [('L',1),('R',-1)]:
        b=rig.pose.bones['wing_root.'+side];axis=b.bone.matrix_local.to_3x3().inverted()@Vector((0,0,1))
        b.rotation_euler=Quaternion(axis,sign*math.radians(78)*(1-amount)).to_euler()
        rig.pose.bones['wing_outer.'+side].rotation_euler=(0,0,0)
    update()
set_roots(0);closed={}
for item in specs:
    b=rig.pose.bones[item['name']];direction=Vector((.1 if item['side']=='L' else -.1,.3,-1))
    q=(b.bone.tail_local-b.bone.head_local).rotation_difference(direction)@b.bone.matrix_local.to_quaternion()
    b.matrix=Matrix.Translation(b.head)@q.to_matrix().to_4x4();update();closed[b.name]=b.rotation_euler.to_quaternion().copy()
for b in rig.pose.bones:b.rotation_euler=(0,0,0);b.location=(0,0,0)
update()
# Small universal pivots and support rods give each separated plate a
# visible mechanical attachment. Existing source surfaces remain unchanged.
if not rig.get('Feather hinge hardware'):
    parts=[];uv_names=[uv.name for uv in obj.data.uv_layers];material=obj.data.materials[1]
    def bind(o,name):
        o.data.materials.append(material);o.vertex_groups.new(name=name).add(list(range(len(o.data.vertices))),1,'REPLACE')
        o.data.uv_layers.active.name=uv_names[0]
        for uvname in uv_names[1:]:
            uv=o.data.uv_layers.new(name=uvname)
            for a,b in zip(o.data.uv_layers[0].data,uv.data):b.uv=a.uv
        a=o.data.attributes.new('original_vertex','INT','POINT')
        for x in a.data:x.value=-1
        for p in o.data.polygons:p.use_smooth=True
        parts.append(o)
    def rod(a,b,name,radius=.11):
        v=b-a
        if v.length<.1:return
        bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=radius,depth=v.length,location=(a+b)/2)
        o=bpy.context.object;o.rotation_euler=v.to_track_quat('Z','Y').to_euler();bind(o,name)
    for item in specs:
        head=Vector(item['head']);hub=Vector(item['hub'])
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=.23,location=head);bind(bpy.context.object,item['parent'])
        rod(hub,head,item['parent'])
        ids=[v.co for v in obj.data.vertices if obj.vertex_groups[v.groups[0].group].name==item['name']]
        near=sorted(ids,key=lambda v:(v-head).length)[:4];base=sum(near,Vector())/len(near)
        rod(head,base,item['name'],.13)
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True)
    for o in parts:o.select_set(True)
    bpy.context.view_layer.objects.active=obj;bpy.ops.object.join();rig['Feather hinge hardware']=True
mesh_edit=bmesh.new();mesh_edit.from_mesh(obj.data)
bmesh.ops.triangulate(mesh_edit,faces=[f for f in mesh_edit.faces if len(f.verts)>4])
mesh_edit.to_mesh(obj.data);mesh_edit.free();obj.data.update()
# Explicit neutral feather channels restore the original appearance of
# all other clips when switching away from WingDeploy in a game engine.
for action in list(bpy.data.actions):
    if action.name=='WingDeploy':continue
    rig.animation_data.action=action
    for item in specs:
        b=rig.pose.bones[item['name']];b.rotation_euler=(0,0,0);b.location=(0,0,0)
        for frame in action.frame_range:b.keyframe_insert('rotation_euler',frame=frame,group=b.name)
rig.animation_data.action=bpy.data.actions['WingDeploy'];previous={};pose_bounds=[];global_min=Vector((1e9,1e9,1e9));global_max=-global_min
for frame in range(1,182):
    scene.frame_set(frame);t=(frame-1)/30
    opened=smooth((t-.25)/1.8)*(1-smooth((t-4.1)/1.65));set_roots(opened)
    for item in specs:
        i=item['index'];amount=smooth((t-(.55+i*.08))/1.65)*(1-smooth((t-(4.1+(4-i)*.06))/1.2))
        b=rig.pose.bones[item['name']];q=closed[b.name].slerp(Quaternion(),amount)
        b.rotation_euler=q.to_euler('XYZ',previous[b.name]) if b.name in previous else q.to_euler();previous[b.name]=b.rotation_euler.copy()
        b.keyframe_insert('rotation_euler',frame=frame,group=b.name)
    for side in ['L','R']:
        for prefix in ['wing_root','wing_outer']:rig.pose.bones[prefix+'.'+side].keyframe_insert('rotation_euler',frame=frame,group=prefix+'.'+side)
    update()
for action in bpy.data.actions:
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    if action.name=='WingDeploy' or 'feather_' in curve.data_path:
                        for key in curve.keyframe_points:key.interpolation='LINEAR'
# Actual deformed bounds include the stowed depth and the full fan-out.
bounds_path=ROOT/'src/seraph-motion-bounds.json';bounds=json.loads(bounds_path.read_text())
for frame in range(1,182):
    scene.frame_set(frame);update();ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
    lo=[min(v.co[a] for v in mesh.vertices)-.08 for a in range(3)];hi=[max(v.co[a] for v in mesh.vertices)+.08 for a in range(3)];ev.to_mesh_clear()
    for a in range(3):global_min[a]=min(global_min[a],lo[a]);global_max[a]=max(global_max[a],hi[a])
    pose_bounds.append({'min':lo,'max':hi})
bounds['WingDeploy']={'min':list(global_min),'max':list(global_max),'poses':pose_bounds};bounds_path.write_text(json.dumps(bounds,indent=2)+'\n')
rig.animation_data.action=None
for b in rig.pose.bones:b.rotation_euler=(0,0,0);b.location=(0,0,0)
update();bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);rig.select_set(True)
for o in scene.objects:
    if o.name.startswith('Muzzle_'):o.select_set(True)
bpy.context.view_layer.objects.active=rig
asset=ROOT/'public/models/seraph-03.glb'
saved_parent=obj.parent;obj.parent=None
bpy.ops.export_scene.gltf(filepath=str(asset),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=False,export_anim_slide_to_zero=True,export_skins=True,export_yup=True,export_texcoords=True,export_normals=True,export_tangents=True,export_image_format='AUTO')
obj.parent=saved_parent
runpy.run_path(str(ROOT/'scripts/fix_export_tangents.py'),init_globals={'ASSET_PATH':asset,'REPORT_PATH':OUT/'feather-tangent-repairs.json'})
runpy.run_path(str(ROOT/'scripts/normalize_animation_times.py'),init_globals={'ASSET_PATH':asset,'REPORT_PATH':OUT/'animation-time-normalization.json'})
metadata=json.loads((OUT/'asset-report.json').read_text());metadata.update(vertices=len(obj.data.vertices),triangles=sum(len(p.vertices)-2 for p in obj.data.polygons),bones=len(rig.data.bones),animations=[{'name':a.name,'frames':list(a.frame_range)} for a in bpy.data.actions]);(OUT/'asset-report.json').write_text(json.dumps(metadata,indent=2)+'\n')
(OUT/'feather-rig.json').write_text(json.dumps({'feathers':specs,'closed_rotations':{n:list(q) for n,q in closed.items()},'duration_s':6,'stagger_s':.08},indent=2)+'\n')
rig.animation_data.action=bpy.data.actions['WingDeploy'];scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/SERAPH-03.blend'));print('SERAPH_FEATHERS_DONE',metadata,flush=True)
