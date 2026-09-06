// Compare the pre-update delivery to current assets; the motion import must
// preserve geometry, skin weights, UVs and the four retained clip values.
import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
const revision=process.argv[2] || 'HEAD';
function read(buffer){const n=buffer.readUInt32LE(12);return {doc:JSON.parse(buffer.subarray(20,20+n)),bin:buffer.subarray(n+28)};}
function bytes(asset,id){const a=asset.doc.accessors[id],v=asset.doc.bufferViews[a.bufferView],sizes={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4},widths={SCALAR:1,VEC2:2,VEC3:3,VEC4:4,MAT4:16};if(v.byteStride)throw Error('Unexpected stride');const at=(v.byteOffset||0)+(a.byteOffset||0);return asset.bin.subarray(at,at+a.count*sizes[a.componentType]*widths[a.type]);}
const reports=[];
for(const id of ['aether-02','atlas-09']){
 const path=`public/models/${id}.glb`,old=read(execFileSync('git',['show',`${revision}:${path}`],{maxBuffer:20e6})),now=read(fs.readFileSync(path));let attributes=0,channels=0;
 const check=(a,b,label)=>{if(!a.equals(b))throw Error(`${id}: changed ${label}`)};
 old.doc.meshes[0].primitives.forEach((p,i)=>{
  const n=now.doc.meshes[0].primitives[i];check(bytes(old,p.indices),bytes(now,n.indices),'triangle indices');
  for(const key of Object.keys(p.attributes)){check(bytes(old,p.attributes[key]),bytes(now,n.attributes[key]),key);attributes++;}
 });
 for(const name of ['Sentinel','Run','KneelFire','Backflip']){
  const a=old.doc.animations.find(a=>a.name===name),b=now.doc.animations.find(a=>a.name===name);
  for(const c of a.channels){const node=old.doc.nodes[c.target.node].name,path=c.target.path;const d=b.channels.find(d=>now.doc.nodes[d.target.node].name===node&&d.target.path===path);if(!d)throw Error('Missing retained track');
   for(const key of ['input','output'])check(bytes(old,a.samplers[c.sampler][key]),bytes(now,b.samplers[d.sampler][key]),`${name}:${node}:${path}:${key}`);channels++;
  }
 }
 reports.push({asset:id,meshAttributesUnchanged:attributes,retainedAnimationChannelsUnchanged:channels});
}
fs.writeFileSync('output/motion/preserved-assets-validation.json',JSON.stringify({revision,reports},null,2)+'\n');console.log(JSON.stringify(reports,null,2));
