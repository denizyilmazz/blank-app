import streamlit as st
import datetime
import sqlite3
import pandas as pd
import random
import base64
import re

st.set_page_config(
    page_title="YKS Pro Koçluk Platformu",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    /* Global Typography & Font Reset */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        -webkit-font-smoothing: antialiased;
    }

    /* Hide Default Streamlit Branding Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}

    /* Premium Modern Dynamic Background */
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 40%, #eef2ff 100%) !important;
        background-attachment: fixed !important;
        color: #0f172a;
    }

    /* Container Spacing & Layout Optimization */
    .main .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 1280px !important;
    }

    /* Glassmorphism Navigation Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: rgba(255, 255, 255, 0.85);
        padding: 8px;
        border-radius: 16px;
        backdrop-filter: blur(12px);
        border: 1px solid rgba(226, 232, 240, 0.8);
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.03);
    }

    .stTabs [data-baseweb="tab"] {
        height: 48px;
        background-color: transparent;
        border-radius: 12px;
        padding: 10px 22px;
        font-weight: 700;
        font-size: 14px;
        color: #64748b;
        border: none !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .stTabs [data-baseweb="tab"]:hover {
        background-color: rgba(241, 245, 249, 0.9);
        color: #4f46e5;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%) !important;
        color: #ffffff !important;
        box-shadow: 0 8px 20px -4px rgba(79, 70, 229, 0.35) !important;
    }

    /* Hero Motivation Card Design */
    .hero-motivation-card {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #ec4899 100%);
        color: #ffffff;
        padding: 24px 30px;
        border-radius: 20px;
        font-weight: 700;
        box-shadow: 0 12px 30px -5px rgba(79, 70, 229, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.2);
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
    }

    .hero-motivation-title {
        font-size: 11px;
        letter-spacing: 2.5px;
        text-transform: uppercase;
        color: rgba(255, 255, 255, 0.85);
        margin-bottom: 8px;
        font-weight: 800;
    }

    .hero-motivation-text {
        font-size: 20px;
        line-height: 1.4;
        font-weight: 800;
        margin: 0;
    }

    /* Metric Cards Styling */
    [data-testid="stMetricValue"] {
        font-size: 26px !important;
        font-weight: 800 !important;
        color: #0f172a !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 13px !important;
        font-weight: 700 !important;
        color: #64748b !important;
    }

    /* Custom Input Fields */
    .stTextInput input, .stSelectbox select, .stNumberInput input, .stTextArea textarea {
        border-radius: 12px !important;
        border: 1px solid #cbd5e1 !important;
        background-color: #ffffff !important;
        padding: 10px 14px !important;
        font-weight: 500 !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
        transition: all 0.2s ease !important;
    }

    .stTextInput input:focus, .stSelectbox select:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.15) !important;
    }

    /* Buttons Styling */
    .stButton > button {
        border-radius: 12px !important;
        font-weight: 700 !important;
        padding: 10px 24px !important;
        transition: all 0.25s ease !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 22px rgba(79, 70, 229, 0.25) !important;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: #ffffff !important;
        border-right: 1px solid #e2e8f0 !important;
    }

    /* Custom Badge / Banner Boxes */
    .coach-feedback-card {
        background: #f0f9ff;
        border-left: 5px solid #0284c7;
        padding: 18px 20px;
        border-radius: 14px;
        margin-top: 14px;
        font-size: 14.5px;
        color: #0369a1;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.06);
    }

    .info-security-card {
        background: #faf5ff;
        border: 1px solid #f0abfc;
        color: #701a75;
        padding: 16px 20px;
        border-radius: 14px;
        font-size: 13.5px;
        margin-bottom: 20px;
    }

    /* Card Container Utility */
    .pro-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 22px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.04);
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

SISTEM_YONETICI_KATILIM_KODU = "YKS2026KOC"

MOTIVASYON_SOZLERI = [
    "🔥 Gelecek, bugün ne yaptığına bağlıdır! İnan ve disiplinle devam et.",
    "🚀 Başarı, her gün ertelemeden tekrarlanan küçük çabaların birikimidir!",
    "🎓 Bugün döktüğün her damla alın teri, hayalindeki üniversitenin kapısını açar!",
    "💪 Zorluklar, potansiyelini keşfetmen için var olan basamaklardır. Pes etmek yok!",
    "✨ Şimdi odaklan ve çalış, gelecekteki kendin seninle gurur duysun!",
    "🎯 Zirveye giden yolda engel yoktur, sadece kararlılıkla aşılacak hedefler vardır!"
]

def sifre_gecerli_mi(sifre):
    """Koç Şifre Güvenlik Kontrolü (Harf + Rakam + Noktalama/Özel Karakter)"""
    if len(sifre) < 6:
        return False, "Şifre en az 6 karakter uzunluğunda olmalıdır!"
    if not re.search(r'[a-zA-ZçğıöşüÇĞİÖŞÜ]', sifre):
        return False, "Şifre en az bir HARF içermelidir!"
    if not re.search(r'\d', sifre):
        return False, "Şifre en az bir RAKAM (sayı) içermelidir!"
    if not re.search(r'[^\w\s]', sifre):
        return False, "Şifre en az bir NOKTALAMA İŞARETİ veya ÖZEL KARAKTER (!, ?, ., @, #, $, %, -, vb.) içermelidir!"
    return True, "Şifre geçerli."

