# Panduan Pengumpulan LMS

Aturan dari screenshot LMS: **kumpulkan satu laporan akhir berformat `.pdf`**. Komponen lain (repo, CSV, grafik, slide) tidak diunggah terpisah, melainkan **dicantumkan sebagai tautan di dalam laporan PDF**. Gabungkan seluruh materi menjadi **satu file PDF utuh**: laporan teknis, ringkasan eksekutif, dan daftar tautan akses ke repositori serta lampiran teknis.

## Langkah
1. Pastikan `laporan/Laporan_Akhir_Sistem_Terdistribusi.pdf` sudah final (maksimal 10 halaman).
2. Bagian 10 laporan sudah memuat tautan klik ke seluruh artefak (13 anotasi link di PDF, 12 hyperlink eksternal di DOCX). Pastikan tautannya dapat dibuka:
   - Repo: https://github.com/bangdhidotcom/sistem-terdistribusi-mqtt-coap
   - `data/raw/messages.csv`, `data/summary/summary.csv`, `data/grafik/`
   - `output-xml/` (XML shape Word editabel), `output/` (PNG), `laporan/Diagram_Editabel_Word.docx`
   - `slide/Slide_Presentasi.pptx`
   - `panduan/Verifikasi_Individu.md`, `panduan/QnA.md`
3. Jika repo belum berisi artefak terbaru: `git add . && git commit -m "Final artifacts" && git push origin main`.
4. Unggah **hanya** file PDF ke LMS pada deadline Senin, 7 Desember 2026 pukul 16.55 WIB.
5. Setelah unggah, muat ulang halaman LMS dan pastikan status submit tampil.

## Checklist cepat
- [ ] PDF ≤ 10 halaman
- [ ] DOCX = 10 halaman, A4, 7 shape editabel (0 gambar raster)
- [ ] Slide ≤ 12 slide
- [ ] CSV mentah + ringkasan + grafik ada
- [ ] Tautan repo aktif
- [ ] Diagram XML + PNG + DOCX ada
- [ ] Pembagian kerja tercantum di laporan
