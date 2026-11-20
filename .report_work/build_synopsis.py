from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
    PageBreak, Table, TableStyle, Image, KeepTogether, HRFlowable, NextPageTemplate)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output'/'pdf'/'CampusFix_Synopsis_Report.pdf'
WORK=ROOT/'.report_work'
SCREEN=Path(r'C:\Users\Aman Kumar\OneDrive\Pictures\Screenshots')
ARCH=WORK/'architecture.png'
CHART=WORK/'ml_metrics.png'

GREEN=colors.HexColor('#0F6C59')
DARK=colors.HexColor('#183C35')
MINT=colors.HexColor('#E9F4F0')
PALE=colors.HexColor('#F4F7F6')
INK=colors.HexColor('#1E2A28')
MUTED=colors.HexColor('#5C6966')
LINE=colors.HexColor('#D4DEDA')

FONT=r'C:\Windows\Fonts\arial.ttf'
FONT_BOLD=r'C:\Windows\Fonts\arialbd.ttf'
pdfmetrics.registerFont(TTFont('Arial',FONT)); pdfmetrics.registerFont(TTFont('Arial-Bold',FONT_BOLD))

styles=getSampleStyleSheet()
styles.add(ParagraphStyle('BodyCampus',parent=styles['BodyText'],fontName='Arial',fontSize=9.7,leading=14.2,textColor=INK,alignment=TA_JUSTIFY,spaceAfter=7,allowWidows=0,allowOrphans=0))
styles.add(ParagraphStyle('BodySmall',parent=styles['BodyText'],fontName='Arial',fontSize=8.4,leading=11.5,textColor=INK,spaceAfter=3))
styles.add(ParagraphStyle('TableHead',fontName='Arial-Bold',fontSize=8.1,leading=10.5,textColor=colors.white,spaceAfter=0))
styles.add(ParagraphStyle('CoverTitle',fontName='Arial-Bold',fontSize=24,leading=30,alignment=TA_CENTER,textColor=DARK,spaceAfter=12))
styles.add(ParagraphStyle('CoverKicker',fontName='Arial-Bold',fontSize=12,leading=17,alignment=TA_CENTER,textColor=GREEN,spaceAfter=4))
styles.add(ParagraphStyle('CoverSub',fontName='Arial',fontSize=11,leading=16,alignment=TA_CENTER,textColor=MUTED,spaceAfter=10))
styles.add(ParagraphStyle('H1Campus',fontName='Arial-Bold',fontSize=16,leading=20,textColor=DARK,spaceBefore=8,spaceAfter=9,keepWithNext=True,outlineLevel=0))
styles.add(ParagraphStyle('H2Campus',fontName='Arial-Bold',fontSize=11.5,leading=15,textColor=GREEN,spaceBefore=7,spaceAfter=4,keepWithNext=True,outlineLevel=1))
styles.add(ParagraphStyle('H3Campus',fontName='Arial-Bold',fontSize=9.8,leading=13,textColor=INK,spaceBefore=5,spaceAfter=3,keepWithNext=True))
styles.add(ParagraphStyle('CaptionCampus',fontName='Arial',fontSize=8.2,leading=10.5,alignment=TA_CENTER,textColor=MUTED,spaceBefore=4,spaceAfter=8))
styles.add(ParagraphStyle('TOCHead',fontName='Arial-Bold',fontSize=20,leading=25,textColor=DARK,spaceAfter=16))
styles.add(ParagraphStyle('BulletCampus',parent=styles['BodyCampus'],leftIndent=15,firstLineIndent=-9,bulletIndent=2,spaceAfter=4))
styles.add(ParagraphStyle('Callout',fontName='Arial',fontSize=8.6,leading=12,textColor=DARK,backColor=MINT,borderColor=LINE,borderWidth=.6,borderPadding=7,spaceBefore=4,spaceAfter=8))

