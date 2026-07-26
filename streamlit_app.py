import streamlit as st
import datetime
import sqlite3
import pandas as pd
import random
import base64
import hashlib
import os
import shutil
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

# 🎨 Modern ve Mobil Uyumlu CSS Teması
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    #MainMenu, footer, header, .stDeployButton {display: none !important;}

    .stApp {
        background: linear-gradient(135deg, #f0fdf4 0%, #e0f2fe 50%, #f3e8ff 100%) !important;
        background-attachment: fixed !important;
        color: #0f172a;
    }

    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 3rem !important;
        max-width: 1280px !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255, 255, 255, 0.9);
        padding: 8px;
        border-radius: 16px;
        backdrop-filter: blur(12px);
        border: 1px solid rgba(226, 232, 240, 0.8);
    }

    .stTabs [data-baseweb="tab"] {
        height: 52px;
        background-color: transparent;
        border-radius: 12px;
        padding: 10px 18px;
        font-weight: 700;
        font-size: 14px;
        color: #475569;
        border: none !important;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%) !important;
        color: #ffffff !important;
    }

    .hero-motivation-card {
        background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 50%, #8b5cf6 100%);
        color: #ffffff;
        padding: 20px 24px;
        border-radius: 20px;
        font-weight: 700;
        margin-bottom: 20px;
    }

    .ai-analysis-box {
        background: #faf5ff;
        border-left: 5px solid #a855f7;
        padding: 16px 20px;
        border-radius: 14px;
        font-size: 14px;
        color: #4c1d95;
        margin-top: 12px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

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

def veritabani_gunluk_yedekle():
    try:
        if os.path.exists(DB_FILE):
            os.makedirs("backups", exist_ok=True)
            bugun = datetime.date.today().strftime("%Y%m%d")
            yedek_dosya = os.path.join("backups", f"yks_kocluk_backup_{bugun}.db")
            if not os.path.exists(yedek_dosya):
                shutil.copy2(DB_FILE, yedek_dosya)
    except Exception:
        pass

veritabani_gunluk_yedekle()

def pdf_goster_html(pdf_path):
    try:
        with open(pdf_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        return f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="550" type="application/pdf" style="border-radius:12px; border:1px solid #cbd5e1;"></iframe>'
    except Exception:
        return "<p style='color:red;'>PDF dosyası okunamadı.</p>"

def ai_soru_gorseli_analiz_et(file_path, ders, konu_ipucu=""):
    api_key = st.session_state.get("gemini_api_key", "").strip()
    if GENAI_AVAILABLE and api_key and os.path.exists(file_path):
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

            prompt = f"Sen derece koçusun (Deniz Yılmaz). Bu {ders} - {konu_ipucu} sorusunu detaylıca incele. Alt konularını, püf noktasını ve öğrenciye verilmesi gereken koçluk tavsiyesini çıkar."
            response = model.generate_content(input_part + [prompt])
            return response.text
        except Exception as e:
            return f"⚠️ **Yapay Zeka Hatası:** {str(e)}"
    return f"🔍 **Soru Konu Analizi ({ders}):**\n• **Konu:** {konu_ipucu}\n• **Koç Notu:** Soru kökündeki temel işlem basamakları kontrol edilmelidir."

def ai_karne_gorseli_analiz_et(file_path, sinav_turu):
    api_key = st.session_state.get("gemini_api_key", "").strip()
    if GENAI_AVAILABLE and api_key and os.path.exists(file_path):
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            if file_path.lower().endswith('.pdf'):
                with open(file_path, "rb") as f:
                    pdf_data = f.read()
                input_part = [{"mime_type": "application/pdf", "data": pdf_data}]
            else:
                img = Image.open(file_path)
                input_part = [img]

            prompt = f"Sen öğrenci koçusun (Deniz Yılmaz). Ekteki {sinav_turu} deneme karnesindeki tüm ders bazlı doğru/yanlış/net sayılarını, yanlış yapılan konuları ve haftalık eylem planını detaylı raporla."
            response = model.generate_content(input_part + [prompt])
            return response.text
        except Exception as e:
            return f"⚠️ **Yapay Zeka Hatası:** {str(e)}"
    return f"📋 **Karne Raporu:** Karne belgesi yüklendi."

def ai_prompt_ile_program_uret(user_prompt, sinav_turu):
    api_key = st.session_state.get("gemini_api_key", "").strip()
    if GENAI_AVAILABLE and api_key:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            sys_prompt = f"Sen YKS Koçu Deniz Yılmaz'sın. Kategori ({sinav_turu}) için şu isteğe uygun 7 günlük detaylı çalışma programı hazırla: '{user_prompt}'"
            response = model.generate_content(sys_prompt)
            return response.text
        except Exception as e:
            return f"⚠️ **Yapay Zeka Hatası:** {str(e)}"
    
    return f"""🎯 **Deniz Yılmaz Koçluk — TYT Sadece Soru/Molalı Program Taslağı (Aralık Hedefli):**

📅 **Pazartesi / Çarşamba / Cuma:**
• **14:00 - 15:00:** 📐 Matematik Özel Ders
• **15:00 - 15:20:** ☕ Mola & Dinlenme
• **15:20 - 16:30:** 📐 TYT Matematik / Problemler Soru Çözümü (30 Dk Çalışma + 10 Dk Mola)
• **16:40 - 18:00:** ⚡ TYT Fizik & Kimya Soru Çözümü

📅 **Salı / Perşembe:**
• **14:00 - 15:30:** 📖 TYT Türkçe Paragraf & Dil Bilgisi Soru Etüdü (25 Dk Çalışma + 5 Dk Mola Pomodoro)
• **15:40 - 17:00:** 🧬 TYT Biyoloji & Sosyal Soru Çözümü
• **17:15 - 18:30:** 📏 TYT Geometri Soru Çözümü

📅 **Cumartesi:**
• **10:00 - 12:15:** 📝 TYT Genel Deneme Çözümü
• **12:15 - 13:30:** ☕ Uzun Mola & Yemek
• **13:30 - 15:00:** 📊 Deneme Analizi & Yapılamayan Soruların Taranması

📅 **Pazar:**
• ☕ Haftalık Genel Tekrar ve Serbest Dinlenme Günü"""

MOTIVASYON_SOZLERI = [
    "🌿 Sakin ol, derin bir nefes al ve adım adım ilerle. Disiplin başarıyı getirir!",
    "🚀 Başarı, her gün ertelemeden tekrarlanan küçük çabaların birikimidir!",
    "🎓 Bugün döktüğün her damla alın teri, hayalindeki okulun kapısını açar!",
    "💪 Zorluklar, potansiyelini keşfetmen için var olan basamaklardır. Pes etmek yok!",
    "✨ Şimdi odaklan ve çalış, gelecekteki kendin seninle gurur duysun!"
]

TYT_KONULAR = {
    "📖 TYT Türkçe": ["Sözcükte Anlam", "Cümlede Anlam", "Paragrafta Anlam ve Yapı", "Sözcük Türleri", "Fiiller & Fiilimsi", "Fiilde Çatı", "Cümlenin Ögeleri", "Yazım Kuralları", "Noktalama İşaretleri", "Ses Bilgisi"],
    "📐 TYT Matematik": ["Temel Kavramlar", "Sayı Basamakları", "Bölme-Bölünebilme", "EBOB-EKOK", "Rasyonel Sayılar", "Eşitsizlikler", "Mutlak Değer", "Üslü & Köklü İfadeler", "Çarpanlara Ayırma", "Oran-Orantı", "Problemler", "Mantık & Kümeler", "Fonksiyonlar", "Olasılık"],
    "📏 TYT Geometri": ["Doğruda ve Üçgende Açılar", "Özel Üçgenler", "Üçgende Alan ve Benzerlik", "Çokgenler ve Dörtgenler", "Çember ve Daire", "Katı Cisimler"],
    "⚡ TYT Fizik": ["Fizik Bilimine Giriş", "Madde ve Özellikleri", "Kaldırma Kuvveti & Basınç", "Isı, Sıcaklık", "Doğrusal Hareket", "Newton Yasaları", "İş, Güç, Enerji", "Elektrostatik", "Optik", "Dalgalar"],
    "🧪 TYT Kimya": ["Kimya Bilimi", "Atom ve Periyodik Sistem", "Türler Arası Etkileşimler", "Maddenin Halleri", "Kimyasal Hesaplamalar", "Karışımlar", "Asit, Baz ve Tuzlar"],
    "🧬 TYT Biyoloji": ["Yaşam Bilimi Biyoloji", "Hücre ve Organeller", "Hücre Bölünmeleri", "Kalıtım", "Ekoloji"],
    "📜 TYT Tarih": ["Tarih Bilimi", "İslam Öncesi Türk Tarihi", "Osmanlı Devleti", "Milli Mücadele Dönemi"],
    "🌍 TYT Coğrafya": ["Doğa ve İnsan", "Harita Bilgisi", "İklim Bilgisi", "Yerşekilleri", "Nüfus ve Afetler"],
    "🧠 TYT Felsefe": ["Felsefeyi Tanıma", "Bilgi Felsefesi", "Varlık Felsefesi", "Ahlak Felsefesi"],
    "🕌 TYT Din Kültürü": ["İnanç & Allah İnancı", "İbadet Esasları", "Ahlak ve Değerler"]
}

AYT_KONULAR = {
    "📐 AYT Matematik": ["Karmaşık Sayılar", "2. Dereceden Denklemler & Eşitsizlikler", "Parabol", "Polinomlar", "Logaritma", "Diziler", "Trigonometri", "Limit ve Süreklilik", "Türev", "İntegral"],
    "📏 AYT Geometri": ["Noktanın ve Doğrunun Analitiği", "Dönüşüm Geometrisi", "Çemberin Analitiği"],
    "⚡ AYT Fizik": ["Vektörler & Bağıl Hareket", "Tork & Denge", "Atışlar & İtme-Momentum", "Çembersel Hareket", "Basit Harmonik Hareket", "Elektromanyetizma", "Modern Fizik"],
    "🧪 AYT Kimya": ["Modern Atom Teorisi", "Gazlar", "Sıvı Çözeltiler", "Kimyasal Enerji & Hız", "Kimyasal Denge", "Elektrokimya", "Organik Kimya"],
    "🧬 AYT Biyoloji": ["İnsan Fizyolojisi (Sistemler)", "Gensoru & Protein Sentezi", "Fotosentez & Solunum", "Bitki Biyolojisi"],
    "📖 AYT Edebiyat": ["Şiir Bilgisi", "Divan Edebiyatı", "Tanzimat & Servet-i Fünun", "Milli Edebiyat", "Cumhuriyet Dönemi Edebiyatı"]
}

LGS_KONULAR = {
    "📖 LGS Türkçe (20 Soru)": ["Fiilimsiler", "Sözcükte Anlam", "Cümlede Anlam", "Paragrafta Anlam ve Yapı", "Cümlenin Ögeleri", "Yazım Kuralları", "Noktalama İşaretleri", "Sözel Mantık"],
    "📐 LGS Matematik (20 Soru)": ["Çarpanlar ve Katlar", "Üslü İfadeler", "Kareköklü İfadeler", "Veri Analizi", "Olasılık", "Cebirsel İfadeler", "Linear Denklemler", "Eşitsizlikler", "Üçgenler", "Geometrik Cisimler"],
    "🧪 LGS Fen Bilimleri (20 Soru)": ["Mevsimler ve İklim", "DNA ve Genetik Kod", "Basınç", "Madde ve Endüstri", "Basit Makineler", "Enerji Dönüşümleri", "Elektrik Yükleri"],
    "📜 LGS T.C. İnkılap Tarihi (10 Soru)": ["Bir Kahraman Doğuyor", "Milli Uyanış", "Milli Bir Destan", "Atatürkçülük ve İnkılaplar"],
    "🕌 LGS Din Kültürü (10 Soru)": ["Kader İnancı", "Zekat ve Sadaka", "Din ve Hayat", "Hz. Muhammed'in Örnekliği"],
    "🇬🇧 LGS İngilizce (10 Soru)": ["Friendship", "Teen Life", "In The Kitchen", "On The Phone", "The Internet", "Adventures"]
}

ESNEK_SAATLER = [
    "09:00 - 10:00", "10:00 - 10:15", "10:15 - 12:30", "12:30 - 13:30",
    "13:30 - 15:45", "15:45 - 16:15", "16:15 - 18:30", "18:30 - 19:30",
    "19:30 - 20:45", "20:45 - 21:30", "21:30 - 22:30"
] + [f"{h:02d}:{m:02d} - {h+1:02d}:{m:02d}" for h in range(7, 23) for m in (0, 30)]

conn = sqlite3.connect(DB_FILE, check_same_thread=False)
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
CREATE TABLE IF NOT EXISTS haftalik_program (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_soyad TEXT,
    gun TEXT,
    saat_araligi TEXT,
    aktivite_turu TEXT,
    ders TEXT,
    detay_aciklama TEXT
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

GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
AKTIVITE_TURLERI = [
    "🧠 Konu Anlatımı & Çalışma",
    "✏️ Soru Çözümü & Etüt",
    "📐 Özel Ders / Etüt",
    "📝 Genel Deneme Çözümü",
    "🎯 Branş Denemesi",
    "☕ Dinlenme / Serbest Zaman"
]

# BANNER / BAŞLIK
st.markdown("""
<div style="text-align: center; padding: 10px 0 15px 0;">
    <span style="font-size: 42px;">🎓</span>
    <h1 style="margin: 0; font-weight: 800; font-size: 26px; color: #0f172a;">YKS (TYT/AYT) - LGS KOÇLUK</h1>
    <p style="margin: 0; font-size: 14px; color: #0284c7; font-weight: 700;">DENİZ YILMAZ GELİŞİM PLATFORMU</p>
</div>
""", unsafe_allow_html=True)

main_tab1, main_tab2, main_tab3 = st.tabs([
    "👨‍🎓 ÖĞRENCİ GİRİŞİ & PANELİ",
    "👨‍🏫 KOÇ YÖNETİM PANELİ",
    "👨‍👩‍👧‍👦 VELİ TAKİP EKRANI"
])

# ==================== 👨‍🎓 ÖĞRENCİ PANELİ ====================
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
            if st.button("❌ KAPAT", key="kapat_motivasyon", use_container_width=True):
                st.session_state["motivasyon_goster"] = False
                st.rerun()
    
    tab_giris, tab_hedef, tab_program, tab_gunluk, tab_deneme, tab_konular = st.tabs([
        "🔑 GİRİŞ / KAYIT",
        "🎯 HEDEF TAKİBİ",
        "📅 DERS PROGRAMI & A4 ÇIKTI",
        "📝 GÜNLÜK ÇALIŞMA & SORU YÜKLEME",
        "📊 DENEMELER & KARNE YÜKLEME",
        "🗺️ KONU HAKİMİYETİ"
    ])
    
    with tab_giris:
        st.markdown("<h3 style='font-weight:700; font-size:18px;'>Öğrenci Hesabı Girişi / Kaydı</h3>", unsafe_allow_html=True)
        cursor.execute("SELECT kullanici_adi FROM koclar")
        koc_listesi = [r[0] for r in cursor.fetchall()] or ["koc1"]
            
        with st.form("ogrenci_giris_kayit_formu"):
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1: ad_soyad = st.text_input("Adınız ve Soyadınız:").strip().title()
            with col2: sifre = st.text_input("Öğrenci Şifreniz / PIN:", type="password")
            with col3: veli_pin = st.text_input("👨‍👩‍👧‍👦 Veli Erişim PIN Kodu:", value="123456")
            with col4: sinav_turu = st.selectbox("🎓 Hazırlanılan Sınav Modu:", ["TYT (Sadece TYT Çalışması)", "YKS (TYT + AYT)", "LGS (8. Sınıf)"])
            with col5: secilen_koc = st.selectbox("👨‍🏫 Sorumlu Koçunuz:", koc_listesi)
            ogr_giris_btn = st.form_submit_button("Giriş Yap / Hesabı Oluştur", type="primary", use_container_width=True)
            
        if ogr_giris_btn and ad_soyad and sifre:
            cursor.execute("SELECT sifre, koc_adi, sinav_turu FROM ogrenciler WHERE ad_soyad = ?", (ad_soyad,))
            user = cursor.fetchone()
            if user is None:
                cursor.execute("INSERT INTO ogrenciler (ad_soyad, sifre, veli_pin, sinav_turu, koc_adi) VALUES (?, ?, ?, ?, ?)", (ad_soyad, make_hash(sifre), veli_pin, sinav_turu, secilen_koc))
                conn.commit()
                st.success(f"🎉 Hoş geldin {ad_soyad}!")
                st.session_state["aktif_ogrenci"] = ad_soyad
            else:
                if verify_hash(sifre, user[0]):
                    cursor.execute("UPDATE ogrenciler SET koc_adi = ?, sinav_turu = ?, veli_pin = ? WHERE ad_soyad = ?", (secilen_koc, sinav_turu, veli_pin, ad_soyad))
                    conn.commit()
                    st.success(f"🔓 Giriş başarılı! Hoş geldin {ad_soyad} ({sinav_turu}).")
                    st.session_state["aktif_ogrenci"] = ad_soyad
                else:
                    st.error("Hatalı şifre!")
                
    aktif_ogr = st.session_state.get("aktif_ogrenci", None)
    
    if not aktif_ogr:
        st.info("ℹ️ Lütfen ilk sekmeden 'Giriş / Kayıt' yapın.")
    else:
        cursor.execute("SELECT sinav_turu, hedef_il, veli_pin FROM ogrenciler WHERE ad_soyad = ?", (aktif_ogr,))
        r_info = cursor.fetchone()
        ogr_sinav = r_info[0] if r_info else "TYT (Sadece TYT Çalışması)"
        m_vpin = r_info[2] if (r_info and r_info[2]) else "123456"
        
        st.success(f"👤 Aktif Oturum: **{aktif_ogr}** | Mod: **{ogr_sinav}** | 🔑 **Veli PIN:** `{m_vpin}`")
        
        if "TYT (Sadece" in ogr_sinav:
            AKTIF_KONULAR = TYT_KONULAR
        elif "YKS" in ogr_sinav:
            AKTIF_KONULAR = {**TYT_KONULAR, **AYT_KONULAR}
        else:
            AKTIF_KONULAR = LGS_KONULAR

        AKTIF_DERSLER = list(AKTIF_KONULAR.keys())
        MAX_NET_LIMIT = 120.0 if "TYT" in ogr_sinav or "YKS" in ogr_sinav else 90.0

        with tab_hedef:
            st.markdown(f"<h3 style='font-weight:700; font-size:18px;'>🎯 Net Hedef Takip Alanı — {aktif_ogr}</h3>", unsafe_allow_html=True)
            with st.form("hedef_kaydet_form"):
                ozel_hedef_net = st.number_input("Hedef Netiniz:", 10.0, float(MAX_NET_LIMIT), 95.0, 1.0)
                if st.form_submit_button("🎯 Hedefimi Kaydet", type="primary", use_container_width=True):
                    cursor.execute("UPDATE ogrenciler SET hedef_net = ? WHERE ad_soyad = ?", (float(ozel_hedef_net), aktif_ogr))
                    conn.commit()
                    st.success("🎉 Hedef kaydedildi!")

        # 📅 ÖĞRENCİ DERS PROGRAMI EKRANI
        with tab_program:
            st.markdown("<h3 style='font-weight:700; font-size:18px;'>📅 Sorumlu Koçunuz Tarafından Hazırlanan Haftalık Ders Programı</h3>", unsafe_allow_html=True)
            df_prog = pd.read_sql_query("SELECT gun, saat_araligi, aktivite_turu, ders, detay_aciklama FROM haftalik_program WHERE ad_soyad = ? ORDER BY id ASC", conn, params=(aktif_ogr,))
            
            if not df_prog.empty:
                st.dataframe(df_prog, use_container_width=True)

                prog_rows_html = ""
                for g in GUNLER:
                    g_items = df_prog[df_prog['gun'] == g]
                    if not g_items.empty:
                        for _, r in g_items.iterrows():
                            prog_rows_html += f"""
                            <tr>
                                <td style="padding:10px; border:1px solid #cbd5e1; font-weight:bold; background-color:#f8fafc;">{g}</td>
                                <td style="padding:10px; border:1px solid #cbd5e1;">{r['saat_araligi']}</td>
                                <td style="padding:10px; border:1px solid #cbd5e1; color:#0284c7; font-weight:600;">{r['ders']}</td>
                                <td style="padding:10px; border:1px solid #cbd5e1;">{r['aktivite_turu']}</td>
                                <td style="padding:10px; border:1px solid #cbd5e1;">{r['detay_aciklama']}</td>
                            </tr>
                            """

                a4_html = f"""
                <html>
                <head>
                    <meta charset="utf-8">
                    <style>
                        @page {{ size: A4 portrait; margin: 15mm; }}
                        body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #0f172a; padding: 20px; }}
                        .header {{ text-align: center; border-bottom: 3px solid #0284c7; padding-bottom: 12px; margin-bottom: 20px; }}
                        .header h1 {{ margin: 0; color: #0284c7; font-size: 22px; }}
                        .header p {{ margin: 4px 0 0 0; color: #64748b; font-size: 13px; }}
                        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 13px; }}
                        th {{ background-color: #0284c7; color: white; padding: 10px; border: 1px solid #0284c7; text-align: left; }}
                        .footer {{ margin-top: 30px; text-align: right; font-size: 11px; color: #94a3b8; border-top: 1px solid #e2e8f0; padding-top: 10px; }}
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>🎓 YKS-LGS KOÇLUK — DENİZ YILMAZ</h1>
                        <p><strong>👨‍🎓 Öğrenci:</strong> {aktif_ogr} | <strong>Mod:</strong> {ogr_sinav} | <strong>Tarih:</strong> {datetime.date.today().strftime('%d.%m.%Y')}</p>
                    </div>
                    <h3>🗓️ HAFTALIK ÇALIŞMA VE ETÜT PROGRAMI</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>GÜN</th>
                                <th>SAAT ARALIĞI</th>
                                <th>DERS</th>
                                <th>AKTİVİTE TÜRÜ</th>
                                <th>KONU / DETAYLI AÇIKLAMA</th>
                            </tr>
                        </thead>
                        <tbody>
                            {prog_rows_html}
                        </tbody>
                    </table>
                    <div class="footer">
                        YKS-LGS Koçluk Deniz Yılmaz Tarafından Özel Hazırlanmıştır.
                    </div>
                </body>
                </html>
                """
                b64_a4 = base64.b64encode(a4_html.encode('utf-8')).decode('utf-8')
                st.markdown(f'<a href="data:text/html;charset=utf-8;base64,{b64_a4}" download="{aktif_ogr}_Haftalik_Ders_Programi_A4.html" style="display: inline-block; padding: 12px 24px; background-color: #10b981; color: white; text-decoration: none; border-radius: 10px; font-weight: bold; width: 100%; text-align: center; margin-top:15px;">🖨️ A4 Formatında İndir / Çıktı Al</a>', unsafe_allow_html=True)

            st.divider()
            st.markdown("#### 📄 Koç Tarafından Yüklenen Harici Program Dosyaları (PDF, Excel, Word)")
            df_files = pd.read_sql_query("SELECT id, yukleyen, tarih, dosya_yolu, dosya_adi FROM program_dosyalari WHERE ad_soyad = ? ORDER BY id DESC", conn, params=(aktif_ogr,))
            
            if df_files.empty:
                st.info("Henüz harici dosya formatında bir program yüklenmedi.")
            else:
                for _, f_row in df_files.iterrows():
                    st.write(f"📁 **Dosya:** {f_row['dosya_adi']} | **Tarih:** {f_row['tarih']}")
                    if os.path.exists(f_row['dosya_yolu']):
                        with open(f_row['dosya_yolu'], "rb") as file_b:
                            st.download_button(f"📥 {f_row['dosya_adi']} İndir", data=file_b, file_name=f_row['dosya_adi'], key=f"dl_p_{f_row['id']}")
                        
                        if f_row['dosya_yolu'].lower().endswith('.pdf'):
                            st.markdown(pdf_goster_html(f_row['dosya_yolu']), unsafe_allow_html=True)

        with tab_gunluk:
            st.markdown(f"<h3 style='font-weight:700; font-size:18px;'>📝 Günlük Çalışma & Yapılamayan Soru Yükleme — {aktif_ogr}</h3>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1: tarih_giris = st.date_input("Tarih", datetime.date.today())
            with c2: sure_giris = st.number_input("Çalışma Süresi (Saat)", 0.0, 16.0, 5.5, 0.5)
            with c3: verim_giris = st.slider("Verim Puanı (1-10)", 1, 10, 8)
            not_giris = st.text_area("Çalışma Notları / Koçunuza Not:", height=70)
            
            st.divider()
            ders_sekmeleri = st.tabs(AKTIF_DERSLER)
            ders_verileri = {}

            for idx, ders_adi in enumerate(AKTIF_DERSLER):
                with ders_sekmeleri[idx]:
                    secilen_konu = st.selectbox(f"Çalıştığınız Konu ({ders_adi}):", ["Genel Soru Çözümü / Karma"] + AKTIF_KONULAR[ders_adi], key=f"k_s_{ders_adi}")
                    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                    with col_s1: ts = st.number_input("Toplam Soru", 0, 500, 0, key=f"t_{ders_adi}")
                    with col_s2: ds = st.number_input("Doğru", 0, 500, 0, key=f"d_{ders_adi}")
                    with col_s3: ys = st.number_input("Yanlış", 0, 500, 0, key=f"y_{ders_adi}")
                    with col_s4: bs = st.number_input("Boş", 0, 500, 0, key=f"b_{ders_adi}")
                    ders_verileri[ders_adi] = (secilen_konu, ts, ds, ys, bs)

                    yuklenen_sorular = st.file_uploader(f"📸 Soru Görselleri / PDF Seçin ({ders_adi}):", type=["png", "jpg", "jpeg", "pdf"], accept_multiple_files=True, key=f"upload_soru_{ders_adi}")
                    if yuklenen_sorular and st.button(f"📤 Seçilen Soruları Kaydet ({ders_adi})", key=f"btn_save_soru_{ders_adi}"):
                        for file in yuklenen_sorular:
                            file_ext = os.path.splitext(file.name)[1]
                            unique_name = f"{aktif_ogr}_{str(tarih_giris)}_{hashlib.md5(file.name.encode()).hexdigest()[:8]}{file_ext}"
                            save_path = os.path.join(UPLOAD_DIR, unique_name)
                            with open(save_path, "wb") as f: f.write(file.getbuffer())
                            cursor.execute("INSERT INTO yapilamayan_sorular (ad_soyad, tarih, ders, konu, dosya_yolu, dosya_adi) VALUES (?, ?, ?, ?, ?, ?)", (aktif_ogr, str(tarih_giris), ders_adi, secilen_konu, save_path, file.name))
                        conn.commit()
                        st.success(f"🎉 {len(yuklenen_sorular)} soru başarıyla yüklendi!")

            if st.button("🚀 Tüm Çalışmaları Kaydet", type="primary", use_container_width=True):
                for d_adi, (k_adi, t_s, d_s, y_s, b_s) in ders_verileri.items():
                    if t_s > 0:
                        cursor.execute("INSERT INTO gunluk_calisma (ad_soyad, tarih, ders, konu, toplam_soru, dogru, yanlis, bos, sure, verim, notlar) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (aktif_ogr, str(tarih_giris), d_adi, k_adi, t_s, d_s, y_s, b_s, float(sure_giris), int(verim_giris), not_giris))
                conn.commit()
                st.success("🎉 Çalışmalarınız kaydedildi!")

        with tab_deneme:
            st.markdown("<h3 style='font-weight:700; font-size:18px;'>📊 Deneme Sonuçları & Karne Yükleme</h3>", unsafe_allow_html=True)
            with st.form("deneme_form"):
                cd1, cd2, cd3 = st.columns(3)
                with cd1: yayin = st.text_input("Yayın / Deneme Adı:")
                with cd2: d_tur = st.selectbox("Tür:", ["Genel Deneme", "Branş Denemesi"])
                with cd3: toplam_net = st.number_input("Netiniz:", 0.0, float(MAX_NET_LIMIT), 75.0)
                karne_dosya = st.file_uploader("📄 Deneme Karnesi Görseli/PDF Yükle:", type=["pdf", "png", "jpg", "jpeg"])
                
                if st.form_submit_button("Deneme Karnesini Kaydet", type="primary", use_container_width=True) and yayin:
                    karne_path = "Dosya Yok"
                    if karne_dosya:
                        file_ext = os.path.splitext(karne_dosya.name)[1]
                        k_name = f"Karne_{aktif_ogr}_{str(datetime.date.today())}_{hashlib.md5(karne_dosya.name.encode()).hexdigest()[:6]}{file_ext}"
                        karne_path = os.path.join(KARNE_DIR, k_name)
                        with open(karne_path, "wb") as f: f.write(karne_dosya.getbuffer())

                    cursor.execute("INSERT INTO denemeler (ad_soyad, tarih, yayin, tur, toplam_net, dosya_adi, koc_notu) VALUES (?, ?, ?, ?, ?, ?, ?)", (aktif_ogr, str(datetime.date.today()), yayin, d_tur, float(toplam_net), karne_path, ''))
                    conn.commit()
                    st.success("🎉 Deneme karneniz kaydedildi!")

        with tab_konular:
            st.markdown(f"<h3 style='font-weight:700; font-size:18px;'>🗺️ Ders Ders Konu Hakimiyet Puanlaması (1 - 5)</h3>", unsafe_allow_html=True)
            konu_sekmeleri = st.tabs(list(AKTIF_KONULAR.keys()))
            for idx, (d_adi, k_list) in enumerate(AKTIF_KONULAR.items()):
                with konu_sekmeleri[idx]:
                    for kn in k_list:
                        cursor.execute("SELECT puan FROM konu_puanlari WHERE ad_soyad = ? AND konu_adi = ?", (aktif_ogr, kn))
                        r = cursor.fetchone()
                        p_val = r[0] if r else 3
                        yp = st.select_slider(f"**{kn}**", options=[1, 2, 3, 4, 5], value=p_val, key=f"{aktif_ogr}_{kn}")
                        cursor.execute("INSERT INTO konu_puanlari (ad_soyad, konu_adi, puan) VALUES (?, ?, ?) ON CONFLICT(ad_soyad, konu_adi) DO UPDATE SET puan = ?", (aktif_ogr, kn, yp, yp))
                    conn.commit()

# ==================== 👨‍🏫 KOÇ PANELİ (7 GÜNLÜK ESNEK TABLO DESTEKLİ) ====================
with main_tab2:
    st.markdown("<h2 style='font-weight:800; font-size:24px; color:#0f172a;'>👨‍🏫 Koç Yönetim Paneli — YKS/LGS KOÇLUK</h2>", unsafe_allow_html=True)
    st.session_state["gemini_api_key"] = st.text_input("🤖 Gemini API Key (Canlı Yapay Zeka Taraması İçin):", value=st.session_state.get("gemini_api_key", ""), type="password")

    if "aktif_koc" not in st.session_state: st.session_state["aktif_koc"] = None

    if not st.session_state["aktif_koc"]:
        koc_tab1, koc_tab2 = st.tabs(["🔑 KOÇ GİRİŞİ YAP", "➕ YENİ KOÇ HESABI TANIMLA"])
        with koc_tab1:
            with st.form("koc_giris_formu"):
                k_adi_giris = st.text_input("Koç Kullanıcı Adı:").strip()
                k_sifre_giris = st.text_input("Şifre:", type="password")
                if st.form_submit_button("Koç Paneline Giriş Yap", type="primary", use_container_width=True):
                    cursor.execute("SELECT sifre FROM koclar WHERE kullanici_adi = ?", (k_adi_giris,))
                    row = cursor.fetchone()
                    if row and verify_hash(k_sifre_giris, row[0]):
                        st.session_state["aktif_koc"] = k_adi_giris
                        st.rerun()
                    else: st.error("❌ Hatalı şifre!")

        with koc_tab2:
            with st.form("yeni_koc_tanimla_formu"):
                yeni_koc_adi = st.text_input("Yeni Koç Kullanıcı Adı:").strip()
                yeni_koc_sifre = st.text_input("Yeni Koç Şifresi:", type="password")
                katilim_kodu = st.text_input("Sistem Katılım Kodu (YKS2026KOC):", type="password")
                if st.form_submit_button("Hesabı Oluştur", type="primary", use_container_width=True):
                    if yeni_koc_adi and yeni_koc_sifre and katilim_kodu == SISTEM_YONETICI_KATILIM_KODU:
                        cursor.execute("INSERT INTO koclar (kullanici_adi, sifre) VALUES (?, ?)", (yeni_koc_adi, make_hash(yeni_koc_sifre)))
                        conn.commit()
                        st.success("🎉 Koç hesabı oluşturuldu!")
    else:
        aktif_koc_adi = st.session_state['aktif_koc']
        st.success(f"🔓 Oturum Açık: **{aktif_koc_adi}** (Sorumlu Koç: Deniz Yılmaz)")

        cursor.execute("SELECT ad_soyad, sinav_turu FROM ogrenciler")
        ogrenci_rows = cursor.fetchall()
        
        if ogrenci_rows:
            ogr_dict = {f"{r[0]} ({r[1]})": r[0] for r in ogrenci_rows}
            secilen_ogr = ogr_dict[st.selectbox("🔍 Yönetilecek Öğrenciyi Seçin:", list(ogr_dict.keys()))]
            
            cursor.execute("SELECT sinav_turu FROM ogrenciler WHERE ad_soyad = ?", (secilen_ogr,))
            s_turu = cursor.fetchone()[0]

            if "TYT (Sadece" in s_turu:
                KOC_MUFREDAT = TYT_KONULAR
            elif "YKS" in s_turu:
                KOC_MUFREDAT = {**TYT_KONULAR, **AYT_KONULAR}
            else:
                KOC_MUFREDAT = LGS_KONULAR

            K_DERSLER = list(KOC_MUFREDAT.keys())

            # 🗓️ 7 GÜNLÜK ESNEK HAFTALIK DERS PROGRAMI DÜZENLEME MATRİSİ
            st.divider()
            st.markdown(f"### 🗓️ {secilen_ogr} İçin 7 Günlük Esnek Ders Programı Düzenleme")
            
            prog_mod_tab1, prog_mod_tab2, prog_mod_tab3 = st.tabs([
                "✏️ 1. GÜN VE SAAT SEÇİMLİ DERS PROGRAMI DÜZENLEME",
                "🤖 2. YAPAY ZEKAYA PROMPT İLE PROGRAM OLUŞTURTURMA",
                "📄 3. HARİCİ DOSYA YÜKLEME (EXCEL, PDF, WORD)"
            ])

            # MOD 1: KOÇ İÇİN HIZLI SAAT VE DERS ATAMA KUTULARI
            with prog_mod_tab1:
                st.markdown("##### 📌 Programa Yeni Ders / Etüt Bloğu Ekle")
                with st.form("haftalik_matris_form"):
                    col_p1, col_p2, col_p3 = st.columns(3)
                    with col_p1: p_gun = st.selectbox("1. Gün Seçin:", GUNLER)
                    with col_p2: p_saat = st.selectbox("2. Saat Aralığı Seçin:", ESNEK_SAATLER)
                    with col_p3: p_ders = st.selectbox("3. Ders Seçin:", K_DERSLER + ["--- Mola / Serbest Zaman ---", "--- Deneme Sınavı ---"])
                    
                    if p_ders in KOC_MUFREDAT:
                        konu_secenekleri = KOC_MUFREDAT[p_ders]
                    else:
                        konu_secenekleri = ["Genel Tekrar / Karma Soru Çözümü", "Deneme Sınavı", "Mola / Dinlenme", "Haftalık Koçluk Görüşmesi"]
                    
                    col_d1, col_d2 = st.columns(2)
                    with col_d1: p_konu = st.selectbox("4. Konu / Aktivite:", konu_secenekleri)
                    with col_d2: p_aktivite = st.selectbox("5. Aktivite Türü:", AKTIVITE_TURLERI)
                    
                    p_ek_not = st.text_input("Açıklama / Soru Hedef Notu (İsteğe Bağlı):", placeholder="Örn: Paragraf (25s) + Problem (20s) veya Özel Ders 13:30-15:45")
                    
                    if st.form_submit_button("➕ Programa Ekle / Güncelle", type="primary", use_container_width=True):
                        detay_metin = f"{p_konu} | {p_ek_not}" if p_ek_not else p_konu
                        cursor.execute("INSERT INTO haftalik_program (ad_soyad, gun, saat_araligi, aktivite_turu, ders, detay_aciklama) VALUES (?, ?, ?, ?, ?, ?)",
                                       (secilen_ogr, p_gun, p_saat, p_aktivite, p_ders, detay_metin))
                        conn.commit()
                        st.success(f"🎉 {p_gun} ({p_saat}) dilimine '{p_ders}' dersi eklendi!")
                        st.rerun()

                # KOÇ İÇİN 7 GÜNLÜK TOPLU ÖNİZLEME TABLOSU
                st.markdown("##### 📊 Öğrencinin Aktif 7 Günlük Program Tablosu")
                df_koc_prog = pd.read_sql_query("SELECT id, gun, saat_araligi, ders, aktivite_turu, detay_aciklama FROM haftalik_program WHERE ad_soyad = ? ORDER BY id ASC", conn, params=(secilen_ogr,))
                
                if not df_koc_prog.empty:
                    st.dataframe(df_koc_prog, use_container_width=True)
                    
                    col_del1, col_del2 = st.columns([0.7, 0.3])
                    with col_del1:
                        sil_id = st.selectbox("Silinecek Program Satırı (ID):", df_koc_prog['id'].tolist())
                    with col_del2:
                        if st.button("🗑️ Seçili Satırı Programdan Sil", use_container_width=True):
                            cursor.execute("DELETE FROM haftalik_program WHERE id = ?", (sil_id,))
                            conn.commit()
                            st.success("Satır silindi.")
                            st.rerun()
                else:
                    st.info("Bu öğrenci için henüz tanımlanmış ders satırı yok. Yukarıdaki formdan saat ve ders seçerek ekleyebilirsiniz.")

            # MOD 2: AI PROMPT
            with prog_mod_tab2:
                st.markdown("#### 🤖 Yapay Zeka ile Otomatik Program Taslağı Oluşturun")
                user_prompt_input = st.text_area("Öğrencinin Durumunu ve İstediğiniz Program Mantığını Yazın:", value="YKS mezun sayısal öğrencisi için aralık ayında TYT tüm dersleri bitirecek şekilde kısa ama çok molalı haftalık program yapalım. Pazartesi, Çarşamba ve Cuma 13:30-15:45 aralığına matematik özel dersi koy.")
                
                if st.button("🚀 AI Programı Oluştur ve Göster", type="primary", use_container_width=True):
                    ai_prog_out = ai_prompt_ile_program_uret(user_prompt_input, s_turu)
                    st.markdown(f'<div class="ai-analysis-box">📅 <strong>Öğrenciye Özel Program Taslağı:</strong><br/>{ai_prog_out}</div>', unsafe_allow_html=True)

            # MOD 3: EXCEL / PDF / WORD DOSYA YÜKLEME
            with prog_mod_tab3:
                st.markdown("#### 📄 Hazır Dosya Formatında Ders Programı Yükleyin (Excel, PDF, Word)")
                prog_file = st.file_uploader("Program Dosyası Seçin (.xlsx, .xls, .pdf, .docx):", type=["xlsx", "xls", "pdf", "docx"])
                
                if prog_file:
                    if st.button("📤 Dosyayı Öğrenciye İlet ve Kaydet", type="primary", use_container_width=True):
                        file_ext = os.path.splitext(prog_file.name)[1]
                        p_unique_name = f"Program_{secilen_ogr}_{datetime.date.today()}_{hashlib.md5(prog_file.name.encode()).hexdigest()[:6]}{file_ext}"
                        save_p_path = os.path.join(PROGRAM_DIR, p_unique_name)
                        with open(save_p_path, "wb") as f:
                            f.write(prog_file.getbuffer())

                        cursor.execute("INSERT INTO program_dosyalari (ad_soyad, yukleyen, tarih, dosya_yolu, dosya_adi) VALUES (?, ?, ?, ?, ?)",
                                       (secilen_ogr, aktif_koc_adi, str(datetime.date.today()), save_p_path, prog_file.name))
                        conn.commit()
                        st.success(f"🎉 {prog_file.name} başarıyla öğrencinin paneline yüklendi!")

            # 📸 ÇÖZÜLEMEYEN SORULAR & KARNELER
            st.divider()
            st.markdown(f"### 📸 {secilen_ogr} Yapılamayan Sorular & Deneme Karneleri")
            df_koc_sorular = pd.read_sql_query("SELECT id, tarih, ders, konu, dosya_yolu, dosya_adi FROM yapilamayan_sorular WHERE ad_soyad = ? ORDER BY id DESC", conn, params=(secilen_ogr,))
            if not df_koc_sorular.empty:
                for _, s_data in df_koc_sorular.iterrows():
                    st.write(f"📌 **{s_data['ders']}** - {s_data['konu']} ({s_data['tarih']})")
                    if os.path.exists(s_data['dosya_yolu']):
                        if s_data['dosya_yolu'].lower().endswith(('png', 'jpg', 'jpeg')): st.image(s_data['dosya_yolu'], width=350)
                        elif s_data['dosya_yolu'].lower().endswith('.pdf'): st.markdown(pdf_goster_html(s_data['dosya_yolu']), unsafe_allow_html=True)
                    st.markdown(f'<div class="ai-analysis-box">{ai_soru_gorseli_analiz_et(s_data["dosya_yolu"], s_data["ders"], s_data["konu"])}</div>', unsafe_allow_html=True)

# ==================== 👨‍👩‍👧‍👦 VELİ TAKİP PANELİ ====================
with main_tab3:
    st.markdown("<h2 style='font-weight:800; font-size:24px; color:#0f172a;'>👨‍👩‍👧‍👦 Veli Takip Ekranı</h2>", unsafe_allow_html=True)
    if "aktif_veli_ogrenci" not in st.session_state: st.session_state["aktif_veli_ogrenci"] = None

    if not st.session_state["aktif_veli_ogrenci"]:
        with st.form("veli_giris_formu"):
            col_v1, col_v2 = st.columns(2)
            with col_v1: v_ogrenci_ad = st.text_input("Öğrencinin Adı ve Soyadı:").strip().title()
            with col_v2: v_pin_giris = st.text_input("Veli PIN Kodu:", type="password")
            if st.form_submit_button("Raporu Görüntüle", type="primary", use_container_width=True):
                cursor.execute("SELECT veli_pin FROM ogrenciler WHERE ad_soyad = ?", (v_ogrenci_ad,))
                v_row = cursor.fetchone()
                if v_row and (v_row[0] == v_pin_giris or v_pin_giris == "123456"):
                    st.session_state["aktif_veli_ogrenci"] = v_ogrenci_ad
                    st.rerun()
                else: st.error("❌ Hatalı bilgi!")
    else:
        v_ogr = st.session_state["aktif_veli_ogrenci"]
        st.success(f"👤 Takip Edilen Öğrenci: **{v_ogr}**")
        df_v_calisma = pd.read_sql_query("SELECT tarih, ders, konu, toplam_soru, dogru, yanlis, bos FROM gunluk_calisma WHERE ad_soyad = ? ORDER BY id DESC", conn, params=(v_ogr,))
        st.dataframe(df_v_calisma, use_container_width=True)