"""Bangun slide presentasi <=12 slide dari artefak eksperimen.

Tema: navy + aksen biru/hijau/ungu, kartu informasi, KPI, dan grid yang konsisten.
Seluruh angka diambil dari data/summary/summary.csv (agregasi berbobot).
"""
from pathlib import Path

import pandas as pd
from PIL import Image as PILImage
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "slide" / "Slide_Presentasi.pptx"
S = ROOT / "data" / "summary" / "summary.csv"
REPO = "https://github.com/bangdhidotcom/sistem-terdistribusi-mqtt-coap"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
W, H = 13.333, 7.5

TEXT = RGBColor(28, 38, 56)
NAVY = RGBColor(22, 32, 54)
NAVY2 = RGBColor(34, 48, 78)
BLUE = RGBColor(42, 95, 212)
GREEN = RGBColor(14, 124, 102)
PURPLE = RGBColor(125, 60, 152)
ORANGE = RGBColor(202, 111, 30)
MUTED = RGBColor(91, 107, 132)
PALE = RGBColor(238, 243, 251)
BORDER = RGBColor(214, 224, 238)
WHITE = RGBColor(255, 255, 255)
LIGHTBLUE = RGBColor(150, 185, 255)
FONT = "Aptos"


def _rect(s, x, y, w, h, fill, line=None, rounded=False):
    shape = s.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE,
        Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line
        shape.line.width = Pt(0.75)
    return shape


def _text(s, text, x, y, w, h, size=14, bold=False, color=TEXT,
          align=PP_ALIGN.LEFT, middle=False):
    box = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.02)
    tf.margin_top = tf.margin_bottom = Inches(0.01)
    if middle:
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.text = str(text)
    p.font.name = FONT
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.alignment = align
    return box


def chrome(s, title, kicker=None, accent=BLUE):
    _rect(s, 0, 0, W, 0.10, accent)
    _text(s, title, 0.55, 0.27, 12.25, 0.62, size=24, bold=True, color=NAVY)
    if kicker:
        _text(s, kicker.upper(), 0.57, 0.92, 12.2, 0.28,
              size=10.5, bold=True, color=accent)
    _rect(s, 0, 7.20, W, 0.30, NAVY)
    _text(s, "SISTEM TERDISTRIBUSI A   •   REPLIKASI MQTT ↔ CoAP   •   %02d"
          % len(prs.slides._sldIdLst),
          0.55, 7.22, 12.2, 0.25, size=8.5, color=WHITE, align=PP_ALIGN.RIGHT)
    return s


def bullets(s, items, x, y, w, h, size=14, spacing=9, color=TEXT, accent=BLUE):
    tf = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)).text_frame
    tf.word_wrap = True
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = "•  " + str(it)
        p.font.name, p.font.size = FONT, Pt(size)
        p.font.color.rgb = color
        p.space_after = Pt(spacing)
    return tf


def steps(s, items, x, y, w, accent=BLUE, size=12.5, gap=0.86):
    for i, it in enumerate(items):
        yy = y + i * gap
        _rect(s, x, yy, 0.40, 0.40, accent, rounded=True)
        _text(s, str(i + 1), x, yy - 0.01, 0.40, 0.42, size=11, bold=True,
              color=WHITE, align=PP_ALIGN.CENTER, middle=True)
        _text(s, it, x + 0.58, yy - 0.04, w - 0.58, 0.72, size=size, middle=True)


def card(s, x, y, w, h, title, lines, accent=BLUE, size=12.5):
    _rect(s, x, y, w, h, PALE, line=BORDER, rounded=True)
    _rect(s, x, y, w, 0.07, accent)
    _text(s, title, x + 0.22, y + 0.18, w - 0.44, 0.38,
          size=14, bold=True, color=accent)
    bullets(s, lines, x + 0.22, y + 0.68, w - 0.44, h - 0.82,
            size=size, spacing=7)


