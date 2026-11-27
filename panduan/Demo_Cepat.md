# Demo Cepat — 5 Menit (Dua Arah)

Panduan ini dipakai untuk sesi live demo di kelas. Jalankan semua perintah dari
**root repositori**. Port 1884 (MQTT) dan 5684 (CoAP) dipakai agar tidak bentrok
dengan proses yang mungkin masih berjalan di port default 1883/5683.

## 0. Siapkan payload (10 detik)

```powershell
python experiments\payload_gen.py --size 4096 --out data\payload_4096.bin
```

## 1. Nyalakan tiga peran inti (30 detik)

Buka tiga terminal PowerShell, masing-masing menjalankan satu perintah:

```powershell
# Terminal A — MQTT broker
python src\mqtt_broker.py --port 1884

# Terminal B — CoAP server
python src\coap_server.py --port 5684

# Terminal C — Conversion server (dua arah)
python src\conversion_server.py --mqtt-port 1884 --coap-port 5684
```

Bukti hidup: `BROKER_READY`, `COAP_READY`, dan dua `CONV_READY` (MQTT + CoAP).

## 2. Pasang penerima dan verifier (20 detik)

```powershell
# Terminal D — menerima hasil translasi dari sisi CoAP
python src\mqtt_subscriber.py --port 1884 --duration 60

# Terminal E — memverifikasi hasil translasi dari sisi MQTT
python src\coap_client.py --mode get --port 5684 --duration 60
```

## 3. Demo arah MQTT → CoAP (60 detik)

```powershell
python src\mqtt_publisher.py --port 1884 --rate 10 --count 20 --payload-file data\payload_4096.bin
```

Bukti: `PUBLISH` di `data/raw/mqtt_publisher.jsonl` → `CONV_IN`/`CONV_OUT` di
`data/raw/conversion_server.jsonl` → `POST_OK`/`GET_OK` di
`data/raw/coap_server.jsonl` → `DELIVER` dengan `verified:true` di
`data/raw/coap_client.jsonl`.

## 4. Demo arah CoAP → MQTT (60 detik)

```powershell
python src\coap_client.py --mode post --port 5684 --rate 10 --count 20 --payload-file data\payload_4096.bin
```

Bukti: `POST` di `data/raw/coap_client.jsonl` → `CONV_IN`/`CONV_OUT` →
`PUBLISH` di `data/raw/mqtt_publisher.jsonl` → `DELIVER` dengan `verified:true`
di `data/raw/mqtt_subscriber.jsonl`. ID dan payload sama di kedua ujung.

## 5. Tutup demo

```powershell
powershell -File scripts\stop_all.ps1
```

## Jika demo gagal

1. Cek healthcheck: `python scripts\healthcheck.py`.
2. Cek baris `ERROR` di file JSONL yang bersangkutan.
3. Tunjukkan bukti cadangan yang sudah ada di `data/bukti_konektivitas/contoh/`
   dan data lengkap di `data/raw/messages.csv` + `data/summary/summary.csv`.
4. Jangan mengulang kampanye 40 run; hasil final sudah tervalidasi seluruhnya.

## Pembagian narasi (2 + 3 + 5 + 3 menit)

| Menit | Pembicara | Isi |
|---|---|---|
| 0–2 | Irfan | Masalah, tujuan replikasi, beda MQTT (TCP pub/sub) vs CoAP (UDP request/response) |
| 2–5 | Hadrian | Arsitektur enam peran, port 1883/1884 & 5683/5684, workflow dua arah |
| 5–10 | Bambang + Irfan | Live demo langsung kedua arah (langkah 0–4 di atas) |
| 10–13 | Hadrian + Bambang | Hasil 40 run, perbandingan artikel, keterbatasan |

Sisa 5–7 menit dipakai untuk tanya jawab dan verifikasi individu.
