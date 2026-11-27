"""Bangun slide presentasi <=12 slide dari artefak eksperimen."""
from pathlib import Path

import pandas as pd
from PIL import Image as PILImage
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "slide" / "Slide_Presentasi.pptx"
S = ROOT / "data" / "summary" / "summary.csv"
REPO = "https://github.com/bangdhidotcom/sistem-terdistribusi-mqtt-coap"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]

NAVY = RGBColor(30, 42, 71)
BLUE = RGBColor(42, 95, 212)
GREEN = RGBColor(14, 124, 102)
PURPLE = RGBColor(125, 60, 152)
ORANGE = RGBColor(202, 111, 30)
MUTED = RGBColor(91, 107, 132)
PALE = RGBColor(238, 243, 251)
WHITE = RGBColor(255, 255, 255)


def _footer(s):
    idx = len(prs.slides._sldIdLst)
    box = s.shapes.add_textbox(Inches(0.4), Inches(7.05), Inches(12.5), Inches(0.3)).text_frame
    p = box.paragraphs[0]
    p.text = "Sistem Terdistribusi A  |  Replikasi MQTT ↔ CoAP  |  " + str(idx)
    p.font.size, p.font.color.rgb = Pt(9), MUTED
    p.alignment = PP_ALIGN.RIGHT


def slide(title, subtitle=None):
    s = prs.slides.add_slide(BLANK)
    # garis aksen atas
    bar = s.shapes.add_shape(1, Inches(0), Inches(0), prs.slide_width, Inches(0.09))
    bar.fill.solid(); bar.fill.fore_color.rgb = BLUE
    bar.line.fill.background()

    p = s.shapes.add_textbox(Inches(0.5), Inches(0.28), Inches(12.3), Inches(0.75)).text_frame.paragraphs[0]
    p.text, p.font.size, p.font.bold, p.font.color.rgb = title, Pt(25), True, NAVY
    p.alignment = PP_ALIGN.CENTER
    if subtitle:
        q = s.shapes.add_textbox(Inches(0.7), Inches(1.0), Inches(12), Inches(0.4)).text_frame.paragraphs[0]
        q.text, q.font.size, q.font.color.rgb = subtitle, Pt(12.5), BLUE
        q.alignment = PP_ALIGN.CENTER
    _footer(s)
    return s


def bullets(s, items, x=0.9, y=1.6, w=11.5, h=5.2, size=16):
    tf = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)).text_frame
    tf.word_wrap = True
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = "• " + it
        p.font.size, p.font.color.rgb = Pt(size), NAVY
        p.space_after = Pt(10)


def picture_fit(s, path, x, y, box_w, box_h):
    """Masukkan gambar ke dalam kotak tanpa meluber / melebar (contain)."""
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


def table_shape(s, rows, x=0.6, y=1.7, w=12.1, h=4.6, size=11):
    t = s.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y),
                           Inches(w), Inches(h)).table
    for i, r in enumerate(rows):
        for j, v in enumerate(r):
            c = t.cell(i, j)
            c.text = str(v)
            c.fill.solid()
            c.fill.fore_color.rgb = NAVY if i == 0 else (PALE if i % 2 == 0 else WHITE)
            for p in c.text_frame.paragraphs:
                p.font.size = Pt(size if i else size + 0.5)
                p.font.bold = i == 0
                p.font.color.rgb = WHITE if i == 0 else NAVY


# ---------------------------------------------------------------- 1 Judul
s = slide("Replikasi Conversion Server MQTT ↔ CoAP",
          "Sistem Terdistribusi A — Project Akhir")
bullets(s, ["Muhammad Irfan Maulana (202310370311480)",
            "Hadrian Rakha Khosyi Javier (202310370311483)",
            "Bambang Adhi Nurbiyanto (202310370311484)",
            "Deadline: 7 Desember 2026, 16.55 WIB",
            "Repo: " + REPO], y=2.0, size=17)

# ---------------------------------------------------------------- 2 Masalah
s = slide("Masalah dan Tujuan")
bullets(s, ["MQTT (TCP, publish/subscribe) dan CoAP (UDP, request/response) perlu saling bertukar pesan.",
            "Tanpa SDN/OpenFlow: enam peran berjalan pada IP konvensional (localhost).",
            "Tujuan: konversi dua arah yang menjaga ID, timestamp, dan payload.",
            "Metrik: success, loss, delay konversi, delay E2E, CPU, memori.",
            "Artikel memakai 200 pesan per skenario; kami menguji 10 menit penuh per run."])

# ---------------------------------------------------------------- 3 Arsitektur
s = slide("Arsitektur Sistem", "Enam peran logis sebagai proses Python terpisah")
picture_fit(s, ROOT / "output" / "mqtt_coap_architecture.png", 1.5, 1.45, 10.3, 5.3)

# ---------------------------------------------------------------- 4 Alur M2C
s = slide("Alur MQTT → CoAP")
picture_fit(s, ROOT / "output" / "flow_mqtt_to_coap.png", 4.3, 1.45, 8.3, 4.9)
bullets(s, ["Publisher → broker → conversion server (validasi + dedup)",
            "POST CoAP ke /target; server menyimpan antrean",
            "CoAP GET client verifikasi ID + SHA-256",
            "conv_delay = conv_send − conv_recv"], x=0.65, y=2.0, w=3.5, h=4.6, size=12)