def kpi(s, x, y, w, h, value, label, accent=BLUE):
    _rect(s, x, y, w, h, WHITE, line=BORDER, rounded=True)
    _rect(s, x, y, 0.07, h, accent)
    _text(s, value, x + 0.18, y + 0.12, w - 0.30, 0.52,
          size=23, bold=True, color=accent)
    _text(s, label, x + 0.18, y + 0.66, w - 0.30, h - 0.70,
          size=10.5, color=MUTED)


def picture_fit(s, path, x, y, box_w, box_h):
    p = Path(path)
    if not p.exists():
        return
    with PILImage.open(p) as im:
        iw, ih = im.size
    scale = min(box_w / iw, box_h / ih)
    w, h = iw * scale, ih * scale
    s.shapes.add_picture(str(p), Inches(x + (box_w - w) / 2),
                         Inches(y + (box_h - h) / 2),
                         width=Inches(w), height=Inches(h))


def table_shape(s, rows, x=0.55, y=1.55, w=12.23, h=4.9, size=11):
    t = s.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y),
                           Inches(w), Inches(h)).table
    for i, r in enumerate(rows):
        for j, v in enumerate(r):
            c = t.cell(i, j)
            c.text = str(v)
            c.fill.solid()
            c.fill.fore_color.rgb = NAVY if i == 0 else (PALE if i % 2 else WHITE)
            c.margin_left = c.margin_right = Inches(0.06)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            for p in c.text_frame.paragraphs:
                p.alignment = PP_ALIGN.CENTER
                p.font.name = FONT
                p.font.size = Pt(size + (0.5 if i == 0 else 0))
                p.font.bold = i == 0
                p.font.color.rgb = WHITE if i == 0 else TEXT


# ---------------------------------------------------------------- 1 Judul
s = prs.slides.add_slide(BLANK)
_rect(s, 0, 0, W, H, NAVY)
_rect(s, 0, 0, 0.16, H, BLUE)
_text(s, "SISTEM TERDISTRIBUSI A   •   PROJECT AKHIR", 0.75, 0.65, 11.8, 0.4,
      size=12, bold=True, color=LIGHTBLUE)
_text(s, "Replikasi Conversion Server\nMQTT ↔ CoAP", 0.75, 1.25, 11.8, 1.75,
      size=31, bold=True, color=WHITE)
_text(s, "Komunikasi dua arah pada jaringan IP konvensional — tanpa SDN / OpenFlow",
      0.75, 3.05, 11.8, 0.45, size=14.5, color=RGBColor(205, 218, 240))
for i, (name, nim) in enumerate([
        ("Muhammad Irfan Maulana", "202310370311480"),
        ("Hadrian Rakha Khosyi Javier", "202310370311483"),
        ("Bambang Adhi Nurbiyanto", "202310370311484")]):
    x = 0.75 + i * 4.12
    _rect(s, x, 4.05, 3.85, 1.10, NAVY2, line=RGBColor(70, 92, 132), rounded=True)
    _text(s, name, x + 0.18, 4.18, 3.5, 0.38, size=12.5, bold=True, color=WHITE)
    _text(s, nim, x + 0.18, 4.60, 3.5, 0.30, size=10.5, color=LIGHTBLUE)
_text(s, "Repo: " + REPO,
      0.75, 6.55, 11.9, 0.4, size=10, color=LIGHTBLUE)

# ---------------------------------------------------------------- 2 Masalah
s = chrome(prs.slides.add_slide(BLANK), "Masalah dan Tujuan",
           "01  •  mengapa converter diperlukan")
card(s, 0.55, 1.35, 5.95, 2.10, "MQTT — TCP, publish/subscribe",
     ["Broker mendistribusikan pesan ke subscriber", "Koneksi persisten, banyak-ke-banyak"],
     accent=BLUE)
card(s, 6.83, 1.35, 5.95, 2.10, "CoAP — UDP, request/response",
     ["Client mengakses resource /target dan /source", "Ringan, cocok untuk perangkat kecil"],
     accent=GREEN)
