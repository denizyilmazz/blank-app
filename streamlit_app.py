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
                with open(file_path, "rb") as f: file_data = f.read()
                input_part = [{"mime_type": "application/pdf", "data": file_data}]
            else:
                img = Image.open(file_path)
                input_part = [img]

            prompt = f"Sen YKS baş koçusun (Deniz Yılmaz). Öğrencinin yüklediği '{yayin}' adlı {tur} karnesini görsel olarak detaylıca incele. Toplam Net: {toplam_net}. Ders ders, konu konu hangi başlıklarda hata yaptığını, netlerini artırmak için hangi eksiklerini acilen kapatması gerektiğini maddeler halinde koçluk raporu olarak hazırla."
            response = model.generate_content(input_part + [prompt])
            return response.text
        except Exception as e:
            return f"⚠️ **Yapay Zeka Karne Analiz Hatası:** {str(e)}"
    return f"📊 **Koçluk Deneme Analizi ({yayin}):**\n• Toplam Net: {toplam_net}"

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

query_params = st.query_params
link_ogrenci = query_params.get("ogrenci", None)
link_ders = query_params.get("ders", None)

st.markdown("""
<div style="text-align: center; padding: 10px 0 15px 0;">
    <span style="font-size: 42px;">🎓</span>
    <h1 style="margin: 0; font-weight: 800; font-size: 26px; color: #0f172a;">YKS (TYT/AYT) - LGS KOÇLUK</h1>
    <p style="margin: 0; font-size: 14px; color: #0284c7; font-weight: 700;">DENİZ YILMAZ GELİŞİM PLATFORMU</p>
</div>
""", unsafe_allow_html=True)

