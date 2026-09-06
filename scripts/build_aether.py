"""Rebuild AETHER-02 from its preserved Tripo retopology, entirely locally."""
import bpy, bmesh, math, json, sys, runpy
import numpy as np
from pathlib import Path
from collections import defaultdict
from mathutils import Vector, Matrix

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/aether-02';TEX=ROOT/'public/textures/aether-02'
OUT.mkdir(parents=True,exist_ok=True);TEX.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'scripts'))
from motion_library import build_motions
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
source=next((ROOT/'assets/aether-02/retopo').glob('*model_url.glb'))
bpy.ops.import_scene.gltf(filepath=str(source))
obj=next(o for o in bpy.context.scene.objects if o.type=='MESH');obj.name='AETHER_02_Armor'
coords=[Matrix.Rotation(-math.pi/2,4,'Z')@(obj.matrix_world@v.co) for v in obj.data.vertices]
lo=min(p.z for p in coords);scale=14/(max(p.z for p in coords)-lo)
for v,p in zip(obj.data.vertices,coords):v.co=(p-Vector((0,0,lo)))*scale
obj.matrix_world=Matrix.Identity(4)
bpy.context.view_layer.objects.active=obj;obj.select_set(True)
mesh=obj.data;intake_triangles=sum(len(f.vertices)-2 for f in mesh.polygons)
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00006)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free();mesh.update()
mesh.uv_layers.active.name='Aether_Surface'
mat=mesh.materials[0];mat.name='AETHER white steel — reactor emission';mat.use_nodes=True
bsdf=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');base=None
textures=[]
for n in list(mat.node_tree.nodes):
 if n.type!='TEX_IMAGE' or not n.image:continue
 im=n.image
 semantic='BaseColor' if any(l.to_socket==bsdf.inputs['Base Color'] for l in n.outputs['Color'].links) else ('Normal' if 'normal' in im.name.lower() else 'ORM')
 if semantic=='BaseColor':base=im
 ext='jpg' if im.packed_file and bytes(im.packed_file.data[:2])==b'\xff\xd8' else 'png'
 im.filepath_raw=str(TEX/f'Aether_{semantic}.{ext}');im.file_format='JPEG' if ext=='jpg' else 'PNG';im.save();im.pack()
 textures.append({'semantic':semantic,'size':list(im.size),'file':im.filepath_raw})
 uv=mat.node_tree.nodes.new('ShaderNodeUVMap');uv.uv_map='Aether_Surface';mat.node_tree.links.new(uv.outputs['UV'],n.inputs['Vector'])
bsdf.inputs['Coat Weight'].default_value=.28;bsdf.inputs['Coat Roughness'].default_value=.22
if base:
 w,h=base.size;px=np.empty(w*h*4,dtype=np.float32);base.pixels.foreach_get(px);px=px.reshape((-1,4))
 mask=np.clip((np.minimum(px[:,1]-px[:,0],px[:,2]-px[:,0])-.045)*8,0,1)
 out=np.zeros_like(px);out[:,:3]=mask[:,None]*np.array([.12,.65,1]);out[:,3]=1
 em=bpy.data.images.new('Aether_Emission',width=w,height=h);em.pixels.foreach_set(out.ravel());em.filepath_raw=str(TEX/'Aether_Emission.png');em.file_format='PNG';em.save();em.pack()
 en=mat.node_tree.nodes.new('ShaderNodeTexImage');en.image=em;uv=mat.node_tree.nodes.new('ShaderNodeUVMap');uv.uv_map='Aether_Surface'
 mat.node_tree.links.new(uv.outputs['UV'],en.inputs['Vector']);mat.node_tree.links.new(en.outputs['Color'],bsdf.inputs['Emission Color']);bsdf.inputs['Emission Strength'].default_value=2.2
