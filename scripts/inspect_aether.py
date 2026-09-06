"""Inspect the normalized source silhouette before placing the new rig."""
import bpy, bmesh, math, json
from mathutils import Matrix, Vector
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
sources=list((ROOT/'assets/aether-02/retopo').glob('*model_url.glb')) or list((ROOT/'assets/aether-02/source').glob('*model_url.glb'))
bpy.ops.import_scene.gltf(filepath=str(sources[0]))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH')
pts=[Matrix.Rotation(-math.pi/2,4,'Z') @ (o.matrix_world@v.co) for v in o.data.vertices]
lo=min(p.z for p in pts);scale=14/(max(p.z for p in pts)-lo)
for v,p in zip(o.data.vertices,pts):v.co=(p-Vector((0,0,lo)))*scale
o.matrix_world=Matrix.Identity(4);o.data.update()
report={}
for z in [0.5,1,2,3,4,5,6,7,8,9,10,11,12,13]:
 p=[v.co for v in o.data.vertices if abs(v.co.z-z)<.1]
 report[z]={'bounds':[[min(v[i] for v in p),max(v[i] for v in p)] for i in range(3)]}
(ROOT/'output/aether-02/slices.json').write_text(json.dumps(report,indent=2))
bpy.context.scene.world.use_nodes=True;bpy.context.scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.18,.18,.18,1)
def aim(o):o.rotation_euler=(Vector((0,0,7))-o.location).to_track_quat('-Z','Y').to_euler()
for pos,power in [((6,-10,20),2300),((-8,-6,12),1800),((6,8,20),2800)]:
 bpy.ops.object.light_add(type='AREA',location=pos);l=bpy.context.object;l.data.energy=power;l.data.shape='DISK';l.data.size=9;aim(l)
bpy.ops.object.camera_add(location=(0,-30,7));c=bpy.context.object;aim(c);c.data.type='ORTHO';c.data.ortho_scale=15.5
s=bpy.context.scene;s.camera=c;s.render.engine='CYCLES';s.cycles.samples=12;s.cycles.use_denoising=True;s.render.resolution_x=800;s.render.resolution_y=1000;s.render.resolution_percentage=100
for name,pos in [('front',(0,-30,7)),('side',(30,0,7))]:
 c.location=pos;aim(c);s.render.filepath=str(ROOT/f'output/aether-02/source-{name}.png');bpy.ops.render.render(write_still=True)
