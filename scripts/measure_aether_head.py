"""Measure helmet bilateral alignment independently from the correction transform."""
import bpy, json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import numpy as np
from mathutils import Vector, kdtree
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/AETHER-02.blend'))
o=bpy.data.objects['AETHER_02_Armor'];idx=o.vertex_groups['head'].index
pts=np.array([v.co[:] for v in o.data.vertices if any(g.group==idx for g in v.groups) and v.co.z>12.55]);center=pts.mean(axis=0);pts-=center
kd=kdtree.KDTree(len(pts))
for i,p in enumerate(pts):kd.insert(Vector(p),i)
kd.balance()
def loss(v):
 n=np.array([1,v[0],v[1]]);n/=np.linalg.norm(n);mirrored=pts-2*(pts@n-v[2])[:,None]*n
 d=np.array([kd.find(Vector(p))[2] for p in mirrored]);return np.mean(np.minimum(d,.2)**2)
v=np.zeros(3);best=loss(v)
for step in [.15,.07,.03,.015,.007,.003,.001]:
 for _ in range(25):
  changed=False
  for axis in range(3):
   for sign in [-1,1]:
    candidate=v.copy();candidate[axis]+=sign*step;q=loss(candidate)
    if q<best:best=q;v=candidate;changed=True
  if not changed:break
n=np.array([1,v[0],v[1]]);n/=np.linalg.norm(n);point=center+v[2]*n
result={'plane_normal':n.tolist(),'plane_point':point.tolist(),'rms_m':float(best**.5),'vertices':len(pts)}
assert abs(n[1])<.01 and abs(n[2])<.01 and abs(point[0])<.01, result
(ROOT/'output/aether-02/head-alignment.json').write_text(json.dumps(result,indent=2));print(result)
