import fs from 'node:fs';
import { validateBytes } from 'gltf-validator';
const file='public/models/atlas-09.glb';
const bytes=fs.readFileSync(file);
const report=await validateBytes(new Uint8Array(bytes),{uri:file,maxIssues:100});
fs.writeFileSync('output/gltf-validation.json',JSON.stringify(report,null,2));
console.log(JSON.stringify({bytes:bytes.length,errors:report.issues.numErrors,warnings:report.issues.numWarnings,infos:report.issues.numInfos,messages:report.issues.messages},null,2));
if(report.issues.numErrors)process.exitCode=1;