glass=mat.copy();glass.name='AETHER opaque smoked glass — reactor emission'
g=next(n for n in glass.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
for name,value in [('Metallic',0.0),('Roughness',.32),('Transmission Weight',0.0),('Alpha',1.0),('IOR',1.48),('Coat Weight',.6),('Coat Roughness',.18)]:
 for link in list(g.inputs[name].links):glass.node_tree.links.remove(link)
 g.inputs[name].default_value=value

# Boundaries follow the inspected silhouette. In particular, the arms have a
# sloping inner boundary in the empty gap beside the torso and outer thighs.
def section(p):
 x,y,z=p;a=abs(x);s='L' if x>0 else 'R'
 if z>12.05 and a<1.15:return 'head'
 arm_inner=min(2.3,1.35+.30*max(0,11.1-z))
 if z>5.9 and a>arm_inner:
  if z>10.85:return 'shoulder.'+s
  if z>9.55:return 'upper_arm.'+s
  if z>7.55:return 'forearm.'+s
  return 'hand.'+s
 if z>9.35:return 'chest'
 if z>8.7 or (z>7.35 and a<.7):return 'pelvis'
 if z>5.55:return 'thigh.'+s
 if z>1.28:return 'shin.'+s
 return 'foot.'+s

def is_glass(f):
 x,y,z=f.center;a=abs(x)
 # Glass domains are bounded by the chest/visor silhouettes, then restricted
 # to the dark texels so neighboring white steel keeps its metal response.
 domain=(y<-.65 and 9.75<z<11.5 and a<1.0) or (y<-.45 and 12.35<z<13.5 and a<.9)
 if not domain or base is None:return False
 uv=sum((mesh.uv_layers['Aether_Surface'].data[i].uv for i in f.loop_indices),Vector((0,0)))/len(f.loop_indices)
 rgb=px[min(h-1,max(0,int(uv.y*h)))*w+min(w-1,max(0,int(uv.x*w))),:3]
 return float(rgb.mean())<.38

parts=defaultdict(list)
for f in mesh.polygons:parts[section(f.center)].append(f.index)
old=mesh;verts=[];faces=[];uvs=[];mats=[];weights=defaultdict(list)
for name,indices in parts.items():
 remap={}
 for fi in indices:
  f=old.polygons[fi];face=[];mats.append(1 if is_glass(f) else 0)
  for li,vi in zip(f.loop_indices,f.vertices):
   if vi not in remap:remap[vi]=len(verts);verts.append(tuple(old.vertices[vi].co));weights[name].append(remap[vi])
   face.append(remap[vi]);uvs.append(tuple(old.uv_layers['Aether_Surface'].data[li].uv))
  faces.append(face)
mesh=bpy.data.meshes.new('AETHER_RigidArmor');mesh.from_pydata(verts,[],faces);mesh.update();obj.data=mesh
mesh.materials.append(mat);mesh.materials.append(glass)
uv=mesh.uv_layers.new(name='Aether_Surface')
for i,co in enumerate(uvs):uv.data[i].uv=co
for f,mi in zip(mesh.polygons,mats):f.material_index=mi;f.use_smooth=True
for name,indices in weights.items():obj.vertex_groups.new(name=name).add(indices,1,'REPLACE')

# Rest-space joints measured from front and side inspection renders (meters).
bpy.ops.object.armature_add(enter_editmode=True);rig=bpy.context.object;rig.name='AETHER_02_RIG';rig.show_in_front=True
eb=rig.data.edit_bones;eb.remove(eb[0])
def bone(name,head,tail,parent=None,deform=True):
 b=eb.new(name);b.head=head;b.tail=tail;b.use_deform=deform
 if parent:b.parent=eb[parent]
bone('root',(0,0,0),(0,0,1),deform=False)
bone('pelvis',(0,.15,8.15),(0,.1,9.35),'root')
bone('chest',(0,.1,9.35),(0,.05,12.05),'pelvis')
bone('head',(0,.05,12.05),(.12,-.15,13.8),'chest')
for s,side in [(1,'L'),(-1,'R')]:
 bone('shoulder.'+side,(s*1.05,.25,11.35),(s*1.65,.25,11.25),'chest')
 bone('upper_arm.'+side,(s*1.65,.25,11.25),(s*2.25,.12,9.5),'shoulder.'+side)
 bone('forearm.'+side,(s*2.25,.12,9.5),(s*2.98,-.1,7.55),'upper_arm.'+side)
 bone('hand.'+side,(s*2.98,-.1,7.55),(s*3.0,-.2,6.25),'forearm.'+side)
 bone('thigh.'+side,(s*.98,.15,8.15),(s*1.45,.25,5.15),'pelvis')
 bone('shin.'+side,(s*1.45,.25,5.15),(s*2.0,.6,1.28),'thigh.'+side)
 bone('foot.'+side,(s*2.0,.6,1.28),(s*2.03,-.75,.3),'shin.'+side)
bpy.ops.object.mode_set(mode='OBJECT')
obj.parent=rig;mod=obj.modifiers.new('Rigid mechanical skin','ARMATURE');mod.object=rig
for b in rig.pose.bones:b.rotation_mode='XYZ'

# The generated source looks 35 degrees left. Correct the head armor in rest
# space so every clip and the downloadable model face along the body axis.
head=rig.data.bones['head'];head_yaw_correction=math.radians(-35)
head_rotation=Matrix.Rotation(head_yaw_correction,3,(head.tail_local-head.head_local).normalized())
for vi in weights['head']:
 mesh.vertices[vi].co=head.head_local+head_rotation@(mesh.vertices[vi].co-head.head_local)
mesh.update()
rig['head_rest_yaw_correction_degrees']=-35

# Compact actuator housings close the visual gaps under the separated armor.
def material(name,color,metallic,roughness):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=color;p.inputs['Metallic'].default_value=metallic;p.inputs['Roughness'].default_value=roughness;return m
joint=material('AETHER graphite actuators',(.022,.032,.045,1),.7,.35)
trim=material('AETHER brushed white steel',(.7,.77,.83,1),.8,.26)
glow=material('AETHER wrist reactor emission',(.03,.25,.4,1),.1,.3)
g=glow.node_tree.nodes.get('Principled BSDF');g.inputs['Emission Color'].default_value=(.12,.65,1,1);g.inputs['Emission Strength'].default_value=3
pieces=[]
def bind(o,name,mat):
 o.data.materials.append(mat);o.vertex_groups.new(name=name).add(list(range(len(o.data.vertices))),1,'REPLACE')
 if o.data.uv_layers:o.data.uv_layers.active.name='Aether_Surface'
 else:o.data.uv_layers.new(name='Aether_Surface')
 for f in o.data.polygons:f.use_smooth=True
 pieces.append(o)
def sphere(center,radius,name):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=radius,location=center);bind(bpy.context.object,name,joint)
def cylinder(center,radius,length,direction,name,mat):
 bpy.ops.mesh.primitive_cylinder_add(vertices=20,radius=radius,depth=length,location=center);o=bpy.context.object;o.rotation_euler=direction.to_track_quat('Z','Y').to_euler();bind(o,name,mat)
