"""Inspect the SCORPIO-05 retopology source before assigning rigid parts."""
import bpy,bmesh,math,json,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/scorpio-05';OUT.mkdir(parents=True,exist_ok=True)
sources=list((ROOT/'assets/scorpio-05/retopo').glob('*model_url.glb')) or list((ROOT/'assets/scorpio-05/source').glob('*model_url.glb'))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(sources[0]))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH')
pts=[Matrix.Rotation(-math.pi/2,4,'Z')@(o.matrix_world@v.co) for v in o.data.vertices];low=min(p.z for p in pts);scale=17/(max(p.z for p in pts)-low)
for v,p in zip(o.data.vertices,pts):v.co=(p-Vector((0,0,low)))*scale
o.matrix_world=Matrix.Identity(4);o.data.update()
p=np.array([v.co[:] for v in o.data.vertices]);np.save(OUT/'inspection-vertices.npy',p)
report={'source':str(sources[0]),'scale':scale,'bounds':[[float(p[:,i].min()),float(p[:,i].max())] for i in range(3)],'slices':{}}
for z in np.arange(.5,17.5,.5):
 q=p[abs(p[:,2]-z)<.15]
 if len(q):report['slices'][float(z)]={'count':len(q),'bounds':[[float(q[:,i].min()),float(q[:,i].max())] for i in range(3)]}
(OUT/'source-inspection.json').write_text(json.dumps(report,indent=2))
for view,axes in [('front',(0,2)),('side',(1,2)),('top',(0,1))]:
 x,y=axes;bounds=[p[:,x].min(),p[:,x].max(),p[:,y].min(),p[:,y].max()];unit=35;w=(bounds[1]-bounds[0])*unit+80;h=(bounds[3]-bounds[2])*unit+80
 svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><rect width="100%" height="100%" fill="#fafafa"/>']
 for a in np.arange(math.floor(bounds[0]),math.ceil(bounds[1])+1):
  sx=40+(a-bounds[0])*unit;svg.append(f'<path d="M{sx} 20V{h-20}" stroke="#ccc"/><text x="{sx+2}" y="20" font-size="10">{a}</text>')
 for a in np.arange(math.floor(bounds[2]),math.ceil(bounds[3])+1):
  sy=h-40-(a-bounds[2])*unit;svg.append(f'<path d="M20 {sy}H{w-20}" stroke="#ccc"/><text x="2" y="{sy}" font-size="10">{a}</text>')
 for v in p[::max(1,len(p)//12000)]:
  sx=40+(v[x]-bounds[0])*unit;sy=h-40-(v[y]-bounds[2])*unit;svg.append(f'<circle cx="{sx}" cy="{sy}" r=".7" fill="#183347" opacity=".5"/>')
 svg.append('</svg>');(OUT/f'source-{view}-coordinates.svg').write_text(''.join(svg))
world=bpy.context.scene.world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.18,.18,.18,1);world.node_tree.nodes['Background'].inputs[1].default_value=.7
point=Vector((0,0,8.5))
def aim(obj):obj.rotation_euler=(point-obj.location).to_track_quat('-Z','Y').to_euler()
for pos,power in [((10,-18,28),4800),((-14,-10,18),3300),((10,15,25),4500)]:
 bpy.ops.object.light_add(type='AREA',location=pos);l=bpy.context.object;l.data.energy=power;l.data.shape='DISK';l.data.size=12;aim(l)
bpy.ops.object.camera_add(location=(0,-45,10));c=bpy.context.object;c.data.type='ORTHO';c.data.ortho_scale=22;aim(c)
s=bpy.context.scene;s.camera=c;s.render.engine='CYCLES';s.cycles.samples=12;s.cycles.use_denoising=True;s.render.resolution_x=1000;s.render.resolution_y=1000;s.render.resolution_percentage=100
for name,pos in [('front',(0,-45,10)),('side',(45,0,10)),('back',(0,45,10))]:
 c.location=pos;aim(c);s.render.filepath=str(OUT/f'source-{name}.png');bpy.ops.render.render(write_still=True)
print('INSPECTION',json.dumps({k:v for k,v in report.items() if k!='slices'}))