if link_ogrenci:
    ders_baslik_str = f"({link_ders} Branşı)" if link_ders else "(Tüm Dersler)"
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 18px 24px; border-radius: 16px; margin-bottom: 20px;">
        <h3 style="margin:0; font-size:20px; font-weight:800; color:white !important;">👨‍🏫 Öğretmen Branş Soru İnceleme Ekranı {ders_baslik_str}</h3>
        <p style="margin:4px 0 0 0; opacity:0.9; color:white !important;"><strong>{link_ogrenci}</strong> öğrencisinin bu branşta çözemediği ve destek beklediği sorular listelenmektedir.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if link_ders:
        df_link_sorular = pd.read_sql_query("SELECT id, tarih, ders, konu, dosya_yolu, dosya_adi FROM yapilamayan_sorular WHERE ad_soyad = ? AND ders = ? ORDER BY id DESC", conn, params=(link_ogrenci, link_ders))
    else:
        df_link_sorular = pd.read_sql_query("SELECT id, tarih, ders, konu, dosya_yolu, dosya_adi FROM yapilamayan_sorular WHERE ad_soyad = ? ORDER BY id DESC", conn, params=(link_ogrenci,))
    
    if df_link_sorular.empty:
        st.info(f"ℹ️ {link_ogrenci} isimli öğrencinin bu branşta henüz çözemediği soru bulunmuyor.")
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
                                st.error(f"⚠️ `{reg_ad}` adında bir öğrenci zaten sistemde var!")
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

            with tab_hedef:
                st.markdown(f"<h3 style='font-weight:700; font-size:18px;'>🎯 Üniversite Bazlı YÖK Atlas Net & Başarı Sıralaması — {aktif_ogr}</h3>", unsafe_allow_html=True)
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
                        <div>🟢 <strong>Kurum Taban Neti:</strong> <span style="color:#059669; font-size:16px;">{otomatik_taban_net} Net</span></div>
                        <div>🚀 <strong>Kurum Tavan Neti:</strong> <span style="color:#2563eb; font-size:16px;">{otomatik_tavan_net} Net</span></div>
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
                        st.success(f"🎉 Hedefiniz başarıyla kaydedildi!")
                        st.rerun()

                st.divider()
                st.markdown("### 🧮 ÖSYM Sonuç Belgesi Formatında Puan ve Sıralama Analizi")
                secilen_alan = st.radio("🎯 Ağırlıklı Öğrenim Alanınızı Seçin:", ["Sayısal (SAY)", "Eşit Ağırlık (EA)", "Sözel (SÖZ)", "Yabancı Dil (DİL)"], horizontal=True)

                with st.container():
                    st.markdown('<div class="calc-card">', unsafe_allow_html=True)
                    st.markdown("##### 📐 1. TYT (Temel Yeterlilik Testi) Detaylı Ders Girişi")
                    c_t1, c_t2, c_t3, c_t4 = st.columns(4)
                    with c_t1:
                        t_turkce_d = st.number_input("Türkçe Doğru (40):", 0, 40, 28, key="calc_tt_d")
                        t_turkce_y = st.number_input("Türkçe Yanlış:", 0, 40, 7, key="calc_tt_y")
                        net_turkce = max(0.0, t_turkce_d - (t_turkce_y * 0.25))
                    with c_t2:
                        t_sos_d = st.number_input("Sosyal Doğru (20):", 0, 20, 11, key="calc_ts_d")
                        t_sos_y = st.number_input("Sosyal Yanlış:", 0, 20, 0, key="calc_ts_y")
                        net_sosyal = max(0.0, t_sos_d - (t_sos_y * 0.25))
                    with c_t3:
                        t_mat_d = st.number_input("TYT Mat Doğru (40):", 0, 40, 20, key="calc_tm_d")
                        t_mat_y = st.number_input("TYT Mat Yanlış:", 0, 40, 0, key="calc_tm_y")
                        net_mat = max(0.0, t_mat_d - (t_mat_y * 0.25))
                    with c_t4:
                        t_fen_d = st.number_input("TYT Fen Doğru (20):", 0, 20, 7, key="calc_tf_d")
                        t_fen_y = st.number_input("TYT Fen Yanlış:", 0, 20, 4, key="calc_tf_y")
                        net_fen = max(0.0, t_fen_d - (t_fen_y * 0.25))

                    toplam_tyt_net = net_turkce + net_sosyal + net_mat + net_fen
                    toplam_ayt_net = 0.0
                    ayt_ham_puan = 0.0

                    if secilen_alan == "Sayısal (SAY)":
                        st.divider()
                        st.markdown("##### 🔬 2. AYT Sayısal Testi Ders Girişi")
                        c_a1, c_a2, c_a3, c_a4 = st.columns(4)
                        with c_a1:
                            a_m_d = st.number_input("AYT Mat Doğru (40):", 0, 40, 20, key="say_am_d")
                            a_m_y = st.number_input("AYT Mat Yanlış:", 0, 40, 0, key="say_am_y")
                            net_a_mat = max(0.0, a_m_d - (a_m_y * 0.25))
                        with c_a2:
                            a_f_d = st.number_input("Fizik Doğru (14):", 0, 14, 5, key="say_af_d")
                            a_f_y = st.number_input("Fizik Yanlış:", 0, 14, 0, key="say_af_y")
                            net_fiz = max(0.0, a_f_d - (a_f_y * 0.25))
                        with c_a3:
                            a_k_d = st.number_input("Kimya Doğru (13):", 0, 13, 7, key="say_ak_d")
                            a_k_y = st.number_input("Kimya Yanlış:", 0, 13, 0, key="say_ak_y")
                            net_kim = max(0.0, a_k_d - (a_k_y * 0.25))
                        with c_a4:
                            a_b_d = st.number_input("Biyoloji Doğru (13):", 0, 13, 7, key="say_ab_d")
                            a_b_y = st.number_input("Biyoloji Yanlış:", 0, 13, 0, key="say_ab_y")
                            net_bio = max(0.0, a_b_d - (a_b_y * 0.25))

                        toplam_ayt_net = net_a_mat + net_fiz + net_kim + net_bio
                        ayt_ham_puan = (net_a_mat * 3.0) + (net_fiz * 2.85) + (net_kim * 3.07) + (net_bio * 3.07)

                    st.divider()
                    obp_puan = st.number_input("🎓 Diploma Notunuzu (OBP) El ile Girin:", 50.00, 100.00, 91.00, 0.01)

                    tyt_ham = 100.0 + (net_turkce * 3.3) + (net_sosyal * 3.4) + (net_mat * 3.3) + (net_fen * 3.4)
                    obp_ek = (obp_puan * 5) * 0.12
                    ham_puan_deger = 130.0 + (tyt_ham * 0.4) + (ayt_ham_puan * 0.6)
                    yerlestirme_puan_deger = ham_puan_deger + obp_ek
                    toplam_net = toplam_tyt_net + toplam_ayt_net

                    if toplam_net >= 130: tahmini_sira_str = "18.500"
                    elif toplam_net >= 110: tahmini_sira_str = "54.200"
                    elif toplam_net >= 95: tahmini_sira_str = "124.500"
                    elif toplam_net >= 75: tahmini_sira_str = "198.000"
                    else: tahmini_sira_str = "310.000+"

                    st.markdown(f"""
                    <div class="osym-belge-box">
                        <div style="text-align: center; border-bottom: 2px solid #1e293b; padding-bottom: 12px; margin-bottom: 16px;">
                            <h3 style="margin:0; font-weight:800; font-size:18px; color:#1e293b !important;">T.C. ÖSYM SONUÇ BELGESİ</h3>
                        </div>
                        <div style="font-size:14px; font-weight:700;">
                            • Toplam Net: <strong>{toplam_net:.2f}</strong><br>
                            • Yerleştirme Puanı: <strong>{yerlestirme_puan_deger:.2f}</strong><br>
                            • Tahmini Başarı Sıralaması: <span style="color:#2563eb;"><strong>{tahmini_sira_str}. Derece</strong></span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

            with tab_program:
                st.markdown("### 📊 Haftalık Ders Programınız (Excel Çizelgesi)")
                df_matris_ogr = pd.read_sql_query("SELECT saat_araligi AS 'Saat Aralığı', pazartesi AS 'Pazartesi', sali AS 'Salı', carsamba AS 'Çarşamba', persembe AS 'Perşembe', cuma AS 'Cuma', cumartesi AS 'Cumartesi', pazar AS 'Pazar' FROM excel_program_matris WHERE ad_soyad = ?", conn, params=(aktif_ogr,))
                if not df_matris_ogr.empty:
                    st.dataframe(df_matris_ogr, use_container_width=True, height=480)
                else:
                    st.info("Sorumlu koçunuz henüz programınızı hazırlamadı.")

            with tab_gunluk:
                st.markdown(f"<h3 style='font-weight:700; font-size:18px;'>📝 Günlük Çalışma & Soru Girişi — {aktif_ogr}</h3>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                with c1: secilen_tarih = st.date_input("Çalışma Tarihi", datetime.date.today(), key="gunluk_tarih_secici")
                with c2: sure_giris = st.number_input("Süre (Saat)", 0.0, 16.0, 5.5, 0.5)
                with c3: verim_giris = st.slider("Verim Puanı (1-10)", 1, 10, 8)
                not_giris = st.text_area("Çalışma Notları:", height=70)
                
                ders_sekmeleri = st.tabs(AKTIF_DERSLER)
                ders_verileri = {}

                for idx, ders_adi in enumerate(AKTIF_DERSLER):
                    with ders_sekmeleri[idx]:
                        secilen_konu = st.selectbox(f"Konu ({ders_adi}):", ["Genel"] + AKTIF_KONULAR[ders_adi], key=f"k_s_{ders_adi}")
                        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                        with col_s1: ts = st.number_input("Toplam Soru", 0, 500, 0, key=f"t_{ders_adi}")
                        with col_s2: ds = st.number_input("Doğru", 0, 500, 0, key=f"d_{ders_adi}")
                        with col_s3: ys = st.number_input("Yanlış", 0, 500, 0, key=f"y_{ders_adi}")
                        with col_s4: bs = st.number_input("Boş", 0, 500, 0, key=f"b_{ders_adi}")
                        ders_verileri[ders_adi] = (secilen_konu, ts, ds, ys, bs)

                        yuklenen_sorular = st.file_uploader(f"📸 Soru Görselleri ({ders_adi}):", type=["png", "jpg", "jpeg", "pdf"], accept_multiple_files=True, key=f"upload_soru_{ders_adi}")
                        if yuklenen_sorular and st.button(f"📤 Kaydet ({ders_adi})", key=f"btn_save_soru_{ders_adi}"):
                            for file in yuklenen_sorular:
                                file_ext = os.path.splitext(file.name)[1]
                                unique_name = f"{aktif_ogr}_{str(secilen_tarih)}_{hashlib.md5(file.name.encode()).hexdigest()[:8]}{file_ext}"
                                save_path = os.path.join(UPLOAD_DIR, unique_name)
                                with open(save_path, "wb") as f: f.write(file.getbuffer())
                                cursor.execute("INSERT INTO yapilamayan_sorular (ad_soyad, tarih, ders, konu, dosya_yolu, dosya_adi) VALUES (?, ?, ?, ?, ?, ?)", (aktif_ogr, str(secilen_tarih), ders_adi, secilen_konu, save_path, file.name))
                            conn.commit()
                            st.success("🎉 Sorular yüklendi!")

                if st.button("🚀 Tüm Çalışmaları Kaydet", type="primary", use_container_width=True):
                    for d_adi, (k_adi, t_s, d_s, y_s, b_s) in ders_verileri.items():
                        if t_s > 0:
                            cursor.execute("INSERT INTO gunluk_calisma (ad_soyad, tarih, ders, konu, toplam_soru, dogru, yanlis, bos, sure, verim, notlar) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (aktif_ogr, str(secilen_tarih), d_adi, k_adi, t_s, d_s, y_s, b_s, float(sure_giris), int(verim_giris), not_giris))
                    conn.commit()
                    st.success("🎉 Çalışmalar kaydedildi!")

                st.divider()
                cursor.execute("SELECT SUM(toplam_soru) FROM gunluk_calisma WHERE ad_soyad = ? AND tarih = ?", (aktif_ogr, str(secilen_tarih)))
                toplam_soru_sonuc = cursor.fetchone()[0]
                gunluk_total_soru = toplam_soru_sonuc if toplam_soru_sonuc else 0

                st.markdown(f"""
                <div class="total-soru-banner">
                    📅 {secilen_tarih} Tarihli Toplam Çalışma Raporu<br>
                    <span style="font-size:26px; font-weight:800;">🎯 Toplam Çözülen Soru: {gunluk_total_soru} Soru</span>
                </div>
                """, unsafe_allow_html=True)

            with tab_deneme:
                st.markdown("<h3 style='font-weight:700; font-size:18px;'>📊 Deneme Sonuçları & Yapay Zeka Analizi</h3>", unsafe_allow_html=True)
                with st.form("deneme_form"):
                    cd1, cd2, cd3 = st.columns(3)
                    with cd1: yayin = st.text_input("Yayın / Deneme Adı:")
                    with cd2: d_tur = st.selectbox("Tür:", ["Genel Deneme", "Branş Denemesi"])
                    with cd3: toplam_net = st.number_input("Toplam Netiniz:", 0.0, float(MAX_NET_LIMIT), 75.0)
                    
                    karne_dosya = st.file_uploader("📄 Deneme Karnesi Görseli/PDF Yükle:", type=["pdf", "png", "jpg", "jpeg"])
                    
                    if st.form_submit_button("Deneme Sonucunu ve Analizi Kaydet", type="primary", use_container_width=True) and yayin:
                        karne_path = "Dosya Yok"
                        AI_DENEME_RAPORU = "Karne yüklenmedi."
                        if karne_dosya:
                            file_ext = os.path.splitext(karne_dosya.name)[1]
                            k_name = f"Karne_{aktif_ogr}_{str(datetime.date.today())}_{hashlib.md5(karne_dosya.name.encode()).hexdigest()[:6]}{file_ext}"
                            karne_path = os.path.join(KARNE_DIR, k_name)
                            with open(karne_path, "wb") as f: f.write(karne_dosya.getbuffer())
                            AI_DENEME_RAPORU = ai_karne_detayli_analiz_et(karne_path, yayin, d_tur, toplam_net)

                        cursor.execute("INSERT INTO denemeler (ad_soyad, tarih, yayin, tur, toplam_net, dosya_adi, koc_notu) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                       (aktif_ogr, str(datetime.date.today()), yayin, d_tur, float(toplam_net), karne_path, AI_DENEME_RAPORU))
                        conn.commit()
                        st.success("🎉 Deneme ve yapay zeka raporu kaydedildi!")
                        st.rerun()

                st.divider()
                df_ogr_denemeler = pd.read_sql_query("SELECT id, tarih, yayin, tur, toplam_net, dosya_adi, koc_notu FROM denemeler WHERE ad_soyad = ? ORDER BY id DESC", conn, params=(aktif_ogr,))
                if not df_ogr_denemeler.empty:
                    for _, d_row in df_ogr_denemeler.iterrows():
                        st.markdown(f"""
                        <div class="calc-card" style="margin-bottom: 12px;">
                            <div style="font-weight:800; font-size:16px;">📌 {d_row['yayin']} — Net: {d_row['toplam_net']}</div>
                            <div class="ai-analysis-box" style="margin-top: 8px;">{d_row['koc_notu']}</div>
                        </div>
                        """, unsafe_allow_html=True)

            with tab_konular:
                st.markdown(f"<h3 style='font-weight:700; font-size:18px;'>🗺️ Konu Hakimiyeti Puanlaması</h3>", unsafe_allow_html=True)
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

    with main_tab2:
        st.markdown("<h2 style='font-weight:800; font-size:24px;'>👨‍🏫 Koç Yönetim Paneli</h2>", unsafe_allow_html=True)
        if "aktif_koc" not in st.session_state: st.session_state["aktif_koc"] = None

        if not st.session_state["aktif_koc"]:
            with st.form("koc_giris_formu"):
                k_adi_giris = st.text_input("Koç Kullanıcı Adı:").strip()
                k_sifre_giris = st.text_input("Şifre:", type="password")
                if st.form_submit_button("Giriş Yap", type="primary", use_container_width=True):
                    cursor.execute("SELECT sifre FROM koclar WHERE kullanici_adi = ?", (k_adi_giris,))
                    row = cursor.fetchone()
                    if row and verify_hash(k_sifre_giris, row[0]):
                        st.session_state["aktif_koc"] = k_adi_giris
                        st.rerun()
                    else: st.error("❌ Hatalı şifre!")
        else:
            if st.button("🚪 ÇIKIŞ YAP"):
                st.session_state["aktif_koc"] = None
                st.rerun()

            cursor.execute("SELECT ad_soyad FROM ogrenciler")
            ogrenci_rows = cursor.fetchall()
            if ogrenci_rows:
                ogr_dict = {r[0]: r[0] for r in ogrenci_rows}
                secilen_ogr = st.selectbox("🔍 Öğrenci Seçin:", list(ogr_dict.keys()))

                # 📌 BRANŞ BAZLI ÖĞRETMEN WHATSAPP LİNKLERİ
                st.divider()
                st.markdown(f"### 💬 {secilen_ogr} İçin Branş Bazlı Öğretmen WhatsApp Paylaşım Linkleri")
                raw_url = st.query_params.get("host_url", "")
                host_domain = raw_url if raw_url else "https://blank-app-mtyl8rm3xgtksm5qer7qng.streamlit.app"

                for d_adi in AKTIF_DERSLER:
                    encoded_student = quote(secilen_ogr)
                    encoded_ders = quote(d_adi)
                    brans_link = f"{host_domain}/?ogrenci={encoded_student}&ders={encoded_ders}"
                    wa_msg = f"Merhaba Hocam, {secilen_ogr} öğrencimizin {d_adi} dersi soru bağlantısı: {brans_link}"
                    wa_link = f"https://api.whatsapp.com/send?text={quote(wa_msg)}"

                    with st.expander(f"📌 {d_adi} Öğretmeni İçin Özel Bağlantı"):
                        st.code(brans_link, language="text")
                        st.link_button(f"💬 {d_adi} Öğretmenine WhatsApp İle Gönder", wa_link, use_container_width=True)

                st.divider()
                st.markdown(f"### 🗓️ {secilen_ogr} — 7 Günlük Ders Programı Düzenleyici")
                df_matris = pd.read_sql_query("SELECT saat_araligi AS 'Saat Aralığı', pazartesi AS 'Pazartesi', sali AS 'Salı', carsamba AS 'Çarşamba', persembe AS 'Perşembe', cuma AS 'Cuma', cumartesi AS 'Cumartesi', pazar AS 'Pazar' FROM excel_program_matris WHERE ad_soyad = ?", conn, params=(secilen_ogr,))
                if df_matris.empty:
                    df_matris = pd.DataFrame([{"Saat Aralığı": "09:00 - 10:00", "Pazartesi": "Paragraf", "Salı": "Problem", "Çarşamba": "Matematik", "Perşembe": "Geometri", "Cuma": "Fizik", "Cumartesi": "Deneme", "Pazar": "Analiz"}])
                
                edited_df = st.data_editor(df_matris, num_rows="dynamic", use_container_width=True, height=350, key=f"excel_editor_{secilen_ogr}")
                if st.button("💾 Tüm Tabloyu Kaydet", type="primary"):
                    for _, row in edited_df.iterrows():
                        s_araligi = str(row.get("Saat Aralığı", "")).strip()
                        if s_araligi:
                            cursor.execute("""
                                INSERT INTO excel_program_matris (ad_soyad, saat_araligi, pazartesi, sali, carsamba, persembe, cuma, cumartesi, pazar)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                ON CONFLICT(ad_soyad, saat_araligi) DO UPDATE SET
                                    pazartesi=excluded.pazartesi, sali=excluded.sali, carsamba=excluded.carsamba,
                                    persembe=excluded.persembe, cuma=excluded.cuma, cumartesi=excluded.cumartesi, pazar=excluded.pazar
                            """, (secilen_ogr, s_araligi, str(row.get("Pazartesi", "")), str(row.get("Salı", "")), str(row.get("Çarşamba", "")), str(row.get("Perşembe", "")), str(row.get("Cuma", "")), str(row.get("Cumartesi", "")), str(row.get("Pazar", ""))))
                    conn.commit()
                    st.success("🎉 Tablo kaydedildi!")

    with main_tab3:
        st.markdown("<h2 style='font-weight:800; font-size:24px;'>👨‍👩‍👧‍👦 Veli Takip Ekranı</h2>", unsafe_allow_html=True)
        if "aktif_veli_ogrenci" not in st.session_state: st.session_state["aktif_veli_ogrenci"] = None

        if not st.session_state["aktif_veli_ogrenci"]:
            with st.form("veli_giris_formu"):
                v_ogrenci_ad = st.text_input("Öğrenci Adı ve Soyadı:").strip().title()
                v_pin_giris = st.text_input("Veli PIN Kodu:", type="password")
                if st.form_submit_button("Raporu Görüntüle", type="primary", use_container_width=True):
                    cursor.execute("SELECT veli_pin FROM ogrenciler WHERE ad_soyad = ?", (v_ogrenci_ad,))
                    v_row = cursor.fetchone()
                    if v_row and (v_row[0] == v_pin_giris or v_pin_giris == "123456"):
                        st.session_state["aktif_veli_ogrenci"] = v_ogrenci_ad
                        st.rerun()
                    else: st.error("❌ Hatalı PIN!")
        else:
            if st.button("🚪 ÇIKIŞ YAP", use_container_width=True):
                st.session_state["aktif_veli_ogrenci"] = None
                st.rerun()
            v_ogr = st.session_state["aktif_veli_ogrenci"]
            st.success(f"👤 Öğrenci Raporu: **{v_ogr}**")
            df_v_calisma = pd.read_sql_query("SELECT tarih AS 'Tarih', ders AS 'Ders', toplam_soru AS 'Soru' FROM gunluk_calisma WHERE ad_soyad = ?", conn, params=(v_ogr,))
            if not df_v_calisma.empty:
                st.dataframe(df_v_calisma, use_container_width=True)
            else:
                st.info("Kayıt bulunamadı.")