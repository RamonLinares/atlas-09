"""Repair zero tangents emitted at rare split vertices by Blender's exporter.

The tangent is derived from a neighboring triangle's position/UV differential
and orthogonalized against the exported normal. Geometry and skin data stay exact.
"""
import json,struct,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
path=Path(globals().get('ASSET_PATH',ROOT/'public/models/atlas-09.glb'));raw=bytearray(path.read_bytes())
json_length=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+json_length]);binary_offset=20+json_length+8
def accessor(index):
 a=doc['accessors'][index];view=doc['bufferViews'][a['bufferView']]
 n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];kind={5121:'B',5123:'H',5125:'I',5126:'f'}[a['componentType']];fmt='<'+kind*n
 stride=view.get('byteStride',struct.calcsize(fmt));offset=binary_offset+view.get('byteOffset',0)+a.get('byteOffset',0)
 return [struct.unpack_from(fmt,raw,offset+i*stride) for i in range(a['count'])],offset,stride
repairs=[]
for mesh in doc.get('meshes',[]):
 for prim in mesh['primitives']:
  at=prim['attributes']
  if 'TANGENT' not in at:continue
  ts,offset,stride=accessor(at['TANGENT']);ps,_,_=accessor(at['POSITION']);ns,_,_=accessor(at['NORMAL']);uv,_,_=accessor(at['TEXCOORD_0']);idx,_,_=accessor(prim['indices']);idx=[a[0] for a in idx]
  for vi,t in enumerate(ts):
   if sum(x*x for x in t[:3])>.5:continue
   normal=ns[vi];replacement=None
   for k in range(0,len(idx),3):
    tri=idx[k:k+3]
    if vi not in tri:continue
    a,b,c=tri;d1=[uv[b][j]-uv[a][j] for j in range(2)];d2=[uv[c][j]-uv[a][j] for j in range(2)];det=d1[0]*d2[1]-d2[0]*d1[1]
    if abs(det)<1e-14:continue
    v=[((ps[b][j]-ps[a][j])*d2[1]-(ps[c][j]-ps[a][j])*d1[1])/det for j in range(3)]
    dot=sum(v[j]*normal[j] for j in range(3));v=[v[j]-normal[j]*dot for j in range(3)];length=math.sqrt(sum(x*x for x in v))
    if length>1e-8:replacement=[x/length for x in v];break
   if replacement is None:raise RuntimeError(f'No valid triangle differential for tangent {vi}')
   struct.pack_into('<3f',raw,offset+vi*stride,*replacement);repairs.append({'vertex':vi,'tangent':replacement})
path.write_bytes(raw)
Path(globals().get('REPORT_PATH',ROOT/'output/tangent-repairs.json')).write_text(json.dumps({'count':len(repairs),'repairs':repairs},indent=2))
print('Export tangent repairs:',len(repairs))