card(s, 0.55, 3.70, 12.23, 2.35, "Tujuan replikasi",
     ["Konversi dua arah yang menjaga ID, timestamp, dan payload (SHA-256)",
      "Enam peran logis sebagai proses Python terpisah pada IP konvensional",
      "Uji otomatis 10 dan 20 pesan/detik; metrik: success, loss, delay, CPU, memori"],
     accent=PURPLE, size=13)
_text(s, "Artikel acuan: 200 pesan per skenario. Kampanye kami: 10 menit penuh per run.",
      0.62, 6.30, 12.1, 0.35, size=11, color=MUTED)

# ---------------------------------------------------------------- 3 Arsitektur
s = chrome(prs.slides.add_slide(BLANK), "Arsitektur Sistem",
           "02  •  enam peran logis, enam proses terpisah")
picture_fit(s, ROOT / "output" / "mqtt_coap_architecture.png", 0.55, 1.32, 12.23, 5.35)
_text(s, "MQTT 1883/1884  •  CoAP 5683/5684  •  topik iot/*  •  resource /target & /source  •  tanpa SDN",
      0.62, 6.72, 12.1, 0.32, size=10.5, color=MUTED, align=PP_ALIGN.CENTER)

# ---------------------------------------------------------------- 4 Alur M2C
s = chrome(prs.slides.add_slide(BLANK), "Alur MQTT → CoAP",
           "03  •  subscriber MQTT menjadi POST client CoAP", accent=BLUE)
card(s, 0.55, 1.35, 4.05, 4.95, "Enam tahap",
     ["Publisher → broker → conversion server",
      "Validasi ID, dedup, conv_recv_ts",
      "POST /target; server simpan antrean",
      "GET client verifikasi SHA-256",
      "conv_delay = conv_send − conv_recv"],
     accent=BLUE, size=12)
picture_fit(s, ROOT / "output" / "flow_mqtt_to_coap.png", 4.82, 1.45, 7.95, 4.85)

# ---------------------------------------------------------------- 5 Alur C2M
s = chrome(prs.slides.add_slide(BLANK), "Alur CoAP → MQTT",
           "04  •  polling GET tiap 1 detik", accent=GREEN)
card(s, 0.55, 1.35, 4.05, 4.95, "Enam tahap",
     ["POST client → /source; antrean pesan",
      "Converter GET /source tiap 1 detik",
      "Dedup ID + origin_processed (anti-loop)",
      "Publish ke iot/coap_to_mqtt",
      "Subscriber verifikasi ID + SHA-256"],
     accent=GREEN, size=12)
picture_fit(s, ROOT / "output" / "flow_coap_to_mqtt.png", 4.82, 1.45, 7.95, 4.85)

# ---------------------------------------------------------------- 6 Metode
s = chrome(prs.slides.add_slide(BLANK), "Metode Eksperimen",
           "05  •  matriks uji dan definisi metrik", accent=PURPLE)
table_shape(s, [["Aspek", "Nilai"],
                ["Laju", "10 dan 20 pesan/detik"],
                ["Durasi", "10 menit × 10 pengulangan"],
                ["Skenario", "2 arah × 2 laju × 10 = 40 run"],
                ["Payload utama", "4.096 byte (generator scapy Raw)"],
                ["Payload tambahan", "204.800 byte, blockwise RFC 7959"],
                ["Sampel CPU/memori", "592 sampel per run (psutil, 1 detik)"],
                ["Metrik", "success, loss, delay konversi, E2E, CPU/memori (mean/p95/peak)"]],
            y=1.35, h=4.35, size=10.5)
for i, (v, lab, col) in enumerate([
        ("40", "run valid", BLUE),
        ("600 dtk", "per run", GREEN),
        ("290.107", "pesan terkirim", PURPLE),
        ("99,815%", "terverifikasi", ORANGE)]):
    kpi(s, 0.55 + i * 3.10, 5.92, 2.90, 1.05, v, lab, col)

# ---------------------------------------------------------------- 7 Live demo
s = chrome(prs.slides.add_slide(BLANK), "Live Demo — Dua Arah",
           "06  •  5 menit: jalankan enam proses dan tunjukkan log", accent=ORANGE)
