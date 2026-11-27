"""Buat DOCX berisi diagram DrawingML editabel dari output-xml."""
from pathlib import Path
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.shared import Pt
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "laporan" / "Diagram_Editabel_Word.docx"

def insert_drawing(doc, name):
    xml = (ROOT / "output-xml" / f"{name}.xml").read_text(encoding="utf-8")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p._p.append(parse_xml(xml))
    doc.add_paragraph(f"Gambar: {name} (shape Word editabel; sumber XML di output-xml/).")

def main():
    doc = Document()
    doc.core_properties.title = "Diagram Editabel - Konversi MQTT CoAP"
    doc.core_properties.author = "Kelompok Sistem Terdistribusi A"
    h = doc.add_heading("Diagram Editabel Word", 0)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("Dokumen ini menyisipkan elemen <w:drawing> native dari folder output-xml. "
                      "Setiap kotak dan panah dapat diklik serta diubah di Microsoft Word. "
                      "File PNG dengan nama yang sama tersedia di folder output untuk versi raster.")
    for style in doc.styles:
        if style.name == "Normal":
            style.font.name = "Calibri"
            style.font.size = Pt(10)
    doc.add_heading("1. Arsitektur Enam Peran", level=1)
    insert_drawing(doc, "mqtt_coap_architecture")
    doc.add_page_break()
    doc.add_heading("2. Alur MQTT ke CoAP", level=1)
    insert_drawing(doc, "flow_mqtt_to_coap")
    doc.add_page_break()
    doc.add_heading("3. Alur CoAP ke MQTT", level=1)
    insert_drawing(doc, "flow_coap_to_mqtt")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUT))
    print("DOCX dibuat:", OUT)

if __name__ == "__main__":
    main()
