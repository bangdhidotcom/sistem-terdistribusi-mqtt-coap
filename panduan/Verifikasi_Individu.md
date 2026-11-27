# Panduan Verifikasi Individu

Tujuan: dosen dapat menilai kontribusi masing-masing anggota (30% dari nilai) dengan menjalankan bukti teknis secara mandiri.

## 1. Irfan — sisi MQTT dan konektivitas
1. Hentikan proses lama: `powershell -File scripts\stop_all.ps1`.
2. Jalankan broker: `python src\mqtt_broker.py --port 1883`.
3. Cek `data\raw\mqtt_broker.jsonl` harus ada `BROKER_READY`.
4. Jalankan publisher: `python src\mqtt_publisher.py --rate 10 --count 20 --payload-file data\payload_4096.bin`.
5. Di terminal lain: `python src\mqtt_subscriber.py --duration 10`.
6. Bukti: entri `PUBLISH` di `data\raw\mqtt_publisher.jsonl` dan koneksi TCP ke port 1883.

## 2. Hadrian — sisi CoAP dan payload
1. Jalankan `python src\coap_server.py --port 5683`; cek `COAP_READY` di `data\raw\coap_server.jsonl`.
2. Buat payload: `python experiments\payload_gen.py --size 4096 --out data\payload_4096.bin`.
3. Uji: `python src\coap_client.py --mode post --count 5 --rate 10 --payload-file data\payload_4096.bin`.
4. Verifikasi: `python src\coap_client.py --mode get --count 5`.
5. Uji tambahan 200 KB: `python experiments\payload_gen.py --size 204800` lalu ulangi POST/GET.

## 3. Bambang — conversion server, metrik, harness
1. Jalankan urutan: broker → CoAP server → conversion server.
2. Cek `CONV_READY`, `CONV_IN`, `CONV_OUT` di `data\raw\conversion_server.jsonl`.
3. Smoke: `python experiments\run_matrix.py --duration 15 --reps 1 --rate 10 --direction both --payload-size 4096`.
4. Ringkas: `python experiments\summarize.py` dan `python experiments\plotting.py`.
5. Bukti: `data\raw\messages.csv`, `data\summary\summary.csv`, `data\grafik\*.png`.

## Kriteria lulus
- ID unik dan timestamp hadir pada setiap pesan.
- `payload_sha256` terverifikasi di penerima.
- Pesan ber-`origin_processed=true` tidak dikonversi ulang (`SKIP_LOOP`).
- CSV dan grafik dapat dibuka serta sesuai data.
