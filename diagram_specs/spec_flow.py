import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from vendor.jump2.uml_core import Diagram, C, FILL
from vendor.jump2.uml_drawml import to_drawingml
from vendor.jump2.uml_png import render_png
from vendor.jump2.uml_validate import validate, report_text_fit

# Kanvas landscape 24x13 (sebelumnya 16x22 portrait -> tinggi cetak turun ~40%)
CANVAS_W, CANVAS_H = 24, 13
# Sumbu lifeline: jarak 4.6 cm supaya chip label (maks ~3.7 cm) muat di sela
XS = [3.0, 7.6, 12.2, 16.8, 21.4]
TOP, BOTTOM = 2.0, 12.0
# Y tiap pesan, jarak 1.3 cm supaya label dan loop tidak bertabrakan
YS = [4.0, 5.3, 6.6, 7.9, 9.2, 10.5]

FORMULA = ("delay konversi = conv_send_ts - conv_recv_ts   |   "
           "delay E2E = dst_recv_ts - sent_ts")


def _head(d, title):
    d.label_at(CANVAS_W / 2, 0.5, title, pt=10.5, bold=True)
    d.label_at(CANVAS_W / 2, 1.45, FORMULA, pt=7, bold=True,
               color=C["muted"], fill=C["paper"])


def _lifelines(d, names, color, fill):
    for x, name in zip(XS, names):
        d.lifeline(name, x, TOP, BOTTOM, 4, name, color, fill)


def _legend(d, acc):
    y = 12.55
    d.rect(None, 1.0, y - 0.13, 0.5, 0.26, fill=acc)
    d.label_at(3.7, y, "pesan antar-peran (arah = arah data)", pt=7)
    d.rect(None, 6.3, y - 0.13, 0.5, 0.26, fill=C["purple_d"])
    d.label_at(9.2, y, "aksi internal (validasi/dedup/antrean)", pt=7)
    d.label_at(14.5, y, "payload: id, seq, sent_ts, sha256", pt=7)
    d.label_at(18.6, y, "nomor 1-6 = urutan tahap", pt=7)


def _draw(d, acc, steps):
    """steps: list of (kind, a, b, label); kind = 'msg' | 'self'."""
    for (kind, a, b, txt), y in zip(steps, YS):
        if kind == "msg":
            x1, x2 = XS[a], XS[b]
            sx = x1 + (0.45 if x2 > x1 else -0.45)
            ex = x2 + (-0.45 if x2 > x1 else 0.45)
            d.edge([(sx, y), (ex, y)], color=acc, lw=1.9,
                   arrow="arrow", label=txt, lsize=7)
        else:
            # self-message: loop ke KIRI dari sumbu, label chip di KANAN sumbu
            x = XS[a]
            d.edge([(x, y), (x - 1.8, y), (x - 1.8, y + 0.5), (x, y + 0.5)],
                   color=C["purple_d"], lw=1.7, arrow="arrow")
            d.label_chip(x + 0.35, y + 0.11, txt, pt=7, fill=C["paper"])


def build_flow_m2c():
    d = Diagram("FlowM2C", CANVAS_W, CANVAS_H)
    _head(d, "Urutan Konversi MQTT ke CoAP")
    _lifelines(d, ["Publisher MQTT", "Broker MQTT", "Conversion Server",
                   "Server CoAP", "Client CoAP"], C["blue_d"], FILL["blue"])
    # Conversion aktif: menerima dari broker sampai selesai POST
    d.activation(XS[2], 5.3, 8.4)

    steps = [
        ("msg", 0, 1, "1. PUBLISH (id, sent_ts)"),
        ("msg", 1, 2, "2. Forward ke subscriber"),
        ("self", 2, 2, "3. conv_recv_ts + dedup ID"),
        ("msg", 2, 3, "4. POST /target (send_ts)"),
        ("self", 3, 3, "5. Simpan antrean /target"),
        ("msg", 4, 3, "6. GET + verifikasi SHA-256"),
    ]
    _draw(d, C["blue_d"], steps)
    _legend(d, C["blue_d"])
    return d


def build_flow_c2m():
    d = Diagram("FlowC2M", CANVAS_W, CANVAS_H)
    _head(d, "Urutan Konversi CoAP ke MQTT")
    _lifelines(d, ["Client CoAP", "Server CoAP", "Conversion Server",
                   "Broker MQTT", "Subscriber MQTT"], C["green_d"], FILL["green"])
    # Conversion aktif: mulai polling sampai selesai publish
    d.activation(XS[2], 6.6, 9.7)

    steps = [
        ("msg", 0, 1, "1. POST /source (id, ts)"),
        ("self", 1, 1, "2. Simpan antrean /source"),
        ("msg", 2, 1, "3. GET polling 1 detik"),
        ("self", 2, 2, "4. Dedup + origin_processed"),
        ("msg", 2, 3, "5. PUBLISH coap_to_mqtt"),
        ("msg", 3, 4, "6. Subscriber verifikasi"),
    ]
    _draw(d, C["green_d"], steps)
    _legend(d, C["green_d"])
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
    save_diagram(build_flow_m2c(), "flow_mqtt_to_coap", 302)
    save_diagram(build_flow_c2m(), "flow_coap_to_mqtt", 303)
