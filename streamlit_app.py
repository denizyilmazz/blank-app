import streamlit as st
import datetime
import sqlite3
import pandas as pd
import random
import base64
import hashlib
import os
import shutil
from urllib.parse import quote
from PIL import Image

# Google Generative AI kütüphane kontrolü
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

st.set_page_config(
    page_title="YKS (TYT/AYT) - LGS KOÇLUK (DENİZ YILMAZ)",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"], .stMarkdown, p, div, label, span, input, textarea, select {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #0f172a !important;
    }

    #MainMenu, footer, header, .stDeployButton {display: none !important;}

    .stApp {
        background: linear-gradient(135deg, #f0fdf4 0%, #e0f2fe 50%, #f3e8ff 100%) !important;
        background-attachment: fixed !important;
    }

    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 3rem !important;
        max-width: 1420px !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background: #ffffff !important;
        padding: 8px;
        border-radius: 16px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        border: 1px solid #cbd5e1 !important;
    }

    .stTabs [data-baseweb="tab"] {
        height: 48px;
        background-color: #f8fafc !important;
        border-radius: 10px;
        padding: 8px 16px;
        font-weight: 700 !important;
        font-size: 13px !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
    }

    .stTabs [data-baseweb="tab"] div {
        color: #0f172a !important;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%) !important;
        border: none !important;
    }

    .stTabs [aria-selected="true"] span, .stTabs [aria-selected="true"] div {
        color: #ffffff !important;
    }

    input, textarea, select, div[data-baseweb="select"] {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1.5px solid #94a3b8 !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }

    div[data-baseweb="select"] * {
        color: #0f172a !important;
        background-color: #ffffff !important;
    }

    .stTextInput > label, .stSelectbox > label, .stNumberInput > label, .stTextArea > label {
        color: #1e293b !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        margin-bottom: 4px !important;
    }

    .hero-motivation-card {
        background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 50%, #8b5cf6 100%);
        color: #ffffff !important;
        padding: 20px 24px;
        border-radius: 20px;
        font-weight: 700;
        margin-bottom: 20px;
    }

    .hero-motivation-card * {
        color: #ffffff !important;
    }

    .ai-analysis-box {
        background: #faf5ff !important;
        border-left: 5px solid #a855f7 !important;
        padding: 16px 20px;
        border-radius: 14px;
        font-size: 14px;
        color: #4c1d95 !important;
        margin-top: 12px;
        margin-bottom: 15px;
    }

    .ai-analysis-box * {
        color: #4c1d95 !important;
    }

    .share-link-card {
        background: linear-gradient(135deg, #059669 0%, #0d9488 100%);
        color: white !important;
        padding: 20px 24px;
        border-radius: 16px;
        box-shadow: 0 10px 25px -5px rgba(5, 150, 105, 0.3);
        margin-bottom: 20px;
    }

    .share-link-card * {
        color: white !important;
    }

    .yok-net-box {
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        border: 2px solid #3b82f6;
        border-radius: 16px;
        padding: 16px 20px;
        margin-bottom: 15px;
    }

    .calc-card {
        background: #ffffff !important;
        border: 1.5px solid #cbd5e1;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        margin-top: 15px;
    }

    .osym-belge-box {
        background: #ffffff !important;
        border: 2px solid #1e293b;
        border-radius: 12px;
        padding: 24px;
        color: #0f172a !important;
        margin-top: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    }

    .osym-belge-box * {
        color: #0f172a !important;
    }

    .total-soru-banner {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white !important;
        padding: 18px 24px;
        border-radius: 16px;
        font-weight: 800;
        font-size: 18px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.25);
    }
</style>
""", unsafe_allow_html=True)

SABIT_GEMINI_API_KEY = "AQ.Ab8RN6Iu0rNJR14IpQDnEyaXDJPMFnkgaOBn4lZ8j2qZrysa6A"
SISTEM_YONETICI_KATILIM_KODU = "YKS2026KOC"
DB_FILE = "yks_kocluk.db"
UPLOAD_DIR = "soru_yuklemeleri"
KARNE_DIR = "karne_yuklemeleri"
PROGRAM_DIR = "program_dosyalari"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(KARNE_DIR, exist_ok=True)
os.makedirs(PROGRAM_DIR, exist_ok=True)

def make_hash(password: str) -> str:
    salt = "YKS_PRO_SECURE_SALT_2026"
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()

def verify_hash(password: str, hashed_password: str) -> bool:
    if not hashed_password: return False
    if password == hashed_password: return True
    return make_hash(password) == hashed_password

def pdf_goster_html(pdf_path):
    try:
        with open(pdf_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        return f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="550" type="application/pdf" style="border-radius:12px; border:1px solid #cbd5e1;"></iframe>'
    except Exception:
        return "<p style='color:red;'>PDF dosyası okunamadı.</p>"

def ai_soru_gorseli_analiz_et(file_path, ders, konu_ipucu=""):
    api_key = SABIT_GEMINI_API_KEY.strip()
    if GENAI_AVAILABLE and api_key and api_key != "AIzaSy..." and os.path.exists(file_path):
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            if file_path.lower().endswith('.pdf'):
                with open(file_path, "rb") as f:
                    file_data = f.read()
                input_part = [{"mime_type": "application/pdf", "data": file_data}]
            else:
                img = Image.open(file_path)
                input_part = [img]

            prompt = f"Sen YKS derece koçusun (Deniz Yılmaz). Bu {ders} - {konu_ipucu} sorusunu incele. Alt konularını, çözüm yöntemini ve öğrenciye özel koçluk tavsiyeni çıkar."
            response = model.generate_content(input_part + [prompt])
            return response.text
        except Exception as e:
            return f"⚠️ **Yapay Zeka Hatası:** {str(e)}"
    return f"🔍 **Soru Konu Analizi ({ders}):**\n• **Konu:** {konu_ipucu}\n• **Koç Notu:** Soru kökündeki temel işlem basamakları kontrol edilmelidir."

def ai_karne_detayli_analiz_et(file_path, yayin, tur, toplam_net):
    api_key = SABIT_GEMINI_API_KEY.strip()
    if GENAI_AVAILABLE and api_key and api_key != "AIzaSy..." and os.path.exists(file_path):
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            if file_path.lower().endswith('.pdf'):
                with open(file_path, "rb") as f:
                    file_data = f.read()
                input_part = [{"mime_type": "application/pdf", "data": file_data}]
            else:
                img = Image.open(file_path)
                input_part = [img]

            prompt = f"Sen YKS baş koçusun (Deniz Yılmaz). Öğrencinin yüklediği '{yayin}' adlı {tur} karnesini/sonuç belgesini görsel olarak detaylıca incele. Toplam Net: {toplam_net}. Ders ders, konu konu hangi başlıklarda hata yaptığını, netlerini artırmak için hangi eksiklerini acilen kapatması gerektiğini maddeler halinde, motive edici ve çok kapsamlı bir koçluk raporu olarak hazırla."
            response = model.generate_content(input_part + [prompt])
            return response.text
        except Exception as e:
            return f"⚠️ **Yapay Zeka Karne Analiz Hatası:** {str(e)}"
    return f"📊 **Koçluk Deneme Analizi ({yayin}):**\n• Toplam Net: {toplam_net}\n• **Tavsiye:** Eksik olduğun konuları tespit edip o konuların tekrarını yapmalısın."

MOTIVASYON_SOZLERI = [
    "🌿 Sakin ol, derin bir nefes al ve adım adım ilerle. Disiplin başarıyı getirir!",
    "🚀 Başarı, her gün ertelemeden tekrarlanan küçük çabaların birikimidir!",
    "🎓 Bugün döktüğün her damla alın teri, hayalindeki okulun kapısını açar!"
]

YOK_ATLAS_UNI_BOLUM_VERITABANI = {
    "Orta Doğu Teknik Üniversitesi (ODTÜ)": {
        "Computer Engineering / Bilgisayar Mühendisliği (SAY)": {"taban_net": 113.5, "tavan_net": 118.5, "taban_sira": "520", "tavan_sira": "15"},
        "Endüstri Mühendisliği (SAY)": {"taban_net": 110.0, "tavan_net": 116.5, "taban_sira": "1.450", "tavan_sira": "65"},
    },
    "Boğaziçi Üniversitesi (İstanbul)": {
        "Computer Engineering / Bilgisayar Mühendisliği (SAY)": {"taban_net": 114.5, "tavan_net": 119.0, "taban_sira": "280", "tavan_sira": "1"},
        "Endüstri Mühendisliği (SAY)": {"taban_net": 111.0, "tavan_net": 117.5, "taban_sira": "1.100", "tavan_sira": "45"},
    }
}

YOK_ATLAS_UNIVERSTITELER = sorted(list(YOK_ATLAS_UNI_BOLUM_VERITABANI.keys()) + ["Boğaziçi Üniversitesi (İstanbul)", "İstanbul Teknik Üniversitesi (İTÜ)", "Orta Doğu Teknik Üniversitesi (ODTÜ)", "Hacettepe Üniversitesi (Ankara)"])
GENEL_BOLUM_LISTESI = sorted(["Tıp Fakültesi (SAY)", "Computer Engineering / Bilgisayar Mühendisliği (SAY)", "Hukuk Fakültesi (EA)", "Psikoloji (EA)"])

TYT_KONULAR = {
    "⚡ 📖 Paragraf + 📐 Problem Rutini": ["Paragraf (25s) + Problem (20s) Günlük Rutin"],
    "📖 TYT Türkçe": ["Sözcükte Anlam", "Cümlede Anlam", "Paragrafta Anlam ve Yapı", "Yazım Kuralları"],
    "📐 TYT Matematik": ["Temel Kavramlar", "Problemler", "Fonksiyonlar"],
    "📏 TYT Geometri": ["Üçgenler", "Çokgenler ve Dörtgenler"],
    "⚡ TYT Fizik": ["Basınç", "Isı Sıcaklık", "Optik"],
    "🧪 TYT Kimya": ["Kimya Bilimi", "Karışımlar"],
    "🧬 TYT Biyoloji": ["Hücre ve Organeller", "Kalıtım"]
}

AYT_KONULAR = {
    "📐 AYT Matematik": ["Polinomlar", "Logaritma", "Trigonometri", "Türev", "İntegral"],
    "📏 AYT Geometri": ["Analitik Geometri", "Çember"],
    "⚡ AYT Fizik": ["Atışlar & İtme-Momentum", "Elektromanyetizma"],
    "🧪 TYT Kimya": ["Gazlar", "Organik Kimya"],
    "🧬 TYT Biyoloji": ["İnsan Fizyolojisi", "Fotosentez"]
}

LGS_KONULAR = {
    "📖 LGS Türkçe (20 Soru)": ["Fiilimsiler", "Sözel Mantık"],
    "📐 LGS Matematik (20 Soru)": ["Üslü İfadeler", "Kareköklü İfadeler"]
}

GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]

conn = sqlite3.connect(DB_FILE, check_same_thread=False, timeout=20)
cursor = conn.cursor()
cursor.execute("PRAGMA journal_mode=WAL;")

cursor.execute("""
CREATE TABLE IF NOT EXISTS ogrenciler (
    ad_soyad TEXT PRIMARY KEY,
    sifre TEXT,
    veli_pin TEXT DEFAULT '123456',
    sinav_turu TEXT DEFAULT 'TYT (Sadece TYT Çalışması)',
    hedef_il TEXT DEFAULT 'İstanbul',
    koc_adi TEXT DEFAULT '',
    hedef_uni TEXT DEFAULT '',
    hedef_bolum TEXT DEFAULT '',
    hedef_net FLOAT DEFAULT 80.0,
    hedef_sira TEXT DEFAULT '',
    program_guncellendi_mi INTEGER DEFAULT 0
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
CREATE TABLE IF NOT EXISTS yapilamayan_sorular (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_soyad TEXT,
    tarih TEXT,
    ders TEXT,
    konu TEXT,
    dosya_yolu TEXT,
    dosya_adi TEXT
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

cursor.execute("""
CREATE TABLE IF NOT EXISTS excel_program_matris (
    ad_soyad TEXT,
    saat_araligi TEXT,
    pazartesi TEXT DEFAULT '',
    sali TEXT DEFAULT '',
    carsamba TEXT DEFAULT '',
    persembe TEXT DEFAULT '',
    cuma TEXT DEFAULT '',
    cumartesi TEXT DEFAULT '',
    pazar TEXT DEFAULT '',
    PRIMARY KEY (ad_soyad, saat_araligi)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS program_dosyalari (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_soyad TEXT,
    yukleyen TEXT,
    tarih TEXT,
    dosya_yolu TEXT,
    dosya_adi TEXT
)
""")
conn.commit()

cursor.execute("SELECT COUNT(*) FROM koclar")
if cursor.fetchone()[0] == 0:
    cursor.execute("INSERT INTO koclar (kullanici_adi, sifre) VALUES (?, ?)", ("koc1", make_hash("Koc123!")))
    conn.commit()

query_params = st.query_params
link_ogrenci = query_params.get("ogrenci", None)

st.markdown("""
<div style="text-align: center; padding: 10px 0 15px 0;">
    <span style="font-size: 42px;">🎓</span>
    <h1 style="margin: 0; font-weight: 800; font-size: 26px; color: #0f172a;">YKS (TYT/AYT) - LGS KOÇLUK</h1>
    <p style="margin: 0; font-size: 14px; color: #0284c7; font-weight: 700;">DENİZ YILMAZ GELİŞİM PLATFORMU</p>
</div>
""", unsafe_allow_html=True)

if link_ogrenci:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 18px 24px; border-radius: 16px; margin-bottom: 20px;">
        <h3 style="margin:0; font-size:20px; font-weight:800; color:white !important;">👨‍🏫 Öğretmen Soru İnceleme Ekranı</h3>
        <p style="margin:4px 0 0 0; opacity:0.9; color:white !important;"><strong>{link_ogrenci}</strong> öğrencisinin çözemediği ve destek beklediği tüm sorular listelenmektedir.</p>
    </div>
    """, unsafe_allow_html=True)
    
    df_link_sorular = pd.read_sql_query("SELECT id, tarih, ders, konu, dosya_yolu, dosya_adi FROM yapilamayan_sorular WHERE ad_soyad = ? ORDER BY id DESC", conn, params=(link_ogrenci,))
    
    if df_link_sorular.empty:
        st.info(f"ℹ️ {link_ogrenci} isimli öğrenci henüz çözemediği soru yüklememiştir.")
    else:
        for _, s_data in df_link_sorular.iterrows():
            st.markdown(f"#### 📌 {s_data['ders']} — {s_data['konu']} <span style='font-size:12px; color:#64748b;'>({s_data['tarih']})</span>", unsafe_allow_html=True)
            if os.path.exists(s_data['dosya_yolu']):
                if s_data['dosya_yolu'].lower().endswith(('png', 'jpg', 'jpeg')):
                    st.image(s_data['dosya_yolu'], width=400)
                elif s_data['dosya_yolu'].lower().endswith('.pdf'):
                    st.markdown(pdf_goster_html(s_data['dosya_yolu']), unsafe_allow_html=True)
            st.markdown(f'<div class="ai-analysis-box">{ai_soru_gorseli_analiz_et(s_data["dosya_yolu"], s_data["ders"], s_data["konu"])}</div>', unsafe_allow_html=True)
            st.divider()

    if st.button("⬅️ Koçluk Platformu Ana Sayfasına Dön", use_container_width=True):
        st.query_params.clear()
        st.rerun()

else:
    main_tab1, main_tab2, main_tab3 = st.tabs([
        "👨‍🎓 ÖĞRENCİ PANELİ",
        "👨‍🏫 KOÇ YÖNETİM PANELİ",
        "👨‍👩‍👧‍👦 VELİ TAKİP EKRANI"
    ])

    with main_tab1:
        aktif_ogr = st.session_state.get("aktif_ogrenci", None)

        if not aktif_ogr:
            st.markdown("<h3 style='font-weight:700; font-size:18px;'>👨‍🎓 Öğrenci Giriş & Kayıt Paneli</h3>", unsafe_allow_html=True)
            tab_ogr_login, tab_ogr_register = st.tabs(["🔑 GİRİŞ YAP", "➕ YENİ ÖĞRENCİ HESABI OLUŞTUR"])

            with tab_ogr_login:
                with st.form("ogrenci_giris_formu"):
                    login_ad = st.text_input("Adınız ve Soyadınız:").strip().title()
                    login_sifre = st.text_input("Öğrenci Şifreniz / PIN:", type="password")
                    if st.form_submit_button("Giriş Yap", type="primary", use_container_width=True):
                        if login_ad and login_sifre:
                            cursor.execute("SELECT sifre FROM ogrenciler WHERE ad_soyad = ?", (login_ad,))
                            usr = cursor.fetchone()
                            if usr and verify_hash(login_sifre, usr[0]):
                                st.session_state["aktif_ogrenci"] = login_ad
                                st.success(f"🔓 Hoş geldin {login_ad}!")
                                st.rerun()
                            else:
                                st.error("❌ Hatalı ad soyad veya şifre!")

            with tab_ogr_register:
                cursor.execute("SELECT kullanici_adi FROM koclar")
                koc_listesi = [r[0] for r in cursor.fetchall()] or ["koc1"]
                with st.form("ogrenci_kayit_formu"):
                    reg_ad = st.text_input("Adınız ve Soyadınız:").strip().title()
                    reg_sifre = st.text_input("Şifre Belirleyin:", type="password")
                    reg_vpin = st.text_input("👨‍👩‍👧‍👦 Veli PIN Kodu:", value="123456")
                    reg_sinav = st.selectbox("🎓 Hazırlanılan Sınav:", ["TYT (Sadece TYT Çalışması)", "YKS (TYT + AYT)", "LGS (8. Sınıf)"])
                    reg_koc = st.selectbox("👨‍🏫 Sorumlu Koçunuz:", koc_listesi)

                    if st.form_submit_button("Hesabımı Oluştur", type="primary", use_container_width=True):
                        if reg_ad and reg_sifre:
                            cursor.execute("SELECT ad_soyad FROM ogrenciler WHERE ad_soyad = ?", (reg_ad,))
                            if cursor.fetchone():
                                st.error(f"⚠️ `{reg_ad}` zaten var!")
                            else:
                                cursor.execute("INSERT INTO ogrenciler (ad_soyad, sifre, veli_pin, sinav_turu, koc_adi) VALUES (?, ?, ?, ?, ?)",
                                               (reg_ad, make_hash(reg_sifre), reg_vpin, reg_sinav, reg_koc))
                                conn.commit()
                                st.session_state["aktif_ogrenci"] = reg_ad
                                st.success("🎉 Hesabınız oluşturuldu!")
                                st.rerun()
        else:
            col_o_head1, col_o_head2 = st.columns([0.8, 0.2])
            with col_o_head1:
                cursor.execute("SELECT sinav_turu FROM ogrenciler WHERE ad_soyad = ?", (aktif_ogr,))
                r_info = cursor.fetchone()
                ogr_sinav = r_info[0] if r_info else "TYT (Sadece TYT Çalışması)"
                st.success(f"👤 Aktif Oturum: **{aktif_ogr}** | Sınav Modu: **{ogr_sinav}**")
            with col_o_head2:
                if st.button("🚪 ÇIKIŞ YAP", key="ogr_logout_btn", use_container_width=True):
                    st.session_state["aktif_ogrenci"] = None
                    st.rerun()

            if "TYT (Sadece" in ogr_sinav: AKTIF_KONULAR = TYT_KONULAR
            elif "YKS" in ogr_sinav: AKTIF_KONULAR = {**TYT_KONULAR, **AYT_KONULAR}
            else: AKTIF_KONULAR = LGS_KONULAR

            AKTIF_DERSLER = list(AKTIF_KONULAR.keys())
            MAX_NET_LIMIT = 120.0 if "TYT" in ogr_sinav or "YKS" in ogr_sinav else 90.0

            tab_hedef, tab_program, tab_gunluk, tab_deneme, tab_konular = st.tabs([
                "🎯 OTOMATİK YÖK ATLAS HEDEFİ",
                "📅 DERS PROGRAMI (EXCEL / PDF)",
                "📝 GÜNLÜK ÇALIŞMA & SORU YÜKLEME",
                "📊 DENEMELER & KARNE YÜKLEME",
                "🗺️ KONU HAKİMİYETİ"
            ])

            with tab_deneme:
                st.markdown("<h3 style='font-weight:700; font-size:18px;'>📊 Deneme Sonuçları & Detaylı Yapay Zeka Koç Analizi</h3>", unsafe_allow_html=True)
                with st.form("deneme_form"):
                    cd1, cd2, cd3 = st.columns(3)
                    with cd1: yayin = st.text_input("Yayın / Deneme Adı:")
                    with cd2: d_tur = st.selectbox("Tür:", ["Genel Deneme", "Branş Denemesi"])
                    with cd3: toplam_net = st.number_input("Toplam Netiniz:", 0.0, float(MAX_NET_LIMIT), 75.0)
                    
                    karne_dosya = st.file_uploader("📄 Deneme Karnesi Görseli/PDF Yükle (Zorunlu / Yapay Zeka İçin):", type=["pdf", "png", "jpg", "jpeg"])
                    
                    if st.form_submit_button("Deneme Sonucunu ve Yapay Zeka Analizini Kaydet", type="primary", use_container_width=True) and yayin:
                        karne_path = "Dosya Yok"
                        AI_DENEME_RAPORU = "Karne yüklenmediği için yapay zeka analizi oluşturulamadı."
                        
                        if karne_dosya:
                            file_ext = os.path.splitext(karne_dosya.name)[1]
                            k_name = f"Karne_{aktif_ogr}_{str(datetime.date.today())}_{hashlib.md5(karne_dosya.name.encode()).hexdigest()[:6]}{file_ext}"
                            karne_path = os.path.join(KARNE_DIR, k_name)
                            with open(karne_path, "wb") as f: f.write(karne_dosya.getbuffer())

                            # YAPAY ZEKA GÖRSEL KARNE ANALİZİNİ ÇALIŞTIR
                            AI_DENEME_RAPORU = ai_karne_detayli_analiz_et(karne_path, yayin, d_tur, toplam_net)

                        cursor.execute("INSERT INTO denemeler (ad_soyad, tarih, yayin, tur, toplam_net, dosya_adi, koc_notu) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                       (aktif_ogr, str(datetime.date.today()), yayin, d_tur, float(toplam_net), karne_path, AI_DENEME_RAPORU))
                        conn.commit()
                        st.success("🎉 Deneme karneniz yapay zeka tarafından incelendi ve rapor oluşturuldu!")
                        st.rerun()

                st.divider()
                st.markdown("#### 📜 Geçmiş Denemeleriniz ve Yapay Zeka Koç Tavsiyeleri")
                df_ogr_denemeler = pd.read_sql_query("SELECT id, tarih, yayin, tur, toplam_net, dosya_adi, koc_notu FROM denemeler WHERE ad_soyad = ? ORDER BY id DESC", conn, params=(aktif_ogr,))
                if df_ogr_denemeler.empty:
                    st.info("Henüz kaydedilmiş bir denemeniz bulunmuyor.")
                else:
                    for _, d_row in df_ogr_denemeler.iterrows():
                        st.markdown(f"""
                        <div class="calc-card" style="margin-bottom: 12px;">
                            <div style="font-weight:800; font-size:16px; color:#1e293b;">📌 {d_row['yayin']} ({d_row['tur']}) — Net: {d_row['toplam_net']} <span style="font-size:12px; color:#64748b; font-weight:500;">({d_row['tarih']})</span></div>
                        """, unsafe_allow_html=True)
                        
                        if d_row['dosya_adi'] != "Dosya Yok" and os.path.exists(d_row['dosya_adi']):
                            col_f1, col_f2 = st.columns(2)
                            with col_f1:
                                with open(d_row['dosya_adi'], "rb") as f_kd:
                                    st.download_button(f"📥 Karneyi İndir", data=f_kd, file_name=d_row['dosya_adi'], key=f"dl_ogr_karne_{d_row['id']}")
                            with col_f2:
                                if d_row['dosya_adi'].lower().endswith(('.png', '.jpg', '.jpeg')):
                                    st.image(d_row['dosya_adi'], width=300, caption="Yüklenen Karne Önizlemesi")
                                elif d_row['dosya_adi'].lower().endswith('.pdf'):
                                    st.markdown(pdf_goster_html(d_row['dosya_adi']), unsafe_allow_html=True)

                        st.markdown(f"""
                            <div class="ai-analysis-box" style="margin-top: 10px;">
                                <strong>🤖 Yapay Zeka Detaylı Deneme Koçluk Raporu:</strong><br>
                                {d_row['koc_notu']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

    with main_tab2:
        st.markdown("<h2 style='font-weight:800; font-size:24px; color:#0f172a;'>👨‍🏫 Koç Yönetim Paneli</h2>", unsafe_allow_html=True)
        if "aktif_koc" not in st.session_state: st.session_state["aktif_koc"] = None

        if not st.session_state["aktif_koc"]:
            with st.form("koc_giris_formu"):
                k_adi_giris = st.text_input("Koç Kullanıcı Adı:").strip()
                k_sifre_giris = st.text_input("Şifre:", type="password")
                if st.form_submit_button("Koç Paneline Giriş Yap", type="primary", use_container_width=True):
                    cursor.execute("SELECT sifre FROM koclar WHERE kullanici_adi = ?", (k_adi_giris,))
                    row = cursor.fetchone()
                    if row and verify_hash(k_sifre_giris, row[0]):
                        st.session_state["aktif_koc"] = k_adi_giris
                        st.rerun()
                    else: st.error("❌ Hatalı giriş!")
        else:
            if st.button("🚪 KOÇ ÇIKIŞ YAP"):
                st.session_state["aktif_koc"] = None
                st.rerun()

            cursor.execute("SELECT ad_soyad FROM ogrenciler")
            ogrenci_rows = cursor.fetchall()
            if ogrenci_rows:
                ogr_dict = {r[0]: r[0] for r in ogrenci_rows}
                secilen_ogr = st.selectbox("🔍 Öğrenci Seçin:", list(ogr_dict.keys()))

                st.divider()
                st.markdown(f"### 📊 {secilen_ogr} — Öğrenci Deneme Analizleri & Karneleri")
                df_koc_denemeler = pd.read_sql_query("SELECT id, tarih, yayin, tur, toplam_net, dosya_adi, koc_notu FROM denemeler WHERE ad_soyad = ? ORDER BY id DESC", conn, params=(secilen_ogr,))
                
                if df_koc_denemeler.empty:
                    st.info("Öğrenci henüz deneme sonucu kaydetmemiştir.")
                else:
                    for _, kd_row in df_koc_denemeler.iterrows():
                        st.markdown(f"""
                        <div class="calc-card" style="margin-bottom: 15px;">
                            <div style="font-weight:800; font-size:16px; color:#1e293b;">📈 {kd_row['yayin']} ({kd_row['tur']}) — Net: {kd_row['toplam_net']} <span style="font-size:12px; color:#64748b;">({kd_row['tarih']})</span></div>
                        """, unsafe_allow_html=True)
                        
                        if kd_row['dosya_adi'] != "Dosya Yok" and os.path.exists(kd_row['dosya_adi']):
                            col_f1, col_f2 = st.columns(2)
                            with col_f1:
                                with open(kd_row['dosya_adi'], "rb") as f_kd:
                                    st.download_button(f"📥 Karneyi İndir", data=f_kd, file_name=kd_row['dosya_adi'], key=f"dl_koc_karne_{kd_row['id']}")
                            with col_f2:
                                if kd_row['dosya_adi'].lower().endswith(('.png', '.jpg', '.jpeg')):
                                    st.image(kd_row['dosya_adi'], width=300, caption="Yüklenen Karne Önizlemesi")
                                elif kd_row['dosya_adi'].lower().endswith('.pdf'):
                                    st.markdown(pdf_goster_html(kd_row['dosya_adi']), unsafe_allow_html=True)
                        
                        st.markdown(f"""
                            <div class="ai-analysis-box" style="margin-top: 10px;">
                                <strong>🤖 Yapay Zeka Detaylı Deneme Koçluk Raporu:</strong><br>
                                {kd_row['koc_notu']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)