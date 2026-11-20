from pathlib import Path
import json, math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output'/'papers'
OUT.mkdir(parents=True,exist_ok=True)
eval_data=json.loads((ROOT/'ml/reports/evaluation-20261119T193117Z.json').read_text(encoding='utf-8'))
robust=json.loads((ROOT/'ml/reports/robustness-results.json').read_text(encoding='utf-8'))
models=[('Word n-gram LinearSVC','linear_svc_word'),('Character n-gram LinearSVC','linear_svc_char'),('Logistic regression','logistic_regression'),('Multinomial Naive Bayes','multinomial_nb')]

# Measured metric comparison figure
fig,ax=plt.subplots(figsize=(7.0,3.3))
x=list(range(4)); w=.34
acc=[eval_data['metrics'][k]['accuracy']*100 for _,k in models]
macro=[eval_data['metrics'][k]['macro_f1']*100 for _,k in models]
ax.bar([i-w/2 for i in x],acc,w,label='Accuracy',color='#4F81BD')
ax.bar([i+w/2 for i in x],macro,w,label='Macro F1',color='#70AD47')
ax.set_ylabel('Score (%)');ax.set_ylim(0,75);ax.set_xticks(x,[m[0] for m in models],rotation=14,ha='right',fontsize=8)
ax.grid(axis='y',alpha=.2);ax.legend(frameon=False,ncol=2,loc='upper right');fig.tight_layout()
chart=ROOT/'.report_work'/'research_metrics.png';fig.savefig(chart,dpi=180,bbox_inches='tight');plt.close(fig)

doc=Document(); sec=doc.sections[0]
sec.top_margin=Inches(.78);sec.bottom_margin=Inches(.72);sec.left_margin=Inches(.86);sec.right_margin=Inches(.86)
styles=doc.styles
styles['Normal'].font.name='Arial';styles['Normal']._element.rPr.rFonts.set(qn('w:eastAsia'),'Arial');styles['Normal'].font.size=Pt(10.2);styles['Normal'].font.color.rgb=RGBColor(36,45,43)
styles['Normal'].paragraph_format.space_after=Pt(6);styles['Normal'].paragraph_format.line_spacing=1.12
for name,size,color in [('Heading 1',15,'174D40'),('Heading 2',12,'17755E'),('Heading 3',10.5,'263A35')]:
 st=styles[name];st.font.name='Arial';st._element.rPr.rFonts.set(qn('w:eastAsia'),'Arial');st.font.size=Pt(size);st.font.bold=True;st.font.color.rgb=RGBColor.from_string(color);st.paragraph_format.space_before=Pt(12);st.paragraph_format.space_after=Pt(5);st.paragraph_format.keep_with_next=True
styles['Title'].font.name='Arial';styles['Title']._element.rPr.rFonts.set(qn('w:eastAsia'),'Arial');styles['Title'].font.size=Pt(23);styles['Title'].font.bold=True;styles['Title'].font.color.rgb=RGBColor(24,60,53);styles['Title'].paragraph_format.space_after=Pt(7)
# Header / page footer
header=sec.header.paragraphs[0];header.alignment=WD_ALIGN_PARAGRAPH.RIGHT
r=header.add_run('CAMPUSFIX  |  RESEARCH PAPER');r.font.name='Arial';r.font.size=Pt(8);r.font.bold=True;r.font.color.rgb=RGBColor(15,108,89)
footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
rr=footer.add_run('Department of Computer Science & Engineering  •  ');rr.font.size=Pt(8);rr.font.color.rgb=RGBColor(92,105,102)
fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');footer._p.append(fld)

def shade(cell,fill):
 tcPr=cell._tc.get_or_add_tcPr();shd=OxmlElement('w:shd');shd.set(qn('w:fill'),fill);tcPr.append(shd)
def set_cell_text(cell,text,bold=False,color='263A35',size=8.5):
 cell.text='';p=cell.paragraphs[0];p.paragraph_format.space_after=Pt(0)
 r=p.add_run(str(text));r.bold=bold;r.font.name='Arial';r.font.size=Pt(size);r.font.color.rgb=RGBColor.from_string(color)
 cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER

