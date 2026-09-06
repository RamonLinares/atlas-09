"""Reproducible Blender preparation: Tripo retopology -> rigid rig -> UVs -> GLB."""
import bpy, bmesh, math, json, sys, runpy
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
from collections import Counter, defaultdict

ROOT=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
source=next((ROOT/'assets/retopo').glob('*model*.glb'))
bpy.ops.import_scene.gltf(filepath=str(source))
obj=next(o for o in bpy.context.scene.objects if o.type=='MESH')
obj.name='ATLAS_09_Armor'
# Evaluate the import transform, then explicitly change X-forward to -Y-forward.
world=obj.matrix_world.copy(); rotation=Matrix.Rotation(-math.pi/2,4,'Z')
coords=[rotation @ (world @ v.co) for v in obj.data.vertices]
lo=min(p.z for p in coords);scale=18/(max(p.z for p in coords)-lo)
for v,p in zip(obj.data.vertices,coords):v.co=(p-Vector((0,0,lo)))*scale
obj.matrix_world=Matrix.Identity(4)
bpy.context.view_layer.objects.active=obj
obj.select_set(True)
mesh=obj.data
source_count={'vertices':len(mesh.vertices),'triangles':sum(len(p.vertices)-2 for p in mesh.polygons)}
# Weld UV seam duplicates by position; loop UV coordinates remain distinct.
bm=bmesh.new();bm.from_mesh(mesh)
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00008)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.to_mesh(mesh);bm.free();mesh.update()
mesh.uv_layers.active.name='Atlas_Surface'
mat=mesh.materials[0];mat.name='Armor_Reactor_Emission';mat.use_nodes=True
nodes=mat.node_tree.nodes;links=mat.node_tree.links
bsdf=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
# Preserve PBR textures, unpack into portable, clearly named files.
texture_report=[];base=None
for node in nodes:
 if node.type=='TEX_IMAGE' and node.image:
  im=node.image
  semantic='BaseColor' if node.outputs['Color'].is_linked and any(l.to_socket==bsdf.inputs['Base Color'] for l in node.outputs['Color'].links) else ('Normal' if 'normal' in im.name.lower() else 'ORM')
  if semantic=='BaseColor':base=im
  fmt='JPEG' if im.packed_file and bytes(im.packed_file.data[:2])==b'\xff\xd8' else 'PNG'
  ext='jpg' if fmt=='JPEG' else 'png'
  im.filepath_raw=str(ROOT/'public/textures'/f'Atlas_{semantic}.{ext}');im.file_format=fmt;im.save();im.pack()
  texture_report.append({'semantic':semantic,'width':im.size[0],'height':im.size[1],'file':f'Atlas_{semantic}.{ext}'})
  uvnode=nodes.new('ShaderNodeUVMap');uvnode.uv_map='Atlas_Surface';links.new(uvnode.outputs['UV'],node.inputs['Vector'])
if base:
 w,h=base.size;px=np.empty(w*h*4,dtype=np.float32);base.pixels.foreach_get(px);px=px.reshape((-1,4))
 # Derive emission data from turquoise painted light elements, keeping armor unlit.
 diff=np.minimum(px[:,1]-px[:,0],px[:,2]-px[:,0]);mask=np.clip((diff-.025)*12,0,1)
 out=np.zeros_like(px);out[:,0]=mask*.16;out[:,1]=mask*.85;out[:,2]=mask;out[:,3]=1
 em=bpy.data.images.new('Atlas_Emission',width=w,height=h);em.pixels.foreach_set(out.ravel());em.filepath_raw=str(ROOT/'public/textures/Atlas_Emission.png');em.file_format='PNG';em.save();em.pack()
 en=nodes.new('ShaderNodeTexImage');en.image=em;un=nodes.new('ShaderNodeUVMap');un.uv_map='Atlas_Surface';links.new(un.outputs['UV'],en.inputs['Vector']);links.new(en.outputs['Color'],bsdf.inputs['Emission Color']);bsdf.inputs['Emission Strength'].default_value=4.5
 texture_report.append({'semantic':'Emission','width':w,'height':h})

