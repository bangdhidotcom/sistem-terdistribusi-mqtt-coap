"""Renderer kanonik: satu sumber blok -> PDF dan DOCX dengan isi identik.

Format: A4, Times New Roman 12 pt, seluruh teks hitam, tanpa garis pembatas
antar bagian. Gambar di DOCX disisipkan sebagai shape DrawingML editabel.
"""
from __future__ import annotations

import difflib
import html
import re
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

try:
    import fitz
except ImportError:
    fitz = None

from content import BLOCKS

ROOT = Path(__file__).resolve().parents[1]
OUT_PDF = ROOT / "laporan" / "Laporan_Akhir_Sistem_Terdistribusi.pdf"
OUT_DOCX = ROOT / "laporan" / "Laporan_Akhir_Sistem_Terdistribusi.docx"

BLACK = colors.black
GRID = colors.HexColor("#BFBFBF")
HEAD_FILL = colors.HexColor("#F0F0F0")
CALLOUT_FILL = colors.HexColor("#F7F7F7")
CONTENT_W = 17.0

FONT = "Times-Roman"
FONT_B = "Times-Bold"
FONT_I = "Times-Italic"

BOLD_RE = re.compile(r"\*\*(.+?)\*\*", re.S)
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
TOKEN_RE = re.compile(
    r"(<br\s*/?>|<b>|</b>|<i>|</i>|\[[^\]]+\]\([^)]+\)|&#\d+;|&amp;|&lt;|&gt;)",
    re.I,
)


def _pre(text: str) -> str:
    return BOLD_RE.sub(r"<b>\1</b>", str(text)).replace("<br>", "<br/>")


def inline_pdf(text: str) -> str:
    s = _pre(text)
    s = LINK_RE.sub(lambda m: "<link href='%s'>%s</link>" % (m.group(2), m.group(1)), s)
    return s.replace("<br>", "<br/>")


def _docx_hyperlink(paragraph, text: str, url: str) -> None:
    part = paragraph.part
    rid = part.relate_to(
        url,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True,
    )
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), rid)
    run = OxmlElement("w:r")
    r_pr = OxmlElement("w:rPr")
    rfonts = OxmlElement("w:rFonts")
    rfonts.set(qn("w:ascii"), "Times New Roman")
    rfonts.set(qn("w:hAnsi"), "Times New Roman")
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), "24")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "000000")
    underline = OxmlElement("w:u")
    underline.set(qn("w:val"), "single")
    r_pr.append(rfonts)
    r_pr.append(sz)
    r_pr.append(color)
    r_pr.append(underline)
    run.append(r_pr)
    t = OxmlElement("w:t")
    t.text = text
    run.append(t)
    hyperlink.append(run)
    paragraph._p.append(hyperlink)


def add_rich(paragraph, text: str) -> None:
    s = _pre(text)
    bold = italic = False
    for token in TOKEN_RE.split(s):
        if not token:
            continue
        low = token.lower()
        if low in ("<br>", "<br/>"):
            r = paragraph.add_run(" ")
            r.font.name = "Times New Roman"
            r.font.size = Pt(12)
            r.font.color.rgb = RGBColor(0, 0, 0)
            r.add_break()
        elif low == "<b>":
            bold = True
        elif low == "</b>":
            bold = False
        elif low == "<i>":
            italic = True
        elif low == "</i>":
            italic = False
        elif token.startswith("[") and "](" in token:
            m = LINK_RE.match(token)
            if m:
                _docx_hyperlink(paragraph, html.unescape(m.group(1)), m.group(2))
            else:
                paragraph.add_run(html.unescape(token))
        else:
            r = paragraph.add_run(html.unescape(token))
            r.bold = bold
            r.italic = italic
            r.font.name = "Times New Roman"
            r.font.size = Pt(12)
            r.font.color.rgb = RGBColor(0, 0, 0)


