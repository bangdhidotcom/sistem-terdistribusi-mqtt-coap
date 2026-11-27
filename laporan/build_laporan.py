"""Renderer kanonik: satu sumber blok -> PDF dan DOCX dengan isi identik.

Jalankan dari mana saja:
    python laporan/build_laporan.py
"""
from __future__ import annotations

import difflib
import html
import re
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
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

INK = colors.HexColor("#1E2A47")
BLUE = colors.HexColor("#2A5FD4")
MUTED = colors.HexColor("#5B6B84")
PALE = colors.HexColor("#EEF3FB")
GRID = colors.HexColor("#9AA5B1")

# ---------------------------------------------------------------- inline markup

BOLD_RE = re.compile(r"\*\*(.+?)\*\*", re.S)
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
TOKEN_RE = re.compile(
    r"(<br\s*/?>|<b>|</b>|<i>|</i>|\[[^\]]+\]\([^)]+\)|&#\d+;|&amp;|&lt;|&gt;)",
    re.I,
)


def _pre(text: str) -> str:
    """Samakan markup ringan sebelum diparse kedua renderer."""
    return BOLD_RE.sub(r"<b>\1</b>", str(text)).replace("<br>", "<br/>")


def inline_pdf(text: str) -> str:
    s = _pre(text)

    def link(m):
        return "<link href='%s'>%s</link>" % (m.group(2), m.group(1))

    s = LINK_RE.sub(link, s)
    return s.replace("<br/>", "<br/>").replace("<br>", "<br/>")


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
    color.set(qn("w:val"), "2A5FD4")
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
    """Tulis teks ber-markup sebagai run DOCX (bold/italic/link/newline)."""
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


def _set_cell_text(cell, text: str, bold=False, color=None, size=8) -> None:
    cell.text = ""
    p = cell.paragraphs[0]
    add_rich(p, text)
    for r in p.runs:
        r.bold = bold or r.bold
        r.font.size = Pt(size)
        if color:
            r.font.color.rgb = RGBColor.from_string(color)


def _style_docx(doc: Document) -> None:
    sec = doc.sections[0]
    sec.top_margin = Cm(1.25)
    sec.bottom_margin = Cm(1.25)
    sec.left_margin = Cm(1.25)
    sec.right_margin = Cm(1.25)
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(9)
    normal.paragraph_format.space_after = Pt(4)
    for name, size, color in (("Title", 18, "1E2A47"), ("Heading 1", 11.5, "1E2A47"), ("Heading 2", 10, "2A5FD4")):
        st = doc.styles[name]
        st.font.name = "Calibri"
        st.font.size = Pt(size)
        st.font.color.rgb = RGBColor.from_string(color)
        st.font.bold = True


def _img_size(path: Path, width_cm: float) -> float:
    with PILImage.open(path) as im:
        return width_cm * im.height / im.width


# ---------------------------------------------------------------- PDF

