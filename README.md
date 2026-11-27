# Sistem Terdistribusi — Konversi MQTT ↔ CoAP

Tugas project kelompok, Fakultas Teknik Informatika, Universitas Muhammadiyah Malang.
Semester Ganjil 2026/2027 — Kelas Sistem Terdistribusi A.

## Topik

Replikasi gagasan utama artikel Sumadi dkk. (TELKOMNIKA 19(5), 2021,
DOI 10.12928/TELKOMNIKA.v19i5.20412) berupa **conversion server dua arah
MQTT ↔ CoAP** pada jaringan IP konvensional. Tidak memakai SDN, OpenFlow,
RYU, Mininet, maupun Open vSwitch.

## Anggota kelompok

- Muhammad Irfan Maulana — 202310370311480
- Hadrian Rakha Khosyi Javier — 202310370311483
- Bambang Adhi Nurbiyanto — 202310370311484

## Isi repository

- `src/` — enam peran logis: publisher, broker, subscriber, conversion server,
  CoAP server, dan CoAP client.
- `config/`, `requirements.txt` — konfigurasi dan dependensi.
- `experiments/` — generator payload, runner matriks eksperimen, dan peringkas hasil.
- `tests/` — pengujian unit dan integrasi dua arah.
- `data/raw/`, `data/summary/summary.csv`, `data/metrics.json` — data mentah dan
  ringkasan 40 run.
- `data/grafik/` — grafik hasil eksperimen.
- `laporan/Laporan_Akhir_Sistem_Terdistribusi.pdf` (10 halaman) dan
  `laporan/Laporan_Akhir_Sistem_Terdistribusi.docx` (10 halaman, tujuh shape
  DrawingML editabel), serta `laporan/Diagram_Editabel_Word.docx`.
- `output-xml/` dan `output/` — sumber diagram/grafik editabel dan preview PNG.
- `slide/Slide_Presentasi.pptx` — 12 slide presentasi.
- `panduan/Demo_Cepat.md` dan `panduan/Verifikasi_Individu.md` — alur demo dan
  verifikasi per anggota.
- `scripts/` — pembantu proses demo dan healthcheck.

## Hasil ringkas

Seluruh 40 run valid: 290.107 pesan terkirim dengan 99,815% terverifikasi.
Rincian per arah dan laju ada di `data/summary/summary.csv`.

## Menjalankan ulang pengujian

```powershell
python experiments/payload_gen.py --size 4096 --out data/payload_4096.bin
python experiments/run_matrix.py --duration 15 --reps 1 --rate 10 --direction both --payload-size 4096
python experiments/summarize.py
python -m unittest discover -s tests
```

Kampanye penuh 40 run (dua arah × dua laju × sepuluh pengulangan × sepuluh
menit) sudah selesai dan tidak perlu diulang. Untuk sesi demo singkat, ikuti
`panduan/Demo_Cepat.md`.

## Tautan

https://github.com/bangdhidotcom/sistem-terdistribusi-mqtt-coap
