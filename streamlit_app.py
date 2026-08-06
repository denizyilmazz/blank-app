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
</style>
""", unsafe_allow_html=True)

SABIT_GEMINI_API_KEY = "AQ.Ab8RN6Iu0rNJR14IpQDnEyaXDJPMFnkgaOBn4lZ8j2qZrysa6A"
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
                with open(file_path, "rb") as f: file_data = f.read()
                input_part = [{"mime_type": "application/pdf", "data": file_data}]
            else:
                img = Image.open(file_path)
                input_part = [img]
            prompt = f"Sen YKS derece koçusun (Deniz Yılmaz). Bu {ders} - {konu_ipucu} sorusunu incele. Alt konularını ve çözüm yöntemini açıkla."
            response = model.generate_content(input_part + [prompt])
            return response.text
        except Exception as e:
            return f"⚠️ **Yapay Zeka Hatası:** {str(e)}"
    return f"🔍 **Soru Konu Analizi ({ders}):**\n• **Konu:** {konu_ipucu}\n• **Koç Notu:** Temel işlem basamakları kontrol edilmelidir."

def ai_deneme_detayli_analiz_et(yayin, tur, toplam_net, ders_netleri_ozeti):
    api_key = SABIT_GEMINI_API_KEY.strip()
    if GENAI_AVAILABLE and api_key and api_key != "AIzaSy...":
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"Sen YKS baş koçusun (Deniz Yılmaz). Öğrencinin '{yayin}' adlı {tur} sonucunu analiz et. Toplam Net: {toplam_net}. Net dağılımı: {ders_netleri_ozeti}. Eksik konuları ve tavsiyeleri açıkla."
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"⚠️ **Yapay Zeka Analiz Hatası:** {str(e)}"
    return f"📊 **Koçluk Deneme Analizi ({yayin}):**\n• Toplam Net: {toplam_net}\n• **Tavsiye:** Eksik konuları tekrar etmelisin."

MOTIVASYON_SOZLERI = [
    "🌿 Sakin ol, derin bir nefes al ve adım adım ilerle. Disiplin başarıyı getirir!",
    "🚀 Başarı, her gün ertelemeden tekrarlanan küçük çabaların birikimidir!",
    "🎓 Bugün döktüğün her damla alın teri, hayalindeki okulun kapısını açar!"
]

# Müfredat ve Dinlenme Aktiviteleri İçeren Kapsamlı Veritabanı
YKS_KAPSAMLI_DERS_KONULAR = {
    "☕ Mola & Dinlenme": [
        "Kısa Dinlenme & Zihin Molası (10-15 dk)",
        "Göz Dinlendirme & Su Molası",
        "Müzik Dinleme & Rahatlama",
        "Serbest Zaman & Sosyal Medya Molası"
    ],
    "🚶‍♂️ Yürüyüş & Aktivite": [
        "Tempolu Açık Hava Yürüyüşü (30 dk)",
        "Hafif Esneme & Pilates Hareketleri",
        "Temiz Hava Alma & Fiziksel Aktivite"
    ],
    "🍲 Öğle & Akşam Yemeği": [
        "Öğle Yemeği & Dinlenme Arası",
        "Akşam Yemeği & Aile Zamanı",
        "Ana Öğün & Kahve/Çay Molası"
    ],
    "⚡ 📖 Paragraf + 📐 Problem Rutini": [
        "Paragraf Hız Kampı (25 Soru)", 
        "Sözel Mantık Rutini", 
        "Yeni Nesil Problemler (20 Soru)", 
        "Sayı-Kesir Problemleri", 
        "Yaş & İşçi Havuz Problemleri", 
        "Yüzde-Kar/Zarar & Karışım", 
        "Hız & Hareket Problemleri", 
        "Grafik & Rutin Olmayan Problemler"
    ],
    "📖 TYT Türkçe": [
        "Sözcükte Anlam", "Cümlede Anlam", "Paragrafta Anlam ve Yapı", 
        "Ses Bilgisi", "Yazım Kuralları", "Noktalama İşaretleri", 
        "Sözcük Türleri", "Fiiller & Fiilimsi", "Cümlenin Ögeleri", "Anlatım Bozuklukları"
    ],
    "📐 TYT Matematik": [
        "Temel Kavramlar", "Sayı Basamakları", "Bölme ve Bölünebilme", 
        "EBOB - EKOK", "Rasyonel Sayılar", "Basit Eşitsizlikler", 
        "Mutlak Değer", "Üslü İfadeler", "Köklü İfadeler", 
        "Çarpanlara Ayırma", "Oran - Orantı", "Denklem Çözme", 
        "Kümeler", "Fonksiyonlar", "Veri, Sayma ve Olasılık"
    ],
    "📏 TYT Geometri": [
        "Doğruda ve Üçgende Açılar", "Özel Üçgenler", 
        "Üçgende Açı-Kenar & Benzerlik", "Üçgende Alan", 
        "Çokgenler ve Dörtgenler", "Özel Dörtgenler (Kare, Dikdörtgen vb.)", 
        "Çember ve Daire", "Katı Cisimler", "Analitik Geometri"
    ],
    "⚡ TYT Fizik": [
        "Fizik Bilimine Giriş", "Madde ve Özellikleri", "Basınç ve Kaldırma Kuvveti", 
        "Isı, Sıcaklık ve Genleşme", "Hareket ve Kuvvet", "Newton Yasaları", 
        "İş, Güç ve Enerji", "Elektrik", "Manyetizma", "Dalgalar", "Optik"
    ],
    "🧪 TYT Kimya": [
        "Kimya Bilimi", "Atom ve Periyodik Sistem", "Türler Arası Etkileşimler", 
        "Maddenin Halleri", "Kimyanın Temel Kanunları", 
        "Kimyasal Hesaplamalar", "Karışımlar", "Asitler, Bazlar ve Tuzlar"
    ],
    "🧬 TYT Biyoloji": [
        "Canlıların Ortak Özellikleri & Temel Bileşenler", "Hücre ve Organelleri", 
        "Madde Geçişleri", "Hücre Bölünmeleri (Mitoz / Mayoz)", 
        "Kalıtım", "Ekoloji"
    ],
    "📜 TYT Tarih": [
        "Tarih Bilimi", "İlk Çağ Medeniyetleri", "İslamiyet Tarihi", 
        "Osmanlı Kuruluş ve Yükselme", "Osmanlı Kültür ve Medeniyeti", 
        "Milli Mücadele Dönemi", "Atatürk İnkılap ve İlkeleri"
    ],
    "🌍 TYT Coğrafya": [
        "Doğa ve İnsan & Harita Bilgisi", "İklim Bilgisi", 
        "İç ve Dış Kuvvetler", "Nüfus ve Yerleşme", "Afetler"
    ],
    "🧠 TYT Felsefe": [
        "Felsefeyi Tanıma", "Bilgi Felsefesi", "Varlık Felsefesi", 
        "Ahlak Felsefesi", "Din, Siyaset ve Sanat Felsefesi"
    ],
    "🕌 TYT Din Kültürü": [
        "İnanç", "İbadet", "Ahlak ve Değerler", "Hz. Muhammed'in Hayatı"
    ],
    "📐 AYT Matematik": [
        "İkinci Dereceden Denklemler & Karmaşık Sayılar", "Parabol", 
        "Eşitsizlikler", "Trigonometri", "Logaritma", "Diziler", 
        "Limit ve Süreklilik", "Türev", "İntegral ve Alan"
    ],
    "⚡ AYT Fizik": [
        "Vektörler & Bağıl Hareket", "Dinamik (Newton)", "Atışlar", 
        "İş, Güç, Enerji", "İtme ve Momentum", "Tork ve Denge", 
        "Çembersel Hareket", "Basit Harmonik Hareket", "Dalga Mekaniği", 
        "Elektrik Alan & Potansiyel", "Manyetizma", "Modern Fizik"
    ],
    "🧪 AYT Kimya": [
        "Modern Atom Teorisi", "Gazlar", "Sıvı Çözeltiler", 
        "Kimyasal Tepkimelerde Enerji", "Hız ve Denge", 
        "Sulu Çözeltilerde Denge (Asit-Baz / KÇ)", "Elektrokimya", 
        "Organik Kimya (Hidrokarbonlar ve Fonksiyonel Gruplar)"
    ],
    "🧬 AYT Biyoloji": [
        "Sinir ve Endokrin Sistem", "Duyu Organları", "Destek ve Hareket / Sindirim / Dolaşım", 
        "Solunum ve Boşaltım / Üreme Sistemi", "Nükleik Asitler ve Protein Sentezi", 
        "Fotosentez ve Solunum", "Bitki Biyolojisi"
    ],
    "📖 AYT Edebiyat": [
        "İslamiyet Öncesi ve Halk Edebiyatı", "Divan Edebiyatı", 
        "Tanzimat ve Servet-i Fünun", "Milli Edebiyat ve Cumhuriyet Dönemi Şiir", 
        "Cumhuriyet Dönemi Roman ve Hikaye"
    ]
}

YOK_ATLAS_UNI_BOLUM_VERITABANI = {
    "Orta Doğu Teknik Üniversitesi (ODTÜ)": {
        "Computer Engineering / Bilgisayar Mühendisliği (SAY)": {"taban_net": 113.5, "tavan_net": 118.5, "taban_sira": "520", "tavan_sira": "15"},
        "Endüstri Mühendisliği (SAY)": {"taban_net": 110.0, "tavan_net": 116.5, "taban_sira": "1.450", "tavan_sira": "65"}
    },
    "Boğaziçi Üniversitesi (İstanbul)": {
        "Computer Engineering / Bilgisayar Mühendisliği (SAY)": {"taban_net": 114.5, "tavan_net": 119.0, "taban_sira": "280", "tavan_sira": "1"}
    }
}

YOK_ATLAS_UNIVERSTITELER = sorted(list(YOK_ATLAS_UNI_BOLUM_VERITABANI.keys()) + ["Boğaziçi Üniversitesi (İstanbul)", "Orta Doğu Teknik Üniversitesi (ODTÜ)", "İstanbul Teknik Üniversitesi (İTÜ)"])
GENEL_BOLUM_LISTESI = ["Tıp Fakültesi (SAY)", "Computer Engineering / Bilgisayar Mühendisliği (SAY)", "Hukuk Fakültesi (EA)"]

TYT_KONULAR = {
    "⚡ 📖 Paragraf + 📐 Problem Rutini": ["Paragraf (25s) + Problem (20s) Günlük Rutin"],
    "📖 TYT Türkçe": ["Sözcükte Anlam", "Cümlede Anlam", "Paragrafta Anlam ve Yapı"],
    "📐 TYT Matematik": ["Temel Kavramlar", "Sayı Basamakları", "Problemler"]
}

AYT_KONULAR = {
    "📐 AYT Matematik": ["Polinomlar", "Logaritma", "Trigonometri", "Türev", "İntegral"]
}

LGS_KONULAR = {
    "📖 LGS Türkçe (20 Soru)": ["Fiilimsiler", "Sözel Mantık"],
    "📐 LGS Matematik (20 Soru)": ["Çarpanlar ve Katlar", "Üslü İfadeler"]
}

conn = sqlite3.connect(DB_FILE, check_same_thread=False, timeout=20)
cursor = conn.cursor()
cursor.execute("PRAGMA journal_mode=WAL;")

cursor.execute("""
CREATE TABLE IF NOT EXISTS ogrenciler (
    ad_soyad TEXT PRIMARY KEY,
    sifre TEXT,
    veli_pin TEXT DEFAULT '123456',
    sinav_turu TEXT DEFAULT 'TYT (Sadece TYT Çalışması)',
    hedef_uni TEXT DEFAULT '',
    hedef_bolum TEXT DEFAULT '',
    hedef_net FLOAT DEFAULT 80.0,
    hedef_sira TEXT DEFAULT ''
)
""")

cursor.execute("CREATE TABLE IF NOT EXISTS koclar (kullanici_adi TEXT PRIMARY KEY, sifre TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS gunluk_calisma (id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT, tarih TEXT, ders TEXT, konu TEXT DEFAULT 'Genel Soru', toplam_soru INTEGER, dogru INTEGER, yanlis INTEGER, bos INTEGER, sure FLOAT, verim INTEGER, notlar TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS yapilamayan_sorular (id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT, tarih TEXT, ders TEXT, konu TEXT, dosya_yolu TEXT, dosya_adi TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS denemeler (id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT, tarih TEXT, yayin TEXT, tur TEXT, toplam_net FLOAT, dosya_adi TEXT, koc_notu TEXT DEFAULT '')")
cursor.execute("CREATE TABLE IF NOT EXISTS konu_puanlari (ad_soyad TEXT, konu_adi TEXT, puan INTEGER, PRIMARY KEY (ad_soyad, konu_adi))")
cursor.execute("CREATE TABLE IF NOT EXISTS excel_program_matris (ad_soyad TEXT, saat_araligi TEXT, pazartesi TEXT DEFAULT '', sali TEXT DEFAULT '', carsamba TEXT DEFAULT '', persembe TEXT DEFAULT '', cuma TEXT DEFAULT '', cumartesi TEXT DEFAULT '', pazar TEXT DEFAULT '', PRIMARY KEY (ad_soyad, saat_araligi))")
cursor.execute("CREATE TABLE IF NOT EXISTS program_dosyalari (id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT, yukleyen TEXT, tarih TEXT, dosya_yolu TEXT, dosya_adi TEXT)")
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
        <p style="margin:4px 0 0 0; opacity:0.9; color:white !important;"><strong>{link_ogrenci}</strong> öğrencisinin çözemediği sorular listelenmektedir.</p>
    </div>
    """, unsafe_allow_html=True)
    
    df_link_sorular = pd.read_sql_query("SELECT id, tarih, ders, konu, dosya_yolu, dosya_adi FROM yapilamayan_sorular WHERE ad_soyad = ? ORDER BY id DESC", conn, params=(link_ogrenci,))
    if df_link_sorular.empty:
        st.info(f"ℹ️ {link_ogrenci} henüz soru yüklemedi.")
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

    if st.button("⬅️ Ana Sayfaya Dön", use_container_width=True):
        st.query_params.clear()
        st.rerun()

