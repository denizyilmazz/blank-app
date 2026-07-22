import streamlit as st
import datetime
import sqlite3
import pandas as pd
import random
import matplotlib.pyplot as plt

# Sayfa Yapılandırması
st.set_page_config(page_title="YKS Profesyonel Koçluk Platformu", page_icon="🎓", layout="wide")

# Custom CSS ile Sekmeleri Belirginleştirme
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 8px 8px 0px 0px;
        padding-top: 8px;
        padding-bottom: 8px;
        padding-left: 16px;
        padding-right: 16px;
        font-weight: bold;
        font-size: 15px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ff4b4b !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

conn = sqlite3.connect("yks_kocluk.db", check_same_thread=False)
cursor = conn.cursor()

def veritabani_hazirla_ve_onar():
    # Tablo 1: Öğrenci Bilgileri
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ogrenciler (
        ad_soyad TEXT PRIMARY KEY,
        sifre TEXT
    )
    """)

    # Tablo 2: Günlük Çalışma
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS gunluk_calisma (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ad_soyad TEXT,
        tarih TEXT,
        ders TEXT,
        konu TEXT,
        toplam_soru INTEGER,
        dogru INTEGER,
        yanlis INTEGER,
        bos INTEGER,
        sure FLOAT,
        verim INTEGER,
        notlar TEXT
    )
    """)

    # Sütun Kontrolü ve Otomatik Onarım
    cursor.execute("PRAGMA table_info(gunluk_calisma)")
    mevcut_sutunlar = [row[1] for row in cursor.fetchall()]
    gerekli_sutunlar = {
        "konu": "TEXT",
        "toplam_soru": "INTEGER",
        "dogru": "INTEGER",
        "yanlis": "INTEGER",
        "bos": "INTEGER",
        "sure": "FLOAT",
        "verim": "INTEGER",
        "notlar": "TEXT"
    }
    for sutun_adi, sutun_tipi in gerekli_sutunlar.items():
        if sutun_adi not in mevcut_sutunlar:
            try:
                cursor.execute(f"ALTER TABLE gunluk_calisma ADD COLUMN {sutun_adi} {sutun_tipi}")
                conn.commit()
            except Exception:
                pass
    conn.commit()

veritabani_hazirla_ve_onar()

# Tablo 3: Denemeler
cursor.execute("""
CREATE TABLE IF NOT EXISTS denemeler (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_soyad TEXT,
    tarih TEXT,
    yayin TEXT,
    tur TEXT,
    toplam_net FLOAT,
    dosya_adi TEXT
)
""")

# Tablo 4: Konu Puanları
cursor.execute("""
CREATE TABLE IF NOT EXISTS konu_puanlari (
    ad_soyad TEXT,
    konu_adi TEXT,
    puan INTEGER,
    PRIMARY KEY (ad_soyad, konu_adi)
)
""")
conn.commit()

KOC_SIFRE = "1234"

MOTIVASYON_SOZLERI = [
    "🔥 Gelecek, bugün ne yaptığına bağlıdır! İnan ve devam et.",
    "🚀 Başarı, her gün tekrarlanan küçük çabaların toplamıdır!",
    "🎓 Bugün atacağın her adım, hayalindeki üniversiteye bir yaklaşmadır!",
    "💪 Zorluklar, başarının değerini artıran süslerdir. Pes etmek yok!",
    "✨ Şimdi çalış, gelecekteki kendin seninle gurur duysun!",
    "🎯 Hedefine giden yolda engel yoktur, sadece aşılacak basamaklar vardır!"
]