def table(headers,rows,widths=None,font=8.5):
 t=doc.add_table(rows=1,cols=len(headers));t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.style='Table Grid';t.autofit=False
 if widths:
  for c,wid in zip(t.columns,widths):c.width=Inches(wid)
 for i,h in enumerate(headers):set_cell_text(t.rows[0].cells[i],h,True,'FFFFFF',font);shade(t.rows[0].cells[i],'174D40')
 for ri,row in enumerate(rows):
  cells=t.add_row().cells
  if widths:
   for c,wid in zip(cells,widths):c.width=Inches(wid)
  for ci,val in enumerate(row):
   set_cell_text(cells[ci],val,False,'263A35',font)
   if ri%2==1:shade(cells[ci],'F1F5F3')
 doc.add_paragraph().paragraph_format.space_after=Pt(1)
 return t

def para(text,italic=False,bold_prefix=None):
 p=doc.add_paragraph()
 if bold_prefix and text.startswith(bold_prefix):
  p.add_run(bold_prefix).bold=True;p.add_run(text[len(bold_prefix):])
 else:
  r=p.add_run(text);r.italic=italic
 return p

def bullet(text):
 p=doc.add_paragraph(style='List Bullet');p.paragraph_format.space_after=Pt(3);p.add_run(text);return p

# Title block
p=doc.add_paragraph(style='Title');p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.add_run('CampusFix: A Role-Based Smart Campus Issue Management Platform with Advisory Text Classification')
p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.space_after=Pt(4)
r=p.add_run('Aman Kumar¹, Aditya Shekhar¹, Abhishek Dubey¹, Aaryan Pandey¹, Aditya Kumar¹');r.bold=True;r.font.size=Pt(10.5)
p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.space_after=Pt(10)
r=p.add_run('¹Department of Computer Science & Engineering, ABES Engineering College, Ghaziabad, India\nProject supervisor: Ms. Yashi Rastogi');r.font.size=Pt(9);r.font.color.rgb=RGBColor(78,91,87)

# Abstract panel
p=doc.add_paragraph();p.paragraph_format.space_before=Pt(3);p.paragraph_format.space_after=Pt(3)
r=p.add_run('Abstract');r.bold=True;r.font.size=Pt(11);r.font.color.rgb=RGBColor(15,108,89)
abstract=('Campus maintenance concerns are often reported through disconnected channels, leaving students uncertain about progress and operations teams without a shared, auditable queue. This paper presents CampusFix, a full-stack campus issue-management prototype that connects student reports, staff work orders, administrator triage, status history, resolution feedback, and student reward points. A text classifier suggests complaint categories while leaving category confirmation and operational decisions to authorized users. Four TF-IDF classifier pipelines were evaluated on 10,430 exact-deduplicated complaint records using a GroupShuffleSplit grouped by issue-template identifier (8,234 training and 2,196 test records). Character n-gram LinearSVC achieved the highest measured accuracy (62.39%), macro F1 (0.6532), and weighted F1 (0.6214). The result is preliminary: the corpus contains templated examples and the grouped test partition has zero IT examples. A separate 22-case hand-written diagnostic yielded 81.82% accuracy, but is too small to estimate deployment performance. The system therefore treats machine learning as routing assistance and requires evaluation on independently collected, human-reviewed campus reports before operational deployment.')
p=doc.add_paragraph(abstract);p.paragraph_format.left_indent=Inches(.18);p.paragraph_format.right_indent=Inches(.18);p.paragraph_format.space_after=Pt(5)
p=doc.add_paragraph();p.paragraph_format.left_indent=Inches(.18);p.paragraph_format.right_indent=Inches(.18);p.paragraph_format.space_after=Pt(9)
r=p.add_run('Keywords: ');r.bold=True;r.font.color.rgb=RGBColor(15,108,89);p.add_run('campus issue management, maintenance ticketing, text classification, TF-IDF, LinearSVC, role-based workflow')