def _shade(cell, hex_color: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tc_pr.append(shd)


def _set_cell_text(cell, text: str, bold=False, size=10) -> None:
    cell.text = ""
    p = cell.paragraphs[0]
    add_rich(p, text)
    for r in p.runs:
        r.bold = bold or r.bold
        r.font.name = "Times New Roman"
        r.font.size = Pt(size)
        r.font.color.rgb = RGBColor(0, 0, 0)


def _force_tnr_black(paragraph) -> None:
    for r in paragraph.runs:
        r.font.name = "Times New Roman"
        r.font.color.rgb = RGBColor(0, 0, 0)


def _shade_cell(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def _style_table_docx(t, header_rows: int = 1, first_col: bool = False) -> None:
    """Beri garis tipis, kepala tabel biru muda, dan selang-seling baris."""
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement("w:" + edge)
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "6")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "B8C6D9")
        borders.append(el)
    t._tbl.tblPr.append(borders)
    for i, row in enumerate(t.rows):
        for j, cell in enumerate(row.cells):
            if i < header_rows:
                _shade_cell(cell, "E8EFFB")
            elif first_col and j == 0:
                _shade_cell(cell, "E8EFFB")
            elif i % 2 == 0:
                _shade_cell(cell, "F6F8FC")


def _style_docx(doc: Document) -> None:
    sec = doc.sections[0]
    sec.page_width = Cm(21.0)
    sec.page_height = Cm(29.7)
    sec.top_margin = Cm(2.0)
    sec.bottom_margin = Cm(2.0)
    sec.left_margin = Cm(2.0)
    sec.right_margin = Cm(2.0)
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    normal.paragraph_format.space_after = Pt(4)
    normal.paragraph_format.line_spacing = 0.95
    for name, size in (("Title", 16), ("Heading 1", 13), ("Heading 2", 12)):
        st = doc.styles[name]
        st.font.name = "Times New Roman"
        st.font.size = Pt(size)
        st.font.color.rgb = RGBColor(0, 0, 0)
        st.font.bold = True


def _img_size(path: Path, width_cm: float) -> float:
    with PILImage.open(path) as im:
        return width_cm * im.height / im.width


def _editable_xml(stem: str) -> str | None:
    for name in (f"{stem}_a4.xml", f"{stem}.xml"):
        p = ROOT / "output-xml" / name
        if p.exists():
            return p.read_text(encoding="utf-8")
    return None


def _add_editable_shape(doc, stem: str, para=None) -> bool:
    xml = _editable_xml(stem)
    if not xml:
        return False
    p = para if para is not None else doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p._p.append(parse_xml(xml))
    return True


def _add_picture(doc, rel_path: str, width_cm: float) -> bool:
    p = ROOT / rel_path
    if not p.exists():
        return False
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para.add_run().add_picture(str(p), width=Cm(min(width_cm, CONTENT_W)))
    return True


def _figure_caption(doc, caption: str) -> None:
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_rich(cap, caption)
    for run in cap.runs:
        run.italic = True
        run.font.name = "Times New Roman"
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(0, 0, 0)


