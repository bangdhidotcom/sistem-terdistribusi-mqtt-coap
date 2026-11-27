"""Buat DOCX berisi 7 gambar (diagram + grafik) sebagai shape Word editabel."""
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "laporan" / "Diagram_Editabel_Word.docx"

NAMES = [
    ("mqtt_coap_architecture", "Gambar 1. Arsitektur enam peran logis."),
    ("flow_mqtt_to_coap", "Gambar 2. Enam tahap MQTT ke CoAP."),
    ("flow_coap_to_mqtt", "Gambar 3. Enam tahap CoAP ke MQTT."),
    ("delay_e2e_per_menit", "Gambar 4. Delay E2E per menit."),
    ("delay_konversi_per_menit", "Gambar 5. Delay konversi per menit."),
    ("cpu_per_menit", "Gambar 6. CPU per menit."),
    ("perbandingan_artikel", "Gambar 7. Loss artikel vs replikasi."),
]


def insert_drawing(doc, name, caption):
    src = ROOT / "output-xml" / f"{name}.xml"
    if not src.exists():
        return False
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p._p.append(parse_xml(src.read_text(encoding="utf-8")))
    cap = doc.add_paragraph(caption)
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for r in cap.runs:
        r.font.name = "Times New Roman"
        r.font.size = Pt(10)
        r.font.color.rgb = RGBColor(0, 0, 0)
    return True


def main():
    doc = Document()
    sec = doc.sections[0]
    sec.top_margin = sec.bottom_margin = Cm(2.5)
    sec.left_margin = sec.right_margin = Cm(2.5)
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    normal.font.color.rgb = RGBColor(0, 0, 0)

    doc.core_properties.title = "Diagram dan Grafik Editabel - Konversi MQTT CoAP"
    doc.core_properties.author = "Kelompok Sistem Terdistribusi A"
    h = doc.add_heading("Diagram dan Grafik Editabel Word", 0)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(
        "Tujuh gambar berikut disisipkan sebagai elemen drawing Word native. "
        "Setiap kotak, garis, dan label dapat diklik serta diubah di Word. "
        "Sumber XML ada di folder output-xml/."
    )
    ok = 0
    for name, caption in NAMES:
        if insert_drawing(doc, name, caption):
            ok += 1
    doc.save(OUT)
    print("DOCX editabel dibuat:", OUT, "shape:", ok)


if __name__ == "__main__":
    main()