def build_pdf() -> int:
    st = getSampleStyleSheet()
    st.add(ParagraphStyle("DocTitle", parent=st["Title"], fontSize=17, leading=21,
                          alignment=TA_CENTER, textColor=INK, spaceAfter=6))
    st.add(ParagraphStyle("DocSub", parent=st["Normal"], fontSize=9, leading=12.5,
                          alignment=TA_CENTER, textColor=MUTED, spaceAfter=8))
    st.add(ParagraphStyle("H1", parent=st["Heading1"], fontSize=11.5, leading=14,
                          textColor=INK, spaceBefore=9, spaceAfter=4))
    st.add(ParagraphStyle("H2", parent=st["Heading2"], fontSize=10, leading=12.5,
                          textColor=BLUE, spaceBefore=6, spaceAfter=3))
    st.add(ParagraphStyle("Body", parent=st["BodyText"], fontSize=8.6, leading=11.4,
                          alignment=TA_JUSTIFY, spaceAfter=4))
    st.add(ParagraphStyle("List", parent=st["BodyText"], fontSize=8.4, leading=11,
                          leftIndent=10, spaceAfter=2))
    st.add(ParagraphStyle("Cap", parent=st["Normal"], fontSize=7.2, leading=9,
                          alignment=TA_CENTER, textColor=MUTED, spaceAfter=6))
    st.add(ParagraphStyle("CallTitle", parent=st["Normal"], fontSize=8.8, leading=11,
                          fontName="Helvetica-Bold", textColor=BLUE, spaceAfter=2))
    st.add(ParagraphStyle("CallBody", parent=st["Normal"], fontSize=8.3, leading=11,
                          alignment=TA_JUSTIFY))
    st.add(ParagraphStyle("Cell", parent=st["Normal"], fontSize=7.4, leading=9.2))
    st.add(ParagraphStyle("CellHead", parent=st["Normal"], fontSize=7.4, leading=9.2,
                          fontName="Helvetica-Bold", textColor=colors.white))

    doc = SimpleDocTemplate(
        str(OUT_PDF), pagesize=A4,
        leftMargin=1.25 * cm, rightMargin=1.25 * cm,
        topMargin=1.2 * cm, bottomMargin=1.2 * cm,
        title="Laporan Akhir Sistem Terdistribusi MQTT-CoAP",
        author="Kelompok Sistem Terdistribusi A",
    )

    def table(rows, widths=None, header=True):
        widths = widths or [16.0 / len(rows[0]) * cm] * len(rows[0])
        t = Table(rows, colWidths=[w * cm if isinstance(w, (int, float)) else w for w in widths],
                  repeatRows=1 if header else 0, hAlign="CENTER")
        style = [
            ("GRID", (0, 0), (-1, -1), 0.4, GRID),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ]
        if header:
            style += [
                ("BACKGROUND", (0, 0), (-1, 0), INK),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
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
                               [3.0, 13.0], header=True))
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
            t = Table(inner, colWidths=[16.0 * cm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), PALE),
                ("BOX", (0, 0), (-1, -1), 0.8, BLUE),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            elems += [t, Spacer(1, 4)]
        elif kind == "glossary":
            rows = [[Paragraph("Istilah", st["CellHead"]), Paragraph("Arti sederhana", st["CellHead"])]]
            rows += [[Paragraph(inline_pdf(a), st["Cell"]), Paragraph(inline_pdf(c), st["Cell"])]
                     for a, c in b["items"]]
            elems.append(table(rows, [3.2, 12.8]))
        elif kind == "table":
            rows = [[Paragraph(inline_pdf(c), st["CellHead"]) for c in b["header"]]]
            rows += [[Paragraph(inline_pdf(c), st["Cell"]) for c in row] for row in b["rows"]]
            elems.append(table(rows, b.get("widths_cm")))
        elif kind == "image":
            p = ROOT / b["path"]
            if p.exists():
                w = b.get("width_cm", 15) * cm
                im = Image(str(p), width=w, height=_img_size(p, w / cm) * cm)
                elems.append(KeepTogether([im, Paragraph(inline_pdf(b["caption"]), st["Cap"])]))
            else:
                elems.append(Paragraph("[gambar tidak tersedia: %s]" % b["path"], st["Cap"]))
        elif kind == "images_row":
            cells = []
            for item in b["items"]:
                p = ROOT / item["path"]
                if p.exists():
                    w = item.get("width_cm", 7.1) * cm
                    im = Image(str(p), width=w, height=_img_size(p, w / cm) * cm)
                    cells.append([im, Paragraph(inline_pdf(item["caption"]), st["Cap"])])
                else:
                    cells.append([Paragraph("[gambar tidak tersedia: %s]" % item["path"], st["Cap"])])
            row = Table([[c for c in cells]], colWidths=[8.15 * cm] * len(cells), hAlign="CENTER")
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


