# Atribusi modul diagram (`vendor/jump2/`)

Empat modul dalam folder ini — `uml_core.py`, `uml_drawml.py`, `uml_png.py`,
`uml_validate.py` — disalin dari toolkit lokal **JUMP2 UML diagrams** yang berada
di `D:\magang\bahan\jump2_diagrams\`. Dokumentasi asli toolkit tersebut ada di
`Dokumentasi_Diagram_JUMP2.docx` di direktori sumber. Modul dipakai **hanya pada
waktu build** untuk menghasilkan `output-xml/*.xml` (DrawingML editabel) dan
`output/*.png`; tidak ada kode vendor yang berjalan saat eksperimen atau demo.

## Status lisensi

Tidak ada berkas `LICENSE`, `COPYING`, atau pernyataan lisensi tertulis di
direktori sumber yang tersedia. Karena itu dokumen ini **tidak mengklaim** modul
berlisensi MIT/Apache/BSD. Jika proyek ini akan Didistribusikan ulang secara
komersial atau dengan cakupan lebih luas, konfirmasi lisensi perlu
diminta kepada pemilik toolkit terlebih dahulu. Untuk keperluan tugas akademik,
modul disertakan sebagai alat build dengan atribusi sumber seperti di atas.

## Perubahan lokal

- `uml_core.py`: resolusi direktori font kini mengikuti sistem operasi dan dapat
  di-override lewat variabel lingkungan `JUMP2_FONT_DIR`. Pada Windows hasilnya
  tetap `C:\Windows\Fonts`, sehingga rendering tidak berubah. Fallback
  DejaVuSans/Liberation Sans ditambahkan agar generator dapat dijalankan di Linux.
- Warna teks lifeline diubah dari putih ke hitam agar kontras memenuhi audit.

Perubahan lain terhadap emitter DrawingML (menghilangkan `w:ind` warisan dokumen)
juga merupakan patch lokal terhadap toolkit sumber dan tercatat di
`DIAGRAM_QA_REPORT.md`.
