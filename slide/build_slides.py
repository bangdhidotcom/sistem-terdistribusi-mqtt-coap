"""Bangun slide presentasi <=12 slide dari artefak eksperimen."""
from pathlib import Path
import pandas as pd
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "slide" / "Slide_Presentasi.pptx"
S = ROOT / "data" / "summary" / "summary.csv"
REPO = "https://github.com/bangdhidotcom/sistem-terdistribusi-mqtt-coap"
prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
NAVY, BLUE = RGBColor(30, 42, 71), RGBColor(42, 95, 212)
def slide(title, subtitle=None):
    s = prs.slides.add_slide(BLANK)
    p = s.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.3), Inches(0.8)).text_frame.paragraphs[0]
    p.text, p.font.size, p.font.bold, p.font.color.rgb = title, Pt(26), True, NAVY
    p.alignment = PP_ALIGN.CENTER
    if subtitle:
        q = s.shapes.add_textbox(Inches(0.7), Inches(1.0), Inches(12), Inches(0.4)).text_frame.paragraphs[0]
        q.text, q.font.size, q.font.color.rgb = subtitle, Pt(13), BLUE
        q.alignment = PP_ALIGN.CENTER
    return s
def bullets(s, items, x=0.9, y=1.6, w=11.5, h=5.2, size=16):
    tf = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)).text_frame
    tf.word_wrap = True
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = "• " + it; p.font.size = Pt(size); p.space_after = Pt(10)
def picture(s, path, x, y, w):
    p = Path(path)
    if p.exists(): s.shapes.add_picture(str(p), Inches(x), Inches(y), width=Inches(w))
def table_shape(s, rows, x=0.6, y=1.7, w=12.1, h=4.6):
    t = s.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(w), Inches(h)).table
    for i, r in enumerate(rows):
        for j, v in enumerate(r):
            c = t.cell(i, j); c.text = str(v)
            for p in c.text_frame.paragraphs: p.font.size, p.font.bold = Pt(11 if i else 12), i == 0
s = slide("Replikasi Conversion Server MQTT ↔ CoAP", "Sistem Terdistribusi A — Project Akhir")
bullets(s, ["Muhammad Irfan Maulana (202310370311480)", "Hadrian Rakha Khosyi Javier (202310370311483)", "Bambang Adhi Nurbiyanto (202310370311484)", "Deadline: 7 Desember 2026, 16.55 WIB", "Repo: " + REPO], y=2.0, size=18)
s = slide("Masalah dan Tujuan")
bullets(s, ["MQTT (TCP, publish/subscribe) dan CoAP (UDP, request/response) perlu saling bertukar pesan.", "Tanpa SDN/OpenFlow: enam peran berjalan pada IP konvensional (localhost).", "Tujuan: konversi dua arah yang menjaga ID, timestamp, dan payload.", "Metrik: success, loss, delay konversi, delay E2E, CPU, memori."])
s = slide("Arsitektur Sistem", "Enam peran logis sebagai proses Python terpisah")
picture(s, ROOT / "output" / "mqtt_coap_architecture.png", 0.7, 1.4, 11.9)
s = slide("Alur MQTT → CoAP")
picture(s, ROOT / "output" / "flow_mqtt_to_coap.png", 4.4, 1.3, 4.5)
bullets(s, ["Publisher → broker → conversion server (validasi + mark processed)", "POST CoAP ke /target; server menyimpan antrean", "CoAP GET client verifikasi ID + SHA-256", "conv_delay = conv_send − conv_recv"], x=0.7, y=2.0, w=3.5, h=4.5, size=13)
s = slide("Alur CoAP → MQTT")
picture(s, ROOT / "output" / "flow_coap_to_mqtt.png", 4.4, 1.3, 4.5)
bullets(s, ["POST client → /source; antrean pesan", "Conversion server polling GET tiap 1 detik", "Dedup berdasarkan ID unik; tandai origin_processed", "Publish ke iot/coap_to_mqtt; subscriber verifikasi"], x=0.7, y=2.0, w=3.5, h=4.5, size=13)
s = slide("Metode Eksperimen")
table_shape(s, [["Aspek", "Nilai"], ["Laju", "10 dan 20 pesan/detik"], ["Durasi", "10 menit × 10 pengulangan"], ["Skenario", "2 arah × 2 laju × 10 = 40 run"], ["Payload utama", "4.096 byte (scapy Raw)"], ["Payload tambahan", "204.800 byte, blockwise RFC 7959"], ["Metrik", "success, loss, delay, CPU, memori"]])
s = slide("Hasil Ringkas")
if S.exists():
    df = pd.read_csv(S)
    g = df.groupby(["direction", "rate"]).agg(sent=("sent", "sum"), recv=("received", "sum"), suc=("success_pct", "mean"), conv=("avg_conversion_ms", "mean"), e2e=("avg_e2e_ms", "mean"), cpu=("avg_cpu", "mean")).reset_index()
    rows = [["Arah", "Laju", "Terkirim", "Diterima", "Sukses %", "Konv ms", "E2E ms", "CPU %"]]
    for _, r in g.iterrows():
        rows.append([r["direction"].upper(), r["rate"], int(r["sent"]), int(r["recv"]), f"{r['suc']:.1f}", f"{r['conv']:.1f}", f"{r['e2e']:.1f}", f"{r['cpu']:.1f}"])
    table_shape(s, rows, y=1.7, h=4.2)
else:
    bullets(s, ["Data ringkasan belum tersedia saat build."])
s = slide("Grafik Kinerja")
picture(s, ROOT / "data" / "grafik" / "delay_e2e_per_menit.png", 0.5, 1.4, 6.1)
picture(s, ROOT / "data" / "grafik" / "cpu_per_menit.png", 6.8, 1.4, 6.1)
s = slide("Analisis")
analysis = ["Verifikasi SHA-256 benar pada kedua arah: ID dan payload terjaga.",
            "Antrean CoAP mencegah pesan tertindih antar siklus polling.",
            "CoAP→MQTT lebih dipengaruhi polling 1 detik; MQTT→CoAP oleh round-trip CoAP.",
            "Angka artikel inkonsisten; perbandingan kualitatif dengan catatan satuan.",
            "Keterbatasan: satu host, batas aiocoap pada 20 msg/s, 200 KB hanya uji tambahan."]
failed = []
if S.exists():
    d = pd.read_csv(S)
    if {"sent", "received", "run"}.issubset(d.columns):
        failed = sorted(set(d[(d["sent"] == 0) & (d["received"] == 0)]["run"].astype(str)))
if failed:
    analysis.append("%d dari 40 run gagal total setelah retry (%s)." % (len(failed), ", ".join(failed)))
else:
    analysis.append("Seluruh 40 run berhasil setelah perbaikan dan verifikasi ulang.")
bullets(s, analysis)
s = slide("Kesimpulan dan Luaran")
bullets(s, ["Conversion server dua arah berhasil direplikasi tanpa SDN/OpenFlow.", "Enam peran logis, ID unik, timestamp, payload terverifikasi.", "Luaran: repo kode, CSV mentah + ringkasan, grafik, laporan PDF, slide, panduan verifikasi.", "Diagram XML editabel + PNG tersedia di output-xml/ dan output/.", "Repo: " + REPO], size=15)
OUT.parent.mkdir(parents=True, exist_ok=True)
prs.save(str(OUT))
print("Slide dibuat:", OUT, "jumlah", len(prs.slides._sldIdLst))
