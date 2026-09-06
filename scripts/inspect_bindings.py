import bpy, json
from pathlib import Path
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/ATLAS-09.blend'))
obj=bpy.data.objects['ATLAS_09_Armor'];m=obj.data
adj=defaultdict(set)
for e in m.edges:
 a,b=e.vertices;adj[a].add(b);adj[b].add(a)
seen=set();groups=defaultdict(list)
for v in m.vertices:
 if v.index in seen:continue
 stack=[v.index];seen.add(v.index);component=[]
 while stack:
  i=stack.pop();component.append(i)
  for j in adj[i]:
   if j not in seen:seen.add(j);stack.append(j)
 name=obj.vertex_groups[v.groups[0].group].name
 if name.startswith(('forearm','hand','thigh')) and len(component)>3:
  co=[m.vertices[i].co for i in component]
  groups[name].append({'vertices':len(component),'bounds':[[round(min(p[k] for p in co),3),round(max(p[k] for p in co),3)] for k in range(3)],'seed':v.index})
print(json.dumps(groups,indent=2))
