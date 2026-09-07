"""Start every exported clip at zero without discarding subframe keys."""
import json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
path=globals().get('ASSET_PATH',ROOT/'public/models/ronin-04.glb')
report_path=globals().get('REPORT_PATH',ROOT/'output/ronin-04/animation-time-normalization.json')
data=Path(path).read_bytes();json_length=struct.unpack_from('<I',data,12)[0]
gltf=json.loads(data[20:20+json_length]);binary=bytearray(data[28+json_length:])
def times(accessor_id):
    a=gltf['accessors'][accessor_id];v=gltf['bufferViews'][a['bufferView']]
    assert a['componentType']==5126 and a['type']=='SCALAR' and not v.get('byteStride')
    offset=v.get('byteOffset',0)+a.get('byteOffset',0)
    return a,offset,list(struct.unpack_from('<'+'f'*a['count'],binary,offset))
plan={};reports=[]
for animation in gltf.get('animations',[]):
    ids={s['input'] for s in animation['samplers']}
    start=min(times(i)[2][0] for i in ids)
    reports.append({'clip':animation['name'],'removed_leading_seconds':start})
    for i in ids:
        if i in plan:assert abs(plan[i]-start)<1e-7
        plan[i]=start
for i,start in plan.items():
    a,offset,values=times(i);values=[max(0,t-start) for t in values]
    struct.pack_into('<'+'f'*len(values),binary,offset,*values)
    a['min']=[min(values)];a['max']=[max(values)]
encoded=json.dumps(gltf,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4)
result=struct.pack('<III',0x46546C67,2,28+len(encoded)+len(binary))+struct.pack('<II',len(encoded),0x4E4F534A)+encoded+struct.pack('<II',len(binary),0x004E4942)+binary
Path(path).write_bytes(result);Path(report_path).write_text(json.dumps(reports,indent=2))
print('Normalized animation starts:',len(reports))
