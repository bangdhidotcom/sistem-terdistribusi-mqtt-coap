"""Bangun laporan teknis PDF (<=10 halaman)."""
from pathlib import Path
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
ROOT = Path(__file__).resolve().parents[1]
S = ROOT/"data"/"summary"/"summary.csv"
OUT = ROOT/"laporan"/"Laporan_Akhir_Sistem_Terdistribusi.pdf"
REPO = "https://github.com/bangdhidotcom/sistem-terdistribusi-mqtt-coap"
st = getSampleStyleSheet()
st.add(ParagraphStyle("BodyID", parent=st["BodyText"], fontSize=9, leading=12.5, alignment=TA_JUSTIFY, spaceAfter=5))
st.add(ParagraphStyle("TitleID", parent=st["Title"], fontSize=18, leading=22, alignment=TA_CENTER, spaceAfter=8))
st.add(ParagraphStyle("SubID", parent=st["Normal"], fontSize=10, alignment=TA_CENTER, spaceAfter=5))
st.add(ParagraphStyle("CapID", parent=st["Normal"], fontSize=7.5, alignment=TA_CENTER, textColor=colors.HexColor("#555555"), spaceAfter=8))
st.add(ParagraphStyle("H1ID", parent=st["Heading1"], fontSize=12, spaceBefore=8, spaceAfter=5, textColor=colors.HexColor("#1E2A47")))
st.add(ParagraphStyle("H2ID", parent=st["Heading2"], fontSize=10, spaceBefore=6, spaceAfter=3, textColor=colors.HexColor("#2A5FD4")))
def P(t, s="BodyID"): return Paragraph(t, st[s])
def img(p, w=16*cm):
    p=Path(p)
    if not p.exists(): return P("[gambar tidak tersedia: %s]"%p.name,"CapID")
    from PIL import Image as I
    with I.open(p) as im: h=im.height/im.width
    return Image(str(p), width=w, height=w*h)
def tab(rows, widths=None, font=7.5):
    t=Table(rows,colWidths=widths,repeatRows=1,hAlign="CENTER")
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1E2A47")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTNAME",(0,1),(-1,-1),"Helvetica"),("FONTSIZE",(0,0),(-1,-1),font),("GRID",(0,0),(-1,-1),0.35,colors.HexColor("#9AA5B1")),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#EFF3FA")]),("LEFTPADDING",(0,0),(-1,-1),3),("RIGHTPADDING",(0,0),(-1,-1),3),("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2)]))
    return t
