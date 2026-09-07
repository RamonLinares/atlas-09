import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
const revision=process.argv[2]||'36e67c0';
function read(b){const n=b.readUInt32LE(12);return {g:JSON.parse(b.subarray(20,20+n)),bin:b.subarray(n+28)};}
function bytes(a,index){const v=a.g.accessors[index],view=a.g.bufferViews[v.bufferView];const widths={SCALAR:1,VEC2:2,VEC3:3,VEC4:4,MAT4:16},sizes={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4};const start=(view.byteOffset||0)+(v.byteOffset||0);return a.bin.subarray(start,start+v.count*widths[v.type]*sizes[v.componentType]);}
const report=[];
for(const id of ['atlas-09','aether-02','seraph-03','ronin-04','scorpio-05']){
 const path=`public/models/${id}.glb`,oldBytes=execFileSync('git',['show',`${revision}:${path}`],{maxBuffer:30e6}),nowBytes=fs.readFileSync(path),old=read(oldBytes),now=read(nowBytes);
 if(id==='scorpio-05'&&!oldBytes.equals(nowBytes))throw Error('Scorpio changed');
 for(const field of ['meshes','nodes','skins','materials','textures','images'])if(JSON.stringify(old.g[field])!==JSON.stringify(now.g[field]))throw Error(`${id}: ${field} changed`);
 for(let i=0;i<old.g.accessors.length;i++)if(!bytes(old,i).equals(bytes(now,i)))throw Error(`${id}: existing accessor ${i} changed`);
 for(const clip of old.g.animations)if(JSON.stringify(clip)!==JSON.stringify(now.g.animations.find(a=>a.name===clip.name)))throw Error(`${id}: ${clip.name} changed`);
 report.push({id,geometryMaterialsRigPreserved:true,existingClipsPreserved:old.g.animations.map(a=>a.name),addedClips:now.g.animations.filter(a=>!old.g.animations.some(b=>b.name===a.name)).map(a=>a.name)});
}
fs.writeFileSync('output/motion/combat-preservation.json',JSON.stringify({revision,report},null,2)+'\n');console.log(JSON.stringify(report,null,2));