def halka_grafik_html(baslik, veri_listesi):
    """Clean & Responsive Custom HTML Conic-Gradient Ring Chart Generator"""
    toplam = sum([v for _, v, _ in veri_listesi])
    if toplam == 0:
        return "<p style='color:#64748b; text-align:center; padding:20px; font-weight:500;'>Henüz görüntülenecek soru verisi bulunmuyor.</p>"
    
    gradient_parcalari = []
    mevcut_yuzde = 0.0
    legend_html = []
    
    for etiket, deger, renk in veri_listesi:
        if deger <= 0:
            continue
        yuzde = (deger / toplam) * 100
        sonraki_yuzde = mevcut_yuzde + yuzde
        gradient_parcalari.append(f"{renk} {mevcut_yuzde:.1f}% {sonraki_yuzde:.1f}%")
        mevcut_yuzde = sonraki_yuzde
        
        item_str = (
            f'<div style="display:flex; align-items:center; margin-bottom:8px; font-size:13.5px; font-family:sans-serif;">'
            f'<span style="width:12px; height:12px; background-color:{renk}; border-radius:50%; display:inline-block; margin-right:10px; flex-shrink:0;"></span>'
            f'<span style="color:#475569; font-weight:600;">{etiket}:</span>&nbsp;'
            f'<span style="color:#0f172a; font-weight:700;">{deger} Adet</span>&nbsp;'
            f'<span style="color:#94a3b8; font-size:11.5px; font-weight:600;">(%{yuzde:.1f})</span>'
            f'</div>'
        )
        legend_html.append(item_str)
        
    gradient_str = ", ".join(gradient_parcalari)
    legend_str = "".join(legend_html)
    
    raw_html = f'''<div style="background-color:#ffffff; padding:22px; border-radius:16px; border:1px solid #e2e8f0; box-shadow:0 4px 15px -3px rgba(0,0,0,0.04); margin-bottom:18px;">
<h4 style="margin-top:0; margin-bottom:18px; color:#0f172a; font-family:sans-serif; text-align:center; font-size:15px; font-weight:700; letter-spacing:-0.2px;">{baslik}</h4>
<div style="display:flex; flex-wrap:wrap; align-items:center; justify-content:center; gap:24px;">
<div style="width:150px; height:150px; border-radius:50%; background:conic-gradient({gradient_str}); position:relative; display:flex; align-items:center; justify-content:center; flex-shrink:0; box-shadow:0 4px 12px rgba(0,0,0,0.06);">
<div style="width:88px; height:88px; background:#ffffff; border-radius:50%; display:flex; flex-direction:column; align-items:center; justify-content:center; font-family:sans-serif; box-shadow:inset 0 2px 6px rgba(0,0,0,0.05);">
<span style="font-size:20px; font-weight:800; color:#0f172a;">{toplam}</span>
<span style="font-size:9.5px; color:#64748b; font-weight:700; letter-spacing:0.8px;">TOPLAM</span>
</div>
</div>
<div style="display:flex; flex-direction:column; justify-content:center;">
{legend_str}
</div>
</div>
</div>'''
    return raw_html