# Spatial sections follow mechanical joints. No smooth skinning of hard armor.
def section(p):
 x,y,z=p; a=abs(x); side='L' if x>0 else 'R'
 if z>15.55 and a<1.12:return 'head'
 if z>10.0 and a<3.45:return 'chest'
 if z>9.05 and a<2.9:return 'pelvis'
 # Below the elbow, the outer thigh reaches x=4.03 while the arm starts
 # at x=4.28. The old 3.35 cutoff sliced thigh panels into forearm/hand
 # groups; keep the boundary inside that actual gap on both sides.
 arm_inner=4.15 if z<12.0 else 3.35
 if z>=8.0 and a>arm_inner:
  if z>13.95 or (z>13.5 and a>5.9):return f'shoulder.{side}'
  if z>12.0:return f'upper_arm.{side}'
  if z>8.25:return f'forearm.{side}'
  return f'hand.{side}'
 if a>4.55 and z>6.3:return f'hand.{side}'
 if z>6.65:return f'thigh.{side}'
 if z>1.7:return f'shin.{side}'
 return f'foot.{side}'

# Split only at bone ownership boundaries, retaining each original UV loop.
parts=defaultdict(list)
for f in mesh.polygons:parts[section(f.center)].append(f.index)
old_mesh=mesh
verts=[];faces=[];uvs=[];weights=defaultdict(list)
for name,indices in parts.items():
 remap={}
 for fi in indices:
  f=old_mesh.polygons[fi];newface=[]
  for li,vi in zip(f.loop_indices,f.vertices):
   if vi not in remap:
    remap[vi]=len(verts);verts.append(tuple(old_mesh.vertices[vi].co));weights[name].append(remap[vi])
   newface.append(remap[vi]);uvs.append(tuple(old_mesh.uv_layers['Atlas_Surface'].data[li].uv))
  faces.append(newface)
mesh=bpy.data.meshes.new('ATLAS_Retopology_RigidSections');mesh.from_pydata(verts,[],faces);mesh.update();obj.data=mesh;mesh.materials.append(mat)
uv=mesh.uv_layers.new(name='Atlas_Surface')
for i,co in enumerate(uvs):uv.data[i].uv=co
for p in mesh.polygons:p.use_smooth=True
for name,indices in weights.items():obj.vertex_groups.new(name=name).add(indices,1.0,'REPLACE')

# Add an independent packed, non-overlapping UV channel for baking/lightmaps.
mesh.uv_layers.new(name='Atlas_Lightmap');mesh.uv_layers.active_index=1
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.008,area_weight=.3,correct_aspect=True,scale_to_bounds=True)
bpy.ops.object.mode_set(mode='OBJECT');mesh.uv_layers.active_index=0;mesh.uv_layers['Atlas_Surface'].active_render=True

# Armature in physical meters, with paired anatomical hinge chains.
bpy.ops.object.armature_add(enter_editmode=True,location=(0,0,0));rig=bpy.context.object;rig.name='ATLAS_09_RIG';rig.show_in_front=True
eb=rig.data.edit_bones;eb.remove(eb[0]);spec={}
def bone(name,head,tail,parent=None,deform=True):
 b=eb.new(name);b.head=head;b.tail=tail;b.use_deform=deform
 if parent:b.parent=eb[parent]
 spec[name]={'head':head,'tail':tail,'parent':parent};return b
bone('root',(0,0,0),(0,0,2),deform=False)
bone('pelvis',(0,0,9.1),(0,0,10.4),'root')
bone('chest',(0,0,10.4),(0,0,15.7),'pelvis')
bone('head',(0,-.15,15.7),(0,-.15,17.6),'chest')
for s,side in [(1,'L'),(-1,'R')]:
 bone('shoulder.'+side,(s*2.8,0,15.1),(s*4.6,0,14.2),'chest')
 bone('upper_arm.'+side,(s*4.6,0,14.2),(s*5.35,-.05,12),'shoulder.'+side)
 bone('forearm.'+side,(s*5.35,-.05,12),(s*6.0,-.3,8.25),'upper_arm.'+side)
 bone('hand.'+side,(s*6.0,-.3,8.25),(s*6.1,-.55,6.6),'forearm.'+side)
 bone('thigh.'+side,(s*2.2,0,9.35),(s*3.0,-.2,6.65),'pelvis')
 bone('shin.'+side,(s*3.0,-.2,6.65),(s*3.65,0,1.7),'thigh.'+side)
 bone('foot.'+side,(s*3.65,0,1.7),(s*3.65,-2.0,.7),'shin.'+side)