for side in ['L','R']:
 for name,radius in [('upper_arm',.40),('forearm',.27),('hand',.22),('thigh',.48),('shin',.38),('foot',.25)]:sphere(rig.data.bones[name+'.'+side].head_local,radius,name+'.'+side)
sphere((0,.1,9.35),.66,'chest');sphere((0,.05,12.05),.32,'head')
f=rig.data.bones['forearm.R'];direction=(f.tail_local-f.head_local).normalized()
center=f.tail_local-direction*.38+Vector((-.18,-.35,0))
cylinder(center,.20,.66,direction,'forearm.R',trim)
cylinder(center+direction*.34,.155,.035,direction,'forearm.R',glow)
bpy.ops.object.empty_add(type='ARROWS',location=center+direction*.38);muzzle=bpy.context.object;muzzle.name='Muzzle_R'
muzzle.rotation_euler=direction.to_track_quat('-Z','Y').to_euler();world=muzzle.matrix_world.copy();muzzle.parent=rig;muzzle.parent_type='BONE';muzzle.parent_bone='forearm.R';muzzle.matrix_world=world
bpy.ops.object.select_all(action='DESELECT');obj.select_set(True)
for o in pieces:o.select_set(True)
bpy.context.view_layer.objects.active=obj;bpy.ops.object.join()
bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>3]);bm.to_mesh(obj.data);bm.free();obj.data.update()
mesh=obj.data
mesh.uv_layers.new(name='Aether_Lightmap');mesh.uv_layers.active_index=1
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.008,area_weight=.3,scale_to_bounds=True);bpy.ops.object.mode_set(mode='OBJECT')
mesh.uv_layers.active_index=0;mesh.uv_layers['Aether_Surface'].active_render=True

scene=bpy.context.scene;scene.render.fps=30
rig.animation_data_create()
def neutral():
 for pb in rig.pose.bones:pb.rotation_euler=(0,0,0);pb.location=(0,0,0);pb.scale=(1,1,1)
def idle(t):
 neutral();rig.pose.bones['head'].rotation_euler.y=.07*math.sin(t)
 for s,side in [(1,'L'),(-1,'R')]:rig.pose.bones['forearm.'+side].rotation_euler.x=.025*(1-math.cos(t));rig.pose.bones['shoulder.'+side].rotation_euler.y=s*.012*math.sin(t)
def awaken(t):
 neutral();rise=(1-math.cos(t))*.5;rig.pose.bones['head'].rotation_euler.x=-.06*rise
 for s,side in [(1,'L'),(-1,'R')]:rig.pose.bones['upper_arm.'+side].rotation_euler.z=s*.07*rise;rig.pose.bones['forearm.'+side].rotation_euler.x=-.2*rise