def build_pdf() -> int:
    st = getSampleStyleSheet()
    st.add(ParagraphStyle("DocTitle", parent=st["Title"], fontName=FONT_B, fontSize=16,
                          leading=19, alignment=TA_CENTER, textColor=BLACK, spaceAfter=6))
    st.add(ParagraphStyle("DocSub", parent=st["Normal"], fontName=FONT, fontSize=11,
                          leading=14, alignment=TA_CENTER, textColor=BLACK, spaceAfter=8))
    st.add(ParagraphStyle("H1", parent=st["Heading1"], fontName=FONT_B, fontSize=13,
                          leading=16, textColor=BLACK, spaceBefore=8, spaceAfter=4))
    st.add(ParagraphStyle("H2", parent=st["Heading2"], fontName=FONT_B, fontSize=12,
                          leading=15, textColor=BLACK, spaceBefore=6, spaceAfter=3))
    st.add(ParagraphStyle("Body", parent=st["BodyText"], fontName=FONT, fontSize=12,
                          leading=13.2, alignment=TA_JUSTIFY, textColor=BLACK, spaceAfter=3))
    st.add(ParagraphStyle("List", parent=st["BodyText"], fontName=FONT, fontSize=11.5,
                          leading=13, leftIndent=12, textColor=BLACK, spaceAfter=2))
    st.add(ParagraphStyle("Cap", parent=st["Normal"], fontName=FONT_I, fontSize=9.5,
                          leading=11.5, alignment=TA_CENTER, textColor=BLACK, spaceAfter=3))
    st.add(ParagraphStyle("CallTitle", parent=st["Normal"], fontName=FONT_B, fontSize=11,
                          leading=13, textColor=BLACK, spaceAfter=1))
    st.add(ParagraphStyle("CallBody", parent=st["Normal"], fontName=FONT, fontSize=10.5,
                          leading=13, alignment=TA_JUSTIFY, textColor=BLACK))
    st.add(ParagraphStyle("Cell", parent=st["Normal"], fontName=FONT, fontSize=9,
                          leading=11, textColor=BLACK))
    st.add(ParagraphStyle("CellHead", parent=st["Normal"], fontName=FONT_B, fontSize=9,
                          leading=11, textColor=BLACK))

    doc = SimpleDocTemplate(
        str(OUT_PDF), pagesize=A4,
        leftMargin=2.0 * cm, rightMargin=2.0 * cm,
        topMargin=2.0 * cm, bottomMargin=2.0 * cm,
        title="Laporan Akhir Sistem Terdistribusi MQTT-CoAP",
        author="Kelompok Sistem Terdistribusi A",
    )

    def table(rows, widths=None, header=True):
        widths = widths or [CONTENT_W / len(rows[0])] * len(rows[0])
        total = float(sum(widths))
        if total > CONTENT_W:
            widths = [w * CONTENT_W / total for w in widths]
        t = Table(rows, colWidths=[w * cm for w in widths],
                  repeatRows=0, hAlign="CENTER")
        style = [
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B8C6D9")),
        ]
        if header:
            style += [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EFFB")),
                ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.HexColor("#2A5FD4")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                 [colors.white, colors.HexColor("#F6F8FC")]),
            ]
        t.setStyle(TableStyle(style))
        return t

    elems = []
    for b in BLOCKS:
        kind = b["type"]
        if kind == "title":
            elems += [Paragraph(inline_pdf(b["text"]), st["DocTitle"]),
                      Paragraph(inline_pdf(b["sub"]), st["DocSub"])]
        elif kind == "meta":
            elems.append(table([[Paragraph(inline_pdf(c), st["CellHead"] if i == 0 else st["Cell"])
                                 for i, c in enumerate(r)] for r in b["rows"]],
                               [3.0, 12.9], header=True))
        elif kind in ("h1", "h2"):
            elems.append(Paragraph(inline_pdf(b["text"]), st["H1" if kind == "h1" else "H2"]))
        elif kind == "p":
            elems.append(Paragraph(inline_pdf(b["text"]), st["Body"]))
        elif kind in ("bullets", "numbered"):
            for i, item in enumerate(b["items"]):
                prefix = "• " if kind == "bullets" else "%d. " % (i + 1)
                elems.append(Paragraph(prefix + inline_pdf(item), st["List"]))
        elif kind == "callout":
            elems.append(Paragraph(inline_pdf(b["text"]), st["Body"]))
        elif kind == "glossary":
            rows = [[Paragraph("Istilah", st["CellHead"]), Paragraph("Arti sederhana", st["CellHead"])]]
            rows += [[Paragraph(inline_pdf(a), st["Cell"]), Paragraph(inline_pdf(c), st["Cell"])]
                     for a, c in b["items"]]
            elems.append(table(rows, [3.2, 12.7]))
        elif kind == "table":
            rows = [[Paragraph(inline_pdf(c), st["CellHead"]) for c in b["header"]]]
            rows += [[Paragraph(inline_pdf(c), st["Cell"]) for c in row] for row in b["rows"]]
            elems.append(table(rows, b.get("widths_cm")))
        elif kind == "image":
            p = ROOT / b["path"]
            if p.exists():
                w = min(b.get("width_cm", 15), CONTENT_W) * cm
                im = Image(str(p), width=w, height=_img_size(p, w / cm) * cm)
                elems.append(KeepTogether([im, Paragraph(inline_pdf(b["caption"]), st["Cap"])]))
            else:
                elems.append(Paragraph("[gambar tidak tersedia: %s]" % b["path"], st["Cap"]))
        elif kind == "images_row":
            cells = []
            for item in b["items"]:
                p = ROOT / item["path"]
                if p.exists():
                    w = min(item.get("width_cm", 7.1), CONTENT_W / 2 - 0.2) * cm
                    im = Image(str(p), width=w, height=_img_size(p, w / cm) * cm)
                    cells.append([im, Paragraph(inline_pdf(item["caption"]), st["Cap"])])
                else:
                    cells.append([Paragraph("[gambar tidak tersedia: %s]" % item["path"], st["Cap"])])
            cw = CONTENT_W / len(cells)
            row = Table([[c for c in cells]], colWidths=[cw * cm] * len(cells), hAlign="CENTER")
            row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                                     ("LEFTPADDING", (0, 0), (-1, -1), 2),
                                     ("RIGHTPADDING", (0, 0), (-1, -1), 2)]))
            elems.append(KeepTogether([row]))
        elif kind == "pagebreak":
            elems.append(PageBreak())

    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    doc.build(elems)
    if fitz is None:
        return 0
    with fitz.open(OUT_PDF) as d:
        return d.page_count