YKS_KONULAR = {
    "📖 Türkçe": [
        "Sözcükte Anlam", "Cümlede Anlam", "Paragraf", "Yazım Kuralları", 
        "Noktalama İşaretleri", "Dil Bilgisi", "Metin Türleri"
    ],
    "📜 Tarih": [
        "Tarih Bilimine Giriş", "İlk Çağ Uygarlıkları", "İslam Öncesi Türk Tarihi", 
        "İslam Tarihi ve Uygarlığı", "Türk İslam Devletleri", "Osmanlı Devleti Kuruluş & Yükselme", 
        "Osmanlı Kültür ve Medeniyeti", "20. Yüzyıl Başlarında Osmanlı", "Milli Mücadele & İnkılap Tarihi", 
        "Atatürkçülük ve İlkeler"
    ],
    "🌍 Coğrafya": [
        "Doğa ve İnsan", "Dünya'nın Şekli ve Hareketleri", "Coğrafi Konum & Harita Bilgisi", 
        "İklim Bilgisi & İklim Tipleri", "Yerin Şekillenmesi (İç ve Dış Kuvvetler)", "Türkiye'nin Yerşekilleri", 
        "Beşeri Sistemler & Nüfus", "Afetler ve Çevre"
    ],
    "🧠 Felsefe": [
        "Felsefeyi Tanıma", "Felsefi Düşünce & Sorgulama", "Bilgi Felsefesi (Epistemoloji)", 
        "Varlık Felsefesi (Ontoloji)", "Ahlak Felsefesi (Etik)", "Sanat Felsefesi", 
        "Siyaset Felsefesi", "Din Felsefesi", "Bilim Felsefesi"
    ],
    "🕌 Din Kültürü": [
        "İnanç & Allah İnancı", "İbadet ve Esasları", "Ahlak ve Değerler", 
        "Hz. Muhammed (S.A.V.) ve Gençlik", "Vahiy ve Akıl", "İslam ve Bilim", "Dünya Dinleri"
    ],
    "📐 Matematik": [
        "Temel Kavramlar", "Sayı Basamakları", "Bölme - Bölünebilme", "EBOB - EKOK", 
        "Rasyonel Sayılar", "Basit Eşitsizlikler", "Mutlak Değer", "Üslü & Köklü İfadeler", 
        "Çarpanlara Ayırma", "Oran - Orantı", "Problemler (Sayı, Kesir, Yaş, Yüzde, Hız)", 
        "Fonksiyonlar", "2. Dereceden Denklemler", "Polinomlar", "Permütasyon - Kombinasyon - Olasılık", 
        "Logaritma", "Diziler", "Trigonometri", "Limit & Süreklilik", "Türev", "İntegral"
    ],
    "📏 Geometri": [
        "Doğruda ve Üçgende Açılar", "Özel Üçgenler", "Üçgende Alan & Benzerlik", 
        "Çokgenler & Dörtgenler", "Çember ve Daire", "Analitik Geometri", "Katı Cisimler"
    ],
    "⚡ Fizik": [
        "Fizik Bilimine Giriş", "Madde ve Özellikleri", "Kuvvet ve Hareket", "İş, Güç, Enerji", 
        "Isı ve Sıcaklık", "Basınç ve Kaldırma Kuvveti", "Elektrostatik & Elektrik", "Optik", 
        "Dalgalar", "Atışlar & Tork", "Çembersel Hareket", "Harmonik Hareket", "Modern Fizik"
    ],
    "🧪 Kimya": [
        "Kimya Bilimi & Atom", "Periyodik Sistem", "Türler Arası Etkileşimler", "Maddenin Halleri", 
        "Mol Kavramı & Tepkimeler", "Karışımlar", "Asit, Baz, Tuz", "Gazlar", "Çözeltiler", 
        "Enerji, Hız ve Denge", "Elektrokimya", "Organik Kimya"
    ],
    "🧬 Biyoloji": [
        "Yaşam Bilimi Biyoloji", "Hücre ve Organeller", "Hücre Bölünmeleri", "Kalıtım", 
        "Ekoloji", "İnsan Fizyologisı (Sistemler)", "Gensa Bilgi & Protein Sentezi", 
        "Fotosentez & Solunum", "Bitki Biyolojisi"
    ]
}

DERSLER = list(YKS_KONULAR.keys())

st.sidebar.title("🎓 YKS Koçluk Sistemi")
giris_turu = st.sidebar.radio("Giriş Paneli Seçin:", ["👨‍🎓 ÖĞRENCİ GİRİŞİ", "👨‍🏫 KOÇ GİRİŞİ"])