for name,frames,fn in [('Sentinel',181,idle),('Awaken',151,awaken)]:
 rig.animation_data.action=None
 for frame in range(1,frames+1,3):
  fn((frame-1)/(frames-1)*math.tau)
  for pb in rig.pose.bones:pb.keyframe_insert('rotation_euler',frame=frame,group=pb.name)
 action=rig.animation_data.action;action.name=name;action.use_fake_user=True;rig.animation_data.action=None
 track=rig.animation_data.nla_tracks.new();track.name=name;track.strips.new(name,1,action);track.mute=True
motion_report=build_motions(rig,obj,dict(run_drop=.48,run_bob=.15,stride=2.0,ankle_z=1.28,ankle_y=.6,ankle_x=2.0,run_x=1.8,step_lift=2.15,
 kneel_drop=4.6,kneel_front=(1.6,-2.8,1.28),kneel_back=(-1.1,4.7,2.3),crouch=1.2,landing=1.1,tuck_width=.5,tuck_back=1.65,tuck_lift=3.7,jump=7.2,pivot=(0,.15,8.15),flight=.32))
(OUT/'bake-report.json').write_text(json.dumps(motion_report,indent=2))
rig['README']='AETHER-02, 14m athletic mecha. Rigid armor, opaque glass (no transmission), five baked clips. Anatomical segmentation follows the inspected model; source retopology remains a realtime prototype.'
neutral();scene.frame_set(1);scene.frame_start=1;scene.frame_end=181
bm=bmesh.new();bm.from_mesh(mesh);boundary=sum(e.is_boundary for e in bm.edges);bm.free()
report={'source':str(source.relative_to(ROOT)),'height_m':14,'source_triangles':intake_triangles,'vertices':len(mesh.vertices),'triangles':sum(len(f.vertices)-2 for f in mesh.polygons),'bones':len(rig.data.bones),'materials':[m.name for m in mesh.materials],'glass_faces':sum(f.material_index==1 for f in mesh.polygons),'boundary_edges':boundary,'textures':textures,'animations':[{'name':a.name,'frames':list(a.frame_range)} for a in bpy.data.actions]}
(OUT/'asset-report.json').write_text(json.dumps(report,indent=2))
bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);rig.select_set(True);muzzle.select_set(True);bpy.context.view_layer.objects.active=rig
obj.parent=None
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models/aether-02.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_nla_strips=True,export_skins=True,export_yup=True,export_texcoords=True,export_normals=True,export_tangents=True,export_image_format='AUTO')
runpy.run_path(str(ROOT/'scripts/fix_export_tangents.py'),init_globals={'ASSET_PATH':ROOT/'public/models/aether-02.glb','REPORT_PATH':OUT/'tangent-repairs.json'},run_name='__main__')
obj.parent=rig

# A reusable studio for Blender inspection, excluded from the GLB selection.
stage=bpy.data.collections.new('STUDIO — excluded from GLB');scene.collection.children.link(stage)
def to_stage(o):
 for c in list(o.users_collection):c.objects.unlink(o)
 stage.objects.link(o)
def aim(o):o.rotation_euler=(Vector((0,0,7))-o.location).to_track_quat('-Z','Y').to_euler()
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.13,.16,.18,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.035));floor=bpy.context.object;floor.name='Studio floor';to_stage(floor);floor.data.materials.append(material('Studio graphite',(.055,.07,.085,1),.15,.8))
for pos,power,color in [((7,-12,22),2600,(.85,.93,1)),((-9,-6,12),1900,(1,.95,.88)),((8,8,20),3500,(.7,.85,1))]:
 bpy.ops.object.light_add(type='AREA',location=pos);l=bpy.context.object;l.data.energy=power;l.data.color=color;l.data.shape='DISK';l.data.size=8;aim(l);to_stage(l)
bpy.ops.object.camera_add(location=(16,-32,14));cam=bpy.context.object;aim(cam);cam.data.type='ORTHO';cam.data.ortho_scale=17;scene.camera=cam;to_stage(cam)
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True;scene.render.resolution_x=1200;scene.render.resolution_y=1500;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX'
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':area.spaces.active.region_3d.view_distance=24;area.spaces.active.region_3d.view_location=(0,0,7);area.spaces.active.shading.type='MATERIAL'
rig.animation_data.action=bpy.data.actions['Sentinel'];scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/AETHER-02.blend'))
scene.render.filepath=str(OUT/'aether-02-beauty.png')
if '--skip-render' not in sys.argv:bpy.ops.render.render(write_still=True)
print('ASSET_REPORT',json.dumps(report))
