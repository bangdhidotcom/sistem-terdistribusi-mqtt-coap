# QnA — Pertanyaan yang Mungkin Muncul Saat Presentasi

## Umum
**Q: Mengapa tidak memakai SDN/OpenFlow/RYU/Mininet seperti artikel?**
A: Spesifikasi tugas secara eksplisit melarangnya dan meminta jaringan IP konvensional. Enam peran logis tetap dipertahankan, tetapi dijalankan sebagai proses Python terpisah pada localhost.

**Q: Apakah ini benar-benar MQTT dan CoAP?**
A: Ya. MQTT memakai packet CONNECT/SUBSCRIBE/PUBLISH 3.1.1 pada broker mandiri; klien memakai paho-mqtt. CoAP memakai aiocoap dengan POST/GET serta blockwise sesuai RFC 7959.

## Desain
**Q: Bagaimana ID dan payload dijamin sama setelah konversi?**
A: Setiap pesan membawa `id` UUID, `seq`, `sent_ts`, payload base64, dan `payload_sha256`. Penerima menghitung ulang SHA-256 dan membandingkannya; hanya pesan valid yang dicatat sebagai `DELIVER`.

**Q: Bagaimana mencegah loop konversi balik?**
A: Conversion server menandai `meta.origin_processed=true` sebelum meneruskan pesan. Pesan dengan penanda ini dilewati (`SKIP_LOOP`). Dedup berbasis `id` juga mencegah pemrosesan ulang (`SKIP_DUP`).

**Q: Mengapa CoAP server menyimpan antrean, bukan satu pesan terakhir?**
A: Polling conversion server setiap 1 detik akan menimpa pesan jika hanya menyimpan satu pesan terakhir. Antrean memastikan semua pesan yang terkirim dapat diambil.

## Eksperimen
**Q: Mengapa payload kampanye 4 KB, bukan 200 KB?**
A: 200 KB diuji berhasil dengan blockwise, tetapi throughput turun ke sekitar 1 pesan/detik. Spesifikasi mengizinkan ukuran aman dengan penjelasan, sehingga kampanye laju 10/20 memakai 4 KB. Hasil 200 KB tetap disimpan sebagai uji tambahan.

**Q: Apakah laju 20 msg/s benar-benar tercapai?**
A: Laju dikonfigurasi 20 msg/s. Throughput aktual tercatat di CSV dan dibahas di laporan; aiocoap pada mesin uji menjadi batas praktis.

**Q: Kolom `payload_sha256` di `messages.csv` kok kosong?**
A: Kolom itu disiapkan sebagai tempat penulisan nilai hash, tetapi `summarize.py` mengosongkannya. Verifikasi integritas terjadi saat runtime: `src/mqtt_subscriber.py` dan `src/coap_client.py` menghitung ulang SHA-256 dan menulis `verified:true` atau `verified:false` ke log JSONL per-run. Dari 290.107 pesan, 289.571 ber-`verified:true` dan tidak ada satu pun `verified:false`, sehingga klaim di laporan tetap benar. Contoh log ada di `data/bukti_konektivitas/`.

**Q: Bagaimana delay konversi dihitung?**
A: `(conv_send_ts − conv_recv_ts) × 1000` ms. Spesifikasi menuliskan selisih terbalik; laporan mencatat penyesuaian ini agar bernilai positif.

**Q: Mengapa angka artikel acuan berbeda jauh?**
A: Artikel memakai OpenFlow dan definisi timestamp yang tampak tidak konsisten (delay puluhan detik pada satu arah, namun loss tinggi pada arah lain). Replikasi ini tidak meniru angka tersebut, melainkan membandingkan secara kualitatif.

## Luaran
**Q: Di mana diagram editabelnya?**
A: `output-xml/*.xml` berisi `<w:drawing>` dengan `wps:wsp`/`wpg:wgp` native Word (tanpa `r:embed`). `output/*.png` adalah render 200 dpi dari display list yang sama. Dokumen Word yang benar-benar editabel adalah `laporan/Diagram_Editabel_Word.docx`; DOCX laporan utama memakai preview PNG supaya teks tidak dobel saat diaudit.

**Q: Bagaimana jika live demo kurang dari 5 menit?**
A: Ikuti urutan ringkas di `panduan/Demo_Cepat.md`: enam perintah sudah disiapkan lengkap dengan port alternatif (1884/5684) dan ekspektasi baris log. Jika demo gagal, buka contoh log di `data/bukti_konektivitas/` sebagai cadangan.

**Q: File apa yang diunggah ke LMS?**
A: Satu laporan PDF saja. Semua komponen lain dicantumkan sebagai tautan di dalam PDF.