if giris_turu == "👨‍🎓 ÖĞRENCİ GİRİŞİ":
    st.title("👨‍🎓 Öğrenci Yönetim Paneli")
    
    tab_giris, tab_gunluk, tab_deneme, tab_konular, tab_analiz = st.tabs([
        "🔑 GİRİŞ / KAYIT",
        "📝 GÜNLÜK DERS VE SORU TAKİBİ",
        "📊 DENEME SONUÇLARI VE KARNE YÜKLEME",
        "🗺️ DERS DERS KONU DERECELENDİRME",
        "📈 BAŞARI ANALİZİ & GRAFİKLER"
    ])
    
    with tab_giris:
        st.subheader("Öğrenci Hesabı Girişi / Kaydı")
        col1, col2 = st.columns(2)
        with col1:
            ad_soyad = st.text_input("Adınız ve Soyadınız:").strip().title()
        with col2:
            sifre = st.text_input("Şifreniz / PIN:", type="password")
            
        if st.button("Giriş Yap / Hesabı Oluştur", type="primary"):
            if ad_soyad and sifre:
                cursor.execute("SELECT sifre FROM ogrenciler WHERE ad_soyad = ?", (ad_soyad,))
                user = cursor.fetchone()
                if user is None:
                    cursor.execute("INSERT INTO ogrenciler (ad_soyad, sifre) VALUES (?, ?)", (ad_soyad, sifre))
                    conn.commit()
                    st.success(f"Hoş geldin {ad_soyad}! Profilin başarıyla oluşturuldu.")
                    st.session_state["aktif_ogrenci"] = ad_soyad
                else:
                    if user[0] == sifre:
                        st.success(f"Başarıyla giriş yapıldı! Hoş geldin {ad_soyad}.")
                        st.session_state["aktif_ogrenci"] = ad_soyad
                    else:
                        st.error("Hatalı şifre! Lütfen şifrenizi kontrol edin.")
            else:
                st.warning("Lütfen ad, soyad ve şifrenizi eksiksiz giriniz.")
                
    aktif_ogr = st.session_state.get("aktif_ogrenci", None)
    
    if not aktif_ogr:
        st.info("⚠️ İşlem yapmak için lütfen önce 'GİRİŞ / KAYIT' sekmesinden hesabınıza giriş yapın.")
    else:
        # Rastgele Motivasyon Kartı
        rastgele_soz = random.choice(MOTIVASYON_SOZLERI)
        st.info(f"💡 **Günün Motivasyon Sözü:** *\"{rastgele_soz}\"*")

        # GÜNLÜK DERS & KONU BAZLI SORU GİRİŞİ
        with tab_gunluk:
            st.subheader(f"📝 Günlük Çalışma Girişi - Öğrenci: {aktif_ogr}")
            tarih_giris = st.date_input("Çalışma Tarihi", datetime.date.today())
            sure_giris = st.number_input("Bugünkü Toplam Çalışma Süresi (Saat)", 0.0, 16.0, 7.5, 0.5)
            verim_giris = st.slider("Günün Verim Puanı (1-10)", 1, 10, 8)
            not_giris = st.text_area("Bugün zorlandığın detaylar / Koçuna iletmek istediğin not:")
            
            st.write("---")
            st.write("### 📚 Ders ve Konu Bazlı Soru Analizi Girişi")
            
            ders_sekmeleri = st.tabs(DERSLER)
            ders_verileri = {}

            for idx, ders_adi in enumerate(DERSLER):
                with ders_sekmeleri[idx]:
                    st.markdown(f"#### {ders_adi} Çalışma Detayları")
                    
                    secilen_konu = st.selectbox(
                        f"Çalıştığınız Konuyu Seçin ({ders_adi}):",
                        options=["Genel Soru Çözümü / Karma"] + YKS_KONULAR[ders_adi],
                        key=f"konu_select_{ders_adi}"
                    )
                    
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        toplam_s = st.number_input(f"Toplam Soru ({ders_adi})", 0, 500, 0, key=f"top_{ders_adi}")
                    with c2:
                        dogru_s = st.number_input(f"Doğru ({ders_adi})", 0, 500, 0, key=f"dog_{ders_adi}")
                    with c3:
                        yanlis_s = st.number_input(f"Yanlış ({ders_adi})", 0, 500, 0, key=f"yan_{ders_adi}")
                    with c4:
                        bos_s = st.number_input(f"Boş ({ders_adi})", 0, 500, 0, key=f"bos_{ders_adi}")
                        
                    if dogru_s + yanlis_s + bos_s > toplam_s:
                        st.error(f"⚠️ {ders_adi}: Doğru + Yanlış + Boş sayısı Toplam Soru sayısından fazla olamaz!")
                    
                    ders_verileri[ders_adi] = (secilen_konu, toplam_s, dogru_s, yanlis_s, bos_s)

            if st.button("🚀 Tüm Ders ve Konu Çalışmalarını Kaydet", type="primary"):
                kaydedilen_ders_sayisi = 0
                for d_adi, (k_adi, t_s, d_s, y_s, b_s) in ders_verileri.items():
                    if t_s > 0:
                        try:
                            # Aynı gün, ders ve konu için daha önce girilmiş kayıt varsa sil
                            cursor.execute("DELETE FROM gunluk_calisma WHERE ad_soyad = ? AND tarih = ? AND ders = ? AND konu = ?", (aktif_ogr, str(tarih_giris), d_adi, k_adi))
                            cursor.execute("""
                            INSERT INTO gunluk_calisma (ad_soyad, tarih, ders, konu, toplam_soru, dogru, yanlis, bos, sure, verim, notlar)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (aktif_ogr, str(tarih_giris), d_adi, k_adi, t_s, d_s, y_s, b_s, float(sure_giris), int(verim_giris), not_giris))
                            conn.commit()
                            kaydedilen_ders_sayisi += 1
                        except sqlite3.OperationalError:
                            conn.rollback()
                            veritabani_hazirla_ve_onar()
                            cursor.execute("DELETE FROM gunluk_calisma WHERE ad_soyad = ? AND tarih = ? AND ders = ? AND konu = ?", (aktif_ogr, str(tarih_giris), d_adi, k_adi))
                            cursor.execute("""
                            INSERT INTO gunluk_calisma (ad_soyad, tarih, ders, konu, toplam_soru, dogru, yanlis, bos, sure, verim, notlar)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (aktif_ogr, str(tarih_giris), d_adi, k_adi, t_s, d_s, y_s, b_s, float(sure_giris), int(verim_giris), not_giris))
                            conn.commit()
                            kaydedilen_ders_sayisi += 1
                if kaydedilen_ders_sayisi > 0:
                    st.balloons()
                    st.success("🎉 TEBRİKLER HEDEFİNE 1 ADIM DAHA YAKLAŞTIN! 🙌")
                    st.toast("Çalışmaların başarıyla kaydedildi! Harika gidiyorsun.", icon="🚀")
                else:
                    st.warning("Lütfen kaydetmeden önce en az bir dersten çözdüğünüz soru sayısını giriniz (0'dan büyük).")

        # DENEME & KARNE SEKMESİ
        with tab_deneme:
            st.subheader("📊 Deneme Sonuçları & Karne Yükleme")
            yayin = st.text_input("Deneme Adı / Yayın:")
            d_tur = st.selectbox("Deneme Türü:", ["TYT Denemesi", "AYT Sayısal Denemesi", "Branş Denemesi"])
            toplam_net = st.number_input("Toplam Netiniz:", 0.0, 160.0, 85.0)
            karne_dosya = st.file_uploader("📄 Deneme Karnesi / Fotoğrafı Yükle:", type=["pdf", "png", "jpg", "jpeg"])
            
            if st.button("Deneme Karnesini Kaydet"):
                dosya_adi = karne_dosya.name if karne_dosya else "Dosya Yüklenmedi"
                cursor.execute("""
                INSERT INTO denemeler (ad_soyad, tarih, yayin, tur, toplam_net, dosya_adi)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (aktif_ogr, str(datetime.date.today()), yayin, d_tur, toplam_net, dosya_adi))
                conn.commit()
                st.balloons()
                st.success("🎉 TEBRİKLER HEDEFİNE 1 ADIM DAHA YAKLAŞTIN! 🙌 Deneme başarın veritabanına eklendi.")

        # KONU DERECELENDİRME SEKMESİ
        with tab_konular:
            st.subheader("🗺️ Ders Ders Konu Hakimiyet Puanlaması (1 - 5)")
            konu_sekmeleri = st.tabs(list(YKS_KONULAR.keys()))
            
            for idx, (d_adi, k_list) in enumerate(YKS_KONULAR.items()):
                with konu_sekmeleri[idx]:
                    for kn in k_list:
                        cursor.execute("SELECT puan FROM konu_puanlari WHERE ad_soyad = ? AND konu_adi = ?", (aktif_ogr, kn))
                        res = cursor.fetchone()
                        mevcut_puan = res[0] if res else 3
                        
                        yeni_p = st.select_slider(
                            f"**{kn}**",
                            options=[1, 2, 3, 4, 5],
                            value=mevcut_puan,
                            format_func=lambda x: {1: "1 - Çok Zayıf 🔴", 2: "2 - Eksik Var 🟠", 3: "3 - Orta 🟡", 4: "4 - İyi 🟢", 5: "5 - Tam Usta 🔵"}[x],
                            key=f"{aktif_ogr}_{kn}"
                        )
                        cursor.execute("""
                        INSERT INTO konu_puanlari (ad_soyad, konu_adi, puan) VALUES (?, ?, ?)
                        ON CONFLICT(ad_soyad, konu_adi) DO UPDATE SET puan = ?
                        """, (aktif_ogr, kn, yeni_p, yeni_p))
                    conn.commit()
            st.success("Konu puanlamalarınız başarıyla güncellendi.")

        # BAŞARI ANALİZİ SEKMESİ (DAİRESEL GRAFİKLER)
        with tab_analiz:
            st.subheader(f"📈 Genel Başarı ve Soru Dağılım Analizi - {aktif_ogr}")
            
            df_analiz = pd.read_sql_query(
                "SELECT ders, SUM(toplam_soru) as toplam, SUM(dogru) as d, SUM(yanlis) as y, SUM(bos) as b FROM gunluk_calisma WHERE ad_soyad = ? GROUP BY ders",
                conn, params=(aktif_ogr,)
            )
            
            if df_analiz.empty or df_analiz["toplam"].sum() == 0:
                st.info("📊 Grafiksel analizinizin oluşması için lütfen 'Günlük Ders ve Soru Takibi' sekmesinden soru çözümlerinizi kaydedin.")
            else:
                col_g1, col_g2 = st.columns(2)
                
                # Grafik 1: Derslere Göre Çözülen Soru Dağılımı (Dairesel Pasta Grafiği)
                with col_g1:
                    st.markdown("#### 🍩 Derslere Göre Çözülen Soru Dağılımı")
                    fig1, ax1 = plt.subplots(figsize=(6, 6))
                    df_filtr = df_analiz[df_analiz["toplam"] > 0]
                    
                    # Pasta dilimlerini oluştur
                    wedges, texts, autotexts = ax1.pie(
                        df_filtr["toplam"], 
                        labels=df_filtr["ders"], 
                        autopct='%1.1f%%',
                        startangle=140,
                        wedgeprops=dict(width=0.4, edgecolor='w') # Halka grafik stili
                    )
                    plt.setp(autotexts, size=9, weight="bold", color="white")
                    plt.setp(texts, size=10)
                    ax1.axis('equal')
                    st.pyplot(fig1)

                # Grafik 2: Toplam Doğru, Yanlış, Boş Oranı (Dairesel Halka Grafiği)
                with col_g2:
                    st.markdown("#### 🎯 Toplam Doğru / Yanlış / Boş Isı Dağılımı")
                    top_d = df_analiz["d"].sum()
                    top_y = df_analiz["y"].sum()
                    top_b = df_analiz["b"].sum()
                    
                    fig2, ax2 = plt.subplots(figsize=(6, 6))
                    labels = ['Doğru 🟢', 'Yanlış 🔴', 'Boş 🟡']
                    values = [top_d, top_y, top_b]
                    colors = ['#2ecc71', '#e74c3c', '#f1c40f']
                    
                    wedges, texts, autotexts = ax2.pie(
                        values, 
                        labels=labels, 
                        autopct='%1.1f%%',
                        colors=colors,
                        startangle=90,
                        wedgeprops=dict(width=0.4, edgecolor='w')
                    )
                    plt.setp(autotexts, size=10, weight="bold", color="white")
                    plt.setp(texts, size=11)
                    ax2.axis('equal')
                    st.pyplot(fig2)

                st.write("---")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Toplam Çözülen Soru", f"{df_analiz['toplam'].sum()} Adet")
                m2.metric("Toplam Doğru", f"{top_d} Adet")
                m3.metric("Toplam Yanlış", f"{top_y} Adet")
                m4.metric("Toplam Boş", f"{top_b} Adet")

else:
    st.title("👨‍🏫 Koç Yönetim ve Analiz Paneli")
    koc_sifre_giris = st.sidebar.text_input("Koç Şifresi:", type="password")
    
    if koc_sifre_giris != KOC_SIFRE:
        st.warning("🔒 Koç paneline erişmek için sol menüden koç şifrenizi girin. (Varsayılan: 1234)")
    else:
        st.success("🔓 Koç Yetkisi Doğrulandı.")
        
        cursor.execute("SELECT ad_soyad FROM ogrenciler")
        ogrenciler = [row[0] for row in cursor.fetchall()]
        
        if not ogrenciler:
            st.info("Sisteme henüz kayıtlı öğrenci bulunmuyor.")
        else:
            secilen_ogr = st.selectbox("🔍 İncelemek İstediğiniz Öğrenciyi Seçin:", ogrenciler)
            
            st.divider()
            st.header(f"📊 Öğrenci Analiz Raporu: {secilen_ogr}")
            
            # Günlük Ders & Konu Dağılımı Tablosu
            st.subheader("📚 Ders & Konu Bazlı Soru, Doğru, Yanlış, Boş Dağılımı")
            df_gunluk = pd.read_sql_query("SELECT id, tarih, ders, konu, toplam_soru, dogru, yanlis, bos, sure, verim, notlar FROM gunluk_calisma WHERE ad_soyad = ?", conn, params=(secilen_ogr,))
            
            if not df_gunluk.empty:
                st.dataframe(df_gunluk, use_container_width=True)
                
                # Hatalı/Çift Girilen Kayıtları Silme Alanı
                with st.expander("🗑️ Hatalı veya Çift Girilmiş Kayıtları Sil"):
                    silinecek_id = st.selectbox("Silmek istediğiniz satırın ID numarasını seçin:", options=df_gunluk["id"].tolist())
                    if st.button("❌ Seçilen Kaydı Sil", type="primary"):
                        cursor.execute("DELETE FROM gunluk_calisma WHERE id = ?", (silinecek_id,))
                        conn.commit()
                        st.success(f"ID: {silinecek_id} olan kayıt başarıyla silindi!")
                        st.rerun()
            else:
                st.info("Bu öğrenci henüz günlük ders ve konu soru verisi girmedi.")
                
            # Denemeler
            st.subheader("📑 Kayıtlı Denemeler ve Karneler")
            df_deneme = pd.read_sql_query("SELECT tarih, yayin, tur, toplam_net, dosya_adi FROM denemeler WHERE ad_soyad = ?", conn, params=(secilen_ogr,))
            if not df_deneme.empty:
                st.dataframe(df_deneme, use_container_width=True)
            else:
                st.info("Bu öğrenci henüz deneme kaydetmedi.")
                
            # Zayıf Konular Alarmı
            st.subheader("🚨 Acil Müdahale Gereken Zayıf Konular (1 ve 2 Puan Verilenler)")
            df_zayif = pd.read_sql_query("SELECT konu_adi, puan FROM konu_puanlari WHERE ad_soyad = ? AND puan IN (1, 2)", conn, params=(secilen_ogr,))
            if not df_zayif.empty:
                st.warning(f"Toplam {len(df_zayif)} konuda eksik tespit edildi!")
                st.dataframe(df_zayif, use_container_width=True)
            else:
                st.success("Öğrencinin acil müdahale gerektiren (1 veya 2 puanlık) konusu bulunmuyor.")