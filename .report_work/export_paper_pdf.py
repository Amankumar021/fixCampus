from pathlib import Path
from xml.sax.saxutils import escape
from docx import Document
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER,TA_JUSTIFY,TA_LEFT,TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,KeepTogether
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
import json

ROOT=Path(__file__).resolve().parents[1];src=ROOT/'output/papers/CampusFix_Research_Paper.docx';out=ROOT/'output/papers/CampusFix_Research_Paper.pdf';work=ROOT/'.report_work'
docx=Document(src)
for font,path in [('Arial',r'C:\Windows\Fonts\arial.ttf'),('Arial-Bold',r'C:\Windows\Fonts\arialbd.ttf'),('Arial-Italic',r'C:\Windows\Fonts\ariali.ttf'),('Arial-BoldItalic',r'C:\Windows\Fonts\arialbi.ttf')]: pdfmetrics.registerFont(TTFont(font,path))
pdfmetrics.registerFontFamily('Arial',normal='Arial',bold='Arial-Bold',italic='Arial-Italic',boldItalic='Arial-BoldItalic')
ss=getSampleStyleSheet();
ss.add(ParagraphStyle('PaperTitle',fontName='Arial-Bold',fontSize=19,leading=23,alignment=TA_CENTER,textColor=colors.HexColor('#183C35'),spaceAfter=8,keepWithNext=True))
ss.add(ParagraphStyle('Authors',fontName='Arial-Bold',fontSize=9.5,leading=13,alignment=TA_CENTER,textColor=colors.HexColor('#263A35'),spaceAfter=4,keepWithNext=True))
ss.add(ParagraphStyle('Affiliation',fontName='Arial',fontSize=8.5,leading=12,alignment=TA_CENTER,textColor=colors.HexColor('#4E5B57'),spaceAfter=10,keepWithNext=True))
ss.add(ParagraphStyle('AbstractHead',fontName='Arial-Bold',fontSize=10.5,leading=13,textColor=colors.HexColor('#0F6C59'),spaceBefore=4,spaceAfter=3,keepWithNext=True))
ss.add(ParagraphStyle('PaperBody',fontName='Arial',fontSize=9.4,leading=13.0,alignment=TA_JUSTIFY,textColor=colors.HexColor('#242D2B'),spaceAfter=6,allowWidows=0,allowOrphans=0))
ss.add(ParagraphStyle('PaperBullet',parent=ss['PaperBody'],leftIndent=15,firstLineIndent=-9,spaceAfter=3))
ss.add(ParagraphStyle('PaperH1',fontName='Arial-Bold',fontSize=13.3,leading=16,textColor=colors.HexColor('#174D40'),spaceBefore=11,spaceAfter=5,keepWithNext=True))
ss.add(ParagraphStyle('PaperH2',fontName='Arial-Bold',fontSize=10.5,leading=13,textColor=colors.HexColor('#17755E'),spaceBefore=8,spaceAfter=4,keepWithNext=True))
ss.add(ParagraphStyle('PaperCaption',fontName='Arial-Italic',fontSize=8.3,leading=10.5,alignment=TA_CENTER,textColor=colors.HexColor('#5C6966'),spaceBefore=2,spaceAfter=7))
ss.add(ParagraphStyle('PaperRef',fontName='Arial',fontSize=8.3,leading=11,alignment=TA_LEFT,leftIndent=17,firstLineIndent=-17,textColor=colors.HexColor('#242D2B'),spaceAfter=5))
ss.add(ParagraphStyle('Keywords',fontName='Arial',fontSize=8.7,leading=11,alignment=TA_LEFT,leftIndent=11,rightIndent=11,spaceAfter=8))
story=[]

def richpara(p,sty):
 parts=[]
 for run in p.runs:
  text=escape(run.text).replace('\n','<br/>')
  if not text: continue
  if run.bold:text=f'<b>{text}</b>'
  if run.italic:text=f'<i>{text}</i>'
  parts.append(text)
 if not parts:
  return None
 return Paragraph(''.join(parts),ss[sty])