conn = sqlite3.connect("yks_kocluk.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS ogrenciler (
    ad_soyad TEXT PRIMARY KEY,
    sifre TEXT,
    koc_adi TEXT DEFAULT ''
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS koclar (
    kullanici_adi TEXT PRIMARY KEY,
    sifre TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS gunluk_calisma (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_soyad TEXT,
    tarih TEXT,
    ders TEXT,
    konu TEXT DEFAULT 'Genel Soru Çözümü / Karma',
    toplam_soru INTEGER,
    dogru INTEGER,
    yanlis INTEGER,
    bos INTEGER,
    sure FLOAT,
    verim INTEGER,
    notlar TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS denemeler (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_soyad TEXT,
    tarih TEXT,
    yayin TEXT,
    tur TEXT,
    toplam_net FLOAT,
    dosya_adi TEXT,
    koc_notu TEXT DEFAULT ''
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS konu_puanlari (
    ad_soyad TEXT,
    konu_adi TEXT,
    puan INTEGER,
    PRIMARY KEY (ad_soyad, konu_adi)
)
""")
conn.commit()

# Ensure default coach account exists
cursor.execute("SELECT COUNT(*) FROM koclar")
if cursor.fetchone()[0] == 0:
    cursor.execute("INSERT INTO koclar (kullanici_adi, sifre) VALUES (?, ?)", ("koc1", "Koc123!"))
    conn.commit()

# Ensure schema migrations are safely applied
for alter_cmd in [
    ("ogrenciler", "koc_adi", "TEXT DEFAULT ''"),
    ("gunluk_calisma", "konu", "TEXT DEFAULT 'Genel Soru Çözümü / Karma'"),
    ("denemeler", "koc_notu", "TEXT DEFAULT ''")
]:
    try:
        cursor.execute(f"ALTER TABLE {alter_cmd[0]} ADD COLUMN {alter_cmd[1]} {alter_cmd[2]}")
        conn.commit()
    except Exception:
        pass

YKS_KONULAR = {
    "📖 Türkçe": ["Sözcükte Anlam", "Cümlede Anlam", "Paragraf", "Yazım Kuralları", "Noktalama İşaretleri", "Dil Bilgisi", "Metin Türleri"],
    "📜 Tarih": ["Tarih Bilimine Giriş", "İlk Çağ Uygarlıkları", "İslam Öncesi Türk Tarihi", "İslam Tarihi ve Uygarlığı", "Türk İslam Devletleri", "Osmanlı Devleti Kuruluş & Yükselme", "Osmanlı Kültür ve Medeniyeti", "20. Yüzyıl Başlarında Osmanlı", "Milli Mücadele & İnkılap Tarihi", "Atatürkçülük ve İlkeler"],
    "🌍 Coğrafya": ["Doğa ve İnsan", "Dünya'nın Şekli ve Hareketleri", "Coğrafi Konum & Harita Bilgisi", "İklim Bilgisi & İklim Tipleri", "Yerin Şekillenmesi (İç ve Dış Kuvvetler)", "Türkiye'nin Yerşekilleri", "Beşeri Sistemler & Nüfus", "Afetler ve Çevre"],
    "🧠 Felsefe": ["Felsefeyi Tanıma", "Felsefi Düşünce & Sorgulama", "Bilgi Felsefesi (Epistemoloji)", "Varlık Felsefesi (Ontoloji)", "Ahlak Felsefesi (Etik)", "Sanat Felsefesi", "Siyaset Felsefesi", "Din Felsefesi", "Bilim Felsefesi"],
    "🕌 Din Kültürü": ["İnanç & Allah İnancı", "İbadet ve Esasları", "Ahlak ve Değerler", "Hz. Muhammed (S.A.V.) ve Gençlik", "Vahiy ve Akıl", "İslam ve Bilim", "Dünya Dinleri"],
    "📐 Matematik": ["Temel Kavramlar", "Sayı Basamakları", "Bölme - Bölünebilme", "EBOB - EKOK", "Rasyonel Sayılar", "Basit Eşitsizlikler", "Mutlak Değer", "Üslü & Köklü İfadeler", "Çarpanlara Ayırma", "Oran - Orantı", "Problemler (Sayı, Kesir, Yaş, Yüzde, Hız)", "Fonksiyonlar", "2. Dereceden Denklemler", "Polinomlar", "Permütasyon - Kombinasyon - Olasılık", "Logaritma", "Diziler", "Trigonometri", "Limit & Süreklilik", "Türev", "İntegral"],
    "📏 Geometri": ["Doğruda ve Üçgende Açılar", "Özel Üçgenler", "Üçgende Alan & Benzerlik", "Çokgenler & Dörtgenler", "Çember ve Daire", "Analitik Geometri", "Katı Cisimler"],
    "⚡ Fizik": ["Fizik Bilimine Giriş", "Madde ve Özellikleri", "Kuvvet ve Hareket", "İş, Güç, Enerji", "Isı ve Sıcaklık", "Basınç ve Kaldırma Kuvveti", "Elektrostatik & Elektrik", "Optik", "Dalgalar", "Atışlar & Tork", "Çembersel Hareket", "Harmonik Hareket", "Modern Fizik"],
    "🧪 Kimya": ["Kimya Bilimi & Atom", "Periyodik Sistem", "Türler Arası Etkileşimler", "Maddenin Halleri", "Mol Kavramı & Tepkimeler", "Karışımlar", "Asit, Baz, Tuz", "Gazlar", "Çözeltiler", "Enerji, Hız ve Denge", "Elektrokimya", "Organik Kimya"],
    "🧬 Biyoloji": ["Yaşam Bilimi Biyoloji", "Hücre ve Organeller", "Hücre Bölünmeleri", "Kalıtım", "Ekoloji", "İnsan Fizyolojisi (Sistemler)", "Gensa Bilgi & Protein Sentezi", "Fotosentez & Solunum", "Bitki Biyolojisi"]
}

DERSLER = list(YKS_KONULAR.keys())

st.sidebar.markdown("""
<div style="text-align: center; padding: 10px 0 20px 0;">
    <span style="font-size: 42px;">🎓</span>
    <h2 style="margin: 5px 0 0 0; font-weight: 800; font-size: 20px; color: #0f172a;">YKS Pro Koçluk</h2>
    <p style="margin: 0; font-size: 12px; color: #64748b; font-weight: 600;">Gelişim & Takip Platformu</p>
</div>
""", unsafe_allow_html=True)

giris_turu = st.sidebar.radio("Giriş Paneli Seçin:", ["👨‍🎓 ÖĞRENCİ GİRİŞİ", "👨‍🏫 KOÇ GİRİŞİ"])

if giris_turu == "👨‍🎓 ÖĞRENCİ GİRİŞİ":
    st.markdown("<h1 style='font-weight:800; font-size:28px; color:#0f172a; margin-bottom:10px;'>👨‍🎓 Öğrenci Yönetim Paneli</h1>", unsafe_allow_html=True)
    
    # Session state motivation quote
    if "motivasyon_goster" not in st.session_state:
        st.session_state["motivasyon_goster"] = True
    if "motivasyon_sozu" not in st.session_state:
        st.session_state["motivasyon_sozu"] = random.choice(MOTIVASYON_SOZLERI)
        
    if st.session_state["motivasyon_goster"]:
        m_col1, m_col2 = st.columns([0.9, 0.1])
        with m_col1:
            st.markdown(f'''
            <div class="hero-motivation-card">
                <div class="hero-motivation-title">⚡ GÜNÜN MOTİVASYON MESAJI ⚡</div>
                <div class="hero-motivation-text">"{st.session_state['motivasyon_sozu']}"</div>
            </div>
            ''', unsafe_allow_html=True)
        with m_col2:
            if st.button("❌ KAPAT", key="kapat_motivasyon", help="Motivasyon kartını kapat", use_container_width=True):
                st.session_state["motivasyon_goster"] = False
                st.rerun()
    
    tab_giris, tab_gunluk, tab_deneme, tab_konular = st.tabs([
        "🔑 GİRİŞ / KAYIT",
        "📝 GÜNLÜK DERS VE SORU TAKİBİ",
        "📊 DENEME SONUÇLARI VE KARNE YÜKLEME",
        "🗺️ DERS DERS KONU DERECELENDİRME"
    ])
    
    # --- TAB 1: STUDENT LOGIN / SIGNUP ---
    with tab_giris:
        st.markdown("<h3 style='font-weight:700; font-size:18px; color:#1e293b; margin-bottom:15px;'>Öğrenci Hesabı Girişi / Kaydı</h3>", unsafe_allow_html=True)
        
        cursor.execute("SELECT kullanici_adi FROM koclar")
        koc_listesi = [r[0] for r in cursor.fetchall()]
        if not koc_listesi:
            koc_listesi = ["koc1"]
            
        with st.form("ogrenci_giris_kayit_formu"):
            col1, col2, col3 = st.columns(3)
            with col1:
                ad_soyad = st.text_input("Adınız ve Soyadınız:").strip().title()
            with col2:
                sifre = st.text_input("Şifreniz / PIN:", type="password")
            with col3:
                secilen_koc = st.selectbox("👨‍🏫 Sorumlu Koçunuzu Seçin:", koc_listesi)
                
            ogr_giris_btn = st.form_submit_button("Giriş Yap / Hesabı Oluştur", type="primary", use_container_width=True)
            
        if ogr_giris_btn:
            if ad_soyad and sifre:
                cursor.execute("SELECT sifre, koc_adi FROM ogrenciler WHERE ad_soyad = ?", (ad_soyad,))
                user = cursor.fetchone()
                if user is None:
                    cursor.execute("INSERT INTO ogrenciler (ad_soyad, sifre, koc_adi) VALUES (?, ?, ?)", (ad_soyad, sifre, secilen_koc))
                    conn.commit()
                    st.success(f"🎉 Hoş geldin {ad_soyad}! Profilin ({secilen_koc} koçluğunda) başarıyla oluşturuldu.")
                    st.session_state["aktif_ogrenci"] = ad_soyad
                else:
                    if user[0] == sifre:
                        cursor.execute("UPDATE ogrenciler SET koc_adi = ? WHERE ad_soyad = ?", (secilen_koc, ad_soyad))
                        conn.commit()
                        st.success(f"🔓 Başarıyla giriş yapıldı! Hoş geldin {ad_soyad}. (Sorumlu Koç: {secilen_koc})")
                        st.session_state["aktif_ogrenci"] = ad_soyad
                    else:
                        st.error("Hatalı şifre! Lütfen şifrenizi kontrol ediniz.")
            else:
                st.warning("Lütfen ad, soyad ve şifre giriniz.")
                
    aktif_ogr = st.session_state.get("aktif_ogrenci", None)
    
    if not aktif_ogr:
        st.info("ℹ️ İşlem yapmak için lütfen ilk sekmeden 'Giriş / Kayıt' yapın.")
    else:
        st.sidebar.success(f"👤 Aktif Öğrenci: **{aktif_ogr}**")
        
        # --- TAB 2: DAILY PROGRESS & QUESTION TRACKING ---
        with tab_gunluk:
            st.markdown(f"<h3 style='font-weight:700; font-size:18px; color:#1e293b;'>📝 Günlük Çalışma Girişi — {aktif_ogr}</h3>", unsafe_allow_html=True)
            
            c_top1, c_top2, c_top3 = st.columns([1, 1, 1])
            with c_top1:
                tarih_giris = st.date_input("Çalışma Tarihi", datetime.date.today())
            with c_top2:
                sure_giris = st.number_input("Bugünkü Toplam Çalışma Süresi (Saat)", 0.0, 16.0, 7.5, 0.5)
            with c_top3:
                verim_giris = st.slider("Günün Verim Puanı (1-10)", 1, 10, 8)
                
            not_giris = st.text_area("Bugün zorlandığın detaylar / Koçuna iletmek istediğin çalışma notu:", height=80)
            
            st.divider()
            st.markdown("<h4 style='font-weight:700; font-size:16px; color:#334155;'>📚 Ders ve Konu Bazlı Soru Analizi Girişi</h4>", unsafe_allow_html=True)
            
            ders_sekmeleri = st.tabs(DERSLER)
            ders_verileri = {}

            for idx, ders_adi in enumerate(DERSLER):
                with ders_sekmeleri[idx]:
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

            if st.button("🚀 Tüm Ders ve Konu Çalışmalarını Kaydet", type="primary", use_container_width=True):
                yeni_kayit = False
                for d_adi, (k_adi, t_s, d_s, y_s, b_s) in ders_verileri.items():
                    if t_s > 0:
                        yeni_kayit = True
                        try:
                            cursor.execute("""
                            DELETE FROM gunluk_calisma 
                            WHERE ad_soyad = ? AND tarih = ? AND ders = ? AND konu = ?
                            """, (aktif_ogr, str(tarih_giris), d_adi, k_adi))
                            
                            cursor.execute("""
                            INSERT INTO gunluk_calisma (ad_soyad, tarih, ders, konu, toplam_soru, dogru, yanlis, bos, sure, verim, notlar)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (aktif_ogr, str(tarih_giris), d_adi, k_adi, t_s, d_s, y_s, b_s, float(sure_giris), int(verim_giris), not_giris))
                            conn.commit()
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Kayıt esnasında teknik bir hata oluştu: {e}")
                
                if yeni_kayit:
                    st.balloons()
                    st.success("🎉 TEBRİKLER HEDEFİNE 1 ADIM DAHA YAKLAŞTIN!")
                    st.info("Soru çözümleriniz kaydedildi. Aşağıdaki başarı grafikleriniz güncellendi!")
                else:
                    st.warning("Lütfen kaydetmeden önce en az bir dersten soru sayısı giriniz.")

            st.divider()
            st.markdown(f"<h4 style='font-weight:700; font-size:16px; color:#1e293b;'>📈 Anlık Soru ve Başarı Grafikleri — {aktif_ogr}</h4>", unsafe_allow_html=True)
            
            df_analiz = pd.read_sql_query(
                "SELECT ders, SUM(toplam_soru) as toplam, SUM(dogru) as d, SUM(yanlis) as y, SUM(bos) as b FROM gunluk_calisma WHERE ad_soyad = ? GROUP BY ders",
                conn, params=(aktif_ogr,)
            )
            
            if df_analiz.empty or df_analiz["toplam"].sum() == 0:
                st.info("📊 Henüz soru verisi bulunmuyor. Yukarıdan soru çözümlerinizi girip kaydettiğinizde grafikleriniz burada otomatik belirecektir.")
            else:
                top_d = int(df_analiz["d"].sum())
                top_y = int(df_analiz["y"].sum())
                top_b = int(df_analiz["b"].sum())
                
                col_g1, col_g2 = st.columns(2)
                
                with col_g1:
                    df_filtr = df_analiz[df_analiz["toplam"] > 0]
                    renk_paleti = ['#4f46e5', '#7c3aed', '#ec4899', '#f97316', '#10b981', '#06b6d4', '#6366f1', '#f59e0b', '#14b8a6', '#64748b']
                    ders_verileri_list = []
                    for idx_row, row in df_filtr.reset_index().iterrows():
                        r_renk = renk_paleti[idx_row % len(renk_paleti)]
                        ders_verileri_list.append((row["ders"], int(row["toplam"]), r_renk))
                        
                    st.markdown(halka_grafik_html("🍩 Derslere Göre Çözülen Soru Dağılımı", ders_verileri_list), unsafe_allow_html=True)

                with col_g2:
                    dyb_verileri = [
                        ("Doğru 🟢", top_d, "#10b981"),
                        ("Yanlış 🔴", top_y, "#ef4444"),
                        ("Boş 🟡", top_b, "#f59e0b")
                    ]
                    st.markdown(halka_grafik_html("🎯 Toplam Doğru / Yanlış / Boş Oranı", dyb_verileri), unsafe_allow_html=True)

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Toplam Çözülen Soru", f"{df_analiz['toplam'].sum()} Adet")
                m2.metric("Toplam Doğru", f"{top_d} Adet")
                m3.metric("Toplam Yanlış", f"{top_y} Adet")
                m4.metric("Toplam Boş", f"{top_b} Adet")

        # --- TAB 3: DENEME TESTS & REPORT CARDS ---
        with tab_deneme:
            st.markdown("<h3 style='font-weight:700; font-size:18px; color:#1e293b;'>📊 Deneme Sonuçları & Karne Yükleme</h3>", unsafe_allow_html=True)
            
            with st.form("deneme_yukle_formu"):
                col_d1, col_d2, col_d3 = st.columns(3)
                with col_d1:
                    yayin = st.text_input("Deneme Adı / Yayın:")
                with col_d2:
                    d_tur = st.selectbox("Deneme Türü:", ["TYT Denemesi", "AYT Sayısal Denemesi", "AYT Eşit Ağırlık Denemesi", "Branş Denemesi"])
                with col_d3:
                    toplam_net = st.number_input("Toplam Netiniz:", 0.0, 160.0, 85.0)
                    
                karne_dosya = st.file_uploader("📄 Deneme Karnesi / Fotoğrafı Yükle:", type=["pdf", "png", "jpg", "jpeg"])
                deneme_sub = st.form_submit_button("Deneme Karnesini Kaydet", type="primary", use_container_width=True)
            
            if deneme_sub:
                dosya_adi = karne_dosya.name if karne_dosya else "Dosya Yüklenmedi"
                cursor.execute("""
                INSERT INTO denemeler (ad_soyad, tarih, yayin, tur, toplam_net, dosya_adi, koc_notu)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (aktif_ogr, str(datetime.date.today()), yayin, d_tur, float(toplam_net), dosya_adi, ''))
                conn.commit()
                st.balloons()
                st.success("🎉 TEBRİKLER HEDEFİNE 1 ADIM DAHA YAKLAŞTIN!")

            st.divider()
            st.markdown("<h4 style='font-weight:700; font-size:16px; color:#1e293b;'>📋 Geçmiş Denemeleriniz ve Koçunuzun Değerlendirmeleri</h4>", unsafe_allow_html=True)
            df_ogr_deneme = pd.read_sql_query(
                "SELECT tarih, yayin, tur, toplam_net, dosya_adi, koc_notu FROM denemeler WHERE ad_soyad = ? ORDER BY id DESC",
                conn, params=(aktif_ogr,)
            )
            if df_ogr_deneme.empty:
                st.info("Henüz kaydedilmiş bir deneme sonucunuz bulunmuyor.")
            else:
                for idx, row in df_ogr_deneme.iterrows():
                    with st.expander(f"📌 {row['tarih']} — {row['yayin']} ({row['tur']}) | Net: {row['toplam_net']}"):
                        st.write(f"**Karne Dosyası:** {row['dosya_adi']}")
                        if row['koc_notu'] and str(row['koc_notu']).strip() != '':
                            st.markdown(f"""
                            <div class="coach-feedback-card">
                                <strong>👨‍🏫 Koçunuzun Deneme Analizi ve Eksik Konu Notları:</strong><br/>
                                <div style="margin-top: 6px; white-space: pre-wrap;">{row['koc_notu']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.info("👨‍🏫 Koçunuz henüz bu deneme için analiz notu eklemedi.")

        # --- TAB 4: SUBJECT MASTERY RATINGS ---
        with tab_konular:
            st.markdown("<h3 style='font-weight:700; font-size:18px; color:#1e293b;'>🗺️ Ders Ders Konu Hakimiyet Puanlaması (1 - 5)</h3>", unsafe_allow_html=True)
            st.caption("Eksik olduğunuz konuları dürüstçe puanlayın. 1 ve 2 puan alan konular koçunuzun analiz ekranında doğrudan 'Acil Müdahale Konuları' olarak belirecektir.")
            
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
            st.success("🎉 Konu hakimiyet puanlamalarınız başarıyla kaydedildi.")

else:
    st.markdown("<h1 style='font-weight:800; font-size:28px; color:#0f172a; margin-bottom:10px;'>👨‍🏫 Koç Yönetim ve Analiz Paneli</h1>", unsafe_allow_html=True)
    
    if "aktif_koc" not in st.session_state:
        st.session_state["aktif_koc"] = None

    if not st.session_state["aktif_koc"]:
        koc_tab_giris, koc_tab_kayit, koc_tab_sifre = st.tabs([
            "🔑 KOÇ GİRİŞİ", 
            "📝 YENİ KOÇ KAYDI (YÖNETİCİ KODU GEREKİR)", 
            "🔒 ŞİFRE DEĞİŞTİR"
        ])

        # --- COACH LOGIN ---
        with koc_tab_giris:
            st.markdown("<h3 style='font-weight:700; font-size:18px; color:#1e293b;'>👨‍🏫 Koç Girişi</h3>", unsafe_allow_html=True)
            with st.form("koc_giris_formu"):
                k_adi_giris = st.text_input("Koç Kullanıcı Adı:").strip()
                k_sifre_giris = st.text_input("Şifre:", type="password")
                giris_btn = st.form_submit_button("Koç Paneline Giriş Yap", type="primary", use_container_width=True)
                
            if giris_btn:
                if not k_adi_giris or not k_sifre_giris:
                    st.warning("Lütfen kullanıcı adı ve şifrenizi giriniz.")
                else:
                    cursor.execute("SELECT sifre FROM koclar WHERE kullanici_adi = ?", (k_adi_giris,))
                    row = cursor.fetchone()
                    if row and row[0] == k_sifre_giris:
                        st.session_state["aktif_koc"] = k_adi_giris
                        st.success(f"🔓 Hoş geldiniz Sayın Koç {k_adi_giris}! Giriş başarılı.")
                        st.rerun()
                    else:
                        st.error("Hatalı kullanıcı adı veya şifre!")

        # --- COACH REGISTRATION ---
        with koc_tab_kayit:
            st.markdown("<h3 style='font-weight:700; font-size:18px; color:#1e293b;'>📝 Yeni Koç Hesabı Oluştur</h3>", unsafe_allow_html=True)
            st.markdown(f"""
            <div class="info-security-card">
                🛡️ <strong>Sistem Güvenlik Kuralları:</strong><br/>
                1. Yeni bir koç hesabı açmak için <strong>Sistem Katılım / Yönetici Kodu</strong> (Varsayılan: <code>YKS2026KOC</code>) zorunludur.<br/>
                2. Koç şifreniz en az 6 karakter olmalı; en az 1 HARF, 1 RAKAM ve 1 NOKTALAMA/ÖZEL KARAKTER (!, ?, ., @, #, vb.) içermelidir.
            </div>
            """, unsafe_allow_html=True)
            
            with st.form("koc_kayit_formu"):
                katilim_kodu_input = st.text_input("🔑 Sistem Katılım / Yönetici Kodu:", type="password")
                yeni_k_adi = st.text_input("Yeni Koç Kullanıcı Adı:").strip()
                yeni_k_sifre = st.text_input("Şifre:", type="password")
                yeni_k_sifre_tekrar = st.text_input("Şifre Tekrarı:", type="password")
                kaydet_btn = st.form_submit_button("Koç Hesabını Kaydet", type="primary", use_container_width=True)
            
            if kaydet_btn:
                if not katilim_kodu_input or not yeni_k_adi or not yeni_k_sifre or not yeni_k_sifre_tekrar:
                    st.warning("Lütfen tüm alanları doldurunuz.")
                elif katilim_kodu_input != SISTEM_YONETICI_KATILIM_KODU:
                    st.error("❌ Hatalı Yönetici Katılım Kodu! Yetkisiz kişiler koç hesabı oluşturamaz.")
                elif yeni_k_sifre != yeni_k_sifre_tekrar:
                    st.error("Girilen şifreler birbiriyle uyuşmuyor!")
                else:
                    gecerli, mesaj = sifre_gecerli_mi(yeni_k_sifre)
                    if not gecerli:
                        st.error(f"⚠️ Şifre Uygun Değil: {mesaj}")
                    else:
                        cursor.execute("SELECT kullanici_adi FROM koclar WHERE kullanici_adi = ?", (yeni_k_adi,))
                        if cursor.fetchone():
                            st.error("Bu kullanıcı adı zaten kullanılıyor! Başka bir kullanıcı adı deneyin.")
                        else:
                            cursor.execute("INSERT INTO koclar (kullanici_adi, sifre) VALUES (?, ?)", (yeni_k_adi, yeni_k_sifre))
                            conn.commit()
                            st.success(f"🎉 Koç hesabı ({yeni_k_adi}) başarıyla oluşturuldu! Şimdi giriş yapabilirsiniz.")

        # --- CHANGE PASSWORD ---
        with koc_tab_sifre:
            st.markdown("<h3 style='font-weight:700; font-size:18px; color:#1e293b;'>🔒 Koç Şifresi Değiştir</h3>", unsafe_allow_html=True)
            with st.form("koc_sifre_degistir_formu"):
                s_k_adi = st.text_input("Kullanıcı Adınız:").strip()
                eski_sifre = st.text_input("Mevcut Şifreniz:", type="password")
                yeni_sifre = st.text_input("Yeni Şifreniz:", type="password")
                yeni_sifre_tekrar = st.text_input("Yeni Şifre Tekrarı:", type="password")
                sifre_guncelle_btn = st.form_submit_button("Şifreyi Güncelle", use_container_width=True)
            
            if sifre_guncelle_btn:
                if not s_k_adi or not eski_sifre or not yeni_sifre or not yeni_sifre_tekrar:
                    st.warning("Lütfen tüm alanları doldurunuz.")
                else:
                    cursor.execute("SELECT sifre FROM koclar WHERE kullanici_adi = ?", (s_k_adi,))
                    row = cursor.fetchone()
                    if not row or row[0] != eski_sifre:
                        st.error("Kullanıcı adı veya mevcut şifre hatalı!")
                    elif yeni_sifre != yeni_sifre_tekrar:
                        st.error("Yeni şifreler birbiriyle eşleşmiyor!")
                    else:
                        gecerli, mesaj = sifre_gecerli_mi(yeni_sifre)
                        if not gecerli:
                            st.error(f"⚠️ Şifre Uygun Değil: {mesaj}")
                        else:
                            cursor.execute("UPDATE koclar SET sifre = ? WHERE kullanici_adi = ?", (yeni_sifre, s_k_adi))
                            conn.commit()
                            st.success("🎉 Şifreniz başarıyla güncellendi! Yeni şifrenizle giriş yapabilirsiniz.")

    else:
        aktif_koc_adi = st.session_state['aktif_koc']
        
        col_koc_top1, col_koc_top2 = st.columns([0.8, 0.2])
        with col_koc_top1:
            st.success(f"🔓 Aktif Koç Oturumu: **{aktif_koc_adi}**")
        with col_koc_top2:
            if st.button("🚪 Çıkış Yap", use_container_width=True):
                st.session_state["aktif_koc"] = None
                st.rerun()

        cursor.execute("SELECT ad_soyad FROM ogrenciler WHERE koc_adi = ? OR koc_adi = '' OR koc_adi IS NULL", (aktif_koc_adi,))
        ogrenciler = [row[0] for row in cursor.fetchall()]
        
        if not ogrenciler:
            st.info(f"👨‍🏫 Sayın Koç {aktif_koc_adi}, şu anda sistemde size bağlı kayıtlı öğrenci bulunmuyor.")
        else:
            secilen_ogr = st.selectbox(f"🔍 Size Bağlı Öğrencilerinizi Seçin ({len(ogrenciler)} Öğrenci):", ogrenciler)
            
            st.divider()
            st.markdown(f"<h2 style='font-weight:800; font-size:22px; color:#0f172a;'>📊 Öğrenci Analiz Raporu: {secilen_ogr}</h2>", unsafe_allow_html=True)
            
            st.markdown("<h4 style='font-weight:700; font-size:16px; color:#334155;'>📚 Ders & Konu Bazlı Soru, Doğru, Yanlış, Boş Dağılımı</h4>", unsafe_allow_html=True)
            df_gunluk = pd.read_sql_query("SELECT id, tarih, ders, konu, toplam_soru, dogru, yanlis, bos, sure, verim, notlar FROM gunluk_calisma WHERE ad_soyad = ?", conn, params=(secilen_ogr,))
            
            if not df_gunluk.empty:
                st.dataframe(df_gunluk, use_container_width=True)
                
                with st.expander("🗑️ Hatalı veya Yanlış Girilmiş Kayıtları Sil"):
                    silinecek_id = st.selectbox("Silmek istediğiniz kaydın 'id' numarasını seçin:", df_gunluk["id"].tolist())
                    if st.button("Seçilen Kaydı Veritabanından Sil", type="primary"):
                        cursor.execute("DELETE FROM gunluk_calisma WHERE id = ?", (silinecek_id,))
                        conn.commit()
                        st.success(f"ID {silinecek_id} numaralı kayıt başarıyla silindi!")
                        st.rerun()
            else:
                st.info("Bu öğrenci henüz günlük ders ve konu soru verisi girmedi.")
                
            st.divider()
            st.markdown("<h4 style='font-weight:700; font-size:16px; color:#334155;'>📑 Kayıtlı Denemeler ve Koç Değerlendirmesi</h4>", unsafe_allow_html=True)
            df_deneme = pd.read_sql_query("SELECT id, tarih, yayin, tur, toplam_net, dosya_adi, koc_notu FROM denemeler WHERE ad_soyad = ?", conn, params=(secilen_ogr,))
            
            if not df_deneme.empty:
                st.dataframe(df_deneme, use_container_width=True)
                
                st.markdown("<h4 style='font-weight:700; font-size:16px; color:#1e293b; margin-top:20px;'>✍️ Denemeye Özel Koç Değerlendirmesi & Otomatik AI Analiz Üretici</h4>", unsafe_allow_html=True)
                deneme_secenekleri = {row['id']: f"ID: {row['id']} - {row['tarih']} | {row['yayin']} ({row['tur']}) - Net: {row['toplam_net']}" for _, row in df_deneme.iterrows()}
                
                secilen_deneme_id = st.selectbox("Analiz yapılacak denemeyi seçin:", options=list(deneme_secenekleri.keys()), format_func=lambda x: deneme_secenekleri[x])
                deneme_row = df_deneme[df_deneme['id'] == secilen_deneme_id].iloc[0]
                
                df_zayif_konular = pd.read_sql_query("SELECT konu_adi FROM konu_puanlari WHERE ad_soyad = ? AND puan IN (1, 2)", conn, params=(secilen_ogr,))
                zayif_liste = df_zayif_konular['konu_adi'].tolist() if not df_zayif_konular.empty else []
                zayif_str = ", ".join(zayif_liste) if zayif_liste else "Acil müdahale gereken 1-2 puanlık konu bulunmamaktadır."

                col_ai1, col_ai2 = st.columns([0.4, 0.6])
                with col_ai1:
                    if st.button("🤖 Otomatik Akıllı Analiz Taslağı Üret", use_container_width=True):
                        otomatik_not = (
                            f"📌 {deneme_row['yayin']} ({deneme_row['tur']}) Değerlendirmesi:\n"
                            f"• Elde edilen Net: {deneme_row['toplam_net']} Net.\n"
                            f"• Tespit Edilen Zayıf Konular: {zayif_str}\n\n"
                            f"💡 Sorumlu Koç ({aktif_koc_adi}) Tavsiyesi & Çalışma Planı:\n"
                            f"1. Yukarıda belirtilen zayıf konulardan her gün en az 30'ar soru çözülmeli.\n"
                            f"2. Denemedeki yanlış yapılan soruların çözümleri tekrar incelenmeli.\n"
                            f"3. Zaman yönetimini geliştirmek için süre tutarak branş denemesi çözülmeli."
                        )
                        st.session_state[f"temp_not_{secilen_deneme_id}"] = otomatik_not
                        st.success("🤖 Otomatik analiz taslağı üretildi! Yanda inceleyip düzenleyebilirsiniz.")

                mevcut_koc_notu = st.session_state.get(f"temp_not_{secilen_deneme_id}", deneme_row['koc_notu'])
                if pd.isna(mevcut_koc_notu):
                    mevcut_koc_notu = ""

                yeni_koc_notu = st.text_area(
                    "Koç Değerlendirmesi (Dilerseniz düzenleyin ve onaylayın):",
                    value=mevcut_koc_notu,
                    height=180,
                    key=f"koc_not_input_{secilen_deneme_id}"
                )
                
                col_save, col_pdf = st.columns(2)
                with col_save:
                    if st.button("💾 Değerlendirmeyi Onayla ve Öğrenciye İlet", type="primary", use_container_width=True):
                        cursor.execute("UPDATE denemeler SET koc_notu = ? WHERE id = ?", (yeni_koc_notu, secilen_deneme_id))
                        conn.commit()
                        st.success("🎉 Deneme analiz notu kaydedildi ve öğrenci paneline gönderildi!")
                
                with col_pdf:
                    st.markdown("##### 📄 Yazdırılabilir / PDF Rapor Karnesi")
                    html_rapor = f"""
                    <div style="font-family: 'Segoe UI', Arial, sans-serif; padding: 25px; border: 2px solid #4f46e5; border-radius: 12px; background-color: #ffffff; color: #0f172a;">
                        <div style="text-align: center; border-bottom: 2px solid #e2e8f0; padding-bottom: 12px; margin-bottom: 18px;">
                            <h2 style="color: #4f46e5; margin: 0; font-size: 22px;">🎓 YKS ÖĞRENCİ GELİŞİM & DENEME KARNESİ</h2>
                            <p style="color: #64748b; margin: 6px 0 0 0; font-size: 13px;"><strong>Tarih:</strong> {datetime.date.today().strftime('%d.%m.%Y')}</p>
                            <p style="color: #64748b; margin: 2px 0 0 0; font-size: 13px;"><strong>Sorumlu Koç:</strong> {aktif_koc_adi}</p>
                        </div>
                        <p style="font-size: 14px;"><strong>👨‍🎓 Öğrenci Adı Soyadı:</strong> {secilen_ogr}</p>
                        <p style="font-size: 14px;"><strong>📑 Deneme Adı / Yayın:</strong> {deneme_row['yayin']} ({deneme_row['tur']})</p>
                        <p style="font-size: 14px;"><strong>🎯 Toplam Net:</strong> <span style="font-size: 18px; color: #4f46e5; font-weight: bold;">{deneme_row['toplam_net']} Net</span></p>
                        <p style="font-size: 14px;"><strong>🚨 Zayıf Olduğu Konular:</strong> {zayif_str}</p>
                        <div style="background-color: #f8fafc; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0; margin-top: 15px;">
                            <strong style="color: #1e293b;">👨‍🏫 Koç Analizi & Tavsiyeler:</strong><br/>
                            <p style="white-space: pre-wrap; margin-top: 8px; font-size: 13.5px; line-height: 1.5;">{yeni_koc_notu}</p>
                        </div>
                    </div>
                    """
                    b64_html = base64.b64encode(html_rapor.encode('utf-8')).decode('utf-8')
                    href = f'<a href="data:text/html;charset=utf-8;base64,{b64_html}" download="{secilen_ogr}_Deneme_Karnesi.html" style="display: inline-block; padding: 10px 20px; background-color: #10b981; color: white; text-decoration: none; border-radius: 10px; font-weight: bold; text-align: center; width: 100%;">📥 PDF / Raporu İndir (HTML/Yazdır)</a>'
                    st.markdown(href, unsafe_allow_html=True)

            else:
                st.info("Bu öğrenci henüz deneme kaydetmedi.")
                
            st.divider()
            st.markdown("<h4 style='font-weight:700; font-size:16px; color:#1e293b;'>🚨 Acil Müdahale Gereken Zayıf Konular (1 ve 2 Puan Verilenler)</h4>", unsafe_allow_html=True)
            df_zayif = pd.read_sql_query("SELECT konu_adi, puan FROM konu_puanlari WHERE ad_soyad = ? AND puan IN (1, 2)", conn, params=(secilen_ogr,))
            if not df_zayif.empty:
                st.warning(f"⚠️ Toplam {len(df_zayif)} konuda eksik tespit edildi!")
                st.dataframe(df_zayif, use_container_width=True)
            else:
                st.success("✨ Öğrencinin acil müdahale gerektiren (1 veya 2 puanlık) konusu bulunmuyor.")