bpy.ops.object.mode_set(mode='OBJECT');rig.data.display_type='OCTAHEDRAL'
obj.parent=rig;mod=obj.modifiers.new('Rigid mechanical skin','ARMATURE');mod.object=rig;mod.use_deform_preserve_volume=False
for pb in rig.pose.bones:pb.rotation_mode='XYZ'
rig['README']='Rigid mechanical rig. Each armor section is bound at weight 1 to one bone. Run, KneelFire and Backflip were authored using analytic two-bone IK and baked into portable FK keys. Source generation remains a prototype mesh.'
rig['Design_height_m']=18.0

# Author two loopable animations in Blender; glTF uses the exact same keyframes.
scene=bpy.context.scene;scene.render.fps=30
def create_action(name,frames,fn):
 rig.animation_data_create();rig.animation_data.action=None
 for pb in rig.pose.bones:pb.rotation_euler=(0,0,0);pb.location=(0,0,0);pb.scale=(1,1,1)
 for f in range(1,frames+1,3):
  t=(f-1)/(frames-1)*2*math.pi;fn(t)
  for pb in rig.pose.bones:pb.keyframe_insert('rotation_euler',frame=f,group=pb.name)
 # Explicit loop closure.
 fn(0)
 for pb in rig.pose.bones:pb.keyframe_insert('rotation_euler',frame=frames,group=pb.name)
 action=rig.animation_data.action;action.name=name;action.use_fake_user=True
 rig.animation_data.action=None
 track=rig.animation_data.nla_tracks.new();track.name=name;track.strips.new(name,1,action);track.mute=True
 return action
def sentinel(t):
 for pb in rig.pose.bones:pb.rotation_euler=(0,0,0)
 rig.pose.bones['head'].rotation_euler[1]=.10*math.sin(t)
 rig.pose.bones['chest'].rotation_euler[1]=.008*math.sin(t)
 for sign,side in [(1,'L'),(-1,'R')]:
  rig.pose.bones['forearm.'+side].rotation_euler[0]=.022*(1-math.cos(t))
  rig.pose.bones['shoulder.'+side].rotation_euler[1]=sign*.012*math.sin(t)
def awaken(t):
 sentinel(0);rise=(1-math.cos(t))*.5
 rig.pose.bones['head'].rotation_euler[0]=-.08*rise
 rig.pose.bones['chest'].rotation_euler[0]=-.018*rise
 for sign,side in [(1,'L'),(-1,'R')]:
  rig.pose.bones['upper_arm.'+side].rotation_euler[2]=sign*.055*rise
  rig.pose.bones['forearm.'+side].rotation_euler[0]=-.17*rise
  rig.pose.bones['hand.'+side].rotation_euler[1]=sign*.07*rise
create_action('Sentinel',181,sentinel);create_action('Awaken',151,awaken)
sys.path.insert(0,str(ROOT/'scripts'))
from motion_library import add_hardware,build_motions
muzzle=add_hardware(obj,rig)
mesh=obj.data
weights={g.name:[] for g in obj.vertex_groups}
for v in mesh.vertices:
 for g in v.groups:weights[obj.vertex_groups[g.group].name].append(v.index)
motion_report=build_motions(rig,obj)
(ROOT/'output/motion/bake-report.json').write_text(json.dumps(motion_report,indent=2))
sentinel(0);scene.frame_set(1);scene.frame_start=1;scene.frame_end=181

# Mesh/UV/rig evidence and UV vector diagrams.
def uv_report(layer):
 invalid=0;degenerate=0;lines=[]
 for f in mesh.polygons:
  pts=[layer.data[i].uv[:] for i in f.loop_indices]
  if any(not math.isfinite(c) or c<-.0001 or c>1.0001 for p in pts for c in p):invalid+=1
  area=abs(sum(pts[i][0]*pts[(i+1)%len(pts)][1]-pts[(i+1)%len(pts)][0]*pts[i][1] for i in range(len(pts))))*.5
  if area<1e-12:degenerate+=1
  lines.append('<polygon points="'+' '.join(f'{x*1024:.2f},{(1-y)*1024:.2f}' for x,y in pts)+'"/>')
 (ROOT/'output'/f'{layer.name}.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024"><rect width="1024" height="1024" fill="#18201d"/><g fill="none" stroke="#d5f3a5" stroke-width="0.35">'+''.join(lines)+'</g></svg>')
 return {'name':layer.name,'out_of_bounds_faces':invalid,'zero_area_faces':degenerate}
