import fs from 'node:fs/promises';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
const req=createRequire('C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1119-907-0_26.1119.907.0_x64__3k8sg7r9htsxt/dependencies/node/node_modules/__runtime__.cjs');
const {FileBlob,PresentationFile}=await import(pathToFileURL(req.resolve('@oai/artifact-tool')).href);
const src='C:/Users/Aman Kumar/Downloads/Presentation3 template.pptx';
const work='C:/Users/Aman Kumar/GIT/fixCampus/.report_work/pptx_build';
const out='C:/Users/Aman Kumar/GIT/fixCampus/output/pptx';
await fs.mkdir(work,{recursive:true}); await fs.mkdir(out,{recursive:true});
const pres=await PresentationFile.importPptx(await FileBlob.load(src));
const slides=Array.from({length:pres.slides.count},(_,i)=>pres.slides.getItem(i));
function setText(id,value,style={}){const s=pres.resolve(id);s.text=value;s.text.style={typeface:'Calibri',fontSize:style.fontSize??21,color:'#000000',alignment:style.alignment??'left',verticalAlignment:style.verticalAlignment??'top',autoFit:'shrinkText',wrap:'square',insets:{left:2,right:2,top:2,bottom:2},...(style.bold?{bold:true}:{})};}
function addText(slideIndex,name,value,pos,style={}){const shape=slides[slideIndex].shapes.add({geometry:'textbox',name,position:pos,fill:'none',line:{style:'solid',fill:'none',width:0}});shape.text=value;shape.text.style={typeface:'Calibri',fontSize:style.fontSize??21,color:style.color??'#000000',alignment:style.alignment??'left',verticalAlignment:style.verticalAlignment??'top',autoFit:'shrinkText',wrap:'square',insets:{left:2,right:2,top:2,bottom:2},...(style.bold?{bold:true}:{})};return shape;}
function bulletSlide(titleId,bodyId,title,items,size=22){setText(titleId,title,{fontSize:34,bold:true});setText(bodyId,items.join('\n\n'),{fontSize:size});}
// Cover: retain the original logo and 4:3 layout.
setText('sh/547294r6','CampusFix\nSmart Campus Issue Reporting and Management Platform\nMini Project BCS554 | 5th Semester',{fontSize:30,bold:true,alignment:'center',verticalAlignment:'middle'});
setText('sh/k3yl0zql','STUDENT NAME [UNIVERSITY ROLL NO]\n1. Aman Kumar — 2400320100155\n2. Aditya Shekhar — 2400320100088\n3. Abhishek Dubey — 2400320100047',{fontSize:20,alignment:'left'});
setText('sh/7qp4be9c','PROJECT SUPERVISOR\nMs. Yashi Rastogi\nDepartment of Computer Science & Engineering',{fontSize:20,alignment:'center'});
// Abstract, problem and literature.
bulletSlide('sh/9072xkry','sh/ove9o7yd','ABSTRACT',[
 'CampusFix gives students one place to report campus maintenance and service issues.',
 'Role-based dashboards support student tracking, staff work orders, and administrator triage.',
 'A FastAPI service stores ticket history and assignments; an ML model suggests issue categories.',
 'Students can earn points for eligible reports and feedback after resolution.',
 'The prototype is implemented and locally verified; campus-scale performance remains unmeasured.'
],22);
bulletSlide('sh/cza94vmx','sh/3ah8rqlg','PROBLEM STATEMENT & OBJECTIVES',[
 'Issue reports can be fragmented across calls, messages, and in-person requests.',
 'Students need status visibility; staff need accountable assignments; administrators need queue oversight.',
 'Provide a mobile-responsive student reporting and tracking experience.',
 'Give staff clear accept, update, reject, and resolve work-order actions.',
 'Give administrators category review, priority, dispatch, and operational metrics.',
 'Use ML only as a category suggestion, with a human reviewer retaining the decision.'
],21);
bulletSlide('sh/1cj2d8b6','sh/kbm987y5','RELATED WORK: TICKETS & TEXT CLASSIFICATION',[
 'Ticketing systems capture a request, route it to a team, record progress, and document closure.',
 'CampusFix uses a shared ticket lifecycle with role-specific queues and student-visible updates.',
 'Joachims (1998) describes support vector machines for sparse text categorization.',
 'Scikit-learn documents TF-IDF vectorization and supervised text-classification pipelines.',
 'CampusFix compares word and character n-grams with linear SVM and baseline classifiers.'
],21);
bulletSlide('sh/dgbulwnm','sh/w32dkbuh','RELATED WORK: ACCOUNT SECURITY',[
 'FastAPI documents OAuth2 bearer-token and JWT patterns for API authentication.',
 'OWASP password-recovery guidance recommends generic responses and expiring, single-use reset tokens.',
 'CampusFix uses password hashing, role and ownership checks, and session invalidation on password reset.',
 'These design references guide implementation; they do not replace an independent security audit.',
 'The current prototype still needs deployment hardening, retention policies, and campus security review.'
],21);
// Method and technology.
bulletSlide('sh/yhg7epsj','sh/87ipkzal','PROPOSED METHODOLOGY',[
 'Student submits a report with issue text and location; evidence is optional.',
 'FastAPI validates the request, creates a ticket and timeline event, and requests a category suggestion.',
 'Administrator reviews category and priority, then assigns a staff member.',
 'Staff accepts or rejects an assignment, updates progress, and records resolution notes.',
 'Student follows updates and may leave feedback; eligible actions create reward-ledger entries.',
 'ML output remains advisory and cannot close a ticket or determine emergency priority.'
],21);
bulletSlide('sh/cb2tkvap','sh/ydkbm5sv','TOOLS & TECHNOLOGIES',[
 'Frontend: React 19, Vite, responsive web interface.',
 'Backend: Python 3.11/3.12, FastAPI, SQLAlchemy, Alembic REST API.',
 'Database: SQLite for local development; PostgreSQL supported in container setup.',
 'Machine learning: scikit-learn text pipeline with TF-IDF character n-grams and LinearSVC.',
 'Developer tooling: Node.js 22, Git, VS Code or equivalent, Docker Compose option.',
 'Deployment needs: HTTPS, managed secrets, SMTP, monitoring, backups, and protected evidence storage.'
],21);
// Implementation snapshots: add screenshots while preserving the supplied ABES logo.
setText('sh/18byd4zy','STUDENT DASHBOARD',{fontSize:40,bold:true});
slides[7].shapes.items.filter(x=>x.id!=='sh/18byd4zy').forEach(x=>{try{x.delete()}catch{}});
setText('sh/1cfmhgne','STAFF DASHBOARD',{fontSize:40,bold:true});
slides[8].shapes.items.filter(x=>x.id!=='sh/1cfmhgne').forEach(x=>{try{x.delete()}catch{}});