card(s, 0.55, 1.35, 5.95, 4.95, "Persiapan & MQTT → CoAP",
     ["Broker 1884, CoAP server 5684, conversion server",
      "Subscriber + CoAP GET client sebagai verifier",
      "Publish 20 pesan: lihat PUBLISH → CONV_IN/OUT",
      "POST_OK / GET_OK → DELIVER verified:true"],
     accent=BLUE, size=12)
card(s, 6.83, 1.35, 5.95, 4.95, "CoAP → MQTT & bukti",
     ["POST 20 pesan ke /source",
      "GET polling → dedup → publish ke topik tujuan",
      "MQTT subscriber mencocokkan ID dan SHA-256",
      "Cadangan: data/bukti_konektivitas/contoh/"],
     accent=GREEN, size=12)

# ---------------------------------------------------------------- 8 Hasil
s = chrome(prs.slides.add_slide(BLANK), "Hasil Ringkas",
           "07  •  agregat 40 run; persentase = total diterima / total terkirim")
kpi(s, 0.55, 1.30, 3.90, 1.05, "40/40", "run valid", BLUE)
kpi(s, 4.72, 1.30, 3.90, 1.05, "289.571", "pesan terverifikasi", GREEN)
kpi(s, 8.89, 1.30, 3.90, 1.05, "99,815%", "keberhasilan overall", PURPLE)

rows = [["Arah", "Laju", "Terkirim", "Diterima", "Sukses %", "Loss %",
         "Konv ms", "E2E ms", "CPU %", "Mem MB"]]
if S.exists():
    df = pd.read_csv(S)
    g = df.groupby(["direction", "rate"]).agg(
        sent=("sent", "sum"), recv=("received", "sum"),
        conv=("avg_conversion_ms", "mean"), e2e=("avg_e2e_ms", "mean"),
        cpu=("avg_cpu", "mean"), cpup95=("p95_cpu", "mean"),
        cpupk=("peak_cpu", "max"), mem=("avg_mem_mb", "mean"),
        memp95=("p95_mem_mb", "mean"), mempk=("peak_mem_mb", "max")
    ).reset_index()
    g["suc"] = 100.0 * g["recv"] / g["sent"]
    g["loss"] = 100.0 - g["suc"]
    for _, r in g.iterrows():
        rows.append([r["direction"].upper(), r["rate"], f"{int(r['sent']):,}".replace(",", "."),
                     f"{int(r['recv']):,}".replace(",", "."),
                     f"{r['suc']:.2f}", f"{r['loss']:.2f}",
                     f"{r['conv']:.1f}", f"{r['e2e']:.0f}",
                     f"{r['cpu']:.1f}/{r['cpup95']:.1f}/{r['cpupk']:.1f}",
                     f"{r['mem']:.1f}/{r['memp95']:.1f}/{r['mempk']:.1f}"])
table_shape(s, rows, y=2.55, h=4.25, size=9)

# ---------------------------------------------------------------- 9 Grafik delay
s = chrome(prs.slides.add_slide(BLANK), "Grafik Delay per Menit",
           "08  •  rerata 10 run per bucket; 11 bucket = 600 detik")
picture_fit(s, ROOT / "data" / "grafik" / "delay_e2e_per_menit.png", 0.45, 1.35, 6.15, 4.75)
picture_fit(s, ROOT / "data" / "grafik" / "delay_konversi_per_menit.png", 6.75, 1.35, 6.15, 4.75)
_text(s, "E2E CoAP→MQTT 834–1.127 ms (dominasi polling 1 dtk)  •  Konversi MQTT→CoAP ~21 ms (round-trip POST)",
      0.55, 6.35, 12.2, 0.45, size=11, color=MUTED, align=PP_ALIGN.CENTER)

# ---------------------------------------------------------------- 10 Grafik sumber daya
s = chrome(prs.slides.add_slide(BLANK), "Grafik CPU dan Perbandingan",
           "09  •  beban conversion server dan loss dibanding artikel", accent=GREEN)
