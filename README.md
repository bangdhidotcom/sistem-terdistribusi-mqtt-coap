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
40 run valid (`data/perfect_done.txt` = `DONE_PERFECT zero=0`).

## Luaran

1. Kode: `src/` (6 peran logis), `config/`, `requirements.txt`, `experiments/`, `tests/`.
2. Laporan teknis: `laporan/Laporan_Akhir_Sistem_Terdistribusi.pdf` (8 halaman) dan
   `laporan/Laporan_Akhir_Sistem_Terdistribusi.docx`. Keduanya dibuat dari satu sumber
   blok `laporan/content.py` oleh `laporan/build_laporan.py`, sehingga isinya identik
   (verifikasi otomatis ≈99,45% kesamaan teks; sisa perbedaan hanya marka layout).
3. Data: `data/raw/messages.csv`, `data/summary/summary.csv`, `data/grafik/*.png`.
4. Slide: `slide/Slide_Presentasi.pptx` (10 slide).
5. Diagram: `output/*.png` (full color, High-DPI), `output-xml/*.xml` (shape Word
   editabel), `diagram_specs/design_v2/*.svg` (desain vektor), dan
   `laporan/Diagram_Editabel_Word.docx`.
6. Panduan: `panduan/Verifikasi_Individu.md`, `Panduan_Pengumpulan_LMS.md`, `QnA.md`.

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
python experiments/run_matrix.py --duration 15 --reps 1 --rate 10 --direction both --payload-size 4096
python experiments/summarize.py
python experiments/plotting.py
python laporan/build_report.py
python slide/build_slides.py
python -m unittest discover -s tests
```

Kampanye penuh: 40 run (40 valid) = dua arah x dua laju x 10 pengulangan x 10 menit.
Payload kampanye 4 KB; uji tambahan 200 KB blockwise tersedia lewat `--payload-size 204800`.

## Link

https://github.com/bangdhidotcom/sistem-terdistribusi-mqtt-coap