def image_from_paragraph(p):
 found=[]
 for blip in p._p.iter(qn('a:blip')):
  rid=blip.get(qn('r:embed'))
  if not rid:continue
  part=docx.part.related_parts[rid]
  ext=part.content_type.split('/')[-1].replace('jpeg','jpg')
  path=work/f'paper-image.{ext}';path.write_bytes(part.blob)
  found.append(path)
 return found

body=docx._element.body
for child in body.iterchildren():
 if child.tag==qn('w:p'):
  p=next((x for x in docx.paragraphs if x._p is child),None)
  if p is None:continue
  sty=p.style.name if p.style else 'Normal'
  imgs=image_from_paragraph(p)
  if imgs:
   for imagepath in imgs:
    im=Image(str(imagepath));im._restrictSize(6.15*inch,3.4*inch);im.hAlign='CENTER';story.append(KeepTogether([im]))
   continue
  if not p.text.strip():continue
  if sty=='Title':target='PaperTitle'
  elif sty=='Heading 1':target='PaperH1'
  elif sty=='Heading 2':target='PaperH2'
  elif sty=='List Bullet':target='PaperBullet'
  elif p.text.strip()=='Abstract':target='AbstractHead'
  elif p.text.strip().startswith('Figure 1.'):target='PaperCaption'
  elif p.text.strip().startswith('Keywords:'):target='Keywords'
  elif p.text.strip().startswith('[') and len(p.text.strip())>60:target='PaperRef'
  elif 'Department of Computer Science' in p.text and 'Project supervisor' in p.text:target='Affiliation'
  elif p.text.strip().startswith('Aman Kumar') and 'Aditya Shekhar' in p.text:target='Authors'
  else:target='PaperBody'
  para=richpara(p,target)
  if para:story.append(para)
 elif child.tag==qn('w:tbl'):
  tbl=next((x for x in docx.tables if x._tbl is child),None)
  if tbl is None:continue
  data=[]
  for row in tbl.rows:
   cells=[]
   for ci,cell in enumerate(row.cells):
    val=escape(cell.text.replace('\n',' '))
    sty='TableHead' if len(data)==0 else 'TableBody'
    if sty not in ss: ss.add(ParagraphStyle('TableHead',fontName='Arial-Bold',fontSize=8,leading=10,textColor=colors.white));ss.add(ParagraphStyle('TableBody',fontName='Arial',fontSize=8,leading=10,textColor=colors.HexColor('#263A35')))
    cells.append(Paragraph(val,ss[sty]))
   data.append(cells)
  widths=[2.7*inch,1.0*inch,1.0*inch,1.1*inch] if len(data[0])==4 else [1.65*inch,1.0*inch,.9*inch,.8*inch,.65*inch]
  t=Table(data,colWidths=widths,repeatRows=1,hAlign='CENTER')
  t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#174D40')),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#D4DEDA')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F1F5F3')]),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
  story.extend([Spacer(1,4),t,Spacer(1,5)])

def page_decoration(canvas,docx):
 canvas.saveState();w,h=letter;canvas.setStrokeColor(colors.HexColor('#D4DEDA'));canvas.setLineWidth(.5);canvas.line(.86*inch,h-.48*inch,w-.86*inch,h-.48*inch);canvas.setFont('Arial-Bold',7.5);canvas.setFillColor(colors.HexColor('#0F6C59'));canvas.drawRightString(w-.86*inch,h-.36*inch,'CAMPUSFIX  |  RESEARCH PAPER');canvas.line(.86*inch,.5*inch,w-.86*inch,.5*inch);canvas.setFont('Arial',8);canvas.setFillColor(colors.HexColor('#5C6966'));canvas.drawCentredString(w/2,.32*inch,f'Department of Computer Science & Engineering  •  {docx.page}');canvas.restoreState()

pdf=SimpleDocTemplate(str(out),pagesize=letter,rightMargin=.86*inch,leftMargin=.86*inch,topMargin=.68*inch,bottomMargin=.68*inch,title='CampusFix Research Paper',author='Aman Kumar; Aditya Shekhar; Abhishek Dubey; Aaryan Pandey; Aditya Kumar')
pdf.build(story,onFirstPage=page_decoration,onLaterPages=page_decoration)
print(out)