def P(text,style='BodyCampus'):
    return Paragraph(text,styles[style])

def bullet(text):
    return Paragraph('&bull;&nbsp; '+text,styles['BulletCampus'])

def h1(text): return P(text,'H1Campus')
def h2(text): return P(text,'H2Campus')
def h3(text): return P(text,'H3Campus')

def table(headers,rows,widths,font=8.1):
    data=[[P(str(x),'TableHead') for x in headers]]
    data += [[P(str(x),'BodySmall') for x in row] for row in rows]
    t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT',splitByRow=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),DARK),('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('FONTNAME',(0,0),(-1,0),'Arial-Bold'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('GRID',(0,0),(-1,-1),.45,LINE),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,PALE]),
        ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
    ]))
    return t

def picture(path,width,caption,max_height=None):
    im=Image(str(path)); ratio=min(width/im.imageWidth, max_height/im.imageHeight) if max_height else width/im.imageWidth
    im.drawWidth=im.imageWidth*ratio; im.drawHeight=im.imageHeight*ratio
    im.hAlign='CENTER'
    return KeepTogether([im,P(caption,'CaptionCampus')])

class CampusDoc(BaseDocTemplate):
    def __init__(self,filename,**kwargs):
        super().__init__(filename,pagesize=letter,leftMargin=.82*inch,rightMargin=.82*inch,topMargin=.78*inch,bottomMargin=.72*inch,**kwargs)
        frame=Frame(self.leftMargin,self.bottomMargin,self.width,self.height,id='normal',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
        self.addPageTemplates([PageTemplate(id='main',frames=frame,onPage=self.decorate)])
        self.toc=TableOfContents()
        self.toc.levelStyles=[
            ParagraphStyle('TOC0',fontName='Arial-Bold',fontSize=9.6,leading=15,leftIndent=0,firstLineIndent=0,textColor=DARK,spaceBefore=3),
            ParagraphStyle('TOC1',fontName='Arial',fontSize=8.7,leading=13,leftIndent=18,firstLineIndent=0,textColor=MUTED),
        ]
    def decorate(self,canvas,doc):
        canvas.saveState()
        w,h=letter
        canvas.setStrokeColor(LINE); canvas.setLineWidth(.6)
        canvas.line(self.leftMargin,h-.48*inch,w-self.rightMargin,h-.48*inch)
        canvas.setFont('Arial-Bold',7.6); canvas.setFillColor(GREEN)
        canvas.drawString(self.leftMargin,h-.37*inch,'ABESEC GHAZIABAD  |  DEPT. OF CSE')
        canvas.setFont('Arial',7.6); canvas.setFillColor(MUTED)
        canvas.drawRightString(w-self.rightMargin,h-.37*inch,'CAMPUSFIX SYNOPSIS  •  SESSION 2026-27')
        canvas.line(self.leftMargin,.48*inch,w-self.rightMargin,.48*inch)
        canvas.setFont('Arial',8); canvas.setFillColor(MUTED)
        canvas.drawString(self.leftMargin,.31*inch,'Department of Computer Science & Engineering')
        canvas.drawRightString(w-self.rightMargin,.31*inch,str(doc.page))
        canvas.restoreState()
    def afterFlowable(self,flowable):
        if isinstance(flowable,Paragraph) and flowable.style.name in ('H1Campus','H2Campus'):
            level=0 if flowable.style.name=='H1Campus' else 1
            text=flowable.getPlainText()
            key=f'toc-{level}-{self.page}-{len(text)}-{text[:14]}'
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text,key,level=level,closed=(level==0))
            self.notify('TOCEntry',(level,text,self.page))

def cover_table():
    rows=[
      ['Group Member 1','Aman Kumar','2400320100155',''],
      ['Group Member 2','Aditya Shekhar','2400320100088',''],
      ['Group Member 3','Abhishek Dubey','2400320100047',''],
      ['Group Member 4','Aaryan Pandey','2400320100010',''],
      ['Group Member 5','Aditya Kumar','2400320100077',''],
    ]
    return table(['Role','Name','University roll no.','Signature'],rows,[1.17*inch,1.6*inch,1.55*inch,1.45*inch],8.4)