# Paper

doc.add_heading('1. Introduction',level=1)
para('Campus maintenance requests can arrive through calls, informal messages, paper forms, or in-person conversations. When each channel is tracked separately, a student may not know whether a report was recorded, staff may receive duplicate requests, and administrators may lack a consistent view of status and workload. A shared ticket workflow can make the report, assignment, progress updates, and resolution visible in one record.')
para('CampusFix addresses this coordination problem with role-specific student, maintenance staff, and administrator workspaces. Its student flow records an issue and location, exposes a status timeline, and supports resolution feedback. Staff receive assigned work orders and can update their state. Administrators review suggested categories, set operational priority, assign work, and monitor queue metrics. Student reward points are attached to eligible reports and feedback as a participation mechanism; the paper makes no claim that rewards improve reporting behavior, since that effect has not been measured.')
para('The paper makes three bounded contributions: (1) a description of an implemented role-based reporting and work-order prototype; (2) a reproducible comparison of four classical text-classification pipelines on a grouped, template-based corpus; and (3) an explicit account of evaluation gaps that must be closed before a campus pilot. The measured results are corpus results, not estimates of live campus performance.')

doc.add_heading('2. Related Work',level=1)
para('Text categorization maps documents to predefined classes. Joachims described support vector machines for text categorization with many relevant features, motivating linear margin-based classifiers for sparse text representations [1]. TF-IDF provides a conventional way to weight terms by their occurrence in a document relative to a corpus, and the scikit-learn text analytics guide documents vectorization and classifier pipelines for text [2]. Character n-grams can represent short substrings across word boundaries, which may help with spelling variation, abbreviations, or morphology; their value for this application must be determined empirically rather than assumed.')
para('A ticketing workflow also depends on access control and explicit state changes. CampusFix uses a browser frontend and a REST API with role-aware routes. Its authentication and password-recovery implementation follows common framework patterns and project-specific controls, but the current work is not a security evaluation. The design preserves a human review step because category suggestions can be wrong and are not a substitute for staff assessment.')

doc.add_heading('3. System Design and Implementation',level=1)
doc.add_heading('3.1 Application architecture',level=2)
para('The client is implemented with React and Vite. The API uses FastAPI, SQLAlchemy, and Alembic, with SQLite for local development and PostgreSQL supported by the container setup. The API persists users, complaints, assignment records, timeline events, feedback, and reward transactions. A complaint submission combines title and description for category inference, stores both the suggested category and confidence signal, and then applies the selected category or uses a fallback when the prediction is not considered confident. The model suggestion does not itself resolve a ticket or determine its priority.')
doc.add_heading('3.2 Workflow',level=2)
for x in [
 'A student submits a campus issue with descriptive text and a location; evidence may be attached.',
 'The API validates the request, creates a ticket and timeline entry, and obtains a category suggestion.',
 'An administrator reviews the issue and assigns it to an appropriate staff member.',
 'Assigned staff accept or reject the work, update progress, and record resolution details.',
 'The student follows the status history and may submit feedback after resolution.',
 'Eligible actions create reward-ledger entries; administrators review queue and service metrics.'
]:bullet(x)
doc.add_heading('3.3 Reward mechanism',level=2)
para('The current implementation awards 10 points for an eligible new issue report and 5 points for eligible resolution feedback. Duplicate reports do not receive an issue-report award, and a configurable daily issue-reward limit defaults to 30 points in a 24-hour period. The student dashboard displays a milestone every 50 points. These are implementation rules, not experimentally established incentives or behavior-change outcomes.')

