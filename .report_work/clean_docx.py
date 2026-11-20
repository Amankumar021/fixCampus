from docx import Document
from docx.oxml.ns import qn

path='CampusFix_Project_Report.docx'
doc=Document(path)
paras=doc.paragraphs
# The previous build pass wrote the last twelve paragraphs then appended the
# duplicate chapter block. Remove that known duplicate tail by locating second
# occurrence of CHAPTER 3 and its last References heading.
heads=[(i,p.text) for i,p in enumerate(paras) if p.text in ('CHAPTER 3','CHAPTER 4','CHAPTER 5','APPENDIX A: API SUMMARY','APPENDIX B: DATA AND DEPLOYMENT NOTES','REFERENCES')]
second=next(i for i,p in enumerate(paras) if p.text=='CHAPTER 3' and i>100)
# Keep the first complete chapters through references, then the final front matter;
# drop duplicated chapters and appendices between the two references headings.
lastref=max(i for i,p in enumerate(paras) if p.text=='REFERENCES')
for p in list(paras[second:lastref+1]):
    p._element.getparent().remove(p._element)
# Remove repeated front matter appended after the duplicate chapter sequence.
paras=doc.paragraphs
decls=[i for i,p in enumerate(paras) if p.text=='DECLARATION']
for p in list(paras[decls[-1]:]):
    p._element.getparent().remove(p._element)
doc.save(path)
print('cleaned',len(doc.paragraphs),len(doc.tables),len(doc.inline_shapes))
