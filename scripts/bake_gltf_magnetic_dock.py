"""Resolve the magnetic constraint against the GLB player's quaternion interpolation."""
import json,struct,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from retarget_library import MotionSource
path=ROOT/'public/models/ronin-04.glb';source=MotionSource(path);g=source.doc
animation=next(a for a in g['animations'] if a['name']=='PunchCombo')
node=source.names['sword.R'];parent_name=g['nodes'][source.parents[node]]['name']
pose=source.sample('PunchCombo',2.4);attachment=pose['chest'].inverted()@pose['sword.R']
channels=[c for c in animation['channels'] if c['target']['node']==node and c['target']['path'] in ['rotation','translation']]
times={round(x[0],7) for c in channels for x in source.values(animation['samplers'][c['sampler']]['input'])}
times.update(i/240 for i in range(576,2257))
# Deduplicate at the actual float32 precision of glTF input accessors.
times=sorted({struct.unpack("<f",struct.pack("<f",t))[0] for t in times})
translations=[];rotations=[];previous=None
for t in times:
    pose=source.sample('PunchCombo',t)
    world=pose['chest']@attachment if 2.4-1e-7<=t<=9.4+1e-7 else pose['sword.R']
    local=pose[parent_name].inverted()@world;p,q,scale=local.decompose()
    if previous is not None and previous.dot(q)<0:q.negate()
    previous=q.copy();translations.append(tuple(p));rotations.append((q.x,q.y,q.z,q.w))
binary=bytearray(source.blob)
def accessor(values,kind):
    flat=[v for row in values for v in row];offset=len(binary);binary.extend(struct.pack('<'+'f'*len(flat),*flat))
    view=len(g['bufferViews']);g['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(flat)*4})
    index=len(g['accessors']);a={'bufferView':view,'componentType':5126,'count':len(values),'type':kind}
    if kind=='SCALAR':a.update(min=[min(flat)],max=[max(flat)])
    g['accessors'].append(a);return index
input_index=accessor([(t,) for t in times],'SCALAR')
for channel in channels:
    kind=channel['target']['path'];output=accessor(rotations if kind=='rotation' else translations,'VEC4' if kind=='rotation' else 'VEC3')
    channel['sampler']=len(animation['samplers']);animation['samplers'].append({'input':input_index,'output':output,'interpolation':'LINEAR'})
g['buffers'][0]['byteLength']=len(binary)
encoded=json.dumps(g,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4)
path.write_bytes(struct.pack('<III',0x46546C67,2,28+len(encoded)+len(binary))+struct.pack('<II',len(encoded),0x4E4F534A)+encoded+struct.pack('<II',len(binary),0x004E4942)+binary)
report={'constraint':'sword.R to chest during magnetic docking','sampling_hz':240,'keys':len(times),'start_s':2.4,'end_s':9.4}
(ROOT/'output/ronin-04/gltf-magnetic-dock.json').write_text(json.dumps(report,indent=2));print(report)