doc.add_heading('4. Machine-Learning Method',level=1)
doc.add_heading('4.1 Dataset',level=2)
para('The repository dataset contains complaint text, location, category, and issue-template identifier fields. The raw file contains 10,800 records, with 1,200 records per each of nine categories. After removing exact duplicate complaint strings, 10,430 records remain. The categories are Cafeteria, Civil Maintenance, Cleanliness, Electrical, Furniture, IT, Plumbing, Sanitation, and Security. The records are templated or synthetic in character; no independently collected, consented campus holdout is present in this evaluation artifact.')
para('The dataset SHA-256 recorded in the evaluation report is '+eval_data['dataset_sha256']+'. Deduplication is performed on complaint text. A single GroupShuffleSplit uses issue_template as the group, random state 42, and a nominal test size of 0.2. The realized split contains 8,234 training records and 2,196 test records. Grouping is intended to reduce leakage from related template variants, but the resulting partition is not class-stratified and has zero IT test support. It therefore cannot validate performance for all nine categories.')
doc.add_heading('4.2 Feature and classifier pipelines',level=2)
para('Four saved scikit-learn pipelines were compared. The word models use TfidfVectorizer with word unigrams and bigrams, minimum document frequency 2, maximum document-frequency ratio 0.98, Unicode accent stripping, and sublinear term frequency. The selected character model uses TfidfVectorizer with analyzer char_wb, character n-grams from length 2 through 5, minimum document frequency 2, a 400,000-feature cap, and sublinear term frequency. LinearSVC uses C=1.0 and balanced class weights. Logistic regression uses C=4.0, a maximum of 2,000 iterations, and balanced class weights. Multinomial Naive Bayes uses alpha=0.1. Accuracy, macro F1, and weighted F1 are reported on the same saved holdout.')
para('The model-selection rule in the training code selects the candidate with the highest macro F1, then refits that model on all deduplicated records for the active inference artifact. The metrics below describe the earlier held-out predictions, not the refitted production artifact.')

doc.add_heading('5. Results',level=1)
rows=[]
for label,key in models:
 m=eval_data['metrics'][key]
 rows.append((label,f"{m['accuracy']*100:.2f}%",f"{m['macro_f1']:.4f}",f"{m['weighted_f1']:.4f}"))
table(['Classifier','Accuracy','Macro F1','Weighted F1'],rows,[2.75,1.05,1.0,1.15],8.3)
para('Character n-gram LinearSVC is the strongest of the four recorded candidates on accuracy, macro F1, and weighted F1. Its accuracy exceeds the word n-gram LinearSVC result by 10.56 percentage points on this split. Macro F1 (0.6532) is higher than weighted F1 (0.6214), reflecting the fact that per-class performance is uneven and the two metrics weight classes differently. The numerical advantage supports using this candidate for further study, not claiming generalization to live reports.')
p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.space_after=Pt(1)
p.add_run().add_picture(str(chart),width=Inches(6.2))
p=doc.add_paragraph('Figure 1. Accuracy and macro F1 from the saved grouped holdout evaluation.');p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.space_after=Pt(8)
# Selected per-class reporting with zero-support made explicit
char=eval_data['metrics']['linear_svc_char']['classification_report']
perclass=[]
for c in eval_data['classes']:
 v=char.get(c,{'precision':0,'recall':0,'f1-score':0,'support':0})
 perclass.append((c,str(int(v['support'])),f"{v['precision']:.3f}",f"{v['recall']:.3f}",f"{v['f1-score']:.3f}"))
table(['Category','Test support','Precision','Recall','F1'],perclass,[1.65,1.15,1.0,.9,.8],8.0)
para('The selected model has zero test support for IT, so no IT-specific precision, recall, or F1 can be estimated from this split. Civil Maintenance recall is 0.404 and Security recall is 0.488, despite precision of 1.000 for both labels. Such a pattern means that predictions for those categories were selective and missed many actual examples. A routing interface should make human review easy and should not silently treat the aggregate score as evidence of uniform category quality.')

doc.add_heading('6. Robustness Diagnostic',level=1)
para(f"A separate hand-written diagnostic contains {robust['cases']} cases, including {robust['known_category_cases']} cases with known categories. Overall accuracy across the full set is {robust['classification_report']['accuracy']*100:.2f}%; accuracy among known-category cases is {robust['known_category_accuracy']*100:.2f}% and macro F1 for that subset is {robust['known_category_macro_f1']:.4f}. This small set is a smoke check for selected examples. Its size and hand-authored construction do not support a population-level performance estimate or a deployment claim.")

