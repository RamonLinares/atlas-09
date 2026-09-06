import bpy,json,numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/RONIN-04.blend'))
o=bpy.data.objects['RONIN_04_Armor']
for g in o.vertex_groups:
 p=np.array([v.co[:] for v in o.data.vertices if any(w.group==g.index for w in v.groups)])
 print(g.name,len(p),p.min(axis=0).round(2).tolist(),p.max(axis=0).round(2).tolist())
from collections import defaultdict
vf=defaultdict(set)
for f in o.data.polygons:
 for vi in f.vertices:vf[vi].add(f.index)
for g in o.vertex_groups:
 if not g.name.startswith(('upper_arm','shoulder','forearm','hand','skirt')):continue
 remaining={f.index for f in o.data.polygons if o.data.vertices[f.vertices[0]].groups[0].group==g.index};out=[]
 while remaining:
  todo=[remaining.pop()];c=set(todo)
  while todo:
   fi=todo.pop()
   for vi in o.data.polygons[fi].vertices:
    fresh=vf[vi]&remaining;remaining-=fresh;c|=fresh;todo.extend(fresh)
  pts=np.array([o.data.vertices[vi].co[:] for fi in c for vi in o.data.polygons[fi].vertices]);out.append((len(c),pts.mean(axis=0).round(2).tolist(),pts.min(axis=0).round(2).tolist(),pts.max(axis=0).round(2).tolist()))
 print('COMPONENTS',g.name,sorted(out,reverse=True)[:10])