setText('sh/xc3mho32','RESEARCH & IP STATUS',{fontSize:40,bold:true});
setText('sh/zelojyl8','Patent: not filed\nResearch paper: not submitted\nThe project evaluates established text-classification methods; it makes no novel algorithm claim.\nNext: prepare an independently reviewed study with campus data.',{fontSize:22});
setText('sh/xcryxg7y','MODEL RESULTS & VALIDATION',{fontSize:40,bold:true});
setText('sh/1gbm9s3a','CONCLUSION & FUTURE SCOPE',{fontSize:39,bold:true});
setText('sh/q50nydsj','REFERENCES',{fontSize:40,bold:true});
const shots=[
 {file:'C:/Users/Aman Kumar/OneDrive/Pictures/Screenshots/Screenshot 2026-11-20 113533.png',slide:7,alt:'CampusFix student dashboard',label:'Student dashboard'},
 {file:'C:/Users/Aman Kumar/OneDrive/Pictures/Screenshots/Screenshot 2026-11-20 113557.png',slide:8,alt:'CampusFix maintenance staff dashboard',label:'Maintenance staff dashboard'}
];
for(const im of shots){slides[im.slide].images.add({blob:new Uint8Array(await fs.readFile(im.file)),contentType:'image/png',alt:im.alt,fit:'contain',position:{left:95,top:205,width:770,height:370}});addText(im.slide,`${im.label} caption`,im.label,{left:96,top:584,width:768,height:32},{fontSize:18,bold:true,alignment:'center'});}
// Slide 10: administrator screen.

// Research/IP status.

// Results: editable chart and directly stated caveats.
setText('sh/n69grmpw','Character n-gram LinearSVC, selected\nAccuracy: 62.39% | Macro F1: 0.6532 | Weighted F1: 0.6214\n\nBaselines: Word n-gram SVM 51.82%; Logistic regression 51.64%; Naive Bayes 41.58%.\n\nTest: 2,196 records, grouped by issue template.\nLimitations: templated corpus; no IT test examples. These scores do not estimate live performance.\n22-case smoke check: 81.82% accuracy.',{fontSize:18});
slides[10].speakerNotes.text='Evaluation artifact: ml/reports/evaluation-20261119T193117Z.json. The corpus is templated. IT has zero test support on the saved grouped split, so aggregate scores do not demonstrate coverage of all categories. Robustness artifact: ml/reports/robustness-results.json (22 manually written diagnostic cases).';
// Conclusion / next steps.
bulletSlide('sh/1gbm9s3a','sh/wvupgz6t','CONCLUSION & FUTURE SCOPE',[
 'CampusFix provides one auditable issue workflow for students, staff, and administrators.',
 'Role dashboards, password recovery, reward points, and category suggestions are implemented.',
 'The selected character model outperformed tested baselines on the saved grouped holdout.',
 'Collect consented, de-identified, human-reviewed campus reports for representative evaluation.',
 'Add campus SSO, email and push notifications, facilities-system integration, and production monitoring.',
 'Complete accessibility, load, privacy, and independent security reviews before a live campus pilot.'
],20);
// References.
setText('sh/q50nydsj','REFERENCES',{fontSize:40,bold:true});
setText('sh/o3i5w3ad','[1] Joachims, “Text categorization with Support Vector Machines,” ECML, 1998. https://www.cs.cornell.edu/~tj/publications/joachims_98a.pdf\n\n[2] Scikit-learn, “Working with text data.” https://scikit-learn.org/stable/tutorial/text_analytics\n\n[3] FastAPI, “OAuth2 with Password and JWT.” https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/\n\n[4] OWASP, “Forgot Password Cheat Sheet.” https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html\n\n[5] CampusFix source code and ML evaluation artifacts, accessed November 2026.',{fontSize:14});
setText('sh/xc7eds76','THANK YOU',{fontSize:58,bold:true,alignment:'center',verticalAlignment:'middle'});
// Render all slides before export.
const previews=[];
for(let i=0;i<slides.length;i++){
 const b=await pres.export({slide:slides[i],format:'png',scale:.6});
 const f=`${work}/slide-${String(i+1).padStart(2,'0')}.png`; await fs.writeFile(f,new Uint8Array(await b.arrayBuffer()));previews.push(f);
}
const draft=`${work}/CampusFix_Synopsis_Presentation.draft.pptx`;
await (await PresentationFile.exportPptx(pres)).save(draft);
console.log(JSON.stringify({slides:slides.length,draft,previewDir:work,chartCount:slides[10].charts.items.length}));



