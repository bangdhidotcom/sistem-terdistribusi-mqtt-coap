"""Sumber tunggal isi laporan.

File ini sengaja hanya berisi data. Renderer PDF dan DOCX membaca BLOCKS yang
sama, sehingga kedua dokumen tidak mungkin berbeda isinya.
"""

BLOCKS = [
    {
        "type": "title",
        "text": "LAPORAN AKHIR SISTEM TERDISTRIBUSI",
        "sub": "Replikasi Conversion Server MQTT &#8596; CoAP pada Jaringan IP Konvensional<br>"
               "Mata Kuliah Sistem Terdistribusi A &#8212; Kelompok 3<br>"
               "Muhammad Irfan Maulana (202310370311480)<br>"
               "Hadrian Rakha Khosyi Javier (202310370311483)<br>"
               "Bambang Adhi Nurbiyanto (202310370311484)<br>"
               "Batas pengumpulan: 7 Desember 2026 pukul 16.55 WIB",
    },
    {
        "type": "meta",
        "rows": [
            ["Topik", "Konversi pesan dua arah MQTT &#8596; CoAP"],
            ["Pendekatan", "Enam peran logis sebagai enam proses Python terpisah pada TCP/IP biasa"],
            ["Status akhir", "40 dari 40 run valid; tidak ada run dengan delivered = 0"],
            ["Repositori", "https://github.com/bangdhidotcom/sistem-terdistribusi-mqtt-coap"],
        ],
    },
    {"type": "h1", "text": "Ringkasan Eksekutif"},
    {
        "type": "p",
        "text": "Laporan ini menjawab satu pertanyaan sederhana: <b>bagaimana dua perangkat yang berbicara "
                "dengan protokol berbeda tetap bisa bertukar pesan tanpa jaringan khusus?</b> Jawabannya "
                "adalah dengan menempatkan sebuah <b>conversion server</b> di tengah. Kami mereplikasi "
                "desain tersebut memakai MQTT (publish/subscribe di atas TCP) dan CoAP (request/response "
                "di atas UDP) pada satu host localhost. Enam peran logis dijalankan terpisah agar "
                "masing-masing dapat diverifikasi. Kampanye eksperimen terdiri dari 40 run: dua arah, "
                "dua laju (10 dan 20 pesan/detik), sepuluh pengulangan, masing-masing 10 menit. "
                "Seluruh 40 run berhasil, dengan total <b>290.107 pesan terkirim</b> dan <b>99,815% "
                "terverifikasi</b>. Kami mengukur tingkat keberhasilan, loss, delay konversi, "
                "delay ujung-ke-ujung (E2E), CPU, dan memori. Payload utama berukuran 4.096 byte; "
                "payload 204.800 byte diuji terpisah dengan blockwise karena ukuran itu terlalu besar "
                "untuk satu datagram CoAP.",
    },
    {
        "type": "callout",
        "title": "Inti project dalam satu kalimat",
        "text": "Conversion server menerima pesan dari satu protokol, menerjemahkannya, lalu "
                "meneruskannya ke protokol lain <b>tanpa mengubah ID, timestamp, dan isi payload</b>.",
    },
    {"type": "h1", "text": "Cara Membaca Laporan Ini"},
    {
        "type": "p",
        "text": "Jika Anda baru membaca laporan teknis, mulailah dari glosarium. Setelah itu ikuti "
                "Gambar 1 untuk melihat siapa berbicara dengan siapa, lalu Gambar 2 dan Gambar 3 untuk "
                "melihat urutan pesan. Bagian Metode menjelaskan cara mengukur, bagian Hasil menampilkan "
                "data, dan bagian Analisis menjelaskan <b>kenapa</b> angkanya bisa seperti itu.",
    },
    {
        "type": "numbered",
        "items": [
            "Baca glosarium untuk mengenal istilah.",
            "Lihat arsitektur untuk memetakan enam peran.",
            "Ikuti dua alur konversi langkah demi langkah.",
            "Pahami matriks dan rumus pengukuran.",
            "Baca grafik, lalu baca penjelasannya di Analisis.",
        ],
    },
    {
        "type": "glossary",
        "items": [
            ["MQTT", "Protokol pesan dengan pola publish/subscribe; cocok untuk koneksi persisten dan komunikasi banyak-ke-banyak."],
            ["CoAP", "Protokol ringan dengan pola request/response; dirancang untuk perangkat kecil di atas UDP."],
            ["Broker", "Pusat distribusi MQTT. Ibarat resepsionis yang menerima surat lalu meneruskannya."],
            ["Topik", "Alamat logika MQTT, misalnya <b>iot/mqtt_to_coap</b>. Bukan alamat IP."],
            ["Resource", "Alamat logika CoAP, misalnya <b>/target</b>. Ibarat nama meja layanan."],
            ["Conversion server", "Jembatan yang menerjemahkan pesan MQTT menjadi CoAP dan sebaliknya."],
            ["Deduplikasi", "Mencegah pesan dengan ID sama diproses dua kali."],
            ["Antrean (queue)", "Tempat penyimpanan sementara agar pesan tidak hilang sebelum diambil."],
            ["Polling", "Pengecekan berulang, di sini setiap 1 detik, untuk mengambil pesan baru."],
            ["E2E delay", "Waktu dari pesan dikirim sampai diterima di ujung tujuan."],
            ["Blockwise", "Memecah data besar menjadi potongan kecil sesuai RFC 7959."],
            ["SHA-256", "Sidik jari digital untuk membuktikan isi pesan tidak berubah."],
        ],
    },
    {
        "type": "p",
        "text": "Istilah-istilah di atas adalah fondasi untuk memahami seluruh bab berikutnya. "
                "Saat membaca alur konversi, coba petakan setiap istilah ke peran yang sesuai: "
                "publisher dan broker memakai topik, CoAP client memakai resource, dan conversion "
                "server menghubungkan keduanya.",
    },
    {"type": "pagebreak"},
    {"type": "h1", "text": "1. Latar Belakang dan Tujuan"},
    {
        "type": "p",
        "text": "Perangkat IoT tidak semuanya berbicara dengan bahasa yang sama. Ada yang memakai MQTT, "
                "ada yang memakai CoAP. MQTT seperti <b>resepsionis</b>: ia menerima pesan di meja "
                "(broker) lalu meneruskannya ke orang yang berlangganan topik tertentu. CoAP seperti "
                "<b>kurir kilat</b>: ia mengetuk alamat tertentu (resource) dan menunggu jawaban. "
                "Conversion server berperan sebagai <b>penerjemah</b> yang duduk di antara keduanya.",
    },
    {
        "type": "callout",
        "title": "Analogi yang dipakai di seluruh laporan",
        "text": "Bayangkan translator di bandara. Ia tidak menulis ulang isi surat; ia hanya "
                "mengganti bahasa sampulnya. Begitu juga conversion server: ID dan payload tetap sama, "
                "yang berubah hanya 'bahasa protokol' dan alamat tujuannya.",
    },
    {
        "type": "p",
        "text": "Tujuan kami ada tiga: (1) mereplikasi mekanisme konversi dua arah tanpa SDN, OpenFlow, "
                "RYU, Mininet, atau OVS; (2) membuktikan pesan tetap utuh dengan ID unik, timestamp, "
                "dan hash SHA-256; (3) mengukur kinerja secara otomatis pada laju 10 dan 20 pesan/detik. "
                "Lingkupnya sengaja dibatasi pada satu host agar hasil mudah direproduksi oleh anggota "
                "kelompok maupun pemeriksa.",
    },
    {
        "type": "bullets",
        "items": [
            "<b>Yang kami lakukan:</b> TCP/IP konvensional, enam proses Python, pengukuran otomatis.",
            "<b>Yang tidak kami lakukan:</b> jaringan software-defined, controller OpenFlow, atau emulator jaringan.",
            "<b>Yang kami dokumentasikan:</b> konflik satuan laju di spesifikasi dan keterbatasan ukuran payload.",
        ],
    },
    {"type": "h1", "text": "2. Tinjauan Pustaka"},
    {
        "type": "p",
        "text": "Acuan utama adalah Sumadi dkk., <i>Enabling seamless communication over several IoT "
                "messaging protocols in OpenFlow network</i>, TELKOMNIKA 19(5), halaman 1544&#8211;1552, "
                "2021, DOI [10.12928/TELKOMNIKA.v19i5.20412](https://doi.org/10.12928/TELKOMNIKA.v19i5.20412). "
                "Artikel itu memakai jaringan OpenFlow dan mengubah topik MQTT menjadi resource CoAP. "
                "Perbedaan kami: tidak ada controller jaringan, dan konversi dilakukan murni oleh "
                "proses aplikasi.",
    },
    {
        "type": "p",
        "text": "Dasar sistem terdistribusi mengikuti Coulouris dkk., <i>Distributed Systems: Concepts "
                "and Design</i>, edisi ke-5, serta materi perkuliahan Sistem Terdistribusi UMM 2026 "
                "tentang replikasi dan toleransi kesalahan. Deduplikasi berbasis ID unik adalah bentuk "
                "sederhana dari toleransi terhadap pengiriman ulang.",
    },
    {
        "type": "callout",
        "title": "Kenapa angka artikel tidak kami salin",
        "text": "Artikel acuan memuat angka yang tampak inkonsisten: delay MQTT&#8596;CoAP puluhan "
                "detik sementara arah sebaliknya sekitar 0,18 detik dengan loss 92&#8211;95%. Kami tidak "
                "mengklaim angka kami lebih benar; kami hanya membandingkan secara kualitatif dan "
                "menjelaskan perbedaan definisi timestamp serta antrean.",
    },
    {"type": "h2", "text": "2.1 Konfigurasi artikel dan adaptasi kami"},
    {
        "type": "table",
        "header": ["Parameter", "Nilai pada artikel", "Adaptasi pada proyek ini"],
        "rows": [
            ["Jumlah pesan per skenario", "200 pesan (bukan target kami)", "Uji durasi 10 menit; 4.492&#8211;11.087 pesan per run"],
            ["Laju pengiriman", "10 dan 20 pesan/detik", "Dipertahankan persis (10 dan 20 pesan/detik)"],
            ["Ukuran payload", "200 KB", "4.096 byte pada matriks utama; 204.800 byte diuji terpisah (blockwise)"],
            ["Arah translasi", "MQTT ke CoAP dan sebaliknya", "Dipertahankan persis"],
            ["Metrik", "delay konversi, RTT, loss, CPU", "Keberhasilan, loss, delay konversi, E2E, CPU dan memori"],
        ],
        "widths_cm": [3.8, 5.0, 7.2],
    },
    {
        "type": "p",
        "text": "Terkait angka <b>200 pesan</b>: artikel menguji 200 pesan per skenario, sehingga pada laju "
                "10 pesan/detik percobaan hanya berlangsung sekitar 20 detik. Kampanye kami justru menguji "
                "<b>beban berkelanjutan 10 menit</b>: setiap run mengirim antara 4.492 dan 11.087 pesan, "
                "sekitar 22&#8211;55 kali lipat jumlah pesan artikel. Jadi 200 pesan adalah parameter "
                "skenario artikel acuan, bukan target jumlah pesan proyek ini. Kami tidak mengabaikan konfigurasi "
                "artikel; kami menggantinya dengan uji lebih panjang agar tren per menit, stabilitas "
                "antrean, dan pemanasan CPU dapat diamati. Perubahan ini kami nyatakan eksplisit di sini "
                "sesuai ketentuan adaptasi teknis spek.",
    },
    {"type": "h2", "text": "2.2 Hasil artikel sebagai pembanding"},
    {
        "type": "table",
        "header": ["Arah", "Pesan/detik", "Delay (s)", "RTT (s)", "Loss (%)"],
        "rows": [
            ["MQTT ke CoAP", "10", "52,43407", "52,9", "0"],
            ["MQTT ke CoAP", "20", "53,11167", "53,5", "0"],
            ["CoAP ke MQTT", "10", "0,179852", "0,1", "92,53731"],
            ["CoAP ke MQTT", "20", "0,182637", "0,1", "95,52239"],
        ],
        "widths_cm": [4.6, 2.8, 3.2, 2.6, 2.8],
    },
    {
        "type": "p",
        "text": "Tabel di atas adalah pembanding, bukan target yang harus ditiru. Artikel memakai RYU, "
                "Open vSwitch, Raspberry Pi, dan ESP8266 dengan payload 200 KB; kami memakai enam proses "
                "Python pada satu host dengan payload 4 KB. Perbedaan definisi timestamp, mekanisme antrean, "
                "interval polling, dan ukuran payload membuat angka tidak sebanding secara langsung. "
                "Kami bahas sebabnya di Bab 7.",
    },
    {"type": "h1", "text": "3. Arsitektur Sistem"},
    {
        "type": "p",
        "text": "Gambar 1 memetakan enam peran. Jalur biru adalah arah MQTT ke CoAP; jalur hijau adalah "
                "arah CoAP ke MQTT; kotak ungu adalah conversion server. Setiap peran berjalan sebagai "
                "proses Python tersendiri, sehingga jika satu proses gagal, proses lain tetap bisa "
                "diperiksa secara terpisah.",
    },
    {
        "type": "image",
        "path": "output/mqtt_coap_architecture.png",
        "caption": "Gambar 1. Arsitektur enam peran logis. Biru = MQTT&#8594;CoAP, hijau = CoAP&#8594;MQTT, "
                   "ungu = conversion server. Kotak melengkung melambangkan proses/peran.",
        "width_cm": 15.5,
    },
    {
        "type": "table",
        "header": ["No", "Peran dan file", "Tanggung jawab", "Alamat / kanal"],
        "rows": [
            ["1", "MQTT broker<br>src/mqtt_broker.py", "Menerima publish dan mendistribusikan lewat TCP", "127.0.0.1:1883 dan :1884"],
            ["2", "CoAP server<br>src/coap_server.py", "Resource POST/GET via UDP, simpan data terbaru", "127.0.0.1:5683 dan :5684"],
            ["3", "Conversion server<br>src/conversion_server.py", "Menjalankan modul MQTT&#8594;CoAP dan CoAP&#8594;MQTT", "subscribe MQTT + POST/GET CoAP"],
            ["4", "MQTT publisher<br>src/mqtt_publisher.py", "Pesan uji ber-ID unik, timestamp, dan payload", "iot/mqtt_to_coap"],
            ["5", "MQTT subscriber<br>src/mqtt_subscriber.py", "Menerima hasil translasi dari sisi CoAP", "iot/coap_to_mqtt"],
            ["6", "CoAP POST/GET client<br>src/coap_client.py", "Kirim ke CoAP dan verifikasi hasil dari MQTT", "/source dan /target"],
        ],
        "widths_cm": [0.8, 4.4, 6.0, 4.8],
    },
    {
        "type": "p",
        "text": "Dua port dipakai per arah supaya dua skenario dapat diverifikasi tanpa bentrok: "
                "MQTT 1883 dengan CoAP 5683 untuk MQTT&#8594;CoAP, dan MQTT 1884 dengan CoAP 5684 untuk "
                "CoAP&#8594;MQTT. Topik <b>iot/mqtt_to_coap</b> dan <b>iot/coap_to_mqtt</b> serta resource "
                "<b>/target</b> dan <b>/source</b> menjadi kontrak antarproses.",
    },
    {"type": "pagebreak"},
    {"type": "h1", "text": "4. Alur Konversi Pesan"},
    {
        "type": "p",
        "text": "Setiap pesan membawa UUID unik, nomor urut, timestamp pengiriman, payload dalam base64, "
                "dan hash SHA-256. Timestamp tambahan dicatat saat converter menerima/mengirim dan saat "
                "tujuan menerima. Dengan begitu, keutuhan dan keterlambatan dapat dihitung ulang dari data mentah.",
    },
    {"type": "h2", "text": "4.1 Arah MQTT ke CoAP"},
    {
        "type": "image",
        "path": "output/flow_mqtt_to_coap.png",
        "caption": "Gambar 2. Enam tahap MQTT&#8594;CoAP. Panah berwarna = pesan; loop ungu = aksi internal; "
                   "bilah pada Conversion Server = masa aktifnya.",
        "width_cm": 12.5,
    },
    {
        "type": "numbered",
        "items": [
            "Publisher membuat JSON berisi <b>id, seq, sent_ts, payload, sha256</b>, lalu publish ke topik <b>iot/mqtt_to_coap</b>.",
            "Broker menerima PUBLISH dan meneruskannya ke subscriber/conversion server.",
            "Conversion server memeriksa ID (dedup) dan hash, lalu menandai <b>origin_processed</b> agar tidak loop.",
            "Converter mencatat <b>conv_recv_ts</b>, melakukan POST CoAP ke resource <b>/target</b>, lalu mencatat <b>conv_send_ts</b>.",
            "CoAP server menyimpan pesan dalam antrean <b>/target</b> agar tidak tertimpa siklus GET berikutnya.",
            "CoAP GET client mengambil pesan, mencocokkan SHA-256, dan mencatat <b>dst_recv_ts</b>.",
        ],
    },
    {
        "type": "table",
        "header": ["Tahap", "1", "2", "3", "4", "5", "6"],
        "rows": [["Bukti minimum (&#167;3.1)", "Log kirim dan ID", "Pesan terlihat di broker",
                  "Log terima dan validasi", "Log mulai translasi", "Log ID tersimpan", "Integritas E2E"]],
        "widths_cm": [2.9, 2.3, 2.3, 2.4, 2.3, 2.0, 1.8],
    },
    {"type": "h2", "text": "4.2 Arah CoAP ke MQTT"},
    {
        "type": "image",
        "path": "output/flow_coap_to_mqtt.png",
        "caption": "Gambar 3. Enam tahap CoAP&#8594;MQTT. Perhatikan tahap 3 (polling 1 detik) dan tahap 4 (dedup).",
        "width_cm": 12.5,
    },
    {
        "type": "numbered",
        "items": [
            "CoAP POST client mengirim JSON ke resource <b>/source</b> pada port 5684.",
            "CoAP server memasukkan pesan ke antrean <b>/source</b>.",
            "Conversion server melakukan GET setiap <b>1 detik</b> untuk mengambil antrean.",
            "Converter membuang ID yang sudah pernah diproses (deduplikasi) dan menandai origin_processed.",
            "Converter publish ke topik <b>iot/coap_to_mqtt</b> lewat broker 1884.",
            "MQTT subscriber menerima, memverifikasi ID/hash, lalu mencatat <b>dst_recv_ts</b>.",
        ],
    },
    {
        "type": "table",
        "header": ["Tahap", "1", "2", "3", "4", "5", "6"],
        "rows": [["Bukti minimum (&#167;3.2)", "Log kirim dan ID", "Log resource dan code",
                  "Log polling dan GET", "Keputusan publish / skip", "Log publish dan koneksi", "Log terima dan validasi"]],
        "widths_cm": [2.9, 2.3, 2.3, 2.4, 2.3, 2.0, 1.8],
    },
    {
        "type": "callout",
        "title": "Kenapa ada antrean dan polling?",
        "text": "CoAP GET tidak bisa 'mendengarkan' seperti MQTT subscribe. Karena itu converter "
                "harus bertanya berulang. Antrean memastikan pesan yang masuk di antara dua pertanyaan "
                "tidak hilang. Polling 1 detik menyederhanakan desain, tetapi menambah delay rata-rata "
                "pada arah CoAP&#8594;MQTT.",
    },
    {
        "type": "p",
        "text": "Anti-loop dijaga dengan penanda <b>origin_processed</b>: pesan yang sudah dikonversi "
                "tidak dikonversi lagi saat muncul di sisi lain. Tanpa penanda ini, pesan bisa "
                "berputar terus antara MQTT dan CoAP.",
    },
    {"type": "pagebreak"},
    {"type": "h1", "text": "5. Metode Eksperimen"},
    {
        "type": "p",
        "text": "Pengujian dijalankan otomatis pada Windows 11, Python 3.14, di localhost. Pustaka "
                "yang dipakai: paho-mqtt 2.2.0, aiocoap 0.4.17, scapy (pembentuk payload), dan psutil "
                "(pengambil CPU/memori). Harness menulis logger JSONL per proses, CSV mentah per pesan, "
                "dan CSV ringkasan per menit.",
    },
    {
        "type": "table",
        "header": ["Aspek", "Nilai", "Alasan"],
        "rows": [
            ["Arah", "MQTT&#8594;CoAP dan CoAP&#8594;MQTT", "Menguji kedua jalur konversi"],
            ["Laju", "10 dan 20 pesan/detik", "Sesuai matriks tugas"],
            ["Pengulangan", "10 kali per kombinasi", "Melihat konsistensi, bukan satu sampel"],
            ["Durasi", "10 menit per run", "Total 40 run"],
            ["Payload utama", "4.096 byte", "Jauh di bawah MTU praktis CoAP"],
            ["Payload tambahan", "204.800 byte", "Uji blockwise RFC 7959 terpisah"],
            ["Metrik", "Sukses, loss, delay konversi, E2E, CPU, memori", "Sesuai rubrik"],
        ],
        "widths_cm": [3.2, 5.8, 7.0],
    },
    {
        "type": "callout",
        "title": "Konflik satuan di spesifikasi",
        "text": "Matriks tugas menyebut '10 pesan/menit' di satu tempat dan '10/20 pesan/detik' di "
                "tempat lain. Kami memilih 10 dan 20 pesan/detik karena itu yang paling konsisten "
                "dengan requirement pengujian beban, dan mencatat konflik ini di laporan.",
    },
    {
        "type": "p",
        "text": "Rumusnya sederhana. <b>Sukses (%) = pesan terverifikasi / pesan terkirim &#215; 100</b>. "
                "<b>Loss (%) = 100 &#8722; sukses</b>. Contoh: dari 1.000 pesan, 998 terverifikasi, "
                "maka sukses = 99,8% dan loss = 0,2%.",
    },
    {
        "type": "p",
        "text": "<b>Delay konversi = (conv_send_ts &#8722; conv_recv_ts) &#215; 1000 ms</b>. "
                "<b>Delay E2E = (dst_recv_ts &#8722; sent_ts) &#215; 1000 ms</b>. Contoh: jika converter "
                "menerima pada 10,000 s dan mengirim pada 10,01234 s, delay konversinya 12,34 ms. "
                "Spesifikasi menuliskan selisih terbalik; kami memakai konvensi positif agar waktu "
                "mundur tidak bernilai negatif, dan kami dokumentasikan.",
    },
    {
        "type": "p",
        "text": "Untuk CPU dan memori, psutil diambil <b>592 sampel per run</b> (interval 1 detik selama "
                "10 menit). Dari sampel itu dihitung tiga ringkasan: <b>rerata</b> (nilai tipikal), "
                "<b>p95</b> (nilai yang hanya terlampaui 5% sampel), dan <b>puncak</b> (nilai maksimum). "
                "Ketiganya wajib dilaporkan. p95 lebih tahan terhadap lonjakan sesaat daripada puncak, "
                "tetapi tetap memperlihatkan beban ekstrem.",
    },
    {
        "type": "callout",
        "title": "Kenapa 200 KB tidak dipakai di kampanye utama?",
        "text": "Payload 204.800 byte memang berhasil dikirim dengan blockwise, tetapi throughput "
                "turun ke sekitar 1 pesan/detik. Memaksanya masuk matriks 10/20 pesan/detik akan "
                "menghasilkan data yang tidak sepadan. Karena itu kampanye utama memakai 4 KB dan "
                "uji 200 KB disimpan sebagai bukti tambahan.",
    },
    {"type": "h1", "text": "6. Hasil Eksperimen"},
    {
        "type": "p",
        "text": "Tabel berikut adalah agregasi dari <b>data/summary/summary.csv</b> (440 baris = 40 run "
                "&#215; 11 entri). Angka diambil langsung dari hasil eksperimen, bukan estimasi.",
    },
    {
        "type": "p",
        "text": "<b>Tabel 6.1.</b> Rerata keberhasilan konversi untuk seluruh pengulangan selama 10 menit. "
                "Kolom Terkirim dan Terverifikasi adalah total akumulasi dari 10 run per kombinasi.",
    },
    {
        "type": "table",
        "header": ["Arah", "Laju", "Terkirim", "Terverifikasi", "Keberhasilan (%)", "Pengulangan"],
        "rows": [
            ["CoAP&#8594;MQTT", "10", "46.599", "46.599", "100,00", "10"],
            ["CoAP&#8594;MQTT", "20", "75.060", "75.055", "99,98", "10"],
            ["MQTT&#8594;CoAP", "10", "57.576", "57.411", "99,28", "10"],
            ["MQTT&#8594;CoAP", "20", "110.872", "110.506", "97,97", "10"],
        ],
        "widths_cm": [3.4, 1.2, 2.6, 2.7, 3.4, 2.7],
    },
    {
        "type": "p",
        "text": "<b>Tabel 6.2.</b> Rerata conversion loss dan pemakaian sumber daya conversion server. "
                "Tiga angka pada kolom CPU dan Memori berturut-turut adalah <b>rerata / p95 / puncak</b>.",
    },
    {
        "type": "table",
        "header": ["Arah", "Laju", "Loss (%)", "Delay konv. (ms)", "Delay E2E (ms)", "CPU (%)", "Memori (MB)"],
        "rows": [
            ["CoAP&#8594;MQTT", "10", "0,00", "3,88", "834,50", "12,67 / 20,28 / 26,5", "49,9 / 53,3 / 54,7"],
            ["CoAP&#8594;MQTT", "20", "0,02", "3,93", "1.126,71", "20,32 / 34,83 / 72,3", "54,2 / 58,7 / 59,9"],
            ["MQTT&#8594;CoAP", "10", "0,72", "21,49", "191,63", "11,04 / 16,43 / 26,5", "43,6 / 44,1 / 44,5"],
            ["MQTT&#8594;CoAP", "20", "2,03", "21,32", "278,94", "17,64 / 25,24 / 54,6", "43,9 / 44,2 / 44,5"],
        ],
        "widths_cm": [2.8, 0.9, 1.3, 2.5, 2.6, 3.1, 2.8],
    },
    {
        "type": "p",
        "text": "<b>Catatan pembacaan tabel:</b> angka di atas adalah agregat rata-rata dari 40 run "
                "eksperimen yang valid (10 pengulangan &#215; 4 kombinasi arah dan laju), bukan hasil "
                "dari satu kali pengiriman. Jumlah pesan pada kolom Terkirim dan Terverifikasi adalah "
                "total akumulasi selama 10 menit per run.",
    },
    {
        "type": "images_row",
        "items": [
            {
                "path": "data/grafik/delay_e2e_per_menit.png",
                "caption": "Gambar 4. E2E delay c2m lebih tinggi karena polling 1 detik.",
                "width_cm": 7.1,
            },
            {
                "path": "data/grafik/delay_konversi_per_menit.png",
                "caption": "Gambar 5. Konversi m2c lebih lama karena round-trip POST CoAP.",
                "width_cm": 7.1,
            },
        ],
    },
    {
        "type": "images_row",
        "items": [
            {
                "path": "data/grafik/cpu_per_menit.png",
                "caption": "Gambar 6. CPU naik saat laju 20 pesan/detik, namun tetap wajar.",
                "width_cm": 7.1,
            },
            {
                "path": "data/grafik/perbandingan_artikel.png",
                "caption": "Gambar 7. Perbandingan kualitatif dengan artikel acuan.",
                "width_cm": 7.1,
            },
        ],
    },
    {
        "type": "p",
        "text": "Cara membaca grafik: garis yang naik berarti delay atau CPU bertambah pada menit "
                "tersebut. Fluktuasi kecil masih wajar pada localhost karena penjadwalan proses. "
                "Yang penting adalah tren dan besaran, bukan satu titik ekstrem. Seluruh grafik "
                "dirata-ratakan per menit dari 10 run, sehingga satu titik tidak mewakili satu pesan "
                "tunggal melainkan ratusan pesan dalam menit itu.",
    },
    {
        "type": "p",
        "text": "Menjawab <b>mengapa</b> angka di tabel muncul: arah CoAP&#8594;MQTT hampir tanpa loss "
                "karena antrean <b>/source</b> menyimpan pesan sampai converter mengambilnya, tetapi E2E "
                "tinggi karena polling 1 detik. Arah MQTT&#8594;CoAP loss-nya lebih besar karena POST CoAP "
                "memiliki batas timeout, sementara E2E tetap rendah karena broker langsung meneruskan "
                "pesan. p95 delay E2E mencapai 1.365&#8211;1.731 ms pada c2m dan 309&#8211;454 ms pada m2c, "
                "menunjukkan ekor distribusi yang jauh lebih panjang dari rerata. CPU dan memori naik "
                "seiring laju 20 pesan/detik, tetapi puncak CPU 72,3% masih menyisakan ruang.",
    },
    {"type": "pagebreak"},
    {"type": "h1", "text": "7. Analisis dan Diskusi"},
    {
        "type": "p",
        "text": "Arah <b>CoAP&#8594;MQTT</b> memiliki E2E delay jauh lebih besar (834&#8211;1.127 ms) "
                "waktu konversinya sangat kecil (~4 ms). Ini membuktikan bahwa delay didominasi "
                "<b>polling 1 detik</b>, bukan proses konversi. Sebaliknya, arah <b>MQTT&#8594;CoAP</b> "
                "memiliki E2E lebih kecil (192&#8211;279 ms) tetapi delay konversi lebih besar (~21 ms), "
                "karena converter menunggu jawaban POST CoAP.",
    },
    {
        "type": "bullets",
        "items": [
            "Keutuhan pesan terjaga: SHA-256 cocok di kedua arah.",
            "Antrean CoAP mencegah pesan tertimpa antar siklus GET.",
            "Deduplikasi ID mencegah pesan diproses dua kali.",
            "Penanda origin_processed mencegah loop balik.",
            "Retry dan perbaikan timeout menghasilkan 40/40 run valid.",
        ],
    },
    {
        "type": "callout",
        "title": "Kenapa 20 pesan/detik lebih berat?",
        "text": "Pada 20 pesan/detik, antrean CoAP lebih cepat penuh dan verifier GET lebih sering "
                "bekerja. Kami memperbaiki stabilitas dengan membatasi jumlah pesan per respons GET, "
                "menaikkan timeout GET, dan mempercepat polling verifikasi.",
    },
    {
        "type": "p",
        "text": "Memori converter relatif stabil: rerata 43,6&#8211;54,2 MB, p95 44,1&#8211;58,7 MB, "
                "dan puncak 44,5&#8211;59,9 MB. Kisaran p95 yang dekat dengan rerata menunjukkan tidak "
                "ada kebocoran memori selama 10 menit; kenaikan mengikuti laju pesan, bukan durasi. "
                "Ini penting karena metrik memori sering terlihat 'datar' pada grafik CPU.",
    },
    {
        "type": "p",
        "text": "Keterbatasan tetap ada: eksperimen memakai satu host sehingga tidak menguji "
                "jitter jaringan nyata; pustaka aiocoap memiliki batas praktis pada beban tinggi; "
                "payload 200 KB hanya diuji terpisah; dan desain ini sengaja tanpa SDN/OpenFlow. "
                "Keterbatasan ini tidak membatalkan kesimpulan utama, tetapi harus diketahui pembaca.",
    },
    {"type": "h1", "text": "8. Pembagian Kerja"},
    {
        "type": "table",
        "header": ["Anggota", "Fokus utama", "Bukti di repositori"],
        "rows": [
            ["Muhammad Irfan Maulana", "Broker, publisher, subscriber, konektivitas", "src/mqtt_*.py"],
            ["Hadrian Rakha Khosyi Javier", "CoAP server/client, payload", "src/coap_server.py, src/coap_client.py"],
            ["Bambang Adhi Nurbiyanto", "Conversion server, metrik, harness, laporan, slide", "src/conversion_server.py, experiments/, laporan/"],
        ],
        "widths_cm": [4.2, 6.0, 5.8],
    },
    {"type": "h1", "text": "9. Kesimpulan"},
    {
        "type": "p",
        "text": "Conversion server dua arah berhasil direplikasi pada jaringan IP konvensional dengan "
                "enam peran logis. ID, timestamp, dan payload terverifikasi tetap terjaga. Seluruh "
                "40 run valid, harness menghasilkan data mentah, ringkasan, dan grafik, serta laporan "
                "dan slide tersedia dalam batas halaman yang diminta. Pendekatan ini layak dipakai "
                "sebagai dasar percobaan lanjutan pada jaringan yang lebih kompleks.",
    },
    {"type": "h1", "text": "10. Daftar Pustaka dan Lampiran"},
    {
        "type": "bullets",
        "items": [
            "F. D. S. Sumadi dkk., \"Enabling seamless communication over several IoT messaging protocols in OpenFlow network,\" TELKOMNIKA 19(5), 1544&#8211;1552, 2021, [doi:10.12928/TELKOMNIKA.v19i5.20412](https://doi.org/10.12928/TELKOMNIKA.v19i5.20412).",
            "Coulouris dkk., <i>Distributed Systems: Concepts and Design</i>, edisi ke-5, Addison-Wesley.",
            "Materi Sistem Terdistribusi 8&#8211;9, Universitas Muhammadiyah Malang, 2026.",
            "RFC 7252 (CoAP) dan RFC 7959 (blockwise transfer).",
        ],
    },
    {
        "type": "p",
        "text": "Lampiran: kode dan konfigurasi di [repositori GitHub](https://github.com/bangdhidotcom/"
                "sistem-terdistribusi-mqtt-coap); data mentah <b>data/raw/messages.csv</b>; ringkasan "
                "<b>data/summary/summary.csv</b>; grafik <b>data/grafik/</b>; diagram editabel "
                "<b>output-xml/</b> dan <b>laporan/Diagram_Editabel_Word.docx</b>; slide "
                "<b>slide/Slide_Presentasi.pptx</b>; panduan <b>panduan/</b>.",
    },
]