def build():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    doc=CampusDoc(str(OUT),title='CampusFix Synopsis Report',author='Aman Kumar; Aditya Shekhar; Abhishek Dubey; Aaryan Pandey; Aditya Kumar')
    s=[]
    # Cover page in the style of the supplied ABESEC synopsis PDF.
    s += [Spacer(1,.42*inch),P('ABESEC GHAZIABAD','CoverKicker'),P('Department of Computer Science &amp; Engineering','CoverSub'),Spacer(1,.12*inch),HRFlowable(width='100%',thickness=2,color=GREEN,spaceBefore=3,spaceAfter=20),P('SYNOPSIS REPORT','CoverKicker'),P('Session 2026-27','CoverSub'),Spacer(1,.12*inch),P('CampusFix','CoverTitle'),P('Smart Campus Issue Reporting and Management Platform','CoverSub'),Spacer(1,.14*inch)]
    s += [P('<b>Project Type:</b> Full-stack campus service application with machine-learning assisted issue categorization','BodyCampus'),Spacer(1,7),cover_table(),Spacer(1,8),P('<b>Project Guide</b>  Ms. Yashi Rastogi','BodyCampus'),P('<b>Department</b>  Computer Science &amp; Engineering','BodyCampus'),P('<b>Remarks</b>  ______________________________________________________________','BodyCampus'),Spacer(1,14),P('<b>Signature</b>  ____________________________     <b>Date of Submission</b>  __________________','BodySmall'),Spacer(1,8),P('Prepared by five students of the Department of Computer Science &amp; Engineering.','Callout'),PageBreak()]
    s += [P('TABLE OF CONTENTS','TOCHead'),doc.toc,PageBreak()]

    # 1. Problem introduction
    s += [h1('1. Problem Introduction'),h2('1.1 Motivation'),P('Campus service requests are often scattered across in-person conversations, calls, forms, and informal messages. Students may have no reliable way to see whether a concern was recorded or who is handling it. Operations teams can receive duplicate requests, lose context during handoffs, and lack a common view of workload and overdue work. These gaps make it harder to coordinate routine maintenance and to communicate progress back to the reporting student.'),P('CampusFix provides a shared ticket workflow for campus concerns. Students can report an issue, attach optional evidence, and follow a status timeline. Staff can accept or reject assigned work and record resolution details. Administrators can review, categorize, prioritize, assign, and monitor issues. A text classifier offers a category suggestion to support routing, while the campus reviewer retains the final decision.'),h2('1.2 Project Objectives')]
    for x in [
      'Provide students with an accessible, mobile-responsive way to report issues and track updates.',
      'Give maintenance staff an assigned work queue with explicit response and resolution actions.',
      'Give administrators tools for triage, staff access management, overdue tracking, and operational metrics.',
      'Use an advisory text classifier to suggest issue categories and retain human review.',
      'Protect accounts, complaint records, and uploaded evidence through authentication, role checks, and access controls.',
      'Recognize constructive participation through a student reward ledger for eligible reports and resolution feedback.',
      'Evaluate the classifier on a grouped holdout and document its limitations before any campus pilot.'
    ]: s.append(bullet(x))
    s += [h2('1.3 Scope of the Project'),P('The current application includes student issue submission and history, staff assignments and work-order actions, administrator triage and metrics, complaint timelines, optional evidence upload, resolution feedback, student rewards, password recovery, and machine-learning category suggestions. The frontend is built with React and Vite; the API uses FastAPI, SQLAlchemy, and Alembic. Local development supports SQLite, with PostgreSQL available through the container setup.'),P('The current version does not integrate with campus single sign-on, an institutional facilities-management system, SMS or push notifications, or a production file-scanning service. Account recovery email requires SMTP configuration. The application is a project prototype: service availability, production load, independent security certification, and real-campus classifier performance have not been measured. Emergency incidents remain subject to the institution’s emergency procedures.')]

    # 2. Previous work
    s += [h1('2. Related Previous Work'),P('Campus issue-management systems typically center on a ticket lifecycle: a report is captured, routed to an accountable team, updated as work progresses, and closed with a record of the outcome. CampusFix follows this workflow and adds student-visible status history, role-specific work queues, and operational summaries so that reporting, dispatch, and follow-up share one record.'),P('For text classification, Joachims describes support vector machines as effective for sparse text categorization, while the scikit-learn text analytics guide demonstrates a pipeline combining text vectorization and supervised classifiers [1, 2]. CampusFix evaluates word and character n-gram features with a linear support vector classifier and baseline alternatives. Character features can tolerate some spelling variation, but performance still depends on representative examples and balanced evaluation.'),P('The authentication design also follows established guidance. FastAPI documents bearer-token and JWT patterns for API authentication [3]. OWASP password-recovery guidance recommends generic responses and one-time expiring reset tokens to reduce account enumeration and token reuse [4]. These sources inform design choices; they do not substitute for an independent security review of the application.')]

    # 3. Dataset
    s += [h1('3. Dataset Description'),P('The repository contains a structured complaint corpus with text, location, category, and issue-template fields. The raw file has 10,800 records: 1,200 records for each of nine categories. Exact duplicate removal leaves 10,430 records. The data includes templated examples and should not be treated as a representative sample of real campus submissions.'),table(['Dataset property','Recorded value'],[
      ('Issue categories','Cafeteria; Civil Maintenance; Cleanliness; Electrical; Furniture; IT; Plumbing; Sanitation; Security'),
      ('Raw records','10,800 (1,200 per category before exact deduplication)'),
      ('After exact deduplication','10,430'),
      ('Input fields','Complaint text, location, category label, issue-template identifier'),
      ('Evaluation split','8,234 train / 2,196 test; GroupShuffleSplit grouped by issue_template; random state 42'),
      ('Dataset limitation','Synthetic or templated patterns; no consented human-labeled campus holdout')
    ],[1.65*inch,4.12*inch]),h2('3.1 Representative Attributes'),bullet('<b>Complaint text:</b> short natural-language description used for category suggestion.'),bullet('<b>Location:</b> campus area or room associated with the issue.'),bullet('<b>Category:</b> one of nine issue labels used as the training target.'),bullet('<b>Issue template:</b> grouping identifier used to separate related examples across the training and test split.'),P('A limitation of the saved grouped split is that the test set contains no IT examples (zero test support for that class). Metrics therefore do not demonstrate coverage of all nine categories. Future acceptance testing should use independently collected, reviewed, de-identified campus reports with coverage for each category.')]

    # 4. Requirements
    s += [h1('4. Software and Hardware Requirements'),h2('Software Requirements')]
    for x in ['Operating system: Windows or Linux for development; container host for the Compose deployment path.','Backend: Python 3.11 or 3.12, FastAPI, SQLAlchemy, Alembic, and a configured SQLite or PostgreSQL database.','Frontend: Node.js 22, React 19, Vite, and a current browser.','Machine learning: Python/scikit-learn-compatible training and inference artifacts stored under the project ML directory.','Development tools: VS Code or equivalent editor, Git, and a terminal.','Optional deployment services: PostgreSQL, SMTP for password recovery, HTTPS reverse proxy, monitoring, and private evidence storage.']: s.append(bullet(x))
    s += [h2('Hardware Requirements'),table(['Component','Project requirement'],[
      ('Processor','Modern dual-core processor or better for local development.'),('Memory','4 GB minimum; 8 GB recommended for running the browser, API, database, and build tools together.'),('Storage','At least 2 GB free for dependencies, database, model artifacts, and development files.'),('GPU','Not required for the current classical text-classification model.'),('Network','Internet access for initial dependency setup; local use can run on a development network.')
    ],[1.4*inch,4.37*inch])]

    # 5. Method
    s += [h1('5. Proposed Method'),P('CampusFix uses a role-based browser client connected to a versioned REST API. The API validates requests, authenticates users, checks role and ownership permissions, and applies complaint, assignment, feedback, and reward workflows. SQLAlchemy persists application records. During complaint creation, the inference service returns a suggested category and confidence signal. The suggestion is saved for review; authorized administrators can confirm or change the category.'),h2('5.1 System Workflow')]
    for i,x in enumerate(['Student submits a report with text and location, with optional evidence.','API validates the request and access, generates a ticket, records a timeline event, and requests an ML category suggestion.','Administrator reviews the issue, adjusts category or priority when needed, and assigns active staff.','Assigned staff accepts or rejects the work; accepted work can be updated and resolved with notes.','Student follows ticket progress and may provide resolution feedback.','The system records eligible report and feedback rewards in a student ledger.','Administrators review queue, status, overdue, and service metrics.'],1): s.append(P(f'<b>{i}.</b> {x}'))
    s += [picture(ARCH,6.1*inch,'Figure 1. CampusFix high-level architecture'),h2('5.2 Machine-Learning Pipeline'),P('The selected classifier uses character n-gram TF-IDF features with a linear support vector classifier. The saved evaluation compares this model with word n-gram LinearSVC, logistic regression, and multinomial Naive Bayes. The issue-template grouping is intended to reduce leakage between near-duplicate templated examples. The model is a routing aid; low-confidence cases should be reviewed by staff, and model output must not close a report or determine emergency priority.'),h2('5.3 Security and Privacy Controls')]
    for x in ['Passwords are stored as Argon2 hashes; authenticated API routes apply role and ownership checks.','Access and refresh sessions can be revoked; password changes and resets invalidate existing sessions.','Password-reset responses are generic and use single-use expiring tokens.','Evidence uploads have size, media-type, and signature checks and are accessed through authorized routes.','A real campus deployment still requires TLS, managed secrets, restricted origins, backup/restore procedures, private file storage, retention rules, monitoring, and independent security testing.']: s.append(bullet(x))

    # 6. Outcomes and measured results
    s += [h1('6. Expected Outcomes and Results'),P('The project has produced a working full-stack prototype, role-specific dashboards, issue and assignment workflows, an advisory classifier, reward points, and setup/deployment documentation. The primary model result below is from the saved grouped holdout evaluation. It is an experimental result on templated data, not a real-world campus performance estimate.'),table(['Model','Accuracy','Macro F1','Weighted F1'],[
      ('LinearSVC, word n-grams','51.82%','0.5064','0.4809'),('LinearSVC, character n-grams (selected)','62.39%','0.6532','0.6214'),('Logistic regression','51.64%','0.5085','0.4899'),('Multinomial Naive Bayes','41.58%','0.4222','0.4051')
    ],[2.55*inch,1.05*inch,1.05*inch,1.12*inch]),picture(CHART,5.65*inch,'Figure 2. Accuracy and macro F1 for the four evaluated baselines.'),P('The selected character model improves accuracy by about 10.57 percentage points over the word n-gram LinearSVC baseline. Class performance varies: recall is 0.4035 for Civil Maintenance and 0.4876 for Security in the saved report, and IT has no test examples. This uneven coverage, together with the templated corpus, limits interpretation of the aggregate scores.'),h2('Robustness diagnostic'),P('A separate manually written diagnostic set contains 22 cases. Accuracy is 81.82% across all 22 cases; among 19 cases with known model categories, accuracy is 89.47% and macro F1 is 0.8133. This small diagnostic set is useful as a smoke check only and cannot estimate live campus performance.'),h2('Software verification'),P('The project verification record reports 20 passing backend regression tests and a successful frontend production build. The frontend linter completed with three pre-existing warnings. Production load, accessibility certification, and independent security testing have not been measured.'),h2('Role-specific interface views'),P('The following screenshots illustrate the student, maintenance staff, and administrator dashboards available in the project. Example names, counts, and tickets are demonstration data.'),PageBreak(),picture(SCREEN/'Screenshot 2026-11-20 113533.png',6.1*inch,'Figure 3. Student dashboard: impact points, reported issues, and status tracking.',max_height=3.25*inch),PageBreak(),picture(SCREEN/'Screenshot 2026-11-20 113557.png',6.1*inch,'Figure 4. Maintenance dashboard: feedback, assignment queue, and work status.',max_height=3.25*inch),PageBreak(),picture(SCREEN/'Screenshot 2026-11-20 113513.png',6.1*inch,'Figure 5. Administrator dashboard: operations summary, triage, and staff dispatch.',max_height=3.25*inch)]

    # 7. Work plan
    s += [h1('7. Project Timeline and Work Plan'),P('The following ten-week sequence summarizes the project work plan used for planning and documentation. The implementation, model evaluation, and synopsis/report artifacts are complete as of November 2026. The timeline is an indicative phase plan rather than a claim that each task consumed exactly the duration shown.'),table(['Phase','Activities','Status'],[
      ('1. Requirements','Problem definition, user roles, feature scope, initial architecture.','Complete'),('2. Design','Workflow, API and data model, dashboard and mobile-use design.','Complete'),('3. Backend','Authentication, complaints, assignments, feedback, rewards, migrations.','Complete'),('4. Frontend','Student, staff, and admin dashboards; responsive interaction.','Complete'),('5. Data preparation','Corpus review, exact deduplication, template grouping.','Complete'),('6. Model development','Baseline evaluation and character n-gram LinearSVC selection.','Complete'),('7. Integration','Frontend/API/ML integration, deployment configuration, seeded demo.','Complete'),('8. Verification','Backend regression suite, frontend build, lint review, robustness check.','Complete'),('9. Documentation','Project report, synopsis content, pilot plan, references.','Complete'),('10. Pilot readiness','Define local privacy, operations, data, and independent evaluation needs.','Prepared; campus pilot not yet measured')
    ],[1.22*inch,3.78*inch,.72*inch])]

    # 8. References
    s += [h1('8. References'),P('[1] T. Joachims, “Text categorization with Support Vector Machines: Learning with many relevant features,” in <i>Proceedings of the 10th European Conference on Machine Learning</i>, 1998, pp. 137-142. https://www.cs.cornell.edu/~tj/publications/joachims_98a.pdf','BodySmall'),P('[2] Scikit-learn developers, “Working with text data,” <i>Scikit-learn User Guide</i>. https://scikit-learn.org/stable/tutorial/text_analytics/working_with_text_data.html','BodySmall'),P('[3] FastAPI contributors, “OAuth2 with Password (and hashing), Bearer with JWT tokens,” <i>FastAPI documentation</i>. https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/','BodySmall'),P('[4] OWASP Foundation, “Forgot Password Cheat Sheet.” https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html','BodySmall'),P('[5] CampusFix project repository, application source, ML dataset and evaluation artifacts, test suite, and campus pilot plan, accessed November 2026.','BodySmall'),P('[6] ABES Engineering College, <i>Synopsis_Report_Disease_Prediction.pdf</i>, provided synopsis layout and section-order reference. Disease-prediction content is not used in this synopsis.','BodySmall'),Spacer(1,9),P('Submitted by Aman Kumar, Aditya Shekhar, and Abhishek Dubey, Department of Computer Science &amp; Engineering, ABESEC Ghaziabad.','BodySmall')]
    doc.multiBuild(s)
    print(OUT)

if __name__=='__main__': build()




