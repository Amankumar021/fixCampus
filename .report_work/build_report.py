from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image, ImageDraw, ImageFont
import math

ROOT=Path(__file__).resolve().parents[1]; WORK=ROOT/'.report_work'
OUT=ROOT/'CampusFix_Project_Report_with_Dashboards.docx'
COVER=Path(r'C:\Users\Aman Kumar\Downloads\Cover Page_CSE.docx')
REG=r'C:\Windows\Fonts\arial.ttf'; BOLD=r'C:\Windows\Fonts\arialbd.ttf'

def pilfont(path,size): return ImageFont.truetype(path,size)
def centered(draw,xy,text,f,fill):
    x,y=xy; box=draw.multiline_textbbox((0,0),text,font=f,align='center',spacing=8)
    draw.multiline_text((x-(box[2]-box[0])/2,y-(box[3]-box[1])/2),text,font=f,fill=fill,align='center',spacing=8)
def box(draw,coords,title,body):
    x1,y1,x2,y2=coords; draw.rounded_rectangle(coords,radius=22,fill='#F3F7FA',outline='#234A63',width=4)
    centered(draw,((x1+x2)//2,y1+52),title,pilfont(BOLD,30),'#173B53')
    centered(draw,((x1+x2)//2,(y1+y2)//2+34),body,pilfont(REG,24),'#243746')
def arrow(draw,start,end,label=''):
    draw.line([start,end],fill='#4B6F83',width=7); a=math.atan2(end[1]-start[1],end[0]-start[0]); l=22
    p1=(end[0]-l*math.cos(a-.45),end[1]-l*math.sin(a-.45)); p2=(end[0]-l*math.cos(a+.45),end[1]-l*math.sin(a+.45))
    draw.polygon([end,p1,p2],fill='#4B6F83')
    if label: centered(draw,((start[0]+end[0])//2,(start[1]+end[1])//2-24),label,pilfont(REG,20),'#435B6B')
def make_arch(path):
    im=Image.new('RGB',(1800,820),'white'); d=ImageDraw.Draw(im); d.text((60,32),'CampusFix application architecture',font=pilfont(BOLD,38),fill='#173B53')
    b=[(45,235,335,580),(405,235,710,580),(790,205,1180,610),(1370,75,1750,350),(1370,470,1750,745)]
    box(d,b[0],'Campus users','Student\nStaff\nAdministrator'); box(d,b[1],'React client','Responsive UI\nTicket tracking\nRole dashboards')
    box(d,b[2],'FastAPI services','Authentication and RBAC\nComplaint workflow\nRewards and analytics')
    box(d,b[3],'Relational database','Users, complaints,\nassignments, events,\nfeedback and rewards')
    box(d,b[4],'Text classifier','TF-IDF character features\nLinear SVM suggestion\nHuman review remains final')
    arrow(d,(335,405),(405,405),'HTTPS / JSON'); arrow(d,(710,405),(790,405),'REST API')
    arrow(d,(1180,320),(1370,230),'SQLAlchemy'); arrow(d,(1180,510),(1370,600),'predict'); arrow(d,(1370,640),(1180,580),'suggestion')
    im.save(path,dpi=(220,220))
def make_erd(path):
    im=Image.new('RGB',(1800,980),'white'); d=ImageDraw.Draw(im); d.text((55,28),'Core entities and relationships',font=pilfont(BOLD,38),fill='#173B53')
    es={'USERS':(45,125,455,390,'id (PK)\nemail, role, active\nreward_points'),
        'COMPLAINTS':(680,125,1120,410,'id (PK), ticket_id\nstudent_id (FK)\ncategory, status, priority'),
        'ASSIGNMENTS':(1340,125,1750,390,'id (PK)\ncomplaint_id, staff_id\nstatus and timestamps'),
        'TIMELINE':(45,620,455,890,'id (PK)\ncomplaint_id, actor_id\naction and comment'),
        'FEEDBACK':(680,620,1120,890,'id (PK)\ncomplaint_id (unique)\nstudent_id, rating'),
        'REWARDS':(1340,620,1750,890,'id (PK)\nstudent_id, complaint_id\npoints and reason')}
    for title,(x1,y1,x2,y2,body) in es.items():
        d.rounded_rectangle((x1,y1,x2,y2),radius=18,fill='#F3F7FA',outline='#234A63',width=4); d.rectangle((x1,y1,x2,y1+60),fill='#E1EBF1',outline='#234A63',width=3)
        centered(d,((x1+x2)//2,y1+30),title,pilfont(BOLD,27),'#173B53'); centered(d,((x1+x2)//2,(y1+y2)//2+30),body,pilfont(REG,22),'#243746')
    arrow(d,(455,250),(680,250),'1:N reports'); arrow(d,(1120,250),(1340,250),'1:N assignments')
    arrow(d,(250,390),(250,620),'actors'); arrow(d,(900,410),(900,620),'0..1 feedback'); arrow(d,(1120,755),(1340,755),'ledger')
    im.save(path,dpi=(220,220))
def make_chart(path):
    im=Image.new('RGB',(1450,700),'white'); d=ImageDraw.Draw(im); d.text((60,30),'Grouped holdout model comparison',font=pilfont(BOLD,38),fill='#173B53')
    l,t,r,b=155,120,1385,555; d.line((l,b,r,b),fill='#475A68',width=3)
    for pct in range(0,71,10):
        y=b-int((b-t)*pct/70); d.line((l,y,r,y),fill='#E0E6EA',width=2); d.text((65,y-14),f'{pct}%',font=pilfont(REG,20),fill='#44515C')
    vals=[('Word n-grams',51.82,50.64),('Character n-grams',62.39,65.32),('Logistic regression',51.64,50.85),('Multinomial NB',41.58,42.22)]
    for i,(name,acc,f1) in enumerate(vals):
        x=195+i*290
        for j,v in enumerate((acc,f1)):
            xx=x+j*78; hh=int((b-t)*v/70); color='#5E8EAC' if j==0 else '#2C7A68'
            d.rectangle((xx,b-hh,xx+56,b),fill=color); d.text((xx-4,b-hh-25),f'{v:.1f}',font=pilfont(REG,18),fill='#243746')
        centered(d,(x+65,b+48),name,pilfont(REG,19),'#263A49')
    d.rectangle((420,638,450,665),fill='#5E8EAC'); d.text((460,638),'Accuracy',font=pilfont(REG,20),fill='#243746')
    d.rectangle((610,638,640,665),fill='#2C7A68'); d.text((650,638),'Macro F1',font=pilfont(REG,20),fill='#243746'); im.save(path,dpi=(220,220))

arch=WORK/'architecture.png'; erd=WORK/'erd.png'; chart=WORK/'ml_metrics.png'
make_arch(arch); make_erd(erd); make_chart(chart)
doc=Document(str(COVER)); cell=doc.tables[0].cell(0,0)
def cover_text(i,text):
    p=cell.paragraphs[i]
    if p.runs:
        p.runs[0].text=text
        for r in p.runs[1:]: r.text=''
    else: p.add_run(text)
for i,s in {1:'Fifth Semester Project Report',5:'CampusFix',8:'Submitted for partial fulfillment of award of',10:'BACHELOR OF TECHNOLOGY',12:'degree',15:'In',17:'Computer Science & Engineering',19:'By',21:'Aman Kumar (2400320100155)',22:'Aditya Shekhar (2400320100047)',23:'Abhishek Dubey (2400320100047)',24:'',26:'Under the Supervision of',27:'Ms. Yashi Rastogi',29:'(Computer Science & Engineering Department)',33:'ABES ENGINEERING COLLEGE, GHAZIABAD',35:'AFFILIATED TO',37:'Dr. A.P.J. Abdul Kalam Technical University, Lucknow',39:'November 2026'}.items(): cover_text(i,s)

# Academic report typography follows the supplied inner-page and fifth-semester guides.
styles=doc.styles; n=styles['Normal']; n.font.name='Times New Roman'; n.font.size=Pt(12); n.font.color.rgb=RGBColor(0,0,0); n._element.rPr.rFonts.set(qn('w:ascii'),'Times New Roman'); n._element.rPr.rFonts.set(qn('w:hAnsi'),'Times New Roman'); n.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY; n.paragraph_format.line_spacing=1.5; n.paragraph_format.space_after=Pt(6)
h=styles['Heading 1']; h.font.name='Times New Roman'; h.font.size=Pt(14); h.font.bold=True; h.font.color.rgb=RGBColor(0,0,0); h.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.CENTER; h.paragraph_format.space_after=Pt(12); h.paragraph_format.keep_with_next=True
h=styles['Heading 2']; h.font.name='Verdana'; h.font.size=Pt(12); h.font.bold=True; h.font.color.rgb=RGBColor(0,0,0); h.paragraph_format.space_before=Pt(8); h.paragraph_format.space_after=Pt(4); h.paragraph_format.keep_with_next=True
h=styles['Heading 3']; h.font.name='Arial'; h.font.size=Pt(12); h.font.bold=True; h.font.color.rgb=RGBColor(0,0,0); h.paragraph_format.space_before=Pt(7); h.paragraph_format.space_after=Pt(3); h.paragraph_format.keep_with_next=True

def page_section(section,roman=False):
    section.page_width=Inches(8.2639); section.page_height=Inches(11.7083); section.top_margin=Inches(.9444); section.bottom_margin=Inches(.8333); section.left_margin=Inches(.7639); section.right_margin=Inches(.5694); section.header_distance=Inches(0); section.footer_distance=Inches(.6417); section.footer.is_linked_to_previous=False
    p=section.footer.paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER; run=p.add_run()
    for typ,val in [('begin',None),('instrText',' PAGE '),('separate',None),('text','1'),('end',None)]:
        tag='w:t' if typ=='text' else ('w:instrText' if typ=='instrText' else 'w:fldChar'); el=OxmlElement(tag)
        if typ=='begin': el.set(qn('w:fldCharType'),'begin')
        elif typ=='separate': el.set(qn('w:fldCharType'),'separate')
        elif typ=='end': el.set(qn('w:fldCharType'),'end')
        elif typ=='instrText': el.set(qn('xml:space'),'preserve'); el.text=val
        else: el.text=val
        run._r.append(el)
    pg=section._sectPr.find(qn('w:pgNumType'))
    if pg is None: pg=OxmlElement('w:pgNumType'); section._sectPr.append(pg)
    pg.set(qn('w:start'),'1'); pg.set(qn('w:fmt'),'lowerRoman' if roman else 'decimal')
    if roman:
        section.different_first_page_header_footer=True
        section.first_page_footer.paragraphs[0].clear()
    for r in p.runs: r.font.name='Times New Roman'; r.font.size=Pt(10)
front=doc.add_section(WD_SECTION.NEW_PAGE); page_section(front,True)

def para(text='',style='Normal',align=None,italic=False):
    p=doc.add_paragraph(style=style)
    if align is not None: p.alignment=align
    r=p.add_run(text); r.italic=italic; r.font.name='Times New Roman'; r.font.color.rgb=RGBColor(0,0,0); r._element.rPr.rFonts.set(qn('w:ascii'),'Times New Roman'); r._element.rPr.rFonts.set(qn('w:hAnsi'),'Times New Roman')
    return p
def fronthead(text):
    p=doc.add_paragraph(style='Heading 1'); p.paragraph_format.page_break_before=True; p.add_run(text.upper()); return p
def chapter(num,title):
    p=doc.add_paragraph(style='Heading 1'); p.paragraph_format.page_break_before=True; p.add_run(f'CHAPTER {num}')
    doc.add_paragraph(title.upper(),style='Heading 1')
def h2(s): return doc.add_paragraph(s,style='Heading 2')
def h3(s): return doc.add_paragraph(s,style='Heading 3')
def bullet(s):
    p=doc.add_paragraph(); p.paragraph_format.left_indent=Inches(.28); p.paragraph_format.first_line_indent=Inches(-.18); p.paragraph_format.line_spacing=1.4
    p.add_run('• ')
    r=p.add_run(s); r.font.name='Times New Roman'; r.font.size=Pt(12); return p
def numbered(s):
    p=doc.add_paragraph(); p.paragraph_format.left_indent=Inches(.28); p.paragraph_format.first_line_indent=Inches(-.2); p.paragraph_format.line_spacing=1.4
    r=p.add_run(f'{numbered.i}. {s}'); r.font.name='Times New Roman'; r.font.size=Pt(12); numbered.i+=1; return p
numbered.i=1
def shade(cell,fill):
    tc=cell._tc.get_or_add_tcPr(); e=OxmlElement('w:shd'); e.set(qn('w:fill'),fill); tc.append(e)
def table(headers,rows,widths,size=9):
    t=doc.add_table(rows=1,cols=len(headers)); t.alignment=WD_TABLE_ALIGNMENT.CENTER; t.autofit=False
    for i,txt in enumerate(headers):
        c=t.rows[0].cells[i]; c.text=str(txt); c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER; shade(c,'E6EDF2')
        if widths: c.width=Inches(widths[i])
        for p in c.paragraphs:
            p.paragraph_format.line_spacing=1.05; p.paragraph_format.space_after=Pt(2)
            for r in p.runs: r.bold=True; r.font.name='Times New Roman'; r.font.size=Pt(size)
    tr=t.rows[0]._tr.get_or_add_trPr(); rep=OxmlElement('w:tblHeader'); rep.set(qn('w:val'),'true'); tr.append(rep)
    for row in rows:
        cells=t.add_row().cells
        for i,txt in enumerate(row):
            c=cells[i]; c.text=str(txt); c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            if widths: c.width=Inches(widths[i])
            for p in c.paragraphs:
                p.paragraph_format.line_spacing=1.05; p.paragraph_format.space_after=Pt(2)
                for r in p.runs: r.font.name='Times New Roman'; r.font.size=Pt(size)
        tr=t.rows[-1]._tr.get_or_add_trPr(); tr.append(OxmlElement('w:cantSplit'))
    borders=OxmlElement('w:tblBorders')
    for edge in ('top','left','bottom','right','insideH','insideV'):
        e=OxmlElement('w:'+edge); e.set(qn('w:val'),'single'); e.set(qn('w:sz'),'5'); e.set(qn('w:color'),'D9D9D9'); borders.append(e)
    t._tbl.tblPr.append(borders); doc.add_paragraph().paragraph_format.space_after=Pt(2); return t
def caption(text):
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.keep_with_next=True; p.paragraph_format.space_before=Pt(4); p.paragraph_format.space_after=Pt(5)
    r=p.add_run(text); r.italic=True; r.font.name='Times New Roman'; r.font.size=Pt(10)
def figure(path,text,width=6.35):
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.keep_with_next=True; p.paragraph_format.keep_together=True
    pic=p.add_run().add_picture(str(path),width=Inches(width)); pic._inline.docPr.set('descr',text); caption(text)

# Front matter follows the supplied inner-page guide.
body=doc.add_section(WD_SECTION.NEW_PAGE); page_section(body,False)

# Front matter
fronthead('Declaration')
para('We declare that the project report titled “CampusFix: Smart Campus Issue Reporting and Management Platform” is submitted as part of the Fifth Semester project work for the Bachelor of Technology programme in Computer Science and Engineering. The implementation and evaluation described here are based on the CampusFix project repository and its recorded artifacts. Material from external sources is acknowledged in the references. The report does not claim deployment or outcomes that have not been measured.')
table(['Student name','University roll number','Signature'],[('Aman Kumar','2400320100155',''),('Aditya Shekhar','2400320100047',''),('Abhishek Dubey','2400320100047','')],[2.3,2.2,1.7],9.5)
para('Place: Ghaziabad\nDate: November 2026')
fronthead('Certificate')
para('This is to certify that the project report entitled “CampusFix: Smart Campus Issue Reporting and Management Platform” has been prepared by Aman Kumar, Aditya Shekhar, and Abhishek Dubey of the Department of Computer Science and Engineering, ABES Engineering College, Ghaziabad, under the supervision of Ms. Yashi Rastogi. The report is submitted in partial fulfillment of the requirements for the Fifth Semester project work of the Bachelor of Technology programme. The work is presented for academic evaluation.')
para('Supervisor: Ms. Yashi Rastogi\nDepartment: Computer Science & Engineering\nSignature: ____________________    Date: ____________________')
para('Project coordinator: ____________________\nHead of Department: ____________________')
fronthead('Acknowledgement')
para('We thank our supervisor, Ms. Yashi Rastogi, for guidance and feedback during the development of CampusFix. We acknowledge the Computer Science and Engineering Department and ABES Engineering College for the academic setting and project review. We also thank the maintainers of the open-source libraries used in the application and the authors of the research and technical references cited in this report.')
fronthead('Abstract')
para('CampusFix is a web-based campus issue reporting and management platform designed to help students report maintenance, sanitation, safety, and other campus concerns and to help authorized staff track their resolution. The application combines a responsive React interface with a FastAPI service, relational persistence, role-based workflows, complaint timelines, optional evidence uploads, staff assignment, feedback, and a capped reward ledger for eligible participation. A text classifier provides a suggested issue category while leaving final review to campus personnel. In a grouped holdout experiment on 10,430 deduplicated records, a character n-gram TF-IDF Linear Support Vector Classifier achieved 62.39% accuracy and 0.653 macro F1, outperforming the evaluated word n-gram, logistic regression, and multinomial Naive Bayes baselines. A separate robustness check contained 22 examples, 19 with known labels, and achieved 89.47% accuracy on those 19 cases; this is diagnostic evidence only. The results do not establish production accuracy because the corpus is limited and templated. The report describes requirements, design, implementation, security controls, evaluation, limitations, and a practical campus pilot plan.')
para('Keywords: campus issue reporting, complaint management, text classification, FastAPI, React, student engagement',italic=True)
fronthead('Contents')
for s in ['Declaration','Certificate','Acknowledgement','Abstract','Contents','List of Figures','List of Tables','Abbreviations','1 Introduction','2 Software Requirements Specification','3 System Design','4 Implementation and Evaluation','5 Conclusion and Future Work','Appendix A: API Summary','Appendix B: Data and Deployment Notes','References']:
    p=para(s); p.paragraph_format.left_indent=Inches(.18)
fronthead('List of Figures')
for s in ['Figure 3.1 CampusFix application architecture','Figure 3.2 Core data entities and relationships','Figure 4.1 Grouped holdout model comparison']: para(s)
fronthead('List of Tables')
for s in ['Table 2.1 User roles and responsibilities','Table 2.2 Functional requirements','Table 2.3 Non-functional requirements','Table 2.4 Core use cases','Table 3.1 Complaint and assignment states','Table 4.1 Model comparison','Table 4.2 Robustness diagnostic','Table 4.3 Verification summary','Table B.1 Core data entities']: para(s)
fronthead('Abbreviations')
table(['Term','Meaning'],[('API','Application Programming Interface'),('JWT','JSON Web Token'),('ML','Machine Learning'),('RBAC','Role-Based Access Control'),('REST','Representational State Transfer'),('SRS','Software Requirements Specification'),('TF-IDF','Term Frequency-Inverse Document Frequency'),('UI','User Interface'),('UX','User Experience')],[1.3,5.3],9.5)
chapter(1,'Introduction')
h2('1.1 Problem Introduction')
para('Campus maintenance issues range from a failed classroom light to a leaking tap or a network outage. When reports arrive through verbal requests, calls, paper forms, or informal messages, students may not know whether a request was recorded, and staff may not have a shared view of its current owner or status. Administrators also need a consistent way to prioritize work, see overdue assignments, and learn which issue categories recur.')
para('CampusFix addresses this coordination problem with a single ticket workflow. Each report receives a ticket identifier, retains the student’s issue description and location, and moves through explicit status changes. Assignment responses and timeline events make operational progress visible to the student and campus team.')
h2('1.2 Motivation')
para('The project is motivated by the need for a traceable, accessible route from issue reporting to resolution. A student-facing dashboard reduces uncertainty after submission. A staff queue supports task ownership, while an administrator view consolidates triage, assignment, and workload information. A category suggestion can shorten routing work, provided it is treated as assistance rather than an authoritative decision.')
h2('1.3 Project Objectives')
for s in ['Provide students with a mobile-friendly form to submit issues and follow ticket timelines.','Give maintenance staff a queue to accept or reject assignments and record resolution notes.','Give administrators tools to review reports, assign active staff, and monitor operational indicators.','Protect account and complaint access with role checks, password hashing, token revocation, and authorized evidence downloads.','Evaluate category suggestions with grouped validation and a small robustness diagnostic set, while documenting the limits of the available data.','Encourage constructive participation through a student reward ledger with a daily report-award cap.']: bullet(s)
h2('1.4 Scope and Limitations')
para('The implemented system covers issue submission, role-based authentication, staff assignment, status transitions, feedback, rewards, attachment upload and access checks, administrative analytics, and advisory text classification. Local development uses SQLite; the Compose configuration supports PostgreSQL. The product does not connect to an institutional single sign-on provider, facilities-management ERP, SMS gateway, or push-notification provider. Password recovery email depends on SMTP configuration. Emergency incidents must continue to use the campus emergency channel; CampusFix is not an emergency dispatch system.')
para('The ML training corpus is templated rather than collected from real campus operations. Evaluation scores therefore describe performance on the supplied grouped holdout and diagnostic examples only. They should not be interpreted as the expected accuracy for a live campus.')
h2('1.5 Related Work')
para('Text categorization maps documents to a fixed set of labels. Joachims describes support vector machines as an effective approach for sparse text representations and discusses why text features can suit large-margin classifiers [1]. TF-IDF vectorization converts token or character n-grams into weighted numeric features; the scikit-learn text analytics guide documents a practical classification pipeline using this representation [2]. CampusFix applies a character n-gram LinearSVC because it performed best in the project’s grouped comparison. The system separately retains the predicted category, confidence signal, and reviewer-confirmed category so later evaluation can distinguish model output from human labels.')
para('Role-aware service applications also require clear authentication boundaries. FastAPI’s security guide explains OAuth2 bearer tokens and JWT-based identity flows [3]. Password recovery is another sensitive boundary: OWASP recommends generic responses, securely generated tokens, one-time use, and expiration to reduce account enumeration and token reuse risks [4]. These sources inform the project’s authentication and recovery design; implementation details are described in Chapters 2 and 4.')
h2('1.6 Organization of the Report')
para('Chapter 1 introduces the problem and objectives. Chapter 2 defines the requirements and actors. Chapter 3 describes the application architecture, data relationships, and ML workflow. Chapter 4 records implementation choices and test/evaluation evidence. Chapter 5 summarizes the outcome and future work. Appendices list principal API routes, core data fields, and deployment/pilot considerations.')

# Chapter 2
chapter(2,'Software Requirements Specification')
h2('2.1 Product Perspective')
para('CampusFix is a browser-based application composed of a React client, a FastAPI REST API, a relational database, and an in-process text-classification component. It is self-contained for the current demonstration deployment. The frontend communicates with the API using JSON over HTTP in local development and can be placed behind Nginx in a container deployment. Authentication is performed by the CampusFix API; no external identity provider is currently integrated.')
para('Users interact with a common ticket model but receive role-specific operations. Students create and follow their reports. Staff operate on assignments addressed to them. Administrators manage staff, triage requests, and view analytics. API authorization is enforced on the server; hiding a control in the interface is not treated as an authorization boundary.')
h2('2.2 User Classes and Responsibilities')
caption('Table 2.1 User roles and responsibilities')
table(['Role','Primary responsibilities'],[
 ('Student','Register or sign in; create a report; attach evidence; view own tickets and timelines; close or reopen eligible issues; submit one resolution feedback record; review own reward balance.'),
 ('Maintenance staff','View assigned work; accept or reject a pending assignment; update accepted work; record resolution notes.'),
 ('Administrator','Review campus issues; change category, priority, or permitted status; create, deactivate, or reactivate staff; assign requests; inspect metrics and overdue work.')
],[1.35,5.3],9.5)
h2('2.3 System Interfaces')
h3('2.3.1 User Interface')
para('The single-page React interface presents distinct student, staff, and administrator dashboards. The report form captures title, location, description, optional category, and optional attachment. The student view shows ticket status and activity; the staff view provides assignment actions; the admin view provides queue filters, staff management, and metrics. Layouts and controls are designed for mobile use, with touch-sized actions and responsive tables and cards.')
h3('2.3.2 Software Interfaces')
para('The frontend uses Axios to call the versioned API at /api/v1. FastAPI validates request and response schemas. SQLAlchemy maps application entities to SQLite or PostgreSQL according to DATABASE_URL. Alembic manages schema changes. The classifier loads a versioned local artifact, with a rule-based fallback when the model cannot be used. SMTP is an optional outbound interface for account recovery; it is not required to submit or resolve reports.')
h3('2.3.3 Hardware and Communication Interfaces')
para('The system has no dedicated hardware-control interface. A supported web browser and network connection are sufficient for interactive use. The local development configuration uses HTTP on localhost; an institutional deployment should place the application behind HTTPS and configure trusted origins and managed secrets.')
h2('2.4 Functional Requirements')
caption('Table 2.2 Functional requirements')
table(['ID','Requirement'],[
 ('FR-01','Public registration creates student accounts and rejects role escalation through the registration payload.'),
 ('FR-02','The system authenticates active users and issues access and refresh tokens with revocation/version checks.'),
 ('FR-03','A student submits a complaint with title, description, location, optional category, and optional evidence.'),
 ('FR-04','Each complaint receives a ticket identifier and timeline events for workflow changes.'),
 ('FR-05','The system suggests a complaint category and retains the suggestion separately from an administrator-reviewed category.'),
 ('FR-06','An administrator assigns an open complaint to an active staff account.'),
 ('FR-07','Assigned staff accept or reject pending work and record completion notes for accepted work.'),
 ('FR-08','Students access only their own complaints; staff access only assigned complaints.'),
 ('FR-09','A student submits feedback after resolution, subject to one feedback record per complaint.'),
 ('FR-10','The system awards points through a ledger, enforces a daily cap on report awards, and exposes a student’s own balance.'),
 ('FR-11','An administrator deactivates or reactivates staff; deactivation revokes active refresh sessions.'),
 ('FR-12','Administrator metrics include overdue pending and accepted assignments.'),
 ('FR-13','Password reset requests receive a generic response and use expiring, single-use reset tokens.')
],[.72,5.93],8.8)
h2('2.5 Non-Functional Requirements')
caption('Table 2.3 Non-functional requirements')
table(['Area','Requirement or design target'],[
 ('Security','Server-side role checks; password hashing; session invalidation after credential changes; authorized evidence downloads.'),
 ('Privacy','Private attachment access and role-limited user records.'),
 ('Usability','Readable forms, explicit status information, responsive layouts, and touch-friendly controls.'),
 ('Reliability','Transactional complaint and reward writes; versioned schema migrations.'),
 ('Maintainability','Separated API, service, repository, model, schema, and frontend feature layers; versioned model artifacts.'),
 ('Performance','Interactive browser usage is the demonstration target; no production load benchmark has been run.'),
 ('Availability','Production availability and backup recovery objectives require campus infrastructure and measurement.')
],[1.25,5.4],9.2)
h2('2.6 Assumptions and Constraints')
for s in ['Campus users can access a modern browser and network connection.','Administrators determine official categories, assignments, priorities, and human-reviewed labels.','SMTP credentials and a trusted frontend origin are required for password-reset email.','The current dataset is a development corpus, not evidence of live-campus model performance.','The Compose configuration is single-host; multi-instance use requires shared private object storage and operational services.','Emergency response remains governed by separate institutional procedures.']: bullet(s)
h2('2.7 Core Use Cases')
caption('Table 2.4 Core use cases')
table(['Use case','Actor','Precondition','Main flow and alternate outcome'],[
 ('Submit issue','Student','Authenticated student','Enter issue details, optionally upload evidence, submit. API validates, predicts a category, writes a ticket and timeline, and applies eligible rewards. Invalid input is rejected.'),
 ('Assign work','Administrator','Open complaint; active staff','Select staff; API records pending assignment and timeline. Inactive staff are ineligible.'),
 ('Respond to work','Staff','Pending assignment belongs to staff','Accept to begin work or reject with a reason; complaint status and timeline update.'),
 ('Resolve issue','Staff','Assignment accepted; complaint in progress','Enter resolution notes; assignment and complaint become resolved.'),
 ('Review issue','Administrator','Complaint exists','Inspect report, set category, priority or status, assign staff, and review overdue work.'),
 ('Recover account','User','Registered email address','Request reset; generic response returned. One-time email link changes password and revokes existing sessions.')
],[1.05,.85,1.45,3.3],8.2)

chapter(3,'System Design')
h2('3.1 Architectural Overview')
para('CampusFix uses a browser client and a backend API. The React application submits JSON requests to FastAPI over HTTP(S). The API authenticates users, applies role and ownership checks, coordinates service operations, and persists data through SQLAlchemy. Complaint creation can call the text classification service for a category suggestion. The response remains advisory: staff and administrators can review or change the category. File evidence is validated and served only to authorized users.')
figure(arch,'Figure 3.1 CampusFix application architecture')
h2('3.2 Workflow and State Model')
para('A student creates a complaint with a description, location, and category context. The API assigns a ticket identifier, records an initial timeline event, and returns the created issue. Staff can accept an assignment, reject it with a reason, update work progress, and submit resolution notes. Administrators can review, prioritize, assign, and monitor issues. Students can follow the timeline and submit feedback after resolution. State transitions are recorded to provide an auditable history.')
table(['Entity','Representative states'],[('Complaint','Open; assigned or pending; in progress; resolved; closed or reopened where supported'),('Assignment','Pending; accepted; rejected; completed'),('Feedback','Not submitted; submitted once for the eligible complaint'),('Reward ledger','Granted under eligibility and daily cap; no negative balance implied')],[1.7,4.9],9)
h2('3.3 Data Model')
para('The relational model links users to complaints, assignments, feedback, timeline events, and reward entries. Complaint records retain the reporting student and current workflow fields. Timeline rows record the actor, event, and optional comment. Reward entries preserve why points were granted, enabling reconciliation instead of relying only on a mutable displayed total. The diagram summarizes the principal entities; the schema may contain additional fields and migration metadata.')
figure(erd,'Figure 3.2 Core data entities and relationships')
h2('3.4 Machine Learning Design')
para('The classifier converts complaint text to character n-gram TF-IDF features and applies a linear support vector classifier. Character features can capture spelling variation and short word fragments in brief reports. Training and test records were grouped by issue template before splitting to reduce leakage between closely related generated examples. The classifier returns a category suggestion and confidence-related signal used by the application’s review path. Low-confidence or uncertain predictions should be routed for human review; the model must not independently close, prioritize, or deny a complaint.')
h2('3.5 Security and Privacy Design')
for s in ['Passwords are stored using Argon2 hashing; credentials are never stored as plaintext.','Access tokens and refresh sessions support authenticated use; password changes and resets revoke existing sessions.','Password reset uses single-use, expiring tokens and a generic request response to reduce account enumeration.','Role and ownership checks protect complaint operations and private attachments.','Uploads are restricted by size, declared type, and file signature for supported image and PDF formats.','Secrets, mail credentials, and production database credentials must be supplied through deployment configuration and excluded from source control.','The service should be deployed behind TLS with restricted CORS origins, database backups, log retention controls, and an incident process.']:
    bullet(s)

chapter(4,'Implementation and Evaluation')
h2('4.1 Implementation')
para('The user interface is implemented as a React application built with Vite. It provides role-oriented views, issue submission, tracking, responsive navigation, and account flows. The backend is a FastAPI REST application with SQLAlchemy persistence and Alembic migrations. Application areas include authentication, complaints, staff assignments, feedback, reward points, and administrative reporting. Local development supports SQLite, while the Compose setup provides a PostgreSQL-backed deployment path. The ML training and evaluation artifacts are maintained under the project ML folder.')
h2('4.2 Reward and Participation Rules')
para('Reward points are intended to recognize constructive participation. The implementation awards points for eligible issue reporting with a daily cap of 10 points, and awards 5 points for eligible feedback. The ledger records the award reason and related issue. The pilot should monitor duplicate, low-quality, or abusive submissions and tune eligibility rules with campus administrators. Points are recognition signals; they should not replace moderation or service prioritization.')
h2('4.3 Evaluation Method')
para('The saved evaluation report records 10,430 deduplicated examples, with 8,234 training records and 2,196 test records. The split groups records by issue template and uses random state 42. Accuracy measures the fraction of exact category matches. Macro F1 gives equal weight to each class and highlights uneven performance on less frequent categories. The evaluation compares a word n-gram LinearSVC, character n-gram LinearSVC, logistic regression, and multinomial Naive Bayes. The character model was selected based on the reported test metrics.')
caption('Table 4.1 Model comparison on grouped holdout data')
table(['Model','Accuracy','Macro F1','Weighted F1'],[
 ('LinearSVC, word n-grams','51.82%','0.5064','0.4809'),('LinearSVC, character n-grams (selected)','62.39%','0.6532','0.6214'),('Logistic regression','51.64%','0.5085','0.4899'),('Multinomial Naive Bayes','41.58%','0.4222','0.4051')],[3.0,1.15,1.15,1.25],9)
figure(chart,'Figure 4.1 Accuracy and macro F1 for evaluated baselines; percentages shown')
para('The character model improves accuracy by about 10.57 percentage points over the word n-gram LinearSVC baseline. Macro F1 is higher than accuracy because it averages class-wise F1; it should not be interpreted as an accuracy percentage. The model remains imperfect: the saved per-class evaluation reports recall of approximately 0.4035 for Civil maintenance and 0.4876 for Security. These categories need more diverse, representative examples and careful review.')
h2('4.4 Robustness Check and Limits')
para('A separate robustness artifact contains 22 diagnostic cases; 19 are labeled with known categories. Accuracy on those 19 known-category cases is 89.47%, and the reported macro F1 on the known categories is approximately 0.8133. The set is very small and is not a representative independent campus test set. Its result should be read as a smoke check for selected inputs, not as a promise of production performance. The training corpus contains templated examples, so template-grouped splitting reduces a specific leakage risk but does not remove source, language, geographic, or class imbalance bias.')
caption('Table 4.2 Robustness diagnostic')
table(['Measure','Result','Interpretation'],[('Diagnostic cases','22','Small hand-selected check'),('Known-category cases','19','Three cases are outside known labels'),('Known-category accuracy','89.47%','19 cases only; not a production estimate'),('Known-category macro F1','0.8133','Class-balanced diagnostic score')],[2.0,1.4,3.1],9)
h2('4.5 Software Verification')
para('The project verification run recorded 20 passing backend regression tests and a successful frontend production build. The frontend linter completed with three pre-existing warnings. These checks provide implementation feedback, not evidence of security certification, load capacity, operational uptime, or end-to-end performance under campus conditions.')
caption('Table 4.3 Verification summary')
table(['Check','Recorded result','Scope'],[('Backend regression suite','20 passed','Automated backend behavior covered by the current suite'),('Frontend production build','Successful','Compilation and bundling'),('Frontend lint','Completed; 3 warnings','Warnings were recorded as pre-existing'),('Production load / security audit','Not measured','Requires a campus deployment environment and separate assessment')],[2.0,1.8,2.7],8.8)
h2('4.6 Risks and Mitigations')
table(['Risk','Mitigation'],[
 ('Misclassification or class imbalance','Show suggestions as advisory, retain human review, measure per-class recall, and gather reviewed campus examples.'),
 ('Sensitive location or image information','Limit collection, restrict access, define retention and deletion rules, and train users not to include unnecessary personal data.'),
 ('Reward gaming or duplicate reports','Apply eligibility rules and caps, preserve an auditable ledger, and permit administrator review.'),
 ('Operational interruption or lost records','Use managed database backups, restore exercises, monitoring, and documented incident response.'),
 ('Unsafe or unsupported uploads','Enforce size/type/signature checks, private storage, authorized downloads, and malware scanning in production.')
],[2.1,4.4],8.6)

chapter(5,'Conclusion and Future Work')
h2('5.1 Conclusion')
para('CampusFix brings campus issue reporting, assignment, progress tracking, resolution, feedback, and student participation rewards into one web application. The current implementation connects a React interface to a FastAPI backend and relational persistence. A text classifier adds category suggestions to the workflow while preserving staff review. In the recorded grouped holdout experiment, character n-gram LinearSVC was the strongest of four evaluated baselines, reaching 62.39% accuracy and 0.6532 macro F1. This result supports using the model as an assistive prototype, while modest class recall and the templated corpus make further evaluation necessary before operational reliance.')
h2('5.2 Future Work')
for s in ['Run a supervised campus pilot with a written privacy notice, accessibility review, defined retention policy, and support owner.','Collect consented, de-identified reports from diverse campus locations and languages; obtain staff-reviewed labels and preserve a truly independent temporal test set.','Track per-class precision, recall, macro F1, abstention rate, calibration, and drift; define thresholds for routing uncertain predictions to manual triage.','Add production observability, backup and restore exercises, rate limits, abuse review, deployment automation, and documented recovery objectives.','Conduct load, accessibility, and independent security testing before broad release.','Review reward rules with students and staff and assess whether points encourage useful reporting without disadvantaging students who cannot participate.']:
    bullet(s)
h2('5.3 Pilot Readiness Checklist')
table(['Area','Before pilot'],[('Ownership','Name campus administrators, staff queues, support contacts, and escalation procedures.'),('Data','Approve collection, visibility, retention, deletion, backup, and incident policies.'),('Access','Configure production secrets, TLS, CORS, role provisioning, and account recovery mail.'),('Operations','Deploy monitored services, validate migrations, rehearse database restore, and document rollback.'),('Model','Keep classification advisory; define review ownership and measure on local held-out examples.'),('Evaluation','Collect usability feedback and report service time, backlog, resolution time, and student satisfaction.')],[1.35,5.15],8.8)

fronthead('Appendix A: API Summary')
para('The backend exposes a REST API. The exact route inventory may vary with the checked-out version; consult the OpenAPI document at /docs when the API is running. The following table groups the core interface areas documented by the application.')
table(['Area','Typical operation'],[
 ('Authentication','Register/login, refresh or revoke sessions, change password, request and complete password reset.'),
 ('Complaints','Create a report; list and view authorized issues; update permitted fields; retrieve timeline.'),
 ('Assignments','Administrator assigns staff; assigned staff accepts, rejects, or completes work.'),
 ('Feedback and rewards','Submit eligible feedback and inspect the student reward balance/history.'),
 ('Administration','Review issue queues, manage staff access, and inspect status/overdue metrics.'),
 ('Evidence','Upload validated attachments and retrieve them only when authorized.')
],[1.55,4.95],9)

fronthead('Appendix B: Data and Deployment Notes')
caption('Table B.1 Core data entities')
table(['Entity','Purpose'],[
 ('User','Identity, role, active state, password hash, and reward summary fields.'),
 ('Complaint','Ticket identifier, reporting student, description, location, category, status, priority, and timestamps.'),
 ('Assignment','Complaint-to-staff allocation and response/resolution state.'),
 ('Timeline event','Actor, action, comment, and time for the issue history.'),
 ('Feedback','Student rating/comment associated with an eligible resolved issue.'),
 ('Reward entry','Student, points, reason, related complaint, and creation time.')
],[1.7,4.8],9)
para('For local development, configure the backend environment, database URL, and secret key using the repository setup guide. SQLite is suitable for a single-user development instance. The Compose configuration provides a PostgreSQL service for integration and deployment practice. Before a real pilot, use a managed or backed-up database, TLS, private attachment storage, real secrets, restricted origins, monitored logs, restore exercises, and an operational contact. Do not expose uploaded evidence or database files from a public static directory.')

fronthead('Appendix C: Dashboard Screenshots')
para('The following screenshots show the student, maintenance staff, and administrator dashboards supplied with the project report materials. They illustrate the role-specific views and example data visible in the CampusFix interface.')
figure(Path(r'C:\Users\Aman Kumar\OneDrive\Pictures\Screenshots\Screenshot 2026-11-20 113533.png'),'Figure C.1 Student dashboard',6.55)
figure(Path(r'C:\Users\Aman Kumar\OneDrive\Pictures\Screenshots\Screenshot 2026-11-20 113557.png'),'Figure C.2 Maintenance staff dashboard',6.55)
figure(Path(r'C:\Users\Aman Kumar\OneDrive\Pictures\Screenshots\Screenshot 2026-11-20 113513.png'),'Figure C.3 Administrator dashboard',6.55)

fronthead('References')
refs=[
 '[1] T. Joachims, “Text categorization with Support Vector Machines: Learning with many relevant features,” in Proceedings of the 10th European Conference on Machine Learning (ECML), 1998, pp. 137–142. Available: https://www.cs.cornell.edu/~tj/publications/joachims_98a.pdf',
 '[2] Scikit-learn developers, “Working with text data,” Scikit-learn User Guide. Available: https://scikit-learn.org/stable/tutorial/text_analytics/working_with_text_data.html',
 '[3] FastAPI contributors, “OAuth2 with Password (and hashing), Bearer with JWT tokens,” FastAPI documentation. Available: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/',
 '[4] OWASP Foundation, “Forgot Password Cheat Sheet.” Available: https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html',
 '[5] CampusFix project repository, backend and frontend source, ML evaluation artifacts, and project documentation, accessed November 2026.',
 '[6] ABES Engineering College, Inner Page_CSE.docx, Cover Page_CSE.docx, and Final report 5th Sem_CSE.docx, project report formatting and structure references.'
]
for s in refs:
    p=para(s); p.paragraph_format.left_indent=Inches(.28); p.paragraph_format.first_line_indent=Inches(-.28); p.paragraph_format.line_spacing=1.1

# Ensure table text and keep rows legible across page breaks.
for t in doc.tables:
    for row in t.rows:
        trPr=row._tr.get_or_add_trPr(); cant=OxmlElement('w:cantSplit'); trPr.append(cant)
        for c in row.cells:
            for p in c.paragraphs:
                for r in p.runs:
                    r.font.name='Times New Roman'; r._element.rPr.rFonts.set(qn('w:ascii'),'Times New Roman'); r._element.rPr.rFonts.set(qn('w:hAnsi'),'Times New Roman')
doc.core_properties.title='CampusFix: Smart Campus Issue Reporting and Management Platform'
doc.core_properties.subject='Fifth Semester Project Report, Computer Science and Engineering'
doc.core_properties.author='Aman Kumar; Aditya Shekhar; Abhishek Dubey'
doc.core_properties.keywords='CampusFix, campus issue reporting, FastAPI, React, text classification'
doc.save(OUT)
print(OUT)
