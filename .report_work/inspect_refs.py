import sys, json, hashlib, zipfile, os
from docx import Document
paths=[r'C:\Users\Aman Kumar\Downloads\Inner Page_CSE.docx',r'C:\Users\Aman Kumar\Downloads\Final report 5th Sem_CSE.docx',r'C:\Users\Aman Kumar\Downloads\Cover Page_CSE.docx']
for path in paths:
 print('\n===',path,'===')
 d=Document(path)
 print('sha256',hashlib.sha256(open(path,'rb').read()).hexdigest())
 for i,s in enumerate(d.sections): print('SECTION',i,'page',s.page_width/914400,s.page_height/914400,'margins',s.top_margin/914400,s.bottom_margin/914400,s.left_margin/914400,s.right_margin/914400,'header_footer',s.header_distance/914400,s.footer_distance/914400)
 for i,p in enumerate(d.paragraphs):
  if p.text.strip(): print('P',i,'style='+p.style.name,'align='+str(p.alignment),'text='+repr(p.text))
 for ti,t in enumerate(d.tables):
  print('TABLE',ti,'rows',len(t.rows),'cols',len(t.columns))
  for ri,row in enumerate(t.rows): print('  ROW',ri, [c.text.replace('\n',' | ') for c in row.cells])
 for si in d.styles:
  if si.type==1 and si.name in ['Normal','Title','Heading 1','Heading 2','Heading 3']:
   f=si.font; pf=si.paragraph_format
   print('STYLE',si.name,'font',f.name,'size',f.size.pt if f.size else None,'bold',f.bold,'align',pf.alignment,'line',pf.line_spacing,'before',pf.space_before.pt if pf.space_before else 0,'after',pf.space_after.pt if pf.space_after else 0)
 for i,s in enumerate(d.sections):
  for n,p in [('HEADER',x) for x in s.header.paragraphs]+[('FOOTER',x) for x in s.footer.paragraphs]:
   if p.text.strip(): print(n,repr(p.text))
 with zipfile.ZipFile(path) as z:
  print('PARTS',[n for n in z.namelist() if n.startswith(('word/media','word/header','word/footer'))])
