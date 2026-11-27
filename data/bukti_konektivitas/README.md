# Bukti konektivitas (ringkas)

Direktori ini menyimpan **cuplikan log nyata** dari dua run percontoh,
`c2m_r10_s01` dan `m2c_r10_s01`, untuk keperluan verifikasi dari clone repositori.
Setiap baris adalah baris asli dari `data/raw/<run>/*.jsonl` (tanpa diubah),
diambil maksimal tiga kejadian per jenis: `BROKER_READY`, `COAP_READY`,
`CONV_READY`, `CONV_IN`, `CONV_OUT`, `POST_OK`, `GET_OK`, `PUBLISH`, dan
`DELIVER`. Kejadian `SKIP_DUP`/`SKIP_LOOP` tidak muncul dalam kampanye karena
tidak ada pesan duplikat maupun loop yang dihasilkan; mekanisme keduanya dibuktikan
oleh `tests/test_dedup.py` dan `tests/test_loop_prevention.py` (17 test lulus).

## Kenapa tidak semua log di-commit?

Log JSONL lengkap untuk 40 run berukuran sekitar 263 MB dan sengaja dikecualikan
lewat `.gitignore` (`data/raw/*/*.jsonl`). Bukti utama yang tetap di-commit adalah:

- `data/raw/messages.csv` — 290.107 baris, berisi ID, timestamp, delay, dan flag
  `delivered` untuk setiap pesan;
- `data/raw/run_*.json` — 40 metadata run (status `ok`, durasi 600 detik, port,
  ukuran payload);
- `data/summary/summary.csv` — 440 baris ringkasan per menit;
- cuplikan di folder `contoh/` ini.

Log lengkap dapat dibuat ulang dengan menjalankan perintah di
`panduan/Verifikasi_Individu.md`. Perlu diingat, `src/common/logging_conf.py`
menulis log proses manual ke `data/raw/` (akar), sedangkan harness `run_matrix.py`
menulisnya ke `data/raw/<run_id>/`.

## Catatan integritas

Kolom `payload_sha256` di `messages.csv` sengaja dikosongkan oleh `summarize.py`.
Verifikasi integritas terjadi saat runtime di `src/mqtt_subscriber.py` dan
`src/coap_client.py`, yang menulis `verified:true` atau `verified:false` ke log
JSONL per-run. Dari 290.107 pesan: 289.571 ber-`verified:true`, 0 ber-`verified:false`.
