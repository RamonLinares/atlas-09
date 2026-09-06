"""Keep only licensed skeletons and selected motion data from the free CC0 packs."""
import json, struct, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'assets/animations/quaternius'
report=[]
for library,names in [(1,['Walk_Loop','Punch_Jab','Punch_Cross','Death01']),(2,['Melee_Hook','Melee_Hook_Rec'])]:
 path=P/f'UAL{library}_Standard.glb';raw=path.read_bytes()
 length=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+length]);binary=raw[28+length:]
 chosen=[a for a in doc['animations'] if a['name'] in names]
 needed=sorted({s[k] for a in chosen for s in a['samplers'] for k in ['input','output']})
 accessors=[];views=[];blob=bytearray();mapping={}
 for old in needed:
  a=doc['accessors'][old].copy();view=doc['bufferViews'][a['bufferView']]
  assert 'byteStride' not in view and 'sparse' not in a
  count={'SCALAR':1,'VEC3':3,'VEC4':4}[a['type']];assert a['componentType']==5126
  start=view.get('byteOffset',0)+a.pop('byteOffset',0);n=a['count']*count*4
  views.append({'buffer':0,'byteOffset':len(blob),'byteLength':n});blob.extend(binary[start:start+n]);a['bufferView']=len(views)-1
  mapping[old]=len(accessors);accessors.append(a)
 for a in chosen:
  for s in a['samplers']:
   for k in ['input','output']:s[k]=mapping[s[k]]
 nodes=[{k:v for k,v in n.items() if k in ['name','children','translation','rotation','scale','matrix']} for n in doc['nodes']]
 out={'asset':{'version':'2.0','generator':'FORGE CC0 motion subset; original Quaternius / Gonzalo Furnier'},'scene':doc.get('scene',0),'scenes':doc['scenes'],'nodes':nodes,'animations':chosen,'accessors':accessors,'bufferViews':views,'buffers':[{'byteLength':len(blob)}]}
 j=json.dumps(out,separators=(',',':')).encode();j+=b' '*((-len(j))%4)
 data=struct.pack('<III',0x46546c67,2,28+len(j)+len(blob))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(blob),0x004e4942)+blob
 target=P/f'UAL{library}_selected.glb';target.write_bytes(data)
 report.append({'library':library,'source_page':'https://quaternius.itch.io/universal-animation-library'+('-2' if library==2 else ''),'original_sha256':hashlib.sha256(raw).hexdigest(),'original_bytes':len(raw),'subset':target.name,'subset_sha256':hashlib.sha256(data).hexdigest(),'clips':names,'license':'CC0-1.0','downloaded':'2026-09-06','price_paid_usd':0})
(P/'provenance.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
