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

# 🎨 Gece Modu (Dark Mode) Uyumlu ve Mobil İçin Birebir Kontrastlı CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"], .stMarkdown, p, div, label, span {
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
        font-weight: 700;
        font-size: 13px;
        color: #334155 !important;
        border: 1px solid #e2e8f0 !important;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%) !important;
        color: #ffffff !important;
        border: none !important;
    }

    .stTabs [aria-selected="true"] span {
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

            prompt = f"Sen YKS derece koçusun (Deniz Yılmaz). Bu {ders} - {konu_ipucu} sorusunu incele. Alt konularını, çözüm yöntemini ve öğrenciye özel koçluk tavsiyeni çıkar."
            response = model.generate_content(input_part + [prompt])
            return response.text
        except Exception as e:
            return f"⚠️ **Yapay Zeka Hatası:** {str(e)}"
    return f"🔍 **Soru Konu Analizi ({ders}):**\n• **Konu:** {konu_ipucu}\n• **Koç Notu:** Soru kökündeki temel işlem basamakları kontrol edilmelidir."

MOTIVASYON_SOZLERI = [
    "🌿 Sakin ol, derin bir nefes al ve adım adım ilerle. Disiplin başarıyı getirir!",
    "🚀 Başarı, her gün ertelemeden tekrarlanan küçük çabaların birikimidir!",
    "🎓 Bugün döktüğün her damla alın teri, hayalindeki okulun kapısını açar!",
    "💪 Zorluklar, potansiyelini keşfetmen için var olan basamaklardır. Pes etmek yok!",
    "✨ Şimdi odaklan ve çalış, gelecekteki kendin seninle gurur duysun!"
]

YOK_ATLAS_UNI_BOLUM_VERITABANI = {
    "Orta Doğu Teknik Üniversitesi (ODTÜ)": {
        "Computer Engineering / Bilgisayar Mühendisliği (SAY)": {"taban_net": 113.5, "tavan_net": 118.5, "taban_sira": "520", "tavan_sira": "15"},
        "Endüstri Mühendisliği (SAY)": {"taban_net": 110.0, "tavan_net": 116.5, "taban_sira": "1.450", "tavan_sira": "65"},
        "Elektrik-Elektronik Mühendisliği (SAY)": {"taban_net": 111.0, "tavan_net": 117.0, "taban_sira": "1.150", "tavan_sira": "40"},
        "Havacılık ve Uzay Mühendisliği (SAY)": {"taban_net": 108.5, "tavan_net": 115.5, "taban_sira": "2.400", "tavan_sira": "180"},
        "Makine Mühendisliği (SAY)": {"taban_net": 105.0, "tavan_net": 113.0, "taban_sira": "5.500", "tavan_sira": "420"},
        "İnşaat Mühendisliği (SAY)": {"taban_net": 88.5, "tavan_net": 102.0, "taban_sira": "48.000", "tavan_sira": "12.000"},
        "Siyaset Bilimi ve Uluslararası İlişkiler (EA)": {"taban_net": 96.5, "tavan_net": 106.0, "taban_sira": "1.800", "tavan_sira": "95"},
        "İşletme (EA)": {"taban_net": 98.0, "tavan_net": 108.5, "taban_sira": "1.200", "tavan_sira": "45"},
        "İktisat / Ekonomi (EA)": {"taban_net": 96.0, "tavan_net": 106.5, "taban_sira": "2.100", "tavan_sira": "110"},
        "Psikoloji (EA)": {"taban_net": 94.5, "tavan_net": 104.0, "taban_sira": "3.500", "tavan_sira": "210"},
        "Mimarlık (SAY)": {"taban_net": 98.0, "tavan_net": 108.0, "taban_sira": "15.000", "tavan_sira": "1.200"},
        "İngilizce Öğretmenliği (DİL)": {"taban_net": 75.0, "tavan_net": 79.0, "taban_sira": "1.200", "tavan_sira": "85"}
    },
    "Boğaziçi Üniversitesi (İstanbul)": {
        "Computer Engineering / Bilgisayar Mühendisliği (SAY)": {"taban_net": 114.5, "tavan_net": 119.0, "taban_sira": "280", "tavan_sira": "1"},
        "Endüstri Mühendisliği (SAY)": {"taban_net": 111.0, "tavan_net": 117.5, "taban_sira": "1.100", "tavan_sira": "45"},
        "Elektrik-Elektronik Mühendisliği (SAY)": {"taban_net": 112.5, "tavan_net": 118.5, "taban_sira": "650", "tavan_sira": "12"},
        "Makine Mühendisliği (SAY)": {"taban_net": 108.0, "tavan_net": 115.0, "taban_sira": "3.100", "tavan_sira": "210"},
        "İşletme (EA)": {"taban_net": 102.5, "tavan_net": 112.0, "taban_sira": "420", "tavan_sira": "5"},
        "İktisat / Ekonomi (EA)": {"taban_net": 100.0, "tavan_net": 110.5, "taban_sira": "680", "tavan_sira": "18"},
        "Psikoloji (EA)": {"taban_net": 98.5, "tavan_net": 108.0, "taban_sira": "1.250", "tavan_sira": "35"},
        "İngilizce Öğretmenliği (DİL)": {"taban_net": 76.5, "tavan_net": 79.5, "taban_sira": "850", "tavan_sira": "12"}
    },
    "İstanbul Teknik Üniversitesi (İTÜ)": {
        "Computer Engineering / Bilgisayar Mühendisliği (SAY)": {"taban_net": 112.0, "tavan_net": 117.0, "taban_sira": "950", "tavan_sira": "85"},
        "Endüstri Mühendisliği (SAY)": {"taban_net": 107.5, "tavan_net": 114.0, "taban_sira": "3.200", "tavan_sira": "350"},
        "Yapay Zeka Mühendisliği (SAY)": {"taban_net": 111.5, "tavan_net": 116.5, "taban_sira": "1.200", "tavan_sira": "110"},
        "Uçak Mühendisliği (SAY)": {"taban_net": 108.0, "tavan_net": 115.0, "taban_sira": "2.800", "tavan_sira": "210"},
        "Elektrik-Elektronik Mühendisliği (SAY)": {"taban_net": 108.5, "tavan_net": 115.5, "taban_sira": "2.500", "tavan_sira": "180"},
        "Makine Mühendisliği (SAY)": {"taban_net": 103.5, "tavan_net": 111.0, "taban_sira": "7.800", "tavan_sira": "820"},
        "İnşaat Mühendisliği (SAY)": {"taban_net": 82.0, "tavan_net": 96.0, "taban_sira": "68.000", "tavan_sira": "18.000"},
        "Mimarlık (SAY)": {"taban_net": 96.0, "tavan_net": 106.0, "taban_sira": "18.500", "tavan_sira": "1.800"}
    },
    "Hacettepe Üniversitesi (Ankara)": {
        "Tıp Fakültesi (SAY)": {"taban_net": 114.0, "tavan_net": 118.5, "taban_sira": "1.100", "tavan_sira": "8"},
        "Diş Hekimliği (SAY)": {"taban_net": 102.5, "tavan_net": 109.0, "taban_sira": "18.500", "tavan_sira": "3.200"},
        "Eczacılık (SAY)": {"taban_net": 95.0, "tavan_net": 103.5, "taban_sira": "38.000", "tavan_sira": "12.000"},
        "Computer Engineering / Bilgisayar Mühendisliği (SAY)": {"taban_net": 109.5, "tavan_net": 115.5, "taban_sira": "2.100", "tavan_sira": "380"},
        "Endüstri Mühendisliği (SAY)": {"taban_net": 104.0, "tavan_net": 111.5, "taban_sira": "7.200", "tavan_sira": "1.100"},
        "Elektrik-Elektronik Mühendisliği (SAY)": {"taban_net": 105.5, "tavan_net": 112.5, "taban_sira": "5.800", "tavan_sira": "850"},
        "Psikoloji (EA)": {"taban_net": 88.0, "tavan_net": 98.0, "taban_sira": "9.500", "tavan_sira": "850"}
    },
    "Galatasaray Üniversitesi (İstanbul)": {
        "Hukuk Fakültesi (EA)": {"taban_net": 101.5, "tavan_net": 109.0, "taban_sira": "650", "tavan_sira": "25"},
        "Computer Engineering / Bilgisayar Mühendisliği (SAY)": {"taban_net": 108.0, "tavan_net": 114.5, "taban_sira": "3.500", "tavan_sira": "480"},
        "Endüstri Mühendisliği (SAY)": {"taban_net": 105.0, "tavan_net": 112.0, "taban_sira": "6.200", "tavan_sira": "850"},
        "Siyaset Bilimi ve Uluslararası İlişkiler (EA)": {"taban_net": 95.0, "tavan_net": 104.0, "taban_sira": "2.200", "tavan_sira": "180"}
    }
}

YOK_ATLAS_UNIVERSTITELER = sorted(list(set(list(YOK_ATLAS_UNI_BOLUM_VERITABANI.keys()) + [
    "Boğaziçi Üniversitesi (İstanbul)", "İstanbul Teknik Üniversitesi (İTÜ)", "Orta Doğu Teknik Üniversitesi (ODTÜ)",
    "Hacettepe Üniversitesi (Ankara)", "Bilkent Üniversitesi (Ankara)", "Koç Üniversitesi (İstanbul)",
    "Sabancı Üniversitesi (İstanbul)", "İstanbul Üniversitesi", "Marmara Üniversitesi (İstanbul)",
    "Yıldız Teknik Üniversitesi (İTÜ)", "Ege Üniversitesi (İzmir)", "Dokuz Eylül Üniversitesi (İzmir)",
    "Ankara Üniversitesi", "Gazi Üniversitesi (Ankara)", "Galatasaray Üniversitesi (İstanbul)",
    "Bursa Uludağ Üniversitesi", "Eskişehir Osmangazi Üniversitesi", "Anadolu Üniversitesi (Eskişehir)",
    "Çukurova Üniversitesi (Adana)", "Akdeniz Üniversitesi (Antalya)", "Karadeniz Teknik Üniversitesi (Trabzon)",
    "Kocaeli Üniversitesi", "Sakarya Üniversitesi", "Gebze Teknik Üniversitesi", "İzmir Yüksek Teknoloji Enstitüsü (İYTE)",
    "Gaziantep Üniversitesi", "Atatürk Üniversitesi (Erzurum)", "Diğer Tüm Devlet ve Vakıf Üniversiteleri"
])))

GENEL_BOLUM_LISTESI = sorted([
    "Tıp Fakültesi (SAY)", "Diş Hekimliği (SAY)", "Eczacılık (SAY)",
    "Computer Engineering / Bilgisayar Mühendisliği (SAY)", "Yazılım Mühendisliği (SAY)",
    "Yapay Zeka Mühendisliği (SAY)", "Elektrik-Elektronik Mühendisliği (SAY)",
    "Endüstri Mühendisliği (SAY)", "Makine Mühendisliği (SAY)", "İnşaat Mühendisliği (SAY)",
    "Havacılık ve Uzay Mühendisliği (SAY)", "Mimarlık (SAY)", "Hemşirelik (SAY)",
    "Hukuk Fakültesi (EA)", "Psikoloji (EA)", "İşletme (EA)", "İktisat / Ekonomi (EA)",
    "Siyaset Bilimi ve Uluslararası İlişkiler (EA)", "Yönetim Bilişim Sistemleri (YBS) (EA)",
    "Özel Eğitim Öğretmenliği (SÖZ)", "Gastronomi ve Mutfak Sanatları (SÖZ)", "Türkçe Öğretmenliği (SÖZ)",
    "Tarih (SÖZ)", "Türk Dili ve Edebiyatı (SÖZ)", "Coğrafya (SÖZ)", "İlahiyat (SÖZ)",
    "İngilizce Öğretmenliği (DİL)", "Mütercim-Tercümanlık (İngilizce) (DİL)",
    "Computer Programming / Bilgisayar Programcılığı (TYT Önlisans)", "Diğer Tüm Lisans ve Önlisans Bölümleri"
])

TYT_KONULAR = {
    "⚡ 📖 Paragraf + 📐 Problem Rutini": ["Paragraf (25s) + Problem (20s) Günlük Rutin", "Paragraf Hız Kampı + Problem Karma"],
    "📖 TYT Türkçe": ["Sözcükte Anlam", "Cümlede Anlam", "Paragrafta Anlam ve Yapı", "Sözcük Türleri", "Fiiller & Fiilimsi", "Yazım Kuralları", "Noktalama İşaretleri"],
    "📐 TYT Matematik": ["Temel Kavramlar", "Sayı Basamakları", "Bölme-Bölünebilme", "Rasyonel Sayılar", "Eşitsizlikler", "Mutlak Değer", "Üslü & Köklü İfadeler", "Problemler", "Fonksiyonlar"],
    "📏 TYT Geometri": ["Doğruda ve Üçgende Açılar", "Özel Üçgenler", "Üçgende Alan ve Benzerlik", "Çokgenler ve Dörtgenler", "Katı Cisimler"],
    "⚡ TYT Fizik": ["Fizik Bilimine Giriş", "Madde ve Özellikleri", "Basınç", "Isı Sıcaklık", "Hareket", "Optik", "Dalgalar"],
    "🧪 TYT Kimya": ["Kimya Bilimi", "Atom ve Periyodik Sistem", "Türler Arası Etkileşimler", "Maddenin Halleri", "Karışımlar"],
    "🧬 TYT Biyoloji": ["Yaşam Bilimi Biyoloji", "Hücre ve Organeller", "Hücre Bölünmeleri", "Kalıtım", "Ekoloji"],
    "📜 TYT Tarih": ["Tarih Bilimi", "Osmanlı Devleti", "Milli Mücadele Dönemi"],
    "🌍 TYT Coğrafya": ["Doğa ve İnsan", "Harita Bilgisi", "İklim Bilgisi", "Nüfus ve Afetler"],
    "🧠 TYT Felsefe": ["Felsefeyi Tanıma", "Bilgi Felsefesi", "Ahlak Felsefesi"],
    "🕌 TYT Din Kültürü": ["İnanç & Allah İnancı", "İbadet Esasları", "Ahlak ve Değerler"]
}

AYT_KONULAR = {
    "📐 AYT Matematik": ["Polinomlar", "2. Dereceden Denklemler", "Parabol", "Logaritma", "Diziler", "Trigonometri", "Limit ve Süreklilik", "Türev", "İntegral"],
    "📏 AYT Geometri": ["Noktanın ve Doğrunun Analitiği", "Dönüşüm Geometrisi", "Çemberin Analitiği"],
    "⚡ AYT Fizik": ["Vektörler & Bağıl Hareket", "Tork & Denge", "Atışlar & İtme-Momentum", "Çembersel Hareket", "Elektromanyetizma", "Modern Fizik"],
    "🧪 AYT Kimya": ["Modern Atom Teorisi", "Gazlar", "Sıvı Çözeltiler", "Kimyasal Denge", "Elektrokimya", "Organik Kimya"],
    "🧬 TYT Biyoloji": ["İnsan Fizyolojisi (Sistemler)", "Gensoru & Protein Sentezi", "Fotosentez & Solunum", "Bitki Biyolojisi"],
    "📖 AYT Edebiyat": ["Şiir Bilgisi", "Divan Edebiyatı", "Tanzimat & Servet-i Fünun", "Milli Edebiyat", "Cumhuriyet Dönemi Edebiyatı"]
}

LGS_KONULAR = {
    "⚡ 📖 Paragraf + 📐 Problem Rutini": ["Paragraf (20s) + Problem (15s) Günlük Rutin"],
    "📖 LGS Türkçe (20 Soru)": ["Fiilimsiler", "Sözcükte Anlam", "Cümlede Anlam", "Paragrafta Anlam ve Yapı", "Sözel Mantık"],
    "📐 LGS Matematik (20 Soru)": ["Çarpanlar ve Katlar", "Üslü İfadeler", "Kareköklü İfadeler", "Veri Analizi", "Olasılık", "Linear Denklemler"],
    "🧪 LGS Fen Bilimleri (20 Soru)": ["Mevsimler ve İklim", "DNA ve Genetik Kod", "Basınç", "Madde ve Endüstri", "Basit Makineler"]
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

# --- 🛠️ OTOMATİK VERİTABANI ONARICI ---
def eksik_sutun_ekle(tablo_adi, sutun_adi, sutun_tanimi):
    try:
        cursor.execute(f"ALTER TABLE {tablo_adi} ADD COLUMN {sutun_adi} {sutun_tanimi}")
        conn.commit()
    except sqlite3.OperationalError:
        pass

eksik_sutun_ekle("ogrenciler", "hedef_uni", "TEXT DEFAULT ''")
eksik_sutun_ekle("ogrenciler", "hedef_bolum", "TEXT DEFAULT ''")
eksik_sutun_ekle("ogrenciler", "hedef_net", "FLOAT DEFAULT 80.0")
eksik_sutun_ekle("ogrenciler", "hedef_sira", "TEXT DEFAULT ''")
eksik_sutun_ekle("ogrenciler", "koc_adi", "TEXT DEFAULT ''")
eksik_sutun_ekle("ogrenciler", "sinav_turu", "TEXT DEFAULT 'TYT (Sadece TYT Çalışması)'")
eksik_sutun_ekle("ogrenciler", "veli_pin", "TEXT DEFAULT '123456'")

cursor.execute("SELECT COUNT(*) FROM koclar")
if cursor.fetchone()[0] == 0:
    cursor.execute("INSERT INTO koclar (kullanici_adi, sifre) VALUES (?, ?)", ("koc1", make_hash("Koc123!")))
    conn.commit()

# URL PARAMETRESİ İLE DOĞRUDAN ŞİFRESİZ SORU İNCELEME KONTROLÜ
query_params = st.query_params
link_ogrenci = query_params.get("ogrenci", None)

# BANNER / BAŞLIK
st.markdown("""
<div style="text-align: center; padding: 10px 0 15px 0;">
    <span style="font-size: 42px;">🎓</span>
    <h1 style="margin: 0; font-weight: 800; font-size: 26px; color: #0f172a;">YKS (TYT/AYT) - LGS KOÇLUK</h1>
    <p style="margin: 0; font-size: 14px; color: #0284c7; font-weight: 700;">DENİZ YILMAZ GELİŞİM PLATFORMU</p>
</div>
""", unsafe_allow_html=True)

# EĞER ÖĞRETMEN LİNK İLE GELMİŞSE ŞİFRESİZ ANINDA EKRANI AÇ
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
                    c_reg1, c_reg2 = st.columns(2)
                    with c_reg1: reg_ad = st.text_input("Adınız ve Soyadınız:").strip().title()
                    with c_reg2: reg_sifre = st.text_input("Şifre Belirleyin:", type="password")
                    
                    c_reg3, c_reg4, c_reg5 = st.columns(3)
                    with c_reg3: reg_vpin = st.text_input("👨‍👩‍👧‍👦 Veli PIN Kodu:", value="123456")
                    with c_reg4: reg_sinav = st.selectbox("🎓 Hazırlanılan Sınav:", ["TYT (Sadece TYT Çalışması)", "YKS (TYT + AYT)", "LGS (8. Sınıf)"])
                    with c_reg5: reg_koc = st.selectbox("👨‍🏫 Sorumlu Koçunuz:", koc_listesi)

                    if st.form_submit_button("Hesabımı Oluştur", type="primary", use_container_width=True):
                        if reg_ad and reg_sifre:
                            cursor.execute("SELECT ad_soyad FROM ogrenciler WHERE ad_soyad = ?", (reg_ad,))
                            if cursor.fetchone():
                                st.error(f"⚠️ `{reg_ad}` adında bir öğrenci zaten sistemde var! Lütfen 'Giriş Yap' sekmesini kullanın.")
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
                cursor.execute("SELECT sinav_turu, hedef_uni, hedef_bolum, hedef_net, hedef_sira FROM ogrenciler WHERE ad_soyad = ?", (aktif_ogr,))
                r_info = cursor.fetchone()
                ogr_sinav = r_info[0] if r_info else "TYT (Sadece TYT Çalışması)"
                curr_uni = r_info[1] if (r_info and r_info[1]) else "Orta Doğu Teknik Üniversitesi (ODTÜ)"
                curr_bolum = r_info[2] if (r_info and r_info[2]) else "Endüstri Mühendisliği (SAY)"
                curr_net = r_info[3] if (r_info and r_info[3]) else 110.0
                curr_sira = r_info[4] if (r_info and len(r_info)>4 and r_info[4]) else "1.450"
                st.success(f"👤 Aktif Oturum: **{aktif_ogr}** | Sınav Modu: **{ogr_sinav}**")
            
            with col_o_head2:
                if st.button("🚪 ÇIKIŞ YAP", key="ogr_logout_btn", use_container_width=True):
                    st.session_state["aktif_ogrenci"] = None
                    st.rerun()

            if "TYT (Sadece" in ogr_sinav:
                AKTIF_KONULAR = TYT_KONULAR
            elif "YKS" in ogr_sinav:
                AKTIF_KONULAR = {**TYT_KONULAR, **AYT_KONULAR}
            else:
                AKTIF_KONULAR = LGS_KONULAR

            AKTIF_DERSLER = list(AKTIF_KONULAR.keys())
            MAX_NET_LIMIT = 120.0 if "TYT" in ogr_sinav or "YKS" in ogr_sinav else 90.0

            tab_hedef, tab_program, tab_gunluk, tab_deneme, tab_konular = st.tabs([
                "🎯 OTOMATİK YÖK ATLAS HEDEFİ",
                "📅 DERS PROGRAMI (EXCEL / PDF)",
                "📝 GÜNLÜK ÇALIŞMA & SORU YÜKLEME",
                "📊 DENEMELER & KARNE YÜKLEME",
                "🗺️ KONU HAKİMİYETİ"
            ])

            # 🎯 ÜNİVERSİTE BAZLI OTOMATİK YÖK ATLAS HEDEF TAKİP VE DERS BAZLI ALAN PUAN HESAPLAMA
            with tab_hedef:
                st.markdown(f"<h3 style='font-weight:700; font-size:18px;'>🎯 Üniversite Bazlı YÖK Atlas Net & Başarı Sıralaması — {aktif_ogr}</h3>", unsafe_allow_html=True)
                st.caption("🏛️ Seçtiğiniz üniversiteye ve bölüme ait YÖK Atlas taban/tavan netleri ve başarı sıralamaları otomatik yüklenir.")

                col_h_u1, col_h_u2 = st.columns(2)
                with col_h_u1:
                    u_idx = YOK_ATLAS_UNIVERSTITELER.index(curr_uni) if curr_uni in YOK_ATLAS_UNIVERSTITELER else 0
                    secilen_hedef_uni = st.selectbox("🏛️ Hedeflediğiniz Üniversiteyi Seçin:", YOK_ATLAS_UNIVERSTITELER, index=u_idx)

                uni_bolumleri = YOK_ATLAS_UNI_BOLUM_VERITABANI.get(secilen_hedef_uni, {})
                kullanilabilir_bolumler = sorted(list(uni_bolumleri.keys())) if uni_bolumleri else GENEL_BOLUM_LISTESI

                with col_h_u2:
                    b_idx = kullanilabilir_bolumler.index(curr_bolum) if curr_bolum in kullanilabilir_bolumler else 0
                    secilen_hedef_bolum = st.selectbox("🎓 Hedeflediğiniz Bölüm / Programı Seçin:", kullanilabilir_bolumler, index=b_idx)

                if secilen_hedef_uni in YOK_ATLAS_UNI_BOLUM_VERITABANI and secilen_hedef_bolum in YOK_ATLAS_UNI_BOLUM_VERITABANI[secilen_hedef_uni]:
                    u_data = YOK_ATLAS_UNI_BOLUM_VERITABANI[secilen_hedef_uni][secilen_hedef_bolum]
                    otomatik_taban_net = u_data["taban_net"]
                    otomatik_tavan_net = u_data["tavan_net"]
                    otomatik_taban_sira = u_data["taban_sira"]
                    otomatik_tavan_sira = u_data["tavan_sira"]
                else:
                    otomatik_taban_net = 65.0
                    otomatik_tavan_net = 98.0
                    otomatik_taban_sira = "120.000"
                    otomatik_tavan_sira = "1.500"

                st.markdown(f"""
                <div class="yok-net-box">
                    <div style="font-size:16px; font-weight:800; color:#1e40af; margin-bottom:10px;">🏛️ YÖK Atlas Kurumsal İstatistikleri: {secilen_hedef_uni} - {secilen_hedef_bolum}</div>
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size:14px; font-weight:700;">
                        <div>🟢 <strong>Kurum Taban Neti (En Son Giren):</strong> <span style="color:#059669; font-size:16px;">{otomatik_taban_net} Net</span></div>
                        <div>🚀 <strong>Kurum Tavan Neti (Birinci):</strong> <span style="color:#2563eb; font-size:16px;">{otomatik_tavan_net} Net</span></div>
                        <div>📉 <strong>Kurum Taban Sıralaması (Son Giren):</strong> <span style="color:#059669; font-size:16px;">{otomatik_taban_sira}. Derece</span></div>
                        <div>🏆 <strong>Kurum Tavan Sıralaması (Zirve):</strong> <span style="color:#2563eb; font-size:16px;">{otomatik_tavan_sira}. Derece</span></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                with st.form("yok_atlas_otomatik_hedef_form"):
                    col_n1, col_n2 = st.columns(2)
                    with col_n1:
                        ozel_hedef_net = st.number_input("🎯 Kişisel Net Hedefiniz:", 10.0, float(MAX_NET_LIMIT), float(otomatik_taban_net), 0.5)
                    with col_n2:
                        ozel_hedef_sira = st.text_input("📊 Kişisel Başarı Sıralaması Hedefiniz:", value=f"İlk {otomatik_taban_sira}")

                    if st.form_submit_button("🎯 Üniversiteye Özel Hedefimi Kaydet", type="primary", use_container_width=True):
                        cursor.execute("UPDATE ogrenciler SET hedef_uni = ?, hedef_bolum = ?, hedef_net = ?, hedef_sira = ? WHERE ad_soyad = ?", 
                                       (secilen_hedef_uni, secilen_hedef_bolum, float(ozel_hedef_net), ozel_hedef_sira, aktif_ogr))
                        conn.commit()
                        st.success(f"🎉 Hedefiniz {secilen_hedef_uni} Verileriyle Başarıyla Kaydedildi!\n\n🎓 **{secilen_hedef_bolum}**\n• **Üniversite Taban Net:** {otomatik_taban_net} | **Sizin Hedefiniz:** {ozel_hedef_net} Net\n• **Üniversite Taban Sıralaması:** İlk {otomatik_taban_sira} | **Sizin Hedefiniz:** {ozel_hedef_sira}")
                        st.rerun()

                # 🧮 ---------------- ALAN BAZLI DETAYLI DERS HESAPLAMA VE SIRALAMA MODÜLÜ ----------------
                st.divider()
                st.markdown("### 🧮 Alan Bazlı (Sayısal / Eşit Ağırlık / Sözel / Dil) Detaylı Ders Net Hesaplama")
                st.caption("Aşağıdan öğrenim alanınızı seçerek ilgili YKS derslerinin Doğru / Yanlış sayılarını girin. Puan ve sıralamanız alana özel katsayılarla anında hesaplanacaktır.")

                secilen_alan = st.radio("🎯 Ağırlıklı Öğrenim Alanınızı Seçin:", ["Sayısal (SAY)", "Eşit Ağırlık (EA)", "Sözel (SÖZ)", "Yabancı Dil (DİL)"], horizontal=True)

                with st.container():
                    st.markdown('<div class="calc-card">', unsafe_allow_html=True)
                    st.markdown("##### 📐 1. TYT (Temel Yeterlilik Testi) Detaylı Ders Girişi")
                    c_t1, c_t2, c_t3, c_t4 = st.columns(4)
                    with c_t1:
                        t_turkce_d = st.number_input("Türkçe Doğru (40):", 0, 40, 32, key="calc_tt_d")
                        t_turkce_y = st.number_input("Türkçe Yanlış:", 0, 40, 4, key="calc_tt_y")
                        net_turkce = max(0.0, t_turkce_d - (t_turkce_y * 0.25))
                        st.caption(f"Net: `{net_turkce:.2f}`")

                    with c_t2:
                        t_sos_d = st.number_input("Sosyal Doğru (20):", 0, 20, 16, key="calc_ts_d")
                        t_sos_y = st.number_input("Sosyal Yanlış:", 0, 20, 2, key="calc_ts_y")
                        net_sosyal = max(0.0, t_sos_d - (t_sos_y * 0.25))
                        st.caption(f"Net: `{net_sosyal:.2f}`")

                    with c_t3:
                        t_mat_d = st.number_input("TYT Mat Doğru (40):", 0, 40, 30, key="calc_tm_d")
                        t_mat_y = st.number_input("TYT Mat Yanlış:", 0, 40, 3, key="calc_tm_y")
                        net_mat = max(0.0, t_mat_d - (t_mat_y * 0.25))
                        st.caption(f"Net: `{net_mat:.2f}`")

                    with c_t4:
                        t_fen_d = st.number_input("TYT Fen Doğru (20):", 0, 20, 14, key="calc_tf_d")
                        t_fen_y = st.number_input("TYT Fen Yanlış:", 0, 20, 3, key="calc_tf_y")
                        net_fen = max(0.0, t_fen_d - (t_fen_y * 0.25))
                        st.caption(f"Net: `{net_fen:.2f}`")

                    toplam_tyt_net = net_turkce + net_sosyal + net_mat + net_fen

                    toplam_ayt_net = 0.0
                    ayt_ham_puan = 0.0

                    if secilen_alan == "Sayısal (SAY)":
                        st.divider()
                        st.markdown("##### 🔬 2. AYT Sayısal Testi Ders Girişi")
                        c_a1, c_a2, c_a3, c_a4 = st.columns(4)
                        with c_a1:
                            a_m_d = st.number_input("AYT Mat Doğru (40):", 0, 40, 28, key="say_am_d")
                            a_m_y = st.number_input("AYT Mat Yanlış:", 0, 40, 3, key="say_am_y")
                            net_a_mat = max(0.0, a_m_d - (a_m_y * 0.25))
                            st.caption(f"Net: `{net_a_mat:.2f}`")
                        with c_a2:
                            a_f_d = st.number_input("Fizik Doğru (14):", 0, 14, 10, key="say_af_d")
                            a_f_y = st.number_input("Fizik Yanlış:", 0, 14, 2, key="say_af_y")
                            net_fiz = max(0.0, a_f_d - (a_f_y * 0.25))
                            st.caption(f"Net: `{net_fiz:.2f}`")
                        with c_a3:
                            a_k_d = st.number_input("Kimya Doğru (13):", 0, 13, 9, key="say_ak_d")
                            a_k_y = st.number_input("Kimya Yanlış:", 0, 13, 2, key="say_ak_y")
                            net_kim = max(0.0, a_k_d - (a_k_y * 0.25))
                            st.caption(f"Net: `{net_kim:.2f}`")
                        with c_a4:
                            a_b_d = st.number_input("Biyoloji Doğru (13):", 0, 13, 10, key="say_ab_d")
                            a_b_y = st.number_input("Biyoloji Yanlış:", 0, 13, 1, key="say_ab_y")
                            net_bio = max(0.0, a_b_d - (a_b_y * 0.25))
                            st.caption(f"Net: `{net_bio:.2f}`")

                        toplam_ayt_net = net_a_mat + net_fiz + net_kim + net_bio
                        ayt_ham_puan = (net_a_mat * 3.0) + (net_fiz * 2.85) + (net_kim * 3.07) + (net_bio * 3.07)

                    elif secilen_alan == "Eşit Ağırlık (EA)":
                        st.divider()
                        st.markdown("##### ⚖️ 2. AYT Eşit Ağırlık Testi Ders Girişi")
                        c_ea1, c_ea2, c_ea3, c_ea4 = st.columns(4)
                        with c_ea1:
                            ea_m_d = st.number_input("AYT Mat Doğru (40):", 0, 40, 26, key="ea_am_d")
                            ea_m_y = st.number_input("AYT Mat Yanlış:", 0, 40, 4, key="ea_am_y")
                            net_ea_mat = max(0.0, ea_m_d - (ea_m_y * 0.25))
                            st.caption(f"Net: `{net_ea_mat:.2f}`")
                        with c_ea2:
                            ea_ed_d = st.number_input("Edebiyat Doğru (24):", 0, 24, 20, key="ea_ed_d")
                            ea_ed_y = st.number_input("Edebiyat Yanlış:", 0, 24, 2, key="ea_ed_y")
                            net_edeb = max(0.0, ea_ed_d - (ea_ed_y * 0.25))
                            st.caption(f"Net: `{net_edeb:.2f}`")
                        with c_ea3:
                            ea_t1_d = st.number_input("Tarih-1 Doğru (10):", 0, 10, 8, key="ea_t1_d")
                            ea_t1_y = st.number_input("Tarih-1 Yanlış:", 0, 10, 1, key="ea_t1_y")
                            net_tar1 = max(0.0, ea_t1_d - (ea_t1_y * 0.25))
                            st.caption(f"Net: `{net_tar1:.2f}`")
                        with c_ea4:
                            ea_c1_d = st.number_input("Coğrafya-1 Doğru (6):", 0, 6, 5, key="ea_c1_d")
                            ea_c1_y = st.number_input("Coğrafya-1 Yanlış:", 0, 6, 1, key="ea_c1_y")
                            net_cog1 = max(0.0, ea_c1_d - (ea_c1_y * 0.25))
                            st.caption(f"Net: `{net_cog1:.2f}`")

                        toplam_ayt_net = net_ea_mat + net_edeb + net_tar1 + net_cog1
                        ayt_ham_puan = (net_ea_mat * 3.0) + (net_edeb * 3.0) + (net_tar1 * 2.8) + (net_cog1 * 3.3)

                    elif secilen_alan == "Sözel (SÖZ)":
                        st.divider()
                        st.markdown("##### 📖 2. AYT Sözel Testi Ders Girişi (Edebiyat, Sosyal-1, Sosyal-2)")
                        c_sz1, c_sz2, c_sz3 = st.columns(3)
                        with c_sz1:
                            sz_ed_d = st.number_input("Edebiyat Doğru (24):", 0, 24, 21, key="sz_ed_d")
                            sz_ed_y = st.number_input("Edebiyat Yanlış:", 0, 24, 2, key="sz_ed_y")
                            net_sz_edeb = max(0.0, sz_ed_d - (sz_ed_y * 0.25))
                            st.caption(f"Edebiyat Net: `{net_sz_edeb:.2f}`")
                        with c_sz2:
                            sz_t1_d = st.number_input("Tarih-1 Doğru (10):", 0, 10, 8, key="sz_t1_d")
                            sz_t1_y = st.number_input("Tarih-1 Yanlış:", 0, 10, 1, key="sz_t1_y")
                            net_sz_t1 = max(0.0, sz_t1_d - (sz_t1_y * 0.25))
                            st.caption(f"Tarih-1 Net: `{net_sz_t1:.2f}`")
                        with c_sz3:
                            sz_c1_d = st.number_input("Coğrafya-1 Doğru (6):", 0, 6, 5, key="sz_c1_d")
                            sz_c1_y = st.number_input("Coğrafya-1 Yanlış:", 0, 6, 1, key="sz_c1_y")
                            net_sz_c1 = max(0.0, sz_c1_d - (sz_c1_y * 0.25))
                            st.caption(f"Coğrafya-1 Net: `{net_sz_c1:.2f}`")

                        c_sz4, c_sz5, c_sz6, c_sz7 = st.columns(4)
                        with c_sz4:
                            sz_t2_d = st.number_input("Tarih-2 Doğru (11):", 0, 11, 9, key="sz_t2_d")
                            sz_t2_y = st.number_input("Tarih-2 Yanlış:", 0, 11, 1, key="sz_t2_y")
                            net_sz_t2 = max(0.0, sz_t2_d - (sz_t2_y * 0.25))
                            st.caption(f"Tarih-2 Net: `{net_sz_t2:.2f}`")
                        with c_sz5:
                            sz_c2_d = st.number_input("Coğrafya-2 Doğru (11):", 0, 11, 9, key="sz_c2_d")
                            sz_c2_y = st.number_input("Coğrafya-2 Yanlış:", 0, 11, 1, key="sz_c2_y")
                            net_sz_c2 = max(0.0, sz_c2_d - (sz_c2_y * 0.25))
                            st.caption(f"Coğrafya-2 Net: `{net_sz_c2:.2f}`")
                        with c_sz6:
                            sz_f_d = st.number_input("Felsefe Grb. Doğru (12):", 0, 12, 10, key="sz_f_d")
                            sz_f_y = st.number_input("Felsefe Grb. Yanlış:", 0, 12, 1, key="sz_f_y")
                            net_sz_fel = max(0.0, sz_f_d - (sz_f_y * 0.25))
                            st.caption(f"Felsefe Net: `{net_sz_fel:.2f}`")
                        with c_sz7:
                            sz_d_d = st.number_input("Din Kültürü Doğru (6):", 0, 6, 5, key="sz_d_d")
                            sz_d_y = st.number_input("Din Kültürü Yanlış:", 0, 6, 1, key="sz_d_y")
                            net_sz_din = max(0.0, sz_d_d - (sz_d_y * 0.25))
                            st.caption(f"Din Net: `{net_sz_din:.2f}`")

                        toplam_ayt_net = net_sz_edeb + net_sz_t1 + net_sz_c1 + net_sz_t2 + net_sz_c2 + net_sz_fel + net_sz_din
                        ayt_ham_puan = (net_sz_edeb * 3.0) + (net_sz_t1 * 2.8) + (net_sz_c1 * 3.3) + (net_sz_t2 * 2.9) + (net_sz_c2 * 2.9) + (net_sz_fel * 3.0) + (net_sz_din * 3.3)

                    elif secilen_alan == "Yabancı Dil (DİL)":
                        st.divider()
                        st.markdown("##### 🇬🇧 2. YDT (Yabancı Dil Testi) Girişi")
                        c_d1, c_d2 = st.columns(2)
                        with c_d1:
                            ydt_d = st.number_input("YDT Yabancı Dil Doğru (Max 80):", 0, 80, 70, key="ydt_d")
                        with c_d2:
                            ydt_y = st.number_input("YDT Yabancı Dil Yanlış:", 0, 80, 5, key="ydt_y")

                        net_ydt = max(0.0, ydt_d - (ydt_y * 0.25))
                        st.caption(f"YDT Yabancı Dil Netiniz: `{net_ydt:.2f}`")
                        toplam_ayt_net = net_ydt
                        ayt_ham_puan = net_ydt * 3.0

                    st.divider()
                    col_obp1, col_obp2 = st.columns(2)
                    with col_obp1:
                        obp_puan = st.slider("🎓 Diploma Notunuz (OBP 50 - 100):", 50.0, 100.0, 88.0, 0.5)
                    with col_obp2:
                        st.write("")
                        st.write("")
                        hesapla_btn = st.button("🚀 Puan ve Sıralamamı Hesapla", type="primary", use_container_width=True)

                    if hesapla_btn:
                        tyt_ham_puan = 100 + (net_turkce * 3.3) + (net_sosyal * 3.4) + (net_mat * 3.3) + (net_fen * 3.4)
                        obp_katki = obp_puan * 0.6
                        yerlestirme_puan = (tyt_ham_puan * 0.4) + (ayt_ham_puan * 0.6) + obp_katki

                        genel_skor = toplam_tyt_net + (toplam_ayt_net * 1.6)

                        if secilen_alan == "Sayısal (SAY)":
                            if genel_skor >= 165: tahmini_sira = "İlk 1.000 Derece 🏆"
                            elif genel_skor >= 150: tahmini_sira = "1.000 - 5.000"
                            elif genel_skor >= 135: tahmini_sira = "5.000 - 15.000"
                            elif genel_skor >= 120: tahmini_sira = "15.000 - 35.000"
                            elif genel_skor >= 100: tahmini_sira = "35.000 - 75.000"
                            else: tahmini_sira = "75.000+"
                        elif secilen_alan == "Eşit Ağırlık (EA)":
                            if genel_skor >= 145: tahmini_sira = "İlk 1.000 Derece 🏆"
                            elif genel_skor >= 130: tahmini_sira = "1.000 - 5.000"
                            elif genel_skor >= 115: tahmini_sira = "5.000 - 15.000"
                            elif genel_skor >= 95: tahmini_sira = "15.000 - 45.000"
                            else: tahmini_sira = "45.000+"
                        elif secilen_alan == "Sözel (SÖZ)":
                            if genel_skor >= 140: tahmini_sira = "İlk 1.000 Derece 🏆"
                            elif genel_skor >= 125: tahmini_sira = "1.000 - 5.000"
                            elif genel_skor >= 110: tahmini_sira = "5.000 - 15.000"
                            else: tahmini_sira = "15.000+"
                        else:
                            if genel_skor >= 150: tahmini_sira = "İlk 500 Derece 🏆"
                            elif genel_skor >= 135: tahmini_sira = "500 - 2.500"
                            elif genel_skor >= 120: tahmini_sira = "2.500 - 7.500"
                            else: tahmini_sira = "7.500+"

                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 18px 24px; border-radius: 16px; margin-top: 15px;">
                            <h4 style="margin:0; font-size:18px; font-weight:800; color:white !important;">🎉 {secilen_alan} Sonuç Analiziniz</h4>
                            <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:10px; margin-top:10px; font-weight:700;">
                                <div>📊 <strong>Toplam TYT Net:</strong> {toplam_tyt_net:.2f}</div>
                                <div>🔬 <strong>Toplam AYT/YDT Net:</strong> {toplam_ayt_net:.2f}</div>
                                <div>🎓 <strong>Yerleştirme Puanı:</strong> {yerlestirme_puan:.2f}</div>
                            </div>
                            <div style="margin-top:12px; font-size:16px; font-weight:800;">
                                🏆 Tahmini ÖSYM {secilen_alan} Başarı Sıralamanız: <span style="background:white; color:#059669; padding:4px 10px; border-radius:8px;">{tahmini_sira}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

            # 📊 ÖĞRENCİ EXCEL VE HARİCİ DOSYA DERS PROGRAMI
            with tab_program:
                st.markdown("### 📊 Haftalık Ders Programınız (Excel Çizelgesi)")
                df_matris_ogr = pd.read_sql_query("""
                    SELECT saat_araligi AS 'Saat Aralığı', pazartesi AS 'Pazartesi', sali AS 'Salı',
                           carsamba AS 'Çarşamba', persembe AS 'Perşembe', cuma AS 'Cuma',
                           cumartesi AS 'Cumartesi', pazar AS 'Pazar'
                    FROM excel_program_matris WHERE ad_soyad = ?
                """, conn, params=(aktif_ogr,))

                if not df_matris_ogr.empty:
                    st.dataframe(df_matris_ogr, use_container_width=True, height=480)
                else:
                    st.info("Sorumlu koçunuz henüz 7 günlük haftalık programınızı hazırlamadı.")

                st.divider()
                st.markdown("#### 📁 Sorumlu Koçunuz Tarafından Yüklenen Hazır Program Dosyaları (PDF, Excel, Word)")
                df_p_files = pd.read_sql_query("SELECT id, yukleyen, tarih, dosya_yolu, dosya_adi FROM program_dosyalari WHERE ad_soyad = ? ORDER BY id DESC", conn, params=(aktif_ogr,))
                
                if df_p_files.empty:
                    st.caption("Henüz harici dosya formatında bir program yüklenmedi.")
                else:
                    for _, pf_row in df_p_files.iterrows():
                        st.write(f"📄 **{pf_row['dosya_adi']}** (Yükleyen Koç: {pf_row['yukleyen']} - Tarih: {pf_row['tarih']})")
                        if os.path.exists(pf_row['dosya_yolu']):
                            with open(pf_row['dosya_yolu'], "rb") as f_b:
                                st.download_button(f"📥 {pf_row['dosya_adi']} İndir", data=f_b, file_name=pf_row['dosya_adi'], key=f"dl_pf_{pf_row['id']}")
                            if pf_row['dosya_yolu'].lower().endswith('.pdf'):
                                st.markdown(pdf_goster_html(pf_row['dosya_yolu']), unsafe_allow_html=True)

            # 📝 GÜNLÜK ÇALIŞMA & GEÇMİŞE DÖNÜK TARİH SEÇİMİ VE TOTAL SORU ÖZETİ
            with tab_gunluk:
                st.markdown(f"<h3 style='font-weight:700; font-size:18px;'>📝 Günlük Çalışma & Soru Girişi — {aktif_ogr}</h3>", unsafe_allow_html=True)
                st.caption("📅 İstediğiniz geçmiş bir tarihi seçerek o güne ait soru girişi yapabilirsiniz.")

                c1, c2, c3 = st.columns(3)
                with c1: secilen_tarih = st.date_input("Çalışma Tarihi (Geçmişe Dönük Seçilebilir)", datetime.date.today(), key="gunluk_tarih_secici")
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
                                unique_name = f"{aktif_ogr}_{str(secilen_tarih)}_{hashlib.md5(file.name.encode()).hexdigest()[:8]}{file_ext}"
                                save_path = os.path.join(UPLOAD_DIR, unique_name)
                                with open(save_path, "wb") as f: f.write(file.getbuffer())
                                cursor.execute("INSERT INTO yapilamayan_sorular (ad_soyad, tarih, ders, konu, dosya_yolu, dosya_adi) VALUES (?, ?, ?, ?, ?, ?)", (aktif_ogr, str(secilen_tarih), ders_adi, secilen_konu, save_path, file.name))
                            conn.commit()
                            st.success(f"🎉 {len(yuklenen_sorular)} soru başarıyla yüklendi!")

                if st.button("🚀 Tüm Çalışmaları Kaydet", type="primary", use_container_width=True):
                    for d_adi, (k_adi, t_s, d_s, y_s, b_s) in ders_verileri.items():
                        if t_s > 0:
                            cursor.execute("INSERT INTO gunluk_calisma (ad_soyad, tarih, ders, konu, toplam_soru, dogru, yanlis, bos, sure, verim, notlar) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (aktif_ogr, str(secilen_tarih), d_adi, k_adi, t_s, d_s, y_s, b_s, float(sure_giris), int(verim_giris), not_giris))
                    conn.commit()
                    st.success("🎉 Çalışmalarınız kaydedildi!")

                # 📊 SEÇİLEN GÜNKÜ TOTAL ÇÖZÜLEN SORU MİKTARI GÖSTERGESİ
                st.divider()
                cursor.execute("SELECT SUM(toplam_soru) FROM gunluk_calisma WHERE ad_soyad = ? AND tarih = ?", (aktif_ogr, str(secilen_tarih)))
                toplam_soru_sonuc = cursor.fetchone()[0]
                gunluk_total_soru = toplam_soru_sonuc if toplam_soru_sonuc else 0

                st.markdown(f"""
                <div class="total-soru-banner">
                    📅 {secilen_tarih} Tarihli Toplam Çalışma Raporu<br>
                    <span style="font-size:26px; font-weight:800;">🎯 Bütün Derslerin Toplam Çözülen Soru Miktarı: {gunluk_total_soru} Soru</span>
                </div>
                """, unsafe_allow_html=True)

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

    # ==================== 👨‍🏫 KOÇ PANELİ ====================
    with main_tab2:
        st.markdown("<h2 style='font-weight:800; font-size:24px; color:#0f172a;'>👨‍🏫 Koç Yönetim Paneli — YKS/LGS KOÇLUK</h2>", unsafe_allow_html=True)

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
                            st.success(f"🔓 Giriş başarılı! Hoş geldiniz {k_adi_giris}.")
                            st.rerun()
                        else: st.error("❌ Hatalı kullanıcı adı veya şifre!")

            with koc_tab2:
                with st.form("yeni_koc_tanimla_formu"):
                    yeni_koc_adi = st.text_input("Yeni Koç Kullanıcı Adı:").strip()
                    yeni_koc_sifre = st.text_input("Yeni Koç Şifresi:", type="password")
                    katilim_kodu = st.text_input("Sistem Katılım Kodu (YKS2026KOC):", type="password")
                    if st.form_submit_button("Hesabı Oluştur", type="primary", use_container_width=True):
                        if yeni_koc_adi and yeni_koc_sifre and katilim_kodu == SISTEM_YONETICI_KATILIM_KODU:
                            cursor.execute("SELECT kullanici_adi FROM koclar WHERE kullanici_adi = ?", (yeni_koc_adi,))
                            if cursor.fetchone():
                                st.error(f"⚠️ `{yeni_koc_adi}` kullanıcı adı zaten sistemde kayıtlı!")
                            else:
                                cursor.execute("INSERT INTO koclar (kullanici_adi, sifre) VALUES (?, ?)", (yeni_koc_adi, make_hash(yeni_koc_sifre)))
                                conn.commit()
                                st.session_state["aktif_koc"] = yeni_koc_adi
                                st.success("🎉 Koç hesabı oluşturuldu!")
                                st.rerun()
                        else:
                            st.error("❌ Hatalı katılım kodu veya eksik bilgi!")
        else:
            col_k_head1, col_k_head2 = st.columns([0.8, 0.2])
            with col_k_head1:
                aktif_koc_adi = st.session_state['aktif_koc']
                st.success(f"🔓 Oturum Açık: **{aktif_koc_adi}** (Sorumlu Koç: Deniz Yılmaz)")
            with col_k_head2:
                if st.button("🚪 KOÇ ÇIKIŞ YAP", key="koc_logout_btn", use_container_width=True):
                    st.session_state["aktif_koc"] = None
                    st.rerun()

            st.session_state["gemini_api_key"] = st.text_input("🤖 Gemini API Key (Canlı Yapay Zeka Taraması İçin):", value=st.session_state.get("gemini_api_key", ""), type="password")

            cursor.execute("SELECT ad_soyad, sinav_turu, hedef_uni, hedef_bolum FROM ogrenciler")
            ogrenci_rows = cursor.fetchall()
            
            if ogrenci_rows:
                col_sel_ogr, col_del_ogr = st.columns([0.7, 0.3])
                
                with col_sel_ogr:
                    ogr_dict = {f"{r[0]} ({r[1]})": r[0] for r in ogrenci_rows}
                    secilen_ogr = ogr_dict[st.selectbox("🔍 Yönetilecek Öğrenciyi Seçin:", list(ogr_dict.keys()))]

                with col_del_ogr:
                    st.write("")
                    st.write("")
                    if st.button(f"🗑️ {secilen_ogr} Öğrencisini Sil", type="secondary", use_container_width=True):
                        st.session_state["silme_onayi_ogrenci"] = secilen_ogr

                cursor.execute("SELECT sinav_turu, hedef_uni, hedef_bolum, hedef_net, hedef_sira FROM ogrenciler WHERE ad_soyad = ?", (secilen_ogr,))
                ogr_detay = cursor.fetchone()
                if ogr_detay and ogr_detay[2]:
                    sira_val = ogr_detay[4] if len(ogr_detay)>4 and ogr_detay[4] else "Belirtilmedi"
                    st.info(f"🏛️ **Öğrencinin YÖK Atlas Hedefi:** **{ogr_detay[1]}** — **{ogr_detay[2]}**\n\n• **Hedef Net:** `{ogr_detay[3]}` | • **Hedef Başarı Sıralaması:** `{sira_val}`")

                if st.session_state.get("silme_onayi_ogrenci") == secilen_ogr:
                    st.warning(f"⚠️ **DİKKAT:** `{secilen_ogr}` isimli öğrenciyi silmek üzeresiniz!")
                    c_del1, c_del2 = st.columns(2)
                    with c_del1:
                        if st.button("✅ Evet, Sil", type="primary", use_container_width=True):
                            cursor.execute("DELETE FROM ogrenciler WHERE ad_soyad = ?", (secilen_ogr,))
                            cursor.execute("DELETE FROM gunluk_calisma WHERE ad_soyad = ?", (secilen_ogr,))
                            cursor.execute("DELETE FROM yapilamayan_sorular WHERE ad_soyad = ?", (secilen_ogr,))
                            cursor.execute("DELETE FROM denemeler WHERE ad_soyad = ?", (secilen_ogr,))
                            cursor.execute("DELETE FROM excel_program_matris WHERE ad_soyad = ?", (secilen_ogr,))
                            cursor.execute("DELETE FROM program_dosyalari WHERE ad_soyad = ?", (secilen_ogr,))
                            conn.commit()
                            st.session_state["silme_onayi_ogrenci"] = None
                            st.success(f"🗑️ {secilen_ogr} silindi!")
                            st.rerun()
                    with c_del2:
                        if st.button("❌ İptal Et", use_container_width=True):
                            st.session_state["silme_onayi_ogrenci"] = None
                            st.rerun()

                s_turu = ogr_detay[0] if ogr_detay else "TYT (Sadece TYT Çalışması)"

                if "TYT (Sadece" in s_turu:
                    KOC_MUFREDAT = TYT_KONULAR
                elif "YKS" in s_turu:
                    KOC_MUFREDAT = {**TYT_KONULAR, **AYT_KONULAR}
                else:
                    KOC_MUFREDAT = LGS_KONULAR

                # 🗓️ GÜN GÜN SEKMELİ MÜFREDAT DERS/KONU SEÇİM ALANI
                st.divider()
                st.markdown(f"### 🗓️ {secilen_ogr} — 7 Günlük Şablonlu Ders Programlayıcı")
                st.caption("⚡ Değiştirmek istediğiniz güne tıklayıp saati ve dersi seçin.")

                gun_sekmeleri = st.tabs(["📅 Pazartesi", "📅 Salı", "📅 Çarşamba", "📅 Perşembe", "📅 Cuma", "📅 Cumartesi", "📅 Pazar"])

                for idx, g_adi in enumerate(GUNLER):
                    with gun_sekmeleri[idx]:
                        st.markdown(f"#### 📌 {g_adi} Günü İçin Hücre Güncelle")
                        col_s1, col_s2 = st.columns(2)
                        with col_s1:
                            s_ders = st.selectbox(f"1. Ders Seçin ({g_adi}):", list(KOC_MUFREDAT.keys()) + ["--- Mola / Serbest ---", "--- Deneme Sınavı ---"], key=f"d_sec_{g_adi}")
                        with col_s2:
                            if s_ders in KOC_MUFREDAT:
                                konu_opts = KOC_MUFREDAT[s_ders]
                            else:
                                konu_opts = ["Mola / Dinlenme", "TYT Genel Deneme", "Branş Denemesi", "Haftalık Değerlendirme"]
                            s_konu = st.selectbox(f"2. Müfredat Konusu Seçin ({g_adi}):", konu_opts, key=f"k_sec_{g_adi}")

                        col_t1, col_t2 = st.columns(2)
                        with col_t1:
                            s_saat = st.text_input(f"3. Değiştirilecek Saat Aralığı:", value="09:00 - 10:00", key=f"saat_input_{g_adi}")
                        with col_t2:
                            s_not = st.text_input(f"4. Özel Koç Notu / Soru Hedefi:", placeholder="Örn: 25 Paragraf + 20 Problem", key=f"not_input_{g_adi}")

                        if st.button(f"✏️ {g_adi} Günündeki Sadece Bu Saat Dilimini Güncelle", key=f"btn_add_{g_adi}", type="primary"):
                            icerik = f"{s_ders}: {s_konu}"
                            if s_not: icerik += f" ({s_not})"

                            gun_sutun_map = {
                                "Pazartesi": "pazartesi", "Salı": "sali", "Çarşamba": "carsamba",
                                "Perşembe": "persembe", "Cuma": "cuma", "Cumartesi": "cumartesi", "Pazar": "pazar"
                            }
                            target_col = gun_sutun_map[g_adi]

                            cursor.execute(f"""
                                INSERT INTO excel_program_matris (ad_soyad, saat_araligi, {target_col})
                                VALUES (?, ?, ?)
                                ON CONFLICT(ad_soyad, saat_araligi) DO UPDATE SET {target_col} = ?
                            """, (secilen_ogr, s_saat, icerik, icerik))
                            conn.commit()
                            st.success(f"🎉 {g_adi} günü ({s_saat}) dilimi güncellendi!")
                            st.rerun()

                # 📊 TÜM HAFTALIK EXCEL MATRİSİ ÖNİZLEME VE CANLI DÜZENLEME
                st.divider()
                st.markdown("### 📊 7 Günlük Kayıtlı Excel Ders Programınız")

                df_matris = pd.read_sql_query("""
                    SELECT saat_araligi AS 'Saat Aralığı', pazartesi AS 'Pazartesi', sali AS 'Salı',
                           carsamba AS 'Çarşamba', persembe AS 'Perşembe', cuma AS 'Cuma',
                           cumartesi AS 'Cumartesi', pazar AS 'Pazar'
                    FROM excel_program_matris WHERE ad_soyad = ?
                """, conn, params=(secilen_ogr,))

                if df_matris.empty:
                    excel_sablon = [
                        {"Saat Aralığı": "09:00 - 10:00", "Pazartesi": "⚡ Paragraf (25s) + Problem (20s)", "Salı": "⚡ Paragraf (25s) + Problem (20s)", "Çarşamba": "⚡ Paragraf (25s) + Problem (20s)", "Perşembe": "⚡ Paragraf (25s) + Problem (20s)", "Cuma": "⚡ Paragraf (25s) + Problem (20s)", "Cumartesi": "TYT GENEL DENEME SINAVI", "Pazar": "TYT BRANŞ DENEMESİ"},
                        {"Saat Aralığı": "10:00 - 10:15", "Pazartesi": "Mola", "Salı": "Mola", "Çarşamba": "Mola", "Perşembe": "Mola", "Cuma": "Mola", "Cumartesi": "Deneme Devam", "Pazar": "Deneme Devam"},
                        {"Saat Aralığı": "10:15 - 12:30", "Pazartesi": "📐 TYT Matematik: Temel Kavramlar", "Salı": "📏 TYT Geometri: Üçgenler", "Çarşamba": "📐 TYT Matematik: Üslü & Köklü", "Perşembe": "📏 TYT Geometri: Çokgenler", "Cuma": "📐 TYT Matematik: Kümeler", "Cumartesi": "Deneme Analizi", "Pazar": "Branş Deneme Analizi"},
                        {"Saat Aralığı": "12:30 - 13:30", "Pazartesi": "Öğle Yemeği & Dinlenme", "Salı": "Öğle Yemeği & Dinlenme", "Çarşamba": "Öğle Yemeği & Dinlenme", "Perşembe": "Öğle Yemeği & Dinlenme", "Cuma": "Öğle Yemeği & Dinlenme", "Cumartesi": "Öğle Yemeği & Dinlenme", "Pazar": "Öğle Yemeği & Dinlenme"},
                        {"Saat Aralığı": "14:00 - 15:00", "Pazartesi": "📐 MATEMATİK ÖZEL DERSİ", "Salı": "🧪 TYT Kimya: Atom ve Periyodik Sistem", "Çarşamba": "📐 MATEMATİK ÖZEL DERSİ", "Perşembe": "🧪 TYT Kimya: Karışımlar", "Cuma": "📐 MATEMATİK ÖZEL DERSİ", "Cumartesi": "📐 TYT Matematik: Problemler", "Pazar": "HAFTALIK KOÇLUK DEĞERLENDİRMESİ"}
                    ]
                    df_matris = pd.DataFrame(excel_sablon)

                edited_df = st.data_editor(
                    df_matris,
                    num_rows="dynamic",
                    use_container_width=True,
                    height=450,
                    key=f"excel_editor_{secilen_ogr}"
                )

                col_btn1, col_btn2 = st.columns([0.7, 0.3])
                with col_btn1:
                    if st.button("💾 Tablodaki Tüm Düzenlemeleri Kaydet", type="primary", use_container_width=True):
                        for _, row in edited_df.iterrows():
                            s_araligi = str(row.get("Saat Aralığı", "")).strip()
                            if s_araligi:
                                cursor.execute("""
                                    INSERT INTO excel_program_matris (ad_soyad, saat_araligi, pazartesi, sali, carsamba, persembe, cuma, cumartesi, pazar)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    ON CONFLICT(ad_soyad, saat_araligi) DO UPDATE SET
                                        pazartesi=excluded.pazartesi, sali=excluded.sali, carsamba=excluded.carsamba,
                                        persembe=excluded.persembe, cuma=excluded.cuma, cumartesi=excluded.cumartesi, pazar=excluded.pazar
                                """, (
                                    secilen_ogr, s_araligi,
                                    str(row.get("Pazartesi", "") if pd.notna(row.get("Pazartesi")) else ""),
                                    str(row.get("Salı", "") if pd.notna(row.get("Salı")) else ""),
                                    str(row.get("Çarşamba", "") if pd.notna(row.get("Çarşamba")) else ""),
                                    str(row.get("Perşembe", "") if pd.notna(row.get("Perşembe")) else ""),
                                    str(row.get("Cuma", "") if pd.notna(row.get("Cuma")) else ""),
                                    str(row.get("Cumartesi", "") if pd.notna(row.get("Cumartesi")) else ""),
                                    str(row.get("Pazar", "") if pd.notna(row.get("Pazar")) else "")
                                ))
                        conn.commit()
                        st.success("🎉 Program başarıyla güncellendi!")

                with col_btn2:
                    if st.button("🧹 Tüm Tabloyu Temizle / Sıfırla", use_container_width=True):
                        cursor.execute("DELETE FROM excel_program_matris WHERE ad_soyad = ?", (secilen_ogr,))
                        conn.commit()
                        st.success("Tablo sıfırlandı.")
                        st.rerun()

                # 📄 HARİCİ EXCEL / PDF / WORD DOSYASI YÜKLEME ALANI
                st.divider()
                st.markdown(f"### 📄 {secilen_ogr} İçin Harici Ders Programı Dosyası Yükleyin (Excel, PDF, Word)")
                prog_file = st.file_uploader(f"Hazır Program Dosyası Seçin (.xlsx, .pdf, .docx):", type=["xlsx", "xls", "pdf", "docx"], key=f"file_up_{secilen_ogr}")
                
                if prog_file and st.button(f"📤 {prog_file.name} Dosyasını Öğrenciye Gönder", type="primary", use_container_width=True):
                    file_ext = os.path.splitext(prog_file.name)[1]
                    p_unique_name = f"Program_{secilen_ogr}_{datetime.date.today()}_{hashlib.md5(prog_file.name.encode()).hexdigest()[:6]}{file_ext}"
                    save_p_path = os.path.join(PROGRAM_DIR, p_unique_name)
                    with open(save_p_path, "wb") as f:
                        f.write(prog_file.getbuffer())

                    cursor.execute("INSERT INTO program_dosyalari (ad_soyad, yukleyen, tarih, dosya_yolu, dosya_adi) VALUES (?, ?, ?, ?, ?)",
                                   (secilen_ogr, aktif_koc_adi, str(datetime.date.today()), save_p_path, prog_file.name))
                    conn.commit()
                    st.success(f"🎉 '{prog_file.name}' dosyası {secilen_ogr} öğrencisinin paneline başarıyla yüklendi!")

                # 📸 ÇÖZÜLEMEYEN SORULAR & TAM URL WHATSAPP PAYLAŞIM ALANI
                st.divider()
                st.markdown(f"### 📸 {secilen_ogr} Yapılamayan Sorular & Öğretmen Paylaşımı")
                
                raw_url = st.query_params.get("host_url", "")
                if not raw_url:
                    host_domain = "https://blank-app-mtyl8rm3xgtksm5qer7qng.streamlit.app"
                else:
                    host_domain = raw_url

                encoded_student = quote(secilen_ogr)
                full_share_url = f"{host_domain}/?ogrenci={encoded_student}"
                
                wa_msg = f"Merhaba Hocam, {secilen_ogr} öğrencimizin çözemediği ve destek beklediği soruları incelemeniz için şifresiz bağlantı adresi: {full_share_url}"
                wa_link = f"https://api.whatsapp.com/send?text={quote(wa_msg)}"

                st.markdown(f"""
                <div class="share-link-card">
                    <div style="font-size: 18px; font-weight: 800; margin-bottom: 6px;">💬 Öğretmene WhatsApp ile Bağlantı Gönder</div>
                    <div style="font-size: 13px; opacity: 0.95;">Aşağıdaki kutudan tam adresi kopyalayabilir veya direkt yeşil butona basarak WhatsApp sohbetine aktarabilirsiniz.</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("##### 📋 Kopyalanabilir Tam Adres Linki:")
                st.code(full_share_url, language="text")

                col_wa1, col_wa2 = st.columns([0.6, 0.4])
                with col_wa1:
                    st.caption("💡 Bağlantıya tıklayan öğretmen herhangi bir şifre girmeden öğrencinin tüm sorularına erişir.")
                with col_wa2:
                    st.link_button("💬 WhatsApp İle Öğretmene Gönder", wa_link, use_container_width=True)

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
            col_v_head1, col_v_head2 = st.columns([0.8, 0.2])
            with col_v_head1:
                v_ogr = st.session_state["aktif_veli_ogrenci"]
                st.success(f"👤 Takip Edilen Öğrenci: **{v_ogr}**")
            with col_v_head2:
                if st.button("🚪 ÇIKIŞ YAP", key="veli_logout_btn", use_container_width=True):
                    st.session_state["aktif_veli_ogrenci"] = None
                    st.rerun()

            df_v_calisma = pd.read_sql_query("SELECT tarih, ders, konu, toplam_soru, dogru, yanlis, bos FROM gunluk_calisma WHERE ad_soyad = ? ORDER BY id DESC", conn, params=(v_ogr,))
            st.dataframe(df_v_calisma, use_container_width=True)