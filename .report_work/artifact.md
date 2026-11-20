# CampusFix report template distillation

## References
- `C:\Users\Aman Kumar\Downloads\Cover Page_CSE.docx` — SHA-256 `87acfd8632579c64ffd263fa0e0c690dfd9bc8636517c5b324c81cc0764e027b`; one portrait US Letter section. One full-width, one-cell cover table, two embedded images, cover fields for report title, degree, department, three/four student slots, supervisor and institution. Use as the working base; preserve both image drawings and cover-table layout.
- `C:\Users\Aman Kumar\Downloads\Inner Page_CSE.docx` — SHA-256 `3c8c5b4f669c687cf8244a2d27f00e65f5103cb084be96c8c5ad5c463580c90f`; two sections, first A4 portrait (8.264 × 11.708 in; margins top .944, bottom .833, left .764, right .569 in; footer distance .642 in), second Letter portrait. Contains declaration, certificate, acknowledgement, abstract (max 250 words), contents, lists of figures/tables, symbols and abbreviations. Use front-matter order and A4 page pattern.
- `C:\Users\Aman Kumar\Downloads\Final report 5th Sem_CSE.docx` — inspect for chapter organization and technical report requirements. One Letter portrait section (margins top 1.378, bottom .788, left 1.378, right .788 in). It is an instructional scaffold, not a finished report; use the full-stack SRS, system design, implementation/results, conclusion, appendices, and numeric-reference requirements, replacing all instructions/examples.
- Page counts and visual render evidence are unresolved: the bundled `render_docx.py` could not locate its required bundled `soffice.exe`, and Word review was stopped with Escape. The final DOCX passed ZIP integrity and structural checks; the two cover image assets remain embedded. References are unmodified.

## Typography and recurring components
- Cover typography and layout come directly from cover table: centered `Mini Project Report`, title 20 pt, author/degree/department lines around 13 pt, supervisor around 11 pt, college/affiliation lines, existing institution artwork. Preserve the image paragraph and its drawings.
- Main report: Times New Roman 12 pt, justified, 1.5 line spacing, paragraph after 6 pt. A4 portrait; use the Inner Page first-section margins above. Chapter headings centered, Times New Roman 14 pt bold; Heading 2 Verdana 12 pt bold; Heading 3 Arial 13 pt bold (reference styles).
- No decorative rules. Use restrained gray table header fill and light-gray borders; captions below figures, table captions above tables, consistent chapter figure/table numbering.
- Use lower-Roman page numbering for front matter and restart Arabic numbering at Chapter 1. No running header. Center page number in footer.

## Ordered content and editable slots
1. Cover: project title; degree/department; exactly three student names and supplied roll numbers; supervisor name and CSE department; supplied institution and affiliation; month/year.
2. Front matter: declaration; supervisor certificate with signature/date slots; acknowledgement; abstract <=250 words; table of contents; lists of figures/tables; abbreviations.
3. Chapter 1 Introduction: problem, motivation, objectives, scope/limitations, related work, report organization.
4. Chapter 2 Software Requirements Specification: product perspective, actors, interfaces, functional/nonfunctional requirements, constraints/assumptions, use cases.
5. Chapter 3 System Design and Methodology: architecture diagram, data flow/use cases, ER overview, ML pipeline.
6. Chapter 4 Implementation and Results: implementation, test cases, current ML evaluation and limitations, measured results.
7. Chapter 5 Conclusion: completed objectives, known limits, future work.
8. Appendices: API overview, data dictionary, deployment/pilot notes; References in numeric order.

## Stable locators and package preservation
- Cover edit slots are the one-cell table at `word/document.xml` / table 0 / row 0 / cell 0 / paragraphs 1, 3, 5, 8, 10, 12, 15, 17, 19, 21-24, 26-29, 33, 35, 37, 39. Embedded institution artwork is in paragraph 31 and must remain untouched. Add subsequent report content after the cover table and retain the original images and relationships.
- Cover package includes `word/media/image1.png` and `word/media/image2.png`; do not replace. Inner Page includes footer and media assets but is reference-only. Final report scaffold contains example tables and body instructions; do not copy sample content.
- Source files must remain byte-for-byte unchanged. Visual fidelity should be checked against the cover and inner-page samples, especially title page, front matter, chapter headings, tables, diagrams/captions, and footer numbering.