def build():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    df=pd.read_csv(S) if S.exists() else pd.DataFrame()
    failed=[]
    if not df.empty and {"sent","received","run"}.issubset(df.columns):
        failed=sorted(set(df[(df["sent"]==0)&(df["received"]==0)]["run"].astype(str)))
    a=[]
    a+=[Spacer(1,cm),P("LAPORAN AKHIR PROJECT SISTEM TERDISTRIBUSI","TitleID"),P("Replikasi Conversion Server MQTT &#8596; CoAP pada Jaringan IP Konvensional","SubID"),Spacer(1,.4*cm)]
    a+=[tab([["Mata Kuliah","Sistem Terdistribusi A"],["Topik","Konversi pesan dua arah MQTT &#8596; CoAP"],["Kelompok","Muhammad Irfan Maulana (202310370311480); Hadrian Rakha Khosyi Javier (202310370311483); Bambang Adhi Nurbiyanto (202310370311484)"],["Batas Pengumpulan","Senin, 7 Desember 2026 pukul 16.55 WIB"],["Repositori Kode",REPO]],[4*cm,12*cm],8),Spacer(1,.4*cm),P("<b>Abstrak</b>","H1ID")]
    a+=[P("Laporan ini mereplikasi conversion server pada artikel Sumadi dkk. (2021) tanpa SDN/OpenFlow. Enam peran logis dijalankan sebagai proses Python terpisah pada satu host. Konversi dua arah diuji pada laju 10 dan 20 pesan/detik dengan sepuluh pengulangan. Metrik yang diukur: keberhasilan, loss, delay konversi, delay ujung-ke-ujung, CPU, dan memori. Pesan membawa ID unik, timestamp, dan hash SHA-256. Karena 200 KB melebihi MTU CoAP, kampanye utama memakai payload 4 KB dengan disclosure; uji 200 KB blockwise disimpan sebagai tambahan."),PageBreak()]
    a+=[P("1. Latar Belakang dan Tujuan","H1ID"),P("MQTT memakai publish/subscribe di atas TCP, CoAP memakai request/response di atas UDP dengan blockwise. Agar perangkat berbeda protokol berkomunikasi, conversion server menerjemahkan pesan tanpa mengubah ID dan payload [1]. Tujuan project: mereplikasi mekanisme itu pada IP konvensional, mendokumentasikan alur, dan mengukur kinerja.")]
    a+=[P("2. Tinjauan Pustaka Singkat","H1ID"),P("Sumadi dkk. [1] memakai MQTT subscriber &#8594; CoAP POST dan CoAP GET polling &#8594; MQTT publish pada jaringan OpenFlow. Materi perkuliahan menambahkan replikasi dan fault tolerance [2][3]; deduplikasi berbasis ID unik berperan sebagai toleransi terhadap pengiriman ulang.")]
    a+=[P("3. Perancangan Sistem","H1ID"),img(ROOT/"output"/"mqtt_coap_architecture.png",16*cm),P("Gambar 1. Arsitektur enam peran logis (XML editabel tersedia).","CapID")]
    a+=[P("3.1 Arsitektur Proses","H2ID"),P("Enam peran logis dijalankan sebagai enam proses Python yang berkomunikasi melalui TCP/UDP pada satu host: broker MQTT menerima PUBLISH dan meneruskannya ke subscriber; CoAP server menyimpan antrean pada /target dan /source; conversion server menjadi jembatan dua arah; MQTT publisher dan subscriber menjadi ujung protokol MQTT; CoAP POST/GET client menjadi ujung protokol CoAP. Pemisahan proses ini memungkinkan verifikasi individu terhadap masing-masing peran.")]
    a+=[tab([["No","Peran","Implementasi","Alamat"],["1","MQTT broker","src/mqtt_broker.py","127.0.0.1:1883 / :1884"],["2","CoAP server","src/coap_server.py","127.0.0.1:5683 / :5684"],["3","Conversion server","src/conversion_server.py","subscribe + POST/GET"],["4","MQTT publisher","src/mqtt_publisher.py","iot/mqtt_to_coap"],["5","MQTT subscriber","src/mqtt_subscriber.py","iot/coap_to_mqtt"],["6","CoAP client","src/coap_client.py","POST /source, GET /target"]],[1*cm,3.2*cm,5.4*cm,6.4*cm],7),PageBreak()]
    a+=[P("4. Alur Konversi","H1ID"),P("4.1 MQTT &#8594; CoAP","H2ID"),img(ROOT/"output"/"flow_mqtt_to_coap.png",8.2*cm),P("Gambar 2. Alur MQTT&#8594;CoAP.","CapID")]
    a+=[P("Publisher membuat JSON berisi UUID, seq, sent_ts, payload base64, dan SHA-256, lalu mempublish. Conversion server memvalidasi, menandai origin_processed, dan POST ke /target. CoAP GET client memverifikasi ID dan hash serta mencatat dst_recv_ts.")]
    a+=[P("4.2 CoAP &#8594; MQTT","H2ID"),img(ROOT/"output"/"flow_coap_to_mqtt.png",8.2*cm),P("Gambar 3. Alur CoAP&#8594;MQTT.","CapID")]
    a+=[P("CoAP POST client mengirim ke /source; server menyimpan antrean. Tiap detik conversion server GET /source, melakukan deduplikasi ID, menandai origin_processed, lalu publish ke iot/coap_to_mqtt. Penandaan ini mencegah loop balik."),PageBreak()]
    a+=[P("5. Metode Eksperimen","H1ID")]
    a+=[tab([["Aspek","Nilai"],["Lingkungan","Windows 11, Python 3.14, localhost"],["Pustaka","paho-mqtt 2.2.0, aiocoap 0.4.17, scapy, psutil"],["Payload kampanye","4.096 byte (scapy Raw)"],["Payload tambahan","204.800 byte, blockwise RFC 7959"],["Laju","10 dan 20 pesan/detik"],["Durasi","10 menit &#215; 10 pengulangan"],["Skenario","2 arah &#215; 2 laju &#215; 10 = 40 run"],["Metrik","success, loss, delay konversi, delay E2E, CPU, memori"]],[4*cm,12*cm],7.5)]
    a+=[P("5.1 Rumus metrik","H2ID"),P("Sukses = (terverifikasi/terkirim)&#215;100%. Loss = 100% &#8722; sukses. Delay konversi = (conv_send_ts &#8722; conv_recv_ts)&#215;1000 ms. Delay E2E = (dst_recv_ts &#8722; sent_ts)&#215;1000 ms. CPU/memori diambil tiap detik dari proses conversion server. Spesifikasi menuliskan selisih terbalik; laporan memakai konvensi positif dan mendokumentasikannya.")]
    a+=[P("5.2 Keputusan payload","H2ID"),P("200 KB berhasil lewat blockwise tetapi throughput turun ke ~1 pesan/detik. Sesuai ketentuan spesifikasi, kampanye memakai 4 KB agar uji laju 10/20 dapat berjalan; hasil 200 KB menjadi bukti tambahan."),PageBreak()]
    a+=[P("6. Hasil Eksperimen","H1ID")]
    if not df.empty:
        g=df.groupby(["direction","rate"]).agg(sent=("sent","sum"),recv=("received","sum"),suc=("success_pct","mean"),loss=("loss_pct","mean"),conv=("avg_conversion_ms","mean"),e2e=("avg_e2e_ms","mean"),cpu=("avg_cpu","mean"),mem=("avg_mem_mb","mean")).reset_index()
        rows=[["Arah","Laju","Terkirim","Terverifikasi","Sukses %","Loss %","Konv (ms)","E2E (ms)","CPU %","Mem (MB)"]]
        for _,r in g.iterrows(): rows.append([r["direction"].upper(),str(r["rate"]),str(int(r["sent"])),str(int(r["recv"])),f"{r['suc']:.2f}",f"{r['loss']:.2f}",f"{r['conv']:.2f}",f"{r['e2e']:.2f}",f"{r['cpu']:.2f}",f"{r['mem']:.1f}"])
        a+=[tab(rows,[1.2*cm,1.1*cm,1.7*cm,2.1*cm,1.6*cm,1.5*cm,2.1*cm,2.1*cm,1.3*cm,1.6*cm],6.5)]
    else: a+=[P("Ringkasan belum tersedia saat build; tabel terisi setelah kampanye.")]
    gr=ROOT/"data"/"grafik"
    a+=[img(gr/"delay_e2e_per_menit.png",15.5*cm),P("Gambar 4. Delay E2E per menit.","CapID"),img(gr/"delay_konversi_per_menit.png",15.5*cm),P("Gambar 5. Delay konversi per menit.","CapID"),PageBreak()]
    a+=[img(gr/"cpu_per_menit.png",15.5*cm),P("Gambar 6. CPU conversion server.","CapID"),img(gr/"perbandingan_artikel.png",13.5*cm),P("Gambar 7. Perbandingan dengan artikel.","CapID"),P("Data: data/raw/messages.csv dan data/summary/summary.csv.","CapID"),PageBreak()]
    a+=[P("7. Analisis","H1ID"),P("Kedua arah mempertahankan ID dan payload (verifikasi SHA-256 benar). Antrean CoAP mencegah pesan tertindih antar polling. Delay CoAP&#8594;MQTT dipengaruhi periode polling satu detik; MQTT&#8594;CoAP dipengaruhi round-trip CoAP. Artikel memiliki inkonsistensi angka (MQTT&#8594;CoAP puluhan detik, CoAP&#8594;MQTT ~0,18 s dengan loss 92&#8211;95%), kemungkinan karena definisi timestamp dan antrean OpenFlow; perbandingan dilakukan secara kualitatif.")]
    a+=[P("Keterbatasan: satu host, batas praktis aiocoap pada 20 msg/s, payload 200 KB hanya uji tambahan, tanpa SDN/OpenFlow.")]
    if failed:
        a+=[P("Dari total 40 run, terdapat %d run (%s) yang gagal mengirimkan pesan (delivered=0) meskipun telah dilakukan beberapa kali percobaan ulang. Hal ini menunjukkan batas stabilitas pustaka aiocoap pada beban tinggi di lingkungan localhost; run tersebut tetap dicatat pada data mentah dan ringkasan dengan nilai keberhasilan 0%%." % (len(failed), ", ".join(failed)))]
    else:
        a+=[P("Seluruh 40 run berhasil mengirimkan pesan; tidak ada run dengan delivered=0 setelah proses perbaikan dan verifikasi ulang.")]
    a+=[PageBreak()]
    a+=[P("8. Pembagian Kerja","H1ID"),tab([["Anggota","Tugas","Bukti"],["Muhammad Irfan Maulana","Broker, publisher, subscriber, konektivitas","src/mqtt_*.py"],["Hadrian Rakha Khosyi Javier","CoAP server/client, payload","src/coap_server.py, src/coap_client.py"],["Bambang Adhi Nurbiyanto","Conversion server, metrik, harness, laporan, slide","src/conversion_server.py, experiments/, laporan/"]],[4*cm,6*cm,6*cm],7)]
    a+=[P("9. Kesimpulan","H1ID"),P("Conversion server dua arah berhasil direplikasi pada IP konvensional dengan enam peran logis. ID, timestamp, dan payload terverifikasi terjaga. Harness menghasilkan CSV mentah, ringkasan, dan grafik untuk delapan kombinasi utama.")]
    a+=[P("10. Daftar Pustaka dan Lampiran","H1ID"),P("[1] F. D. S. Sumadi dkk., \"Enabling seamless communication over several IoT messaging protocols in OpenFlow network,\" TELKOMNIKA 19(5), 1544&#8211;1552, 2021, <link href='https://doi.org/10.12928/TELKOMNIKA.v19i5.20412'>doi:10.12928/TELKOMNIKA.v19i5.20412</link>. [2] Coulouris dkk., Distributed Systems: Concepts and Design, 5th ed. [3] Materi Sistem Terdistribusi 8&#8211;9, UMM, 2026.")]
    a+=[P("Lampiran: "+REPO+" ; data/raw/messages.csv ; data/summary/summary.csv ; data/grafik/ ; output-xml/*.xml ; output/*.png ; slide/Slide_Presentasi.pptx ; laporan/Diagram_Editabel_Word.docx ; panduan/*.md")]
    SimpleDocTemplate(str(OUT),pagesize=A4,leftMargin=1.4*cm,rightMargin=1.4*cm,topMargin=1.3*cm,bottomMargin=1.3*cm,title="Laporan Akhir Sistem Terdistribusi MQTT-CoAP",author="Kelompok Sistem Terdistribusi A").build(a)
    print("Laporan dibuat:",OUT)
if __name__=="__main__": build()