bm=bmesh.new();bm.from_mesh(mesh);boundary=sum(e.is_boundary for e in bm.edges);nonmanifold=sum(not e.is_manifold for e in bm.edges);bm.free()
report={'source':str(source.relative_to(ROOT)),'retopo_intake':source_count,'vertices':len(mesh.vertices),'triangles':sum(len(f.vertices)-2 for f in mesh.polygons),'materials':len(mesh.materials),'textures':texture_report,'height_m':18,'bounds':[[min(v.co[i] for v in mesh.vertices),max(v.co[i] for v in mesh.vertices)] for i in range(3)],'bones':len(rig.data.bones),'rigid_sections':{k:len(v) for k,v in weights.items()},'uv_maps':[uv_report(l) for l in mesh.uv_layers],'unweighted_vertices':sum(not v.groups for v in mesh.vertices),'boundary_edges_after_joint_separation':boundary,'nonmanifold_edges_after_joint_separation':nonmanifold,'animations':[{'name':a.name,'frames':list(a.frame_range)} for a in bpy.data.actions],'limitations':['Automatic triangular retopology, not hand-authored subdivision edge loops.','Rigid sections have open boundaries at joints, covered by added joint housings. Arbitrary extreme poses still require manual cleanup.','FK export with analytic IK used during motion baking. Five supplied clips; no interactive IK controls or finger articulation.','UV0 retains baked source textures; UV1 is a new packed Blender lightmap unwrap. UV0 overlap has not been exhaustively measured.','No collision shapes, LODs, or mobile device performance certification.']}
(ROOT/'output/asset-report.json').write_text(json.dumps(report,indent=2))

# Export the same rig and animated mesh used in the .blend.
bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig
muzzle.select_set(True)
obj.parent=None
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models/atlas-09.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_nla_strips=True,export_skins=True,export_yup=True,export_texcoords=True,export_normals=True,export_tangents=True,export_image_format='AUTO')
runpy.run_path(str(ROOT/'scripts/fix_export_tangents.py'),run_name='__main__')
obj.parent=rig

# Inspection stage is Blender-native and excluded from the character export.
def point(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
world=scene.world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.11,.14,.12,1);world.node_tree.nodes['Background'].inputs[1].default_value=.5
stage=bpy.data.collections.new('STUDIO — excluded from GLB');scene.collection.children.link(stage)
def to_stage(o):
 for c in list(o.users_collection):c.objects.unlink(o)
 stage.objects.link(o)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.07));floor=bpy.context.object;floor.name='Studio ground';to_stage(floor)
ground=bpy.data.materials.new('Studio graphite');ground.diffuse_color=(.075,.09,.07,1);ground.use_nodes=True;ground.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.075,.09,.07,1);ground.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.85;floor.data.materials.append(ground)
for pos,power,size,color in [((7,-13,25),3300,10,(1,.88,.68)),((-12,-5,13),2200,12,(.75,.88,1)),((8,10,22),4200,9,(.65,.86,1))]:
 bpy.ops.object.light_add(type='AREA',location=pos);light=bpy.context.object;light.data.energy=power;light.data.shape='DISK';light.data.size=size;light.data.color=color;point(light,(0,0,10));to_stage(light)
bpy.ops.object.camera_add(location=(24,-43,21));cam=bpy.context.object;point(cam,(0,0,9));cam.data.type='ORTHO';cam.data.ortho_scale=23;scene.camera=cam;to_stage(cam)
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True;scene.render.resolution_x=1300;scene.render.resolution_y=1500;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
# Set default viewport to useful material view and select the rig.
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':
  area.spaces.active.region_3d.view_distance=32;area.spaces.active.region_3d.view_location=(0,0,9);area.spaces.active.shading.type='MATERIAL'
sentinel(0);rig.animation_data.action=bpy.data.actions['Sentinel'];scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/ATLAS-09.blend'))
scene.render.filepath=str(ROOT/'output/atlas-09-beauty.png')
if '--skip-render' not in sys.argv:bpy.ops.render.render(write_still=True)
print('ASSET_REPORT',json.dumps(report))
