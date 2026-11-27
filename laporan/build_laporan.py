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
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "000000")
    underline = OxmlElement("w:u")
    underline.set(qn("w:val"), "single")
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
            paragraph.add_run().add_break()
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


def _style_docx(doc: Document) -> None:
    sec = doc.sections[0]
    sec.top_margin = Cm(2.0)
    sec.bottom_margin = Cm(2.0)
    sec.left_margin = Cm(2.0)
    sec.right_margin = Cm(2.0)
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    normal.paragraph_format.space_after = Pt(4)
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


def _add_editable_shape(doc, stem: str) -> bool:
    xml = _editable_xml(stem)
    if not xml:
        return False
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p._p.append(parse_xml(xml))
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
                  repeatRows=1 if header else 0, hAlign="CENTER")
        style = [
            ("GRID", (0, 0), (-1, -1), 0.35, GRID),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ]
        if header:
            style += [
                ("BACKGROUND", (0, 0), (-1, 0), HEAD_FILL),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CALLOUT_FILL]),
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
            inner = [[Paragraph(inline_pdf(b["title"]), st["CallTitle"])],
                     [Paragraph(inline_pdf(b["text"]), st["CallBody"])]]
            t = Table(inner, colWidths=[CONTENT_W * cm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), CALLOUT_FILL),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            elems += [t, Spacer(1, 3)]
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
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_rich(p, b["sub"])
        elif kind == "meta":
            t = doc.add_table(rows=0, cols=2)
            t.style = "Table Grid"
            t.alignment = WD_TABLE_ALIGNMENT.CENTER
            for row in b["rows"]:
                cells = t.add_row().cells
                _set_cell_text(cells[0], row[0], bold=True, size=10)
                _shade(cells[0], "F0F0F0")
                _set_cell_text(cells[1], row[1], size=10)
            t.columns[0].width = Cm(3)
            t.columns[1].width = Cm(12.9)
        elif kind in ("h1", "h2"):
            doc.add_heading(b["text"], 1 if kind == "h1" else 2)
        elif kind == "p":
            add_rich(doc.add_paragraph(), b["text"])
        elif kind in ("bullets", "numbered"):
            for i, item in enumerate(b["items"]):
                prefix = "• " if kind == "bullets" else "%d. " % (i + 1)
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Cm(0.5)
                add_rich(p, prefix + item)
        elif kind == "callout":
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.2)
            add_rich(p, "**" + b["title"] + ":** " + b["text"])
            p_pr = p._p.get_or_add_pPr()
            shd = OxmlElement("w:shd")
            shd.set(qn("w:val"), "clear")
            shd.set(qn("w:fill"), "F7F7F7")
            p_pr.append(shd)
        elif kind == "glossary":
            t = doc.add_table(rows=1, cols=2)
            t.style = "Table Grid"
            for i, h in enumerate(["Istilah", "Arti sederhana"]):
                _set_cell_text(t.rows[0].cells[i], h, bold=True, size=10)
                _shade(t.rows[0].cells[i], "F0F0F0")
            for a, c in b["items"]:
                cells = t.add_row().cells
                _set_cell_text(cells[0], a, bold=True, size=10)
                _set_cell_text(cells[1], c, size=10)
            t.columns[0].width = Cm(3.2)
            t.columns[1].width = Cm(12.7)
        elif kind == "table":
            t = doc.add_table(rows=1, cols=len(b["header"]))
            t.style = "Table Grid"
            t.alignment = WD_TABLE_ALIGNMENT.CENTER
            for i, h in enumerate(b["header"]):
                _set_cell_text(t.rows[0].cells[i], h, bold=True, size=9.5)
                _shade(t.rows[0].cells[i], "F0F0F0")
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
        elif kind == "image":
            stem = Path(b["path"]).stem
            if not _add_editable_shape(doc, stem):
                p = ROOT / b["path"]
                if p.exists():
                    pic = doc.add_paragraph()
                    pic.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    pic.add_run().add_picture(str(p), width=Cm(min(b.get("width_cm", 15), CONTENT_W)))
                else:
                    add_rich(doc.add_paragraph(), "[gambar tidak tersedia: %s]" % b["path"])
            _figure_caption(doc, b["caption"])
        elif kind == "images_row":
            for item in b["items"]:
                stem = Path(item["path"]).stem
                if not _add_editable_shape(doc, stem):
                    p = ROOT / item["path"]
                    if p.exists():
                        pic = doc.add_paragraph()
                        pic.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        pic.add_run().add_picture(str(p), width=Cm(min(item.get("width_cm", 7.1), CONTENT_W)))
                _figure_caption(doc, item["caption"])
        elif kind == "pagebreak":
            doc.add_page_break()

    OUT_DOCX.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT_DOCX)
    return len(doc.paragraphs), len(doc.tables)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def verify_identity() -> float:
    if fitz is None:
        return 0.0
    with fitz.open(OUT_PDF) as d:
        pdf = _norm(" ".join(page.get_text() for page in d))
    doc = Document(OUT_DOCX)
    parts = []
    for child in doc.element.body.iterchildren():
        if child.tag in (qn("w:p"), qn("w:tbl")):
            parts.append("".join((t.text or "") for t in child.iter(qn("w:t"), qn("a:t"))))
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