# ---------------------------------------------------------------- 5 Alur C2M
s = slide("Alur CoAP → MQTT")
picture_fit(s, ROOT / "output" / "flow_coap_to_mqtt.png", 4.3, 1.45, 8.3, 4.9)
bullets(s, ["POST client → /source; antrean pesan",
            "Conversion server polling GET tiap 1 detik",
            "Dedup ID; tandai origin_processed (anti-loop)",
            "Publish ke iot/coap_to_mqtt; subscriber verifikasi"],
        x=0.65, y=2.0, w=3.5, h=4.6, size=12)

# ---------------------------------------------------------------- 6 Metode
s = slide("Metode Eksperimen")
table_shape(s, [["Aspek", "Nilai"],
                ["Laju", "10 dan 20 pesan/detik"],
                ["Durasi", "10 menit × 10 pengulangan"],
                ["Skenario", "2 arah × 2 laju × 10 = 40 run"],
                ["Payload utama", "4.096 byte (scapy Raw)"],
                ["Payload tambahan", "204.800 byte, blockwise RFC 7959"],
                ["Sampel CPU/memori", "592 sampel per run (psutil, 1 detik)"],
                ["Metrik", "success, loss, delay, CPU, memori (rerata/p95/puncak)"]],
            h=4.9, size=10.5)

# ---------------------------------------------------------------- 7 Live Demo
s = slide("Live Demo — Dua Arah", "5 menit: jalankan enam proses dan tunjukkan bukti")
bullets(s, ["Jalankan broker MQTT, CoAP server, lalu conversion server.",
            "MQTT→CoAP: publish JSON → POST /target → verifikasi SHA-256.",
            "CoAP→MQTT: POST /source → polling 1 detik → publish → verifikasi.",
            "Tunjukkan log: ID yang sama + empat timestamp.",
            "Tunjukkan data/raw/, summary.csv, dan grafik."], size=16)

# ---------------------------------------------------------------- 8 Hasil
s = slide("Hasil Ringkas", "Agregat 40 run × 10 menit; CPU/memori = rerata / p95 / puncak")
if S.exists():
    df = pd.read_csv(S)
    g = df.groupby(["direction", "rate"]).agg(
        sent=("sent", "sum"), recv=("received", "sum"),
        suc=("success_pct", "mean"), loss=("loss_pct", "mean"),
        conv=("avg_conversion_ms", "mean"), e2e=("avg_e2e_ms", "mean"),
        cpu=("avg_cpu", "mean"), cpup95=("p95_cpu", "mean"), cpupk=("peak_cpu", "max"),
        mem=("avg_mem_mb", "mean"), memp95=("p95_mem_mb", "mean"),
        mempk=("peak_mem_mb", "max")).reset_index()
    rows = [["Arah", "Laju", "Terkirim", "Diterima", "Sukses %", "Loss %",
             "Konv ms", "E2E ms", "CPU %", "Mem MB"]]
    for _, r in g.iterrows():
        rows.append([r["direction"].upper(), r["rate"], int(r["sent"]), int(r["recv"]),
                     f"{r['suc']:.2f}", f"{r['loss']:.2f}", f"{r['conv']:.1f}",
                     f"{r['e2e']:.0f}",
                     f"{r['cpu']:.1f}/{r['cpup95']:.1f}/{r['cpupk']:.1f}",
                     f"{r['mem']:.1f}/{r['memp95']:.1f}/{r['mempk']:.1f}"])
    table_shape(s, rows, y=1.65, h=4.4, size=9.5)
else:
    bullets(s, ["Data ringkasan belum tersedia saat build."])

# ---------------------------------------------------------------- 9 Grafik delay
s = slide("Grafik Delay per Menit")
picture_fit(s, ROOT / "data" / "grafik" / "delay_e2e_per_menit.png", 0.55, 1.45, 6.0, 4.8)
picture_fit(s, ROOT / "data" / "grafik" / "delay_konversi_per_menit.png", 6.8, 1.45, 6.0, 4.8)

# ---------------------------------------------------------------- 10 Grafik resource
s = slide("Grafik CPU dan Perbandingan")
picture_fit(s, ROOT / "data" / "grafik" / "cpu_per_menit.png", 0.55, 1.45, 6.0, 4.8)
picture_fit(s, ROOT / "data" / "grafik" / "perbandingan_artikel.png", 6.8, 1.45, 6.0, 4.8)

# ---------------------------------------------------------------- 11 Analisis
s = slide("Analisis")
analysis = ["Verifikasi SHA-256 benar pada kedua arah: ID dan payload terjaga.",
            "Antrean CoAP mencegah pesan tertindih antar siklus polling.",
            "CoAP→MQTT didominasi polling 1 detik (E2E 834–1.127 ms).",
            "MQTT→CoAP didominasi round-trip POST CoAP (konversi ~21 ms).",
            "Memori stabil 43,6–54,2 MB; puncak CPU 72,3% pada laju 20.",
            "Keterbatasan: satu host, batas aiocoap, 200 KB hanya uji tambahan."]
bullets(s, analysis, size=15)

# ---------------------------------------------------------------- 12 Kesimpulan
s = slide("Kesimpulan dan Luaran")
bullets(s, ["Conversion server dua arah berhasil direplikasi tanpa SDN/OpenFlow.",
            "Enam peran logis, ID unik, timestamp, payload terverifikasi.",
            "Seluruh 40 run valid; 290.107 pesan terkirim, 99,815% terverifikasi.",
            "Luaran: repo, CSV mentah + ringkasan, grafik, laporan PDF, slide, panduan.",
            "Diagram editabel: output-xml/ dan laporan/Diagram_Editabel_Word.docx.",
            "Repo: " + REPO], size=14)

OUT.parent.mkdir(parents=True, exist_ok=True)
prs.save(str(OUT))
print("Slide dibuat:", OUT, "jumlah", len(prs.slides._sldIdLst))
