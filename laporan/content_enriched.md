# Laporan Akhir: Jembatan Konversi Protokol MQTT dan CoAP

> **Dokumen arsip.** Ini adalah draf awal. Sumber kanonik laporan final adalah
> `laporan/content.py` yang dirender oleh `laporan/build_laporan.py` menjadi
> `Laporan_Akhir_Sistem_Terdistribusi.pdf` / `.docx`. Angka dan pembagian kerja di bawah
> sudah diselaraskan dengan artefak final, tetapi jangan dipakai sebagai sumber build.

## Ringkasan Eksekutif
Proyek ini mengimplementasikan *conversion server* dua arah yang menjembatani protokol MQTT dan CoAP untuk memungkinkan pertukaran data perangkat IoT pada jaringan IP konvensional tanpa bantuan SDN.

## Panduan Membaca dan Glosarium
Laporan ini disusun secara teknis untuk menjelaskan alur data dan hasil eksperimen.

*   **MQTT**: Protokol *publish-subscribe* berbasis TCP yang ringan.
*   **CoAP**: Protokol *request-response* berbasis UDP, dirancang untuk efisiensi di perangkat terbatas.
*   **Broker**: Pusat kendali MQTT yang menerima pesan dari *publisher* dan meneruskannya ke *subscriber*.
*   **Topik (MQTT)**: Jalur komunikasi untuk mengelompokkan pesan.
*   **Resource (CoAP)**: Endpoint (seperti `/target`) yang diakses via CoAP.
*   **Conversion Server**: Proses perantara yang menerjemahkan pesan antar protokol.
*   **Dedup**: Mekanisme untuk mencegah duplikasi pesan menggunakan ID unik.
*   **Anti-loop**: Teknik mencegah pesan berputar kembali ke asalnya.
*   **E2E Delay**: Waktu total pesan dari pengirim awal hingga diterima tujuan akhir.
*   **Blockwise**: Metode RFC 7959 untuk mengirim payload besar dengan membaginya ke blok-blok kecil.
*   **SHA-256**: Algoritma pengecekan integritas pesan.

## Latar Belakang
IoT membutuhkan efisiensi. MQTT cocok untuk komunikasi stabil, sementara CoAP cocok untuk efisiensi energi. Menjembatani keduanya memungkinkan fleksibilitas desain jaringan. Protokol standar TCP/IP tanpa SDN (Software Defined Networking) dipilih untuk menunjukkan bahwa integrasi ini dapat dilakukan di perangkat lunak *application layer*.

## Arsitektur Logis
Enam peran logis beroperasi:
1.  **MQTT Publisher**: Mengirim data ke topik `iot/mqtt_to_coap` (Port 1883).
2.  **Conversion Server**: Menunggu pesan MQTT dan meneruskannya ke CoAP `/target` (Port 5683/5684).
3.  **CoAP Server**: Menampung data pada resource `/target` dan `/source`.
4.  **CoAP Client**: Melakukan POST ke `/source` (c2m) dan GET `/target` untuk verifikasi (m2c); conversion server melakukan GET `/source` setiap 1 detik.
5.  **MQTT Subscriber**: Menerima data dari topik `iot/coap_to_mqtt` (Port 1884).

## Desain Konversi
Proses konversi mengikuti langkah:
1.  **Penerimaan**: Data diterima, divalidasi, dan diperiksa ID uniknya untuk dedup.
2.  **Pengecekan Loop**: Memeriksa tag `origin_processed` pada metadata.
3.  **Konversi**: Payload disesuaikan (MQTT ke CoAP atau sebaliknya).
4.  **Pengiriman**: Pesan dikirim ke tujuan dengan timestamp (`conv_send_ts`).
5.  **Polling**: CoAP client melakukan polling setiap 1 detik.

## Metode Eksperimen
Eksperimen melibatkan 40 run valid dengan payload 4.096 byte dan payload besar (204.800 byte).
*   **Conversion Delay (ms)**: `(conv_send_ts − conv_recv_ts) × 1000`
*   **E2E Delay (ms)**: `(dst_recv_ts − sent_ts) × 1000`
Konvensi positif digunakan agar delay selalu menunjukkan durasi yang terukur.

## Hasil Eksperimen (Ringkasan)
Data diambil dari 40 run stabil:
| Arah | Laju (msg/detik) | Rata-rata Conversion Delay (ms) | Rata-rata E2E Delay (ms) |
| :--- | :--- | :--- | :--- |
| M2C | 10 | 21.5 | 191.6 |
| C2M | 10 | 3.9 | 834.5 |
| M2C | 20 | 21.3 | 278.9 |
| C2M | 20 | 3.9 | 1126.7 |

## Analisis
Delay E2E lebih besar pada arah C2M karena mekanisme polling 1 detik pada CoAP. Payload besar yang menggunakan *blockwise* meningkatkan waktu pemrosesan, namun sistem tetap stabil pada batas beban.

## Kesimpulan
Proyek ini berhasil mendemonstrasikan interoperabilitas MQTT-CoAP melalui *conversion server*.
**Pembagian Kerja**:
*   Muhammad Irfan Maulana: Broker, publisher, subscriber, konektivitas.
*   Hadrian Rakha Khosyi Javier: CoAP server/client, payload.
*   Bambang Adhi Nurbiyanto: Conversion server, metrik, harness, laporan, slide.

**Sitasi**: Sumadi dkk., TELKOMNIKA 19(5):1544–1552, 2021, DOI 10.12928/TELKOMNIKA.v19i5.20412.