doc.add_heading('7. Discussion and Limitations',level=1)
para('The results show that character n-gram features improved the recorded holdout scores relative to the word n-gram baseline. A plausible explanation is that character features capture substrings in short and variable complaint text. This interpretation is consistent with the feature design, but the experiment does not isolate the cause of the improvement or establish that it will persist on naturally written campus reports.')
for x in [
 'The dataset may contain synthetic templates and is not a representative, consented sample of campus reports.',
 'Template grouping reduces a specific leakage risk but yielded zero IT test examples; coverage across all categories is therefore unverified.',
 'Only one grouped random split is reported. The paper does not provide confidence intervals, repeated cross-validation, or a prospective temporal evaluation.',
 'The 22-case diagnostic is small and manually written; it is not an independent test cohort.',
 'No production load, accessibility certification, independent security audit, or live-campus workflow outcome is measured.',
 'The reward mechanism is implemented, but no causal or survey study has evaluated its effect on student participation.'
]:bullet(x)
para('These limitations matter to how the classifier should be used. It is an advisory routing signal, with staff or administrators retaining category review. Future acceptance work should collect de-identified reports with consent and institutional review, define category labels and adjudication rules, ensure category coverage in grouped and temporal splits, measure calibration and per-class error, and set operational thresholds with campus stakeholders. Production readiness also requires monitored deployment, privacy and retention controls, access reviews, backups, and incident procedures.')

doc.add_heading('8. Conclusion',level=1)
para('CampusFix implements a shared campus issue workflow spanning student reporting, staff assignments, administrator triage, visible ticket history, feedback, and reward accounting. The saved classifier comparison selected character n-gram LinearSVC, which achieved 62.39% accuracy and 0.6532 macro F1 on one issue-template-grouped holdout. Because that holdout is based on templated data and includes no IT examples, the result is preliminary and cannot support a claim of real-campus accuracy. The next research step is a governed evaluation on representative, human-reviewed campus data, accompanied by operational and security testing. Until then, category output should remain advisory.')

doc.add_heading('References',level=1)
refs=[
 '[1] T. Joachims, “Text categorization with support vector machines: Learning with many relevant features,” in Proceedings of the 10th European Conference on Machine Learning (ECML), pp. 137–142, 1998. https://www.cs.cornell.edu/~tj/publications/joachims_98a.pdf',
 '[2] Scikit-learn Developers, “Working with text data,” Scikit-learn User Guide. https://scikit-learn.org/stable/tutorial/text_analytics/working_with_text_data.html',
 '[3] FastAPI Contributors, “OAuth2 with Password (and hashing), Bearer with JWT tokens,” FastAPI Documentation. https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/',
 '[4] OWASP Foundation, “Forgot Password Cheat Sheet.” https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html',
 '[5] CampusFix project artifacts, application source, complaint dataset, evaluation report evaluation-20261119T193117Z.json, robustness-results.json, and model manifest, accessed November 2026.'
]
for ref in refs:
 p=doc.add_paragraph();p.paragraph_format.left_indent=Inches(.22);p.paragraph_format.first_line_indent=Inches(-.22);p.paragraph_format.space_after=Pt(6);p.add_run(ref).font.size=Pt(9)

# Core metadata
props=doc.core_properties;props.title='CampusFix: A Role-Based Smart Campus Issue Management Platform with Advisory Text Classification';props.subject='System design and preliminary machine-learning evaluation';props.author='Aman Kumar; Aditya Shekhar; Abhishek Dubey; Aaryan Pandey; Aditya Kumar';props.keywords='CampusFix, campus issue management, text classification, LinearSVC'
path=OUT/'CampusFix_Research_Paper.docx';doc.save(path);print(path)

