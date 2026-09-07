"""Append animation tracks while preserving the delivered geometry and clips."""
import copy,json,struct
from pathlib import Path

def read(path):
    data=Path(path).read_bytes();size=struct.unpack_from('<I',data,12)[0]
    return json.loads(data[20:20+size]),bytearray(data[28+size:])

def append_animations(destination,source,names):
    dst,binary=read(destination);src,blob=read(source)
    nodes={n['name']:i for i,n in enumerate(dst['nodes']) if 'name' in n}
    selected=[a for a in src['animations'] if a['name'] in names]
    assert {a['name'] for a in selected}==set(names)
    used={c['target']['node'] for a in selected for c in a['channels']}
    for i in used:
        n=src['nodes'][i];old=dst['nodes'][nodes[n['name']]]
        for key,default in [('translation',[0,0,0]),('rotation',[0,0,0,1]),('scale',[1,1,1])]:
            a=n.get(key,default);b=old.get(key,default)
            error=min(max(abs(x-y) for x,y in zip(a,b)),max(abs(x+y) for x,y in zip(a,b))) if key=='rotation' else max(abs(x-y) for x,y in zip(a,b))
            assert error<1e-4,(n['name'],key,a,b)
    remap={}
    def accessor(index):
        if index in remap:return remap[index]
        a=copy.deepcopy(src['accessors'][index]);v=src['bufferViews'][a['bufferView']]
        assert 'byteStride' not in v and a['componentType']==5126 and 'sparse' not in a
        width={'SCALAR':1,'VEC3':3,'VEC4':4}[a['type']]
        offset=v.get('byteOffset',0)+a.pop('byteOffset',0);size=a['count']*width*4
        a['bufferView']=len(dst['bufferViews'])
        dst['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':size})
        binary.extend(blob[offset:offset+size]);remap[index]=len(dst['accessors']);dst['accessors'].append(a)
        return remap[index]
    dst['animations']=[a for a in dst['animations'] if a['name'] not in names]
    for a in selected:
        a=copy.deepcopy(a)
        for s in a['samplers']:
            for key in ['input','output']:s[key]=accessor(s[key])
        for c in a['channels']:c['target']['node']=nodes[src['nodes'][c['target']['node']]['name']]
        dst['animations'].append(a)
    dst['buffers'][0]['byteLength']=len(binary)
    encoded=json.dumps(dst,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4)
    Path(destination).write_bytes(struct.pack('<III',0x46546c67,2,28+len(encoded)+len(binary))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(binary),0x004e4942)+binary)
    return {'added_clips':list(names),'preserved_mesh_and_existing_tracks':True}
