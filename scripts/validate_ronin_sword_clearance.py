"""Regress the katana/leg collision using evaluated blade and armor surfaces."""
import bpy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/RONIN-04.blend'))
r=bpy.data.objects['RONIN_04_RIG'];o=bpy.data.objects['RONIN_04_Armor'];s=bpy.context.scene;clip=sys.argv[sys.argv.index('--clip')+1] if '--clip' in sys.argv else 'SwordCombo';r.animation_data.action=bpy.data.actions[clip]
g={v.index:o.vertex_groups[max(v.groups,key=lambda x:x.weight).group].name for v in o.data.vertices}
blade=[tuple(p.vertices) for p in o.data.polygons if p.material_index==0 and all(g[i]=='sword.R' for i in p.vertices)]
legs={n:[tuple(p.vertices) for p in o.data.polygons if all(g[i]==n for i in p.vertices)] for n in ['thigh.L','shin.L','foot.L','skirt.L','thigh.R','shin.R','foot.R','skirt.R']}
assert len({i for p in blade for i in p})==63, 'Missing source blade geometry'
assert all(legs.values()), 'Missing leg armor'
start,end=map(int,r.animation_data.action.frame_range)
sample_count=(end-start)*8+1
result=[]
minimum=1e9
final_lateral_gap=1e9
left_leg_vertices={i for name,polygons in legs.items() if name.endswith('.L') for polygon in polygons for i in polygon}
blade_vertices={i for p in blade for i in p}
for tick in range(sample_count):
 f=start+tick/8;s.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update()
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();verts=[v.co.copy() for v in m.vertices];ev.to_mesh_clear();b=BVHTree.FromPolygons(verts,blade)
 trees={n:BVHTree.FromPolygons(verts,p) for n,p in legs.items()}
 hits={n:len(b.overlap(tree)) for n,tree in trees.items()};hits={n:v for n,v in hits.items() if v}
 for tree in trees.values():
  minimum=min(minimum,min(tree.find_nearest(verts[i])[3] for i in blade_vertices))
 if 2.1<=(f-1)/30<=3.5334:
  final_lateral_gap=min(final_lateral_gap,min(verts[i].x for i in left_leg_vertices)-max(verts[i].x for i in blade_vertices))
 if hits:result.append({'t':(f-1)/30,'hits':hits})
report={'clip':clip,'samples':sample_count,'sample_rate_hz':240,'intersections':result,'minimum_blade_vertex_to_leg_surface_m':minimum,'final_sweep_lateral_gap_m':final_lateral_gap}
(ROOT/('output/motion/ronin-slash-clearance.json' if clip=='SwordSlash' else 'output/motion/ronin-sword-clearance.json')).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
assert not result, 'Katana intersects leg armor'
assert minimum>.05, 'Insufficient katana clearance'

assert clip!='SwordCombo' or final_lateral_gap>.5, 'Final blade sweep crosses the left leg silhouette'
