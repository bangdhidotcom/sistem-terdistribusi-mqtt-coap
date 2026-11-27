import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from vendor.jump2.uml_core import Diagram, C, FILL
from vendor.jump2.uml_drawml import to_drawingml
from vendor.jump2.uml_png import render_png
from vendor.jump2.uml_validate import validate, report_text_fit

def build_architecture():
    d = Diagram("Architecture", 26, 17)
    d.label_at(13, 0.55, "Arsitektur Sistem Replikasi MQTT <-> CoAP", pt=12, bold=True)

    # --- 3 swimlane: WAJIB container=True agar validator tidak menganggapnya node.
    # Kanvas tinggi 11 (y 2..13) supaya legenda di bawah tidak menimpa panel.
    d.rrect("side_mqtt", 0.5, 2, 7.5, 11, fill=FILL["panel"],
            line=C["gray"], container=True)
    d.label_chip(0.5, 1.45, "SISI MQTT (TCP)", pt=9, bold=True,
                 color=C["white"], fill=C["ink"])

    d.rrect("side_conv", 9, 2, 8, 11, fill=FILL["sky"],
            line=C["gray"], container=True)
    d.label_chip(9, 1.45, "CONVERSION SERVER", pt=9, bold=True,
                 color=C["white"], fill=C["purple_d"])

    d.rrect("side_coap", 18, 2, 7.5, 11, fill=FILL["panel"],
            line=C["gray"], container=True)
    d.label_chip(18, 1.45, "SISI COAP (UDP)", pt=9, bold=True,
                 color=C["white"], fill=C["ink"])

    # --- 6 peran logis sesuai tabel spek (nomor 1..6)
    def comp(id_, x, y, w, h, text, color, fill, badge):
        d.rrect(id_, x, y, w, h, fill=fill, line=color, lw=1.6)
        # badge nomor: dipusatkan tepat di atas kotak
        d.label_chip(x + w / 2 - 0.20, y - 0.30, str(badge),
                     pt=9, fill=color, color=C["white"])
        d.rect(None, x, y + 0.4, w, h - 0.4, text=text, tsize=8, bold=True)
        return x + w / 2, y + h / 2

    comp("p1", 2, 3, 4.5, 2.5, "MQTT Publisher\niot/mqtt_to_coap",
         C["blue_d"], FILL["blue"], 1)
    comp("p5", 2, 6, 4.5, 2.5, "MQTT Subscriber\niot/coap_to_mqtt",
         C["blue_d"], FILL["blue"], 5)
    comp("p2", 2, 9, 4.5, 2.5, "MQTT Broker\nport 1883 / 1884",
         C["blue_d"], FILL["blue"], 2)
    comp("p3", 10.75, 5, 4.5, 5, "Conversion Server\ndedup ID + anti-loop",
         C["purple_d"], FILL["purple"], 3)
    comp("p4", 19.5, 3, 4.5, 2.5, "CoAP Server\nport 5683 / 5684",
         C["orange_d"], FILL["orange"], 4)
    comp("p6", 19.5, 9, 4.5, 2.5, "CoAP Client\nGET memverifikasi",
         C["orange_d"], FILL["orange"], 6)

    # --- Jalur 1: MQTT -> CoAP (solid biru)
    d.edge([(6.5, 10.25), (10.75, 7.5)], color=C["blue_d"], lw=2.2,
           arrow="arrow", label="iot/mqtt_to_coap")
    d.edge([(15.25, 7.5), (19.5, 4.25)], color=C["blue_d"], lw=2.2,
           arrow="arrow", label="POST /target")

    # --- Jalur 2: CoAP -> MQTT (putus-putus hijau)
    d.edge([(19.5, 10.25), (15.25, 7.5)], color=C["green_d"], lw=2.2,
           dash="dash", arrow="arrow", label="POST /source")
    d.edge([(10.75, 7.5), (6.5, 7.25)], color=C["green_d"], lw=2.2,
           dash="dash", arrow="arrow", label="iot/coap_to_mqtt")

    # --- Dedup / anti-loop: self-loop di sisi bawah Conversion Server.
    # Diletakkan di bawah p3 karena jalur atas/kanan/kiri sudah dilewati edge lain
    # (kalau tidak, validator melaporkan EDGE-CROSS).
    d.edge([(12.0, 10.0), (12.0, 11.2), (13.5, 11.2), (13.5, 10.0)],
           color=C["purple_d"], lw=1.8, dash="dash", arrow="arrow",
           label="dedup + anti-loop", lsize=7)

    # --- Legenda (container, agar tidak ikut diperiksa sebagai node)
    d.rrect("leg", 1, 13.5, 24, 2.9, fill=C["white"],
            line=C["gray"], container=True)

    # baris 1: kunci warna + kunci gaya garis
    d.label_at(2.4, 14.15, "Legenda", pt=8.5, bold=True)
    d.rect(None, 4.0, 14.0, 0.55, 0.30, fill=C["blue_d"])
    d.label_at(6.9, 14.15, "Jalur MQTT -> CoAP (solid)", pt=7.5)
    d.rect(None, 9.0, 14.0, 0.55, 0.30, fill=C["green_d"])
    d.label_at(12.4, 14.15, "Jalur CoAP -> MQTT (putus-putus)", pt=7.5)
    d.rect(None, 14.7, 14.0, 0.55, 0.30, fill=C["purple_d"])
    d.label_at(17.8, 14.15, "dedup / anti-loop", pt=7.5)

    # baris 2: kunci badge + footer larangan spek
    d.circle(2.4, 15.4, 0.20, fill=C["blue_d"], line=C["blue_d"])
    d.label_at(2.4, 15.4, "1", pt=7, bold=True, color=C["white"])
    d.label_at(5.4, 15.4, "= nomor komponen sesuai tabel spek", pt=7.5)
    d.label_at(17.6, 15.4,
               "IP konvensional - tanpa SDN / OpenFlow / RYU / Mininet / OVS",
               pt=7.5, color=C["muted"])

    return d

def save_diagram(d, name, doc_id):
    xml_path = f"output-xml/{name}.xml"
    png_path = f"output/{name}.png"
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(to_drawingml(d, doc_id=doc_id, name=name))
    # Versi A4 dipakai laporan supaya shape editabel muat margin 2,5 cm.
    with open(f"output-xml/{name}_a4.xml", "w", encoding="utf-8") as f:
        f.write(to_drawingml(d, doc_id=doc_id, name=name + "_a4", max_w=15.8))
    render_png(d, png_path, dpi=200)
    print(f"--- Validating {name} ---")
    validate(d)
    report_text_fit(d)

if __name__ == "__main__":
    d = build_architecture()
    save_diagram(d, "mqtt_coap_architecture", 301)
