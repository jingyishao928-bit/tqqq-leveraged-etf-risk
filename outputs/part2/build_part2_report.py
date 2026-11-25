"""Produce the short Part 2 section for the group report."""
import argparse
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

PART2_ROOT = Path(__file__).resolve().parent


def build(source: Path, output: Path) -> None:
    """Convert the reviewed report Markdown to a styled Word document."""
    with TemporaryDirectory(prefix='part2-report-') as directory:
        raw = Path(directory) / 'report.docx'
        run(['pandoc', str(source.resolve()), '--from=markdown', '--to=docx',
             f'--resource-path={source.parent.resolve()}', '--output', str(raw)], check=True)
        doc = Document(raw)
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Inches(8.27), Inches(11.69)
    sec.top_margin, sec.bottom_margin = Inches(.70), Inches(.66)
    sec.left_margin = sec.right_margin = Inches(.79)
    ink = RGBColor.from_string('34383C')
    muted = RGBColor.from_string('62676B')
    for name,size in (
        ('Normal',11),('Body Text',11),('First Paragraph',11),('Compact',9.75),
        ('Heading 1',22),('Heading 2',15),('Heading 3',12),('Caption',9.5),('Image Caption',9.5),
    ):
        if name not in doc.styles:
            continue
        style = doc.styles[name]
        style.font.name,style.font.size,style.font.color.rgb = 'Times New Roman',Pt(size),ink
        properties = style.element.get_or_add_rPr()
        for key in ('themeColor','themeTint','themeShade'):
            properties.find(qn('w:color')).attrib.pop(qn('w:'+key),None)
        properties.rFonts.set(qn('w:eastAsia'),'Noto Serif CJK SC')
        formatting = style.paragraph_format
        formatting.space_after = Pt(5)
        formatting.line_spacing = 1.08
        if name.startswith('Heading'):
            formatting.space_before = Pt(12)
            formatting.keep_with_next = True
    for par in doc.paragraphs:
        if par.text.startswith(('2.3','2.4')):
            par.paragraph_format.page_break_before = True
        if par.text.strip() and not par.style.name.startswith('Heading'):
            par.paragraph_format.widow_control = True
    for table in doc.tables:
        table.rows[0]._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
        for i, table_row in enumerate(table.rows):
            table_row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
            for cell in table_row.cells:
                if i == 0:
                    shading = OxmlElement('w:shd')
                    shading.set(qn('w:fill'),'F2F3F4')
                    cell._tc.get_or_add_tcPr().append(shading)
                for par in cell.paragraphs:
                    par.paragraph_format.space_after = Pt(2)
                    par.paragraph_format.space_before = Pt(2)
                    for inline in par.runs:
                        inline.font.size = Pt(9 if len(table_row.cells) > 4 else 9.8)
                        inline.font.bold = i == 0
    for paragraph, label in (
        (sec.header.paragraphs[0],'RMSC 5003  /  GROUP PROJECT'),
        (sec.footer.paragraphs[0],'PART 2  /  '),
    ):
        mark = paragraph.add_run(label)
        mark.font.name, mark.font.size, mark.font.color.rgb = 'Times New Roman',Pt(8),muted
    foot = sec.footer.paragraphs[0]
    foot.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    field = OxmlElement('w:fldSimple')
    field.set(qn('w:instr'),'PAGE')
    foot._p.append(field)
    doc.core_properties.title = 'Daily-reset valuation and historical risk'
    doc.core_properties.subject = 'RMSC 5003 · Part 2 · Group report section'
    doc.core_properties.language = 'en-GB'
    doc.core_properties.author = ''
    doc.core_properties.last_modified_by = ''
    output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=PART2_ROOT/'report/Part2_Report.md')
    parser.add_argument('--output', type=Path, default=PART2_ROOT/'report/Part2_Report.docx')
    args = parser.parse_args()
    build(args.source, args.output)


if __name__ == '__main__':
    main()