def build_docx() -> tuple[int, int]:
    doc = Document()
    _style_docx(doc)

    for b in BLOCKS:
        kind = b["type"]
        if kind == "title":
            h = doc.add_heading(b["text"], 0)
            h.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in h.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(16)
                r.font.color.rgb = RGBColor(0, 0, 0)
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_rich(p, b["sub"])
        elif kind == "meta":
            t = doc.add_table(rows=0, cols=2)
            t.style = None
            t.alignment = WD_TABLE_ALIGNMENT.CENTER
            for row in b["rows"]:
                cells = t.add_row().cells
                _set_cell_text(cells[0], row[0], bold=True, size=10)
                _set_cell_text(cells[1], row[1], size=10)
            t.columns[0].width = Cm(3)
            t.columns[1].width = Cm(12.9)
            _style_table_docx(t, header_rows=0, first_col=True)
        elif kind in ("h1", "h2"):
            level = 1 if kind == "h1" else 2
            h = doc.add_heading(b["text"], level)
            for r in h.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(13 if level == 1 else 12)
                r.font.color.rgb = RGBColor(0, 0, 0)
        elif kind == "p":
            add_rich(doc.add_paragraph(), b["text"])
        elif kind in ("bullets", "numbered"):
            for i, item in enumerate(b["items"]):
                prefix = "• " if kind == "bullets" else "%d. " % (i + 1)
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Cm(0.5)
                add_rich(p, prefix + item)
        elif kind == "callout":
            add_rich(doc.add_paragraph(), b["text"])
        elif kind == "glossary":
            t = doc.add_table(rows=1, cols=2)
            t.style = None
            for i, h in enumerate(["Istilah", "Arti sederhana"]):
                _set_cell_text(t.rows[0].cells[i], h, bold=True, size=10)
            for a, c in b["items"]:
                cells = t.add_row().cells
                _set_cell_text(cells[0], a, bold=True, size=10)
                _set_cell_text(cells[1], c, size=10)
            t.columns[0].width = Cm(3.2)
            t.columns[1].width = Cm(12.7)
            _style_table_docx(t)
        elif kind == "table":
            t = doc.add_table(rows=1, cols=len(b["header"]))
            t.style = None
            t.alignment = WD_TABLE_ALIGNMENT.CENTER
            for i, h in enumerate(b["header"]):
                _set_cell_text(t.rows[0].cells[i], h, bold=True, size=9.5)
            for row in b["rows"]:
                cells = t.add_row().cells
                for i, val in enumerate(row):
                    _set_cell_text(cells[i], val, size=9.5)
            widths = b.get("widths_cm") or [CONTENT_W / len(b["header"])] * len(b["header"])
            total = float(sum(widths))
            if total > CONTENT_W:
                widths = [w * CONTENT_W / total for w in widths]
            for col, w in zip(t.columns, widths):
                col.width = Cm(w)
            _style_table_docx(t)
        elif kind == "image":
            if not _add_editable_shape(doc, Path(b["path"]).stem):
                if not _add_picture(doc, b["path"], b.get("width_cm", 15)):
                    add_rich(doc.add_paragraph(), "[gambar tidak tersedia: %s]" % b["path"])
            _figure_caption(doc, b["caption"])
        elif kind == "images_row":
            t = doc.add_table(rows=1, cols=len(b["items"]))
            t.style = None
            t.alignment = WD_TABLE_ALIGNMENT.CENTER
            cw = CONTENT_W / len(b["items"]) - 0.2
            for i, item in enumerate(b["items"]):
                cell = t.rows[0].cells[i]
                cell.width = Cm(cw)
                pic = cell.paragraphs[0]
                pic.alignment = WD_ALIGN_PARAGRAPH.CENTER
                stem = Path(item["path"]).stem
                if not _add_editable_shape(doc, stem, para=pic):
                    p = ROOT / item["path"]
                    if p.exists():
                        pic.add_run().add_picture(str(p), width=Cm(cw))
                cap = cell.add_paragraph()
                cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                add_rich(cap, item["caption"])
                for run in cap.runs:
                    run.italic = True
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(10)
                    run.font.color.rgb = RGBColor(0, 0, 0)
        elif kind == "pagebreak":
            doc.add_page_break()

    for p in doc.paragraphs:
        _force_tnr_black(p)
        p.paragraph_format.line_spacing = 0.95
        p.paragraph_format.space_after = Pt(1)
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    _force_tnr_black(p)
                    p.paragraph_format.space_after = Pt(0)

    OUT_DOCX.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT_DOCX)
    return len(doc.paragraphs), len(doc.tables)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def _visible_text(node) -> str:
    """Teks tubuh dokumen, tanpa label di dalam shape DrawingML editabel."""
    out = []
    for t in node.iter(qn("w:t")):
        anc = t.getparent()
        inside_drawing = False
        while anc is not None:
            if anc.tag == qn("w:drawing"):
                inside_drawing = True
                break
            anc = anc.getparent()
        if not inside_drawing:
            out.append(t.text or "")
    return "".join(out)


def verify_identity() -> float:
    if fitz is None:
        return 0.0
    with fitz.open(OUT_PDF) as d:
        pdf = _norm(" ".join(page.get_text() for page in d))
    doc = Document(OUT_DOCX)
    parts = []
    for child in doc.element.body.iterchildren():
        if child.tag == qn("w:p"):
            parts.append(_visible_text(child))
        elif child.tag == qn("w:tbl"):
            cells = [_visible_text(tc) for tc in child.iter(qn("w:tc"))]
            parts.append(" ".join(cells))
    word = _norm(" ".join(parts))
    return difflib.SequenceMatcher(None, pdf, word, autojunk=False).ratio()


if __name__ == "__main__":
    pages = build_pdf()
    paras, tables = build_docx()
    ratio = verify_identity()
    print("PDF halaman :", pages)
    print("DOCX paragraf:", paras, "tabel:", tables)
    print("Kesamaan teks: %.2f%%" % (ratio * 100))
    if pages > 10:
        print("PERINGATAN: PDF melebihi 10 halaman")
