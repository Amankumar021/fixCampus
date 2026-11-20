import fs from 'node:fs/promises';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
const req=createRequire('C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1119-907-0_26.1119.907.0_x64__3k8sg7r9htsxt/dependencies/node/node_modules/__runtime__.cjs');
const tool=await import(pathToFileURL(req.resolve('@oai/artifact-tool')).href); const {FileBlob,PresentationFile}=tool;
const src='C:/Users/Aman Kumar/Downloads/Presentation3 template.pptx', out='.report_work/pptx_template_inspect';
const p=await PresentationFile.importPptx(await FileBlob.load(src));
console.log('slideCount',p.slides.count,'size',p.slides.getItem(0).size);
await fs.mkdir(out,{recursive:true});
for(let i=0;i<p.slides.count;i++){
 const slide=p.slides.getItem(i); const b=await p.export({slide,format:'png',scale:.65});
 await fs.writeFile(`${out}/slide-${String(i+1).padStart(2,'0')}.png`,new Uint8Array(await b.arrayBuffer()));
}
const x=await p.inspect({kind:'slide,textbox,shape,image,table,chart',maxChars:120000}); await fs.writeFile(`${out}/inspect.ndjson`,x.ndjson||'');
