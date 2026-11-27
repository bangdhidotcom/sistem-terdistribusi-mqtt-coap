# Sistem Terdistribusi - Konversi MQTT <-> CoAP

Tugas Project Kelompok, Fakultas Teknik Informatika, Universitas Muhammadiyah Malang.
Semester Ganjil 2026/2027 - Kelas Sistem Terdistribusi A.

## Topik

Replikasi gagasan utama artikel Sumadi dkk. (TELKOMNIKA 19(5), 2021,
DOI 10.12928/TELKOMNIKA.v19i5.20412) berupa **conversion server dua arah
MQTT <-> CoAP** pada jaringan IP konvensional. Tidak memakai SDN, OpenFlow,
RYU, Mininet, maupun Open vSwitch.

## Anggota kelompok

- Muhammad Irfan Maulana - 202310370311480
- Hadrian Rakha Khosyi Javier - 202310370311483
- Bambang Adhi Nurbiyanto - 202310370311484

## Status

Tahap akhir. Kode, konfigurasi, skrip eksperimen, data, laporan **PDF dan DOCX**,
slide, diagram editabel, dan panduan sudah tersedia di repositori ini. Seluruh
40 run valid: 290.107 pesan terkirim, 99,815% terverifikasi
(`data/summary/summary.csv`, `data/metrics.json`).

## Luaran

1. Kode: `src/` (6 peran logis), `config/`, `requirements.txt`, `experiments/`, `tests/`.
2. Laporan teknis: `laporan/Laporan_Akhir_Sistem_Terdistribusi.pdf` (10 halaman) dan
   `laporan/Laporan_Akhir_Sistem_Terdistribusi.docx`. Format A4, Times New Roman 12,
   margin 2 cm, seluruh teks hitam, tanpa garis pembatas antar bagian. Keduanya dibuat
   dari satu sumber blok `laporan/content.py` oleh `laporan/build_laporan.py`.
   Kesamaan teks 100% (audit `w:t` DOCX terhadap teks PDF). Laporan memakai preview PNG
   agar label diagram tidak terhitung dua kali; versi shape editabel disimpan terpisah
   di `laporan/Diagram_Editabel_Word.docx`.
3. Data: `data/raw/messages.csv`, `data/summary/summary.csv` (440 baris x 18 kolom),
   `data/grafik/*.png`.
4. Slide: `slide/Slide_Presentasi.pptx` (12 slide).
5. Diagram dan grafik: `output/*.png` + `data/grafik/*.png` (preview 200 DPI) dan
   `output-xml/*.xml` (DrawingML asli berupa `wps:wsp`, tanpa `r:embed`/media tertanam).
   DOCX laporan dan PDF menyisipkan **preview PNG**; dokumen yang memuat shape editabel
   adalah `laporan/Diagram_Editabel_Word.docx` (1.282 `wps:wsp`, 0 media). Diagram
   berasal dari `diagram_specs/`, grafik dari `laporan/chart_shapes.py`; salinan SVG
   lama tidak dijadikan rujukan.
6. Panduan: `panduan/Verifikasi_Individu.md`, `panduan/Demo_Cepat.md`,
   `panduan/Panduan_Pengumpulan_LMS.md`, `panduan/QnA.md`. Contoh log per-run ada di
   `data/bukti_konektivitas/`; log JSONL lengkap (~263 MB) sengaja di-ignore dan dapat
   diregenerasi dengan perintah di `panduan/Verifikasi_Individu.md`.

## Sumber tunggal folder

Satu-satunya folder proyek yang aktif adalah folder repositori ini
(`D:\Sistem Terdistribusi\project\sistem-terdistribusi-mqtt-coap`). Folder induk
`D:\Sistem Terdistribusi\project` hanya menyimpan dokumen sumber tugas
(`Tugas Project Sistem Terdistribusi.pdf`) dan catatan data (`data.txt`).
Salinan lama `config/`, `src/`, `experiments/`, `output/`, dll. di folder induk
adalah artefak staging dari sesi pembuatan diagram awal dan sudah dihapus agar
tidak ada dua versi kode yang membingungkan. Repository GitHub juga hanya
berisi satu salinan per path — tidak ada duplikat struktur di remote.

## Cara menjalankan

```powershell
python experiments/payload_gen.py --size 4096 --out data/payload_4096.bin
# Smoke test singkat (kampanye penuh 40 run sudah selesai, jangan dijalankan ulang):
python experiments/run_matrix.py --duration 15 --reps 1 --rate 10 --direction both --payload-size 4096
python experiments/summarize.py
python diagram_specs/build_diagrams.py
python diagram_specs/spec_flow.py
python experiments/plotting.py       # = laporan/chart_shapes.py, XML + PNG satu sumber
python laporan/build_docx.py
python laporan/build_laporan.py
python slide/build_slides.py
python -m unittest discover -s tests
```

Urutan regenerasi di atas wajib berurutan: diagram → grafik editabel → DOCX → PDF → slide.
`laporan/build_report.py` adalah pembuat laporan versi lama yang menimpa path PDF yang sama
dan menghasilkan gambar statis (bukan shape editabel) — **jangan dijalankan**. Satu-satunya
sumber kanonik adalah `laporan/content.py` lewat `laporan/build_laporan.py`; file lama
dibiarkan hanya sebagai arsip, bukan entry point.

Kampanye penuh: 40 run (40 valid) = dua arah x dua laju x 10 pengulangan x 10 menit.
Payload kampanye 4 KB; uji tambahan 200 KB blockwise tersedia lewat `--payload-size 204800`.

## Link

https://github.com/bangdhidotcom/sistem-terdistribusi-mqtt-coap