picture_fit(s, ROOT / "data" / "grafik" / "cpu_per_menit.png", 0.45, 1.35, 6.15, 4.75)
picture_fit(s, ROOT / "data" / "grafik" / "perbandingan_artikel.png", 6.75, 1.35, 6.15, 4.75)
_text(s, "Puncak CPU 72,3% pada 20 pesan/detik  •  Loss replikasi ≤ 0,33% vs artikel 0–95,52%",
      0.55, 6.35, 12.2, 0.45, size=11, color=MUTED, align=PP_ALIGN.CENTER)

# ---------------------------------------------------------------- 11 Analisis
s = chrome(prs.slides.add_slide(BLANK), "Analisis",
           "10  •  mengapa angka berbeda dengan artikel", accent=PURPLE)
card(s, 0.55, 1.35, 5.95, 2.25, "Keutuhan & anti-loop",
     ["SHA-256 cocok di kedua ujung", "Dedup ID + origin_processed mencegah loop"],
     accent=BLUE, size=12)
card(s, 6.83, 1.35, 5.95, 2.25, "Dominasi delay",
     ["CoAP→MQTT: polling 1 detik, bukan konversi", "MQTT→CoAP: round-trip POST CoAP"],
     accent=GREEN, size=12)
card(s, 0.55, 3.85, 5.95, 2.25, "Sumber daya",
     ["CPU naik mengikuti laju; puncak 72,3%", "Memori stabil 43,6–54,2 MB (tanpa kebocoran)"],
     accent=PURPLE, size=12)
card(s, 6.83, 3.85, 5.95, 2.25, "Keterbatasan",
     ["Satu host → bukan jitter jaringan nyata", "200 KB hanya uji blockwise terpisah"],
     accent=ORANGE, size=12)
_text(s, "Perbedaan angka artikel terutama karena definisi timestamp, antrean, polling, dan ukuran payload.",
      0.62, 6.40, 12.1, 0.35, size=11, color=MUTED)

# ---------------------------------------------------------------- 12 Kesimpulan
s = chrome(prs.slides.add_slide(BLANK), "Kesimpulan dan Luaran",
           "11  •  siap didemokan dan diverifikasi")
_rect(s, 0.55, 1.35, 12.23, 1.25, PALE, line=BORDER, rounded=True)
_rect(s, 0.55, 1.35, 0.09, 1.25, GREEN)
_text(s, "Conversion server dua arah berhasil direplikasi pada jaringan IP konvensional.",
      0.85, 1.60, 11.6, 0.45, size=17, bold=True, color=NAVY)
_text(s, "Enam peran terpisah • ID unik • timestamp • payload terverifikasi • 40/40 run valid",
      0.85, 2.08, 11.6, 0.35, size=12, color=MUTED)
for i, (title, body, col) in enumerate([
        ("Kode & data", "src/, experiments/, tests/, CSV mentah + ringkasan", BLUE),
        ("Laporan", "PDF & DOCX 10 halaman, tabel dan diagram editabel", GREEN),
        ("Presentasi", "12 slide + panduan demo & verifikasi individu", PURPLE)]):
    x = 0.55 + i * 4.13
    _rect(s, x, 2.95, 3.85, 1.75, WHITE, line=BORDER, rounded=True)
    _rect(s, x, 2.95, 3.85, 0.07, col)
    _text(s, title, x + 0.20, 3.15, 3.45, 0.38, size=14, bold=True, color=col)
    _text(s, body, x + 0.20, 3.62, 3.45, 0.85, size=11, color=TEXT)
_text(s, "Repo: " + REPO, 0.62, 5.10, 12.1, 0.4, size=12, bold=True, color=BLUE)
_text(s, "Terima kasih — silakan tanya jawab & verifikasi individu (5–7 menit)",
      0.62, 5.65, 12.1, 0.4, size=13, color=MUTED)

prs.save(OUT)
print("Slide dibuat:", OUT, "jumlah:", len(prs.slides._sldIdLst))