else:
    main_tab1, main_tab2, main_tab3 = st.tabs([
        "👨‍🎓 ÖĞRENCİ PANELİ",
        "👨‍🏫 KOÇ YÖNETİM PANELİ",
        "👨‍👩‍👧‍👦 VELİ TAKİP EKRANI"
    ])

    with main_tab1:
        if "motivasyon_goster" not in st.session_state: st.session_state["motivasyon_goster"] = True
        if "motivasyon_sozu" not in st.session_state: st.session_state["motivasyon_sozu"] = random.choice(MOTIVASYON_SOZLERI)
            
        if st.session_state["motivasyon_goster"]:
            m_col1, m_col2 = st.columns([0.9, 0.1])
            with m_col1:
                st.markdown(f'''
                <div class="hero-motivation-card">
                    <div style="font-size:11px; letter-spacing:2px; font-weight:800; color:rgba(255,255,255,0.85); margin-bottom:4px;">⚡ GÜNÜN MOTİVASYON MESAJI</div>
                    <div style="font-size:16px; font-weight:800;">"{st.session_state['motivasyon_sozu']}"</div>
                </div>
                ''', unsafe_allow_html=True)
            with m_col2:
                if st.button("❌", key="kapat_motivasyon", use_container_width=True):
                    st.session_state["motivasyon_goster"] = False
                    st.rerun()
        
        aktif_ogr = st.session_state.get("aktif_ogrenci", None)

        if not aktif_ogr:
            st.markdown("<h3 style='font-weight:700; font-size:18px;'>👨‍🎓 Öğrenci Giriş & Kayıt Paneli</h3>", unsafe_allow_html=True)
            tab_ogr_login, tab_ogr_register = st.tabs(["🔑 GİRİŞ YAP", "➕ YENİ HESAP OLUŞTUR"])

            with tab_ogr_login:
                with st.form("ogrenci_giris_formu"):
                    login_ad = st.text_input("Adınız ve Soyadınız:").strip().title()
                    login_sifre = st.text_input("Şifre / PIN:", type="password")
                    if st.form_submit_button("Giriş Yap", type="primary", use_container_width=True):
                        if login_ad and login_sifre:
                            cursor.execute("SELECT sifre FROM ogrenciler WHERE ad_soyad = ?", (login_ad,))
                            usr = cursor.fetchone()
                            if usr and verify_hash(login_sifre, usr[0]):
                                st.session_state["aktif_ogrenci"] = login_ad
                                st.rerun()
                            else:
                                st.error("❌ Hatalı ad veya şifre!")

            with tab_ogr_register:
                with st.form("ogrenci_kayit_formu"):
                    reg_ad = st.text_input("Adınız ve Soyadınız:").strip().title()
                    reg_sifre = st.text_input("Şifre Belirleyin:", type="password")
                    reg_sinav = st.selectbox("Hazırlanılan Sınav:", ["TYT (Sadece TYT Çalışması)", "YKS (TYT + AYT)", "LGS (8. Sınıf)"])

                    if st.form_submit_button("Hesabımı Oluştur", type="primary", use_container_width=True):
                        if reg_ad and reg_sifre:
                            cursor.execute("SELECT ad_soyad FROM ogrenciler WHERE ad_soyad = ?", (reg_ad,))
                            if cursor.fetchone():
                                st.error(f"⚠️ `{reg_ad}` zaten kayıtlı!")
                            else:
                                cursor.execute("INSERT INTO ogrenciler (ad_soyad, sifre, sinav_turu) VALUES (?, ?, ?)",
                                               (reg_ad, make_hash(reg_sifre), reg_sinav))
                                conn.commit()
                                st.session_state["aktif_ogrenci"] = reg_ad
                                st.rerun()
        else:
            col_o_head1, col_o_head2 = st.columns([0.8, 0.2])
            with col_o_head1:
                cursor.execute("SELECT sinav_turu, hedef_uni, hedef_bolum, hedef_net FROM ogrenciler WHERE ad_soyad = ?", (aktif_ogr,))
                r_info = cursor.fetchone()
                ogr_sinav = r_info[0] if r_info else "TYT (Sadece TYT Çalışması)"
                curr_uni = r_info[1] if (r_info and r_info[1]) else "Orta Doğu Teknik Üniversitesi (ODTÜ)"
                curr_bolum = r_info[2] if (r_info and r_info[2]) else "Endüstri Mühendisliği (SAY)"
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
                "🎯 YÖK ATLAS & ÖSYM",
                "📅 DERS PROGRAMI",
                "📝 GÜNLÜK ÇALIŞMA",
                "📊 DENEMELER",
                "🗺️ KONU HAKİMİYETİ"
            ])

            with tab_hedef:
                st.markdown(f"<h3 style='font-weight:700; font-size:18px;'>🎯 Üniversite Bazlı YÖK Atlas Net — {aktif_ogr}</h3>", unsafe_allow_html=True)
                col_h_u1, col_h_u2 = st.columns(2)
                with col_h_u1:
                    u_idx = YOK_ATLAS_UNIVERSTITELER.index(curr_uni) if curr_uni in YOK_ATLAS_UNIVERSTITELER else 0
                    secilen_hedef_uni = st.selectbox("Hedef Üniversite:", YOK_ATLAS_UNIVERSTITELER, index=u_idx)
                uni_bolumleri = YOK_ATLAS_UNI_BOLUM_VERITABANI.get(secilen_hedef_uni, {})
                kullanilabilir_bolumler = sorted(list(uni_bolumleri.keys())) if uni_bolumleri else GENEL_BOLUM_LISTESI
                with col_h_u2:
                    b_idx = kullanilabilir_bolumler.index(curr_bolum) if curr_bolum in kullanilabilir_bolumler else 0
                    secilen_hedef_bolum = st.selectbox("Hedef Bölüm:", kullanilabilir_bolumler, index=b_idx)

                if secilen_hedef_uni in YOK_ATLAS_UNI_BOLUM_VERITABANI and secilen_hedef_bolum in YOK_ATLAS_UNI_BOLUM_VERITABANI[secilen_hedef_uni]:
                    u_data = YOK_ATLAS_UNI_BOLUM_VERITABANI[secilen_hedef_uni][secilen_hedef_bolum]
                    otk_net, otk_sira = u_data["taban_net"], u_data["taban_sira"]
                else:
                    otk_net, otk_sira = 65.0, "120.000"

                st.markdown(f"""
                <div class="yok-net-box">
                    <div style="font-size:15px; font-weight:800; color:#1e40af; margin-bottom:6px;">🏛️ {secilen_hedef_uni} - {secilen_hedef_bolum}</div>
                    <div>🟢 Taban Net: <strong>{otk_net} Net</strong> | 📉 Taban Sıralama: <strong>İlk {otk_sira}</strong></div>
                </div>
                """, unsafe_allow_html=True)

                with st.form("hedef_form"):
                    ozel_net = st.number_input("Kişisel Net Hedefiniz:", 10.0, float(MAX_NET_LIMIT), float(otk_net), 0.5)
                    if st.form_submit_button("Hedefimi Kaydet", type="primary", use_container_width=True):
                        cursor.execute("UPDATE ogrenciler SET hedef_uni = ?, hedef_bolum = ?, hedef_net = ? WHERE ad_soyad = ?", 
                                       (secilen_hedef_uni, secilen_hedef_bolum, float(ozel_net), aktif_ogr))
                        conn.commit()
                        st.success("Hedef kaydedildi!")
                        st.rerun()

            with tab_program:
                st.markdown("### 📊 Haftalık Ders Programınız")
                df_p = pd.read_sql_query("SELECT saat_araligi AS 'Saat', pazartesi AS 'Pazartesi', sali AS 'Salı', carsamba AS 'Çarşamba', persembe AS 'Perşembe', cuma AS 'Cuma', cumartesi AS 'Cumartesi', pazar AS 'Pazar' FROM excel_program_matris WHERE ad_soyad = ?", conn, params=(aktif_ogr,))
                if not df_p.empty:
                    st.dataframe(df_p, use_container_width=True)
                else:
                    st.info("Koçunuz henüz haftalık programınızı oluşturmadı.")

                df_dosyalar = pd.read_sql_query("SELECT dosya_adi, dosya_yolu FROM program_dosyalari WHERE ad_soyad = ?", conn, params=(aktif_ogr,))
                for _, f_row in df_dosyalar.iterrows():
                    if os.path.exists(f_row['dosya_yolu']):
                        with open(f_row['dosya_yolu'], "rb") as fb:
                            st.download_button(f"📥 {f_row['dosya_adi']} İndir", data=fb, file_name=f_row['dosya_adi'])

            with tab_gunluk:
                st.markdown(f"### 📝 Günlük Çalışma Girişi — {aktif_ogr}")
                s_tarih = st.date_input("Tarih:", datetime.date.today())
                
                ders_sekmeleri = st.tabs(AKTIF_DERSLER)
                for idx, d_adi in enumerate(AKTIF_DERSLER):
                    with ders_sekmeleri[idx]:
                        s_konu = st.selectbox(f"Konu ({d_adi}):", ["Genel Soru Çözümü"] + AKTIF_KONULAR[d_adi], key=f"ks_{d_adi}")
                        ts = st.number_input(f"Toplam Soru ({d_adi}):", 0, 400, 0, key=f"ts_{d_adi}")
                        
                        yuklenen = st.file_uploader(f"📸 Çözülemeyen Soru Fotoğrafı ({d_adi}):", type=["png", "jpg", "jpeg"], key=f"up_{d_adi}")
                        if yuklenen and st.button(f"📤 Kaydet ({d_adi})", key=f"btn_{d_adi}"):
                            ext = os.path.splitext(yuklenen.name)[1]
                            fname = f"{aktif_ogr}_{s_tarih}_{hashlib.md5(yuklenen.name.encode()).hexdigest()[:6]}{ext}"
                            fpath = os.path.join(UPLOAD_DIR, fname)
                            with open(fpath, "wb") as f: f.write(yuklenen.getbuffer())
                            cursor.execute("INSERT INTO yapilamayan_sorular (ad_soyad, tarih, ders, konu, dosya_yolu, dosya_adi) VALUES (?, ?, ?, ?, ?, ?)",
                                           (aktif_ogr, str(s_tarih), d_adi, s_konu, fpath, yuklenen.name))
                            conn.commit()
                            st.success("Soru yüklendi!")

                if st.button("🚀 Çalışmaları Kaydet", type="primary", use_container_width=True):
                    st.success("Çalışmalarınız başarıyla kaydedildi!")

            with tab_deneme:
                st.markdown("### 📊 Denemeler & Yapay Zeka Koç Analizi")
                with st.form("deneme_ogr"):
                    dyayin = st.text_input("Yayın Adı:")
                    dnet = st.number_input("Toplam Net:", 0.0, float(MAX_NET_LIMIT), 75.0)
                    if st.form_submit_button("Analiz Et ve Kaydet", type="primary", use_container_width=True) and dyayin:
                        ai_rapor = ai_deneme_detayli_analiz_et(dyayin, "Genel Deneme", dnet, "Genel Dersler")
                        cursor.execute("INSERT INTO denemeler (ad_soyad, tarih, yayin, tur, toplam_net, koc_notu) VALUES (?, ?, ?, ?, ?, ?)",
                                       (aktif_ogr, str(datetime.date.today()), dyayin, "Genel Deneme", float(dnet), ai_rapor))
                        conn.commit()
                        st.success("Deneme kaydedildi!")

                df_d = pd.read_sql_query("SELECT yayin, toplam_net, koc_notu FROM denemeler WHERE ad_soyad = ?", conn, params=(aktif_ogr,))
                for _, row in df_d.iterrows():
                    st.markdown(f"""
                    <div class="calc-card">
                        <strong>📌 {row['yayin']} — Net: {row['toplam_net']}</strong>
                        <div class="ai-analysis-box">{row['koc_notu']}</div>
                    </div>
                    """, unsafe_allow_html=True)

            with tab_konular:
                st.markdown("### 🗺️ Konu Hakimiyeti Puanlama (1-5)")
                for d_adi, k_list in AKTIF_KONULAR.items():
                    st.markdown(f"**{d_adi}**")
                    for kn in k_list:
                        cursor.execute("SELECT puan FROM konu_puanlari WHERE ad_soyad = ? AND konu_adi = ?", (aktif_ogr, kn))
                        r = cursor.fetchone()
                        p_val = r[0] if r else 3
                        yp = st.select_slider(kn, options=[1, 2, 3, 4, 5], value=p_val, key=f"kp_{aktif_ogr}_{kn}")
                        cursor.execute("INSERT INTO konu_puanlari (ad_soyad, konu_adi, puan) VALUES (?, ?, ?) ON CONFLICT(ad_soyad, konu_adi) DO UPDATE SET puan = ?", (aktif_ogr, kn, yp, yp))
                    conn.commit()

    with main_tab2:
        st.markdown("## 👨‍🏫 Koç Yönetim Paneli")
        if "aktif_koc" not in st.session_state: st.session_state["aktif_koc"] = None

        if not st.session_state["aktif_koc"]:
            with st.form("koc_giris"):
                k_ad = st.text_input("Koç Kullanıcı Adı:")
                k_sif = st.text_input("Şifre:", type="password")
                if st.form_submit_button("Giriş Yap", type="primary"):
                    cursor.execute("SELECT sifre FROM koclar WHERE kullanici_adi = ?", (k_ad,))
                    r = cursor.fetchone()
                    if r and verify_hash(k_sif, r[0]):
                        st.session_state["aktif_koc"] = k_ad
                        st.rerun()
                    else: st.error("Hatalı!")
        else:
            if st.button("🚪 ÇIKIŞ YAP", key="koc_out"):
                st.session_state["aktif_koc"] = None
                st.rerun()

            cursor.execute("SELECT ad_soyad FROM ogrenciler")
            ogrs = [row[0] for row in cursor.fetchall()]
            if ogrs:
                secilen_ogr = st.selectbox("Yönetilecek Öğrenci:", ogrs)
                
                # ÖĞRENCİNİN YÜKLEDİĞİ SORULARI KOÇ EKRANINDA GÖSTERME ALANI
                st.markdown(f"### 📸 {secilen_ogr} — Öğrencinin Çözemediği Sorular")
                df_koc_sorular = pd.read_sql_query("SELECT id, tarih, ders, konu, dosya_yolu FROM yapilamayan_sorular WHERE ad_soyad = ? ORDER BY id DESC", conn, params=(secilen_ogr,))
                if df_koc_sorular.empty:
                    st.info(f"ℹ️ {secilen_ogr} henüz soru yüklemedi.")
                else:
                    for _, s_row in df_koc_sorular.iterrows():
                        st.markdown(f"**{s_row['ders']}** — {s_row['konu']} <span style='font-size:12px; color:#64748b;'>({s_row['tarih']})</span>", unsafe_allow_html=True)
                        if os.path.exists(s_row['dosya_yolu']):
                            if s_row['dosya_yolu'].lower().endswith(('png', 'jpg', 'jpeg')):
                                st.image(s_row['dosya_yolu'], width=350)
                            elif s_row['dosya_yolu'].lower().endswith('.pdf'):
                                st.markdown(pdf_goster_html(s_row['dosya_yolu']), unsafe_allow_html=True)
                        st.markdown(f'<div class="ai-analysis-box">{ai_soru_gorseli_analiz_et(s_row["dosya_yolu"], s_row["ders"], s_row["konu"])}</div>', unsafe_allow_html=True)
                        st.divider()

                # ÖĞRENCİNİN DENEME SONUÇLARI VE KARNELERİNİ KOÇ EKRANINDA GÖSTERME ALANI
                st.markdown(f"### 📊 {secilen_ogr} — Öğrenci Deneme Karneleri & Sonuçları")
                df_koc_denemeler = pd.read_sql_query("SELECT yayin, toplam_net, koc_notu, tarih FROM denemeler WHERE ad_soyad = ? ORDER BY id DESC", conn, params=(secilen_ogr,))
                if df_koc_denemeler.empty:
                    st.info(f"ℹ️ {secilen_ogr} henüz deneme sonucu kaydetmedi.")
                else:
                    for _, d_row in df_koc_denemeler.iterrows():
                        st.markdown(f"""
                        <div class="calc-card">
                            <strong>📌 {d_row['yayin']} — Toplam Net: {d_row['toplam_net']}</strong> <span style="font-size:12px; color:#64748b;">({d_row['tarih']})</span>
                            <div class="ai-analysis-box">{d_row['koc_notu']}</div>
                        </div>
                        """, unsafe_allow_html=True)

                # EXCEL TABLOSU GİBİ HÜCRELER ÜZERİNDEN SEÇİLEBİLEN HAFTALIK PROGRAM DÜZENLEYİCİ (MOLA VE YEMEKLER DAHİL)
                st.divider()
                st.markdown(f"### 🗓️ {secilen_ogr} — Excel Görünümlü Pratik Haftalık Program Matrisi")
                st.caption("⚡ Saat aralığını girip her gün (Pazartesi'den Pazar'a) için mola, yemek, yürüyüş veya YKS ders/konu seçenekleriyle hücreleri anında doldurabilirsin.")

                with st.form("saat_ekleme_formu"):
                    c_s1, c_s2 = st.columns(2)
                    with c_s1:
                        yeni_saat_araligi = st.text_input("Yeni Saat Dilimi Ekle (Örn: 09:00 - 10:00):", value="10:00 - 11:30")
                    with c_s2:
                        hedef_gun_sec = st.selectbox("Uygulanacak Gün:", ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"])
                    
                    c_s3, c_s4 = st.columns(2)
                    with c_s3:
                        sec_ders_matris = st.selectbox("Ders / Aktivite Seçin:", list(YKS_KAPSAMLI_DERS_KONULAR.keys()), key="m_ders")
                    with c_s4:
                        sec_konu_matris = st.selectbox("Alt Konu / Detay Seçin:", YKS_KAPSAMLI_DERS_KONULAR.get(sec_ders_matris, ["Genel Soru"]), key="m_konu")

                    if st.form_submit_button("📥 Bu Hücreyi Tabloya İşle", type="primary", use_container_width=True):
                         hucre_degeri = f"{sec_ders_matris}\n↳ {sec_konu_matris}"
                         gun_sutun_map = {
                             "Pazartesi": "pazartesi", "Salı": "sali", "Çarşamba": "carsamba",
                             "Perşembe": "persembe", "Cuma": "cuma", "Cumartesi": "cumartesi", "Pazar": "pazar"
                         }
                         t_sutun = gun_sutun_map[hedef_gun_sec]
                         cursor.execute(f"""
                             INSERT INTO excel_program_matris (ad_soyad, saat_araligi, {t_sutun})
                             VALUES (?, ?, ?)
                             ON CONFLICT(ad_soyad, saat_araligi) DO UPDATE SET {t_sutun} = ?
                         """, (secilen_ogr, yeni_saat_araligi, hucre_degeri, hucre_degeri))
                         conn.commit()
                         st.success(f"🎉 {hedef_gun_sec} günü ({yeni_saat_araligi}) başarıyla güncellendi!")
                         st.rerun()

                st.markdown("#### 📊 Canlı Excel Program Tablosu (Doğrudan Üzerinden Düzenleyebilirsin)")
                df_matris = pd.read_sql_query("SELECT saat_araligi AS 'Saat Aralığı', pazartesi AS 'Pazartesi', sali AS 'Salı', carsamba AS 'Çarşamba', persembe AS 'Perşembe', cuma AS 'Cuma', cumartesi AS 'Cumartesi', pazar AS 'Pazar' FROM excel_program_matris WHERE ad_soyad = ?", conn, params=(secilen_ogr,))
                
                if df_matris.empty:
                    df_matris = pd.DataFrame([{"Saat Aralığı": "09:00 - 10:00", "Pazartesi": "", "Salı": "", "Çarşamba": "", "Perşembe": "", "Cuma": "", "Cumartesi": "", "Pazar": ""}])

                edited_matris = st.data_editor(
                    df_matris,
                    num_rows="dynamic",
                    use_container_width=True,
                    height=400,
                    key=f"excel_matris_editor_{secilen_ogr}"
                )

                if st.button("💾 Tablodaki Tüm Değişiklikleri Kaydet", type="primary", use_container_width=True):
                    for _, row in edited_matris.iterrows():
                        s_ar = str(row.get("Saat Aralığı", "")).strip()
                        if s_ar:
                            cursor.execute("""
                                INSERT INTO excel_program_matris (ad_soyad, saat_araligi, pazartesi, sali, carsamba, persembe, cuma, cumartesi, pazar)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                ON CONFLICT(ad_soyad, saat_araligi) DO UPDATE SET 
                                    pazartesi=excluded.pazartesi, sali=excluded.sali, carsamba=excluded.carsamba, 
                                    persembe=excluded.persembe, cuma=excluded.cuma, cumartesi=excluded.cumartesi, pazar=excluded.pazar
                            """, (
                                secilen_ogr, s_ar,
                                str(row.get("Pazartesi", "") if pd.notna(row.get("Pazartesi")) else ""),
                                str(row.get("Salı", "") if pd.notna(row.get("Salı")) else ""),
                                str(row.get("Çarşamba", "") if pd.notna(row.get("Çarşamba")) else ""),
                                str(row.get("Perşembe", "") if pd.notna(row.get("Perşembe")) else ""),
                                str(row.get("Cuma", "") if pd.notna(row.get("Cuma")) else ""),
                                str(row.get("Cumartesi", "") if pd.notna(row.get("Cumartesi")) else ""),
                                str(row.get("Pazar", "") if pd.notna(row.get("Pazar")) else "")
                            ))
                    conn.commit()
                    st.success("🎉 Haftalık program tablosu güncellendi!")

                st.divider()
                sec_ogr_adi = locals().get('secilen_ogr', 'Öğrenci')
                st.markdown(f"### 📄 {sec_ogr_adi} İçin Program Dosyası Yükle (PDF / Word / Excel)")
                p_file = st.file_uploader("Dosya Seç:", type=["pdf", "docx", "xlsx"], key=f"pf_{sec_ogr_adi}")
                if p_file and st.button("📤 Dosyayı Öğrenciye Gönder", type="primary"):
                    f_ext = os.path.splitext(p_file.name)[1]
                    f_path = os.path.join(PROGRAM_DIR, f"Prog_{sec_ogr_adi}_{hashlib.md5(p_file.name.encode()).hexdigest()[:6]}{f_ext}")
                    with open(f_path, "wb") as f: f.write(p_file.getbuffer())
                    cursor.execute("INSERT INTO program_dosyalari (ad_soyad, yukleyen, tarih, dosya_yolu, dosya_adi) VALUES (?, ?, ?, ?, ?)",
                                   (sec_ogr_adi, st.session_state["aktif_koc"], str(datetime.date.today()), f_path, p_file.name))
                    conn.commit()
                    st.success("Dosya yüklendi!")

                st.divider()
                st.markdown(f"### 💬 {sec_ogr_adi} WhatsApp Paylaşım Linki")
                host_url = "https://blank-app-mtyl8rm3xgtksm5qer7qng.streamlit.app"
                share_url = f"{host_url}/?ogrenci={quote(sec_ogr_adi)}"
                st.code(share_url, language="text")
                st.link_button("💬 WhatsApp İle Gönder", f"https://api.whatsapp.com/send?text={quote(f'Soru linki: {share_url}')}")

    with main_tab3:
        st.markdown("## 👨‍👩‍👧‍👦 Veli Takip Ekranı")
        v_ad = st.text_input("Öğrenci Adı:").strip().title()
        if v_ad:
            df_v = pd.read_sql_query("SELECT tarih, ders, toplam_soru FROM gunluk_calisma WHERE ad_soyad = ?", conn, params=(v_ad,))
            if not df_v.empty:
                st.dataframe(df_v, use_container_width=True)
            else:
                st.info("Kayıt bulunamadı.")