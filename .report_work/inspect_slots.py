from docx import Document
for path in [r'C:\Users\Aman Kumar\Downloads\Final report 5th Sem_CSE.docx',r'C:\Users\Aman Kumar\Downloads\Cover Page_CSE.docx']:
 print('\n###',path)
 d=Document(path)
 print('body paragraphs',len(d.paragraphs),'tables',len(d.tables),'sections',len(d.sections))
 for idx,p in enumerate(d.paragraphs[:100]):
  if p.text.strip():
   print(idx,repr(p.text),p.style.name, 'break',p.paragraph_format.page_break_before, 'runs',[(r.text[:24],r.font.name,r.font.size.pt if r.font.size else None,r.bold, bool(r._element.xpath('.//w:drawing'))) for r in p.runs[:3]])
 for ti,t in enumerate(d.tables):
  print('TABLE',ti)
  for ri,row in enumerate(t.rows):
   for ci,c in enumerate(row.cells):
    for pi,p in enumerate(c.paragraphs):
     print(f'cell {ri},{ci},p{pi}',repr(p.text),'alignment',p.alignment, 'runs',[(r.text[:26],r.font.name,r.font.size.pt if r.font.size else None,r.bold, bool(r._element.xpath('.//w:drawing'))) for r in p.runs])