# ---------------------------------------------------------------- DOCX

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
                _set_cell_text(cells[0], row[0], bold=True, color="FFFFFF")
                _shade(cells[0], "1E2A47")
                _set_cell_text(cells[1], row[1])
            t.columns[0].width = Cm(3)
            t.columns[1].width = Cm(13)
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
            p.paragraph_format.left_indent = Cm(0.3)
            add_rich(p, "**" + b["title"] + ":** " + b["text"])
            p_pr = p._p.get_or_add_pPr()
            shd = OxmlElement("w:shd")
            shd.set(qn("w:val"), "clear")
            shd.set(qn("w:fill"), "EEF3FB")
            p_pr.append(shd)
        elif kind == "glossary":
            t = doc.add_table(rows=1, cols=2)
            t.style = "Table Grid"
            for i, h in enumerate(["Istilah", "Arti sederhana"]):
                _set_cell_text(t.rows[0].cells[i], h, bold=True, color="FFFFFF")
                _shade(t.rows[0].cells[i], "1E2A47")
            for a, c in b["items"]:
                cells = t.add_row().cells
                _set_cell_text(cells[0], a, bold=True)
                _set_cell_text(cells[1], c)
            t.columns[0].width = Cm(3.2)
            t.columns[1].width = Cm(12.8)
        elif kind == "table":
            t = doc.add_table(rows=1, cols=len(b["header"]))
            t.style = "Table Grid"
            t.alignment = WD_TABLE_ALIGNMENT.CENTER
            for i, h in enumerate(b["header"]):
                _set_cell_text(t.rows[0].cells[i], h, bold=True, color="FFFFFF")
                _shade(t.rows[0].cells[i], "1E2A47")
            for row in b["rows"]:
                cells = t.add_row().cells
                for i, val in enumerate(row):
                    _set_cell_text(cells[i], val)
            widths = b.get("widths_cm") or [16 / len(b["header"])] * len(b["header"])
            for col, w in zip(t.columns, widths):
                col.width = Cm(w)
        elif kind == "image":
            p = ROOT / b["path"]
            if p.exists():
                pic = doc.add_paragraph()
                pic.alignment = WD_ALIGN_PARAGRAPH.CENTER
                pic.add_run().add_picture(str(p), width=Cm(b.get("width_cm", 15)))
                cap = doc.add_paragraph()
                cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = add_rich(cap, b["caption"])
                for run in cap.runs:
                    run.italic = True
                    run.font.size = Pt(7.2)
            else:
                add_rich(doc.add_paragraph(), "[gambar tidak tersedia: %s]" % b["path"])
        elif kind == "images_row":
            t = doc.add_table(rows=1, cols=len(b["items"]))
            t.autofit = False
            for i, item in enumerate(b["items"]):
                cell = t.cell(0, i)
                cell.text = ""
                p = cell.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                path = ROOT / item["path"]
                if path.exists():
                    p.add_run().add_picture(str(path), width=Cm(item.get("width_cm", 7.1)))
                cap = cell.add_paragraph()
                cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                add_rich(cap, item["caption"])
                for run in cap.runs:
                    run.italic = True
                    run.font.size = Pt(7)
                cell.width = Cm(8.1)
        elif kind == "pagebreak":
            doc.add_page_break()

    OUT_DOCX.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT_DOCX)
    return len(doc.paragraphs), len(doc.tables)


# ---------------------------------------------------------------- verification

def _norm(text: str) -> str:
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def verify_identity() -> float:
    if fitz is None:
        return 0.0
    with fitz.open(OUT_PDF) as d:
        pdf = _norm(" ".join(page.get_text() for page in d))
    doc = Document(OUT_DOCX)
    parts = []
    for child in doc.element.body.iterchildren():
        if child.tag in (qn("w:p"), qn("w:tbl")):
            parts.append("".join(t.text or "" for t in child.iter(qn("w:t"))))
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
