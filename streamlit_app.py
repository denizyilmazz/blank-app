import streamlit as st
import datetime
import sqlite3
import pandas as pd
import random
import base64
import hashlib
import os
from urllib.parse import quote
from PIL import Image
import shutil
import glob

st.set_page_config(
    page_title="YKS (TYT/AYT) - LGS KOÇLUK (DENİZ YILMAZ)",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- OTOMATİK VERİTABANI YEDEKLEME VE KURTARMA SİSTEMİ ---
DB_FILE = "yks_kocluk.db"
YEDEK_DIR = "veritabani_yedekleri"
KARNE_DIR = "karne_yuklemeleri"
os.makedirs(YEDEK_DIR, exist_ok=True)
os.makedirs(KARNE_DIR, exist_ok=True)

def veritabani_kurtar_ve_yedekle():
    if not os.path.exists(DB_FILE) or os.path.getsize(DB_FILE) == 0:
        yedekler = sorted(glob.glob(os.path.join(YEDEK_DIR, "yks_kocluk_yedek_*.db")))
        if yedekler:
            en_son_yedek = yedekler[-1]
            try:
                shutil.copy2(en_son_yedek, DB_FILE)
            except Exception:
                pass

    if os.path.exists(DB_FILE) and os.path.getsize(DB_FILE) > 0:
        bugun = datetime.date.today().strftime("%Y-%m-%d")
        yedek_yolu = os.path.join(YEDEK_DIR, f"yks_kocluk_yedek_{bugun}.db")
        if not os.path.exists(yedek_yolu):
            try:
                shutil.copy2(DB_FILE, yedek_yolu)
            except Exception:
                pass

veritabani_kurtar_ve_yedekle()

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def tablo_olustur():
    c = get_db_connection()
    cur = c.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ogrenciler (
        ad_soyad TEXT PRIMARY KEY,
        sifre TEXT,
        veli_pin TEXT DEFAULT '123456',
        sinav_turu TEXT DEFAULT 'YKS (TYT + AYT)',
        alan TEXT DEFAULT 'SAY (Sayısal)',
        hedef_uni TEXT DEFAULT '',
        hedef_bolum TEXT DEFAULT '',
        hedef_net FLOAT DEFAULT 80.0,
        hedef_sira TEXT DEFAULT '',
        koc_adi TEXT DEFAULT '',
        onaylandi INTEGER DEFAULT 0
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ozel_universiteler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        universite_adi TEXT,
        bolum_adi TEXT,
        kategori TEXT,
        taban_net FLOAT,
        taban_sira TEXT,
        tyt_net FLOAT,
        ayt_net FLOAT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS koclar (
        kullanici_adi TEXT PRIMARY KEY,
        sifre TEXT,
        onaylandi INTEGER DEFAULT 1
    )
    """)
    cur.execute("CREATE TABLE IF NOT EXISTS gunluk_calisma (id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT, tarih TEXT, ders TEXT, konu TEXT, soru_sayisi INTEGER DEFAULT 0, konu_anlatim_sure INTEGER DEFAULT 0, soru_cozum_sure INTEGER DEFAULT 0)")
    cur.execute("CREATE TABLE IF NOT EXISTS konu_ilerleme (ad_soyad TEXT, ders TEXT, konu_adi TEXT, tamamlandi INTEGER DEFAULT 0, soru_miktari INTEGER DEFAULT 0, PRIMARY KEY (ad_soyad, ders, konu_adi))")
    cur.execute("CREATE TABLE IF NOT EXISTS yapilamayan_sorular (id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT, tarih TEXT, ders TEXT, konu TEXT, dosya_yolu TEXT, dosya_adi TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS denemeler (id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT, tarih TEXT, yayin TEXT, tur TEXT, toplam_net FLOAT, dosya_yolu TEXT DEFAULT '', dosya_adi TEXT DEFAULT '', koc_notu TEXT DEFAULT '')")
    cur.execute("CREATE TABLE IF NOT EXISTS konu_puanlari (ad_soyad TEXT, konu_adi TEXT, puan INTEGER, PRIMARY KEY (ad_soyad, konu_adi))")
    cur.execute("CREATE TABLE IF NOT EXISTS excel_program_matris (ad_soyad TEXT, saat_araligi TEXT, pazartesi TEXT DEFAULT '', sali TEXT DEFAULT '', carsamba TEXT DEFAULT '', persembe TEXT DEFAULT '', cuma TEXT DEFAULT '', cumartesi TEXT DEFAULT '', pazar TEXT DEFAULT '', PRIMARY KEY (ad_soyad, saat_araligi))")
    cur.execute("CREATE TABLE IF NOT EXISTS program_dosyalari (id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT, yukleyen TEXT, tarih TEXT, dosya_yolu TEXT, dosya_adi TEXT)")
    
    # --- HAYATİ GÜVENLİK: ESKİ VERİTABANLARINI ÇÖKMEYE KARŞI OTOMATİK GÜNCELLE ---
    try: cur.execute("ALTER TABLE ogrenciler ADD COLUMN alan TEXT DEFAULT 'SAY (Sayısal)'")
    except sqlite3.OperationalError: pass
    
    try: cur.execute("ALTER TABLE ogrenciler ADD COLUMN veli_pin TEXT DEFAULT '123456'")
    except sqlite3.OperationalError: pass
    
    try: cur.execute("ALTER TABLE ogrenciler ADD COLUMN koc_adi TEXT DEFAULT ''")
    except sqlite3.OperationalError: pass
    
    try: cur.execute("ALTER TABLE ogrenciler ADD COLUMN onaylandi INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    
    try: cur.execute("ALTER TABLE koclar ADD COLUMN onaylandi INTEGER DEFAULT 1")
    except sqlite3.OperationalError: pass

    # koc1 kullanıcısını sistemden tamamen siliyoruz
    try:
        cur.execute("DELETE FROM koclar WHERE kullanici_adi = 'koc1'")
    except Exception:
        pass
    
    c.commit()
    c.close()

tablo_olustur()

st.markdown("""
<script>
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (prefersDark) {
        document.documentElement.setAttribute('data-theme', 'dark');
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
    }
</script>

<style>
    /* CSS FONT DÜZELTMESİ: İkonları (span) bozmamak için sadece temel metin etiketlerine uygulandı */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, p, label, input, textarea, select, h1, h2, h3, h4, h5, h6 {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-gradient: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #020617 100%);
            --text-color: #f8fafc;
            --container-bg: #1e293b;
            --border-color: #334155;
            --input-bg: #0f172a;
            --input-text: #f8fafc;
            --tab-bg: #1e293b;
            --yok-box-bg: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            --hero-bg: linear-gradient(135deg, #0284c7 0%, #4f46e5 50%, #7c3aed 100%);
        }
    }

    @media (prefers-color-scheme: light) {
        :root {
            --bg-gradient: linear-gradient(135deg, #f0fdf4 0%, #e0f2fe 50%, #f3e8ff 100%);
            --text-color: #0f172a;
            --container-bg: #ffffff;
            --border-color: #cbd5e1;
            --input-bg: #ffffff;
            --input-text: #0f172a;
            --tab-bg: #ffffff;
            --yok-box-bg: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
            --hero-bg: linear-gradient(135deg, #0ea5e9 0%, #6366f1 50%, #8b5cf6 100%);
        }
    }

    html, body, p, label, input, textarea, select {
        color: var(--text-color, #0f172a) !important;
    }

    #MainMenu, footer, header, .stDeployButton {display: none !important;}

    .stApp {
        background: var(--bg-gradient, linear-gradient(135deg, #f0fdf4 0%, #e0f2fe 50%, #f3e8ff 100%)) !important;
        background-attachment: fixed !important;
    }

    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 3rem !important;
        max-width: 1420px !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background: var(--tab-bg, #ffffff) !important;
        padding: 8px;
        border-radius: 16px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        border: 1px solid var(--border-color, #cbd5e1) !important;
    }

    .stTabs [data-baseweb="tab"] {
        height: 48px;
        background-color: var(--container-bg, #ffffff) !important;
        border-radius: 10px;
        padding: 8px 16px;
        font-weight: 700 !important;
        font-size: 13px !important;
        color: var(--text-color, #0f172a) !important;
        border: 1px solid var(--border-color, #cbd5e1) !important;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%) !important;
        border: none !important;
    }

    .stTabs [aria-selected="true"] span, .stTabs [aria-selected="true"] div {
        color: #ffffff !important;
    }

    input, textarea, select, div[data-baseweb="select"] {
        background-color: var(--input-bg, #ffffff) !important;
        color: var(--input-text, #0f172a) !important;
        border: 1.5px solid var(--border-color, #94a3b8) !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }

    div[data-baseweb="select"] > div {
        background-color: var(--input-bg, #ffffff) !important;
        color: var(--input-text, #0f172a) !important;
    }
    
    div[data-baseweb="select"] span {
        color: var(--input-text, #0f172a) !important;
    }

    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[data-baseweb="menu"] {
        background-color: var(--container-bg, #ffffff) !important;
    }
    
    div[data-baseweb="popover"] div, li[role="option"], span[data-baseweb="tag"] {
        color: var(--text-color, #0f172a) !important;
        background-color: var(--container-bg, #ffffff) !important;
    }
    
    li[role="option"]:hover {
        background-color: #0284c7 !important;
        color: #ffffff !important;
    }

    .hero-motivation-card {
        background: var(--hero-bg, linear-gradient(135deg, #0ea5e9 0%, #6366f1 50%, #8b5cf6 100%)) !important;
        color: #ffffff !important;
        padding: 20px 24px;
        border-radius: 20px;
        font-weight: 700;
        margin-bottom: 20px;
    }

    .hero-motivation-card * {
        color: #ffffff !important;
    }

    .yok-net-box {
        background: var(--yok-box-bg, linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%)) !important;
        border: 2px solid #3b82f6;
        border-radius: 16px;
        padding: 18px 22px;
        margin-bottom: 15px;
    }
    
    .yok-net-box * {
        color: var(--text-color, #0f172a) !important;
    }

    .program-header-box {
        background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%) !important;
        color: white !important;
        padding: 20px;
        border-radius: 16px;
        margin-bottom: 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(2, 132, 199, 0.2);
    }
    
    .program-header-box * {
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

def make_hash(password: str) -> str:
    salt = "YKS_PRO_SECURE_SALT_2026"
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()

def verify_hash(password: str, hashed_password: str) -> bool:
    if not hashed_password: return False
    if password == hashed_password: return True
    if make_hash(password) == hashed_password: return True
    try:
        if hashlib.sha256(password.encode('utf-8')).hexdigest() == hashed_password:
            return True
    except Exception:
        pass
    return False

def pdf_goster_html(pdf_path):
    try:
        with open(pdf_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        return f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="550" type="application/pdf" style="border-radius:12px; border:1px solid #cbd5e1;"></iframe>'
    except Exception:
        return "<p style='color:red;'>PDF dosyası okunamadı.</p>"

def html_to_pdf_bytes(df, ogrenci_adi):
    html_content = f"""
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <title>{ogrenci_adi} - Haftalık Ders Programı</title>
        <style>
            body {{ font-family: 'Helvetica', Arial, sans-serif; padding: 25px; color: #0f172a; }}
            h2 {{ text-align: center; color: #0284c7; margin-bottom: 5px; }}
            p {{ text-align: center; color: #64748b; font-size: 12px; margin-bottom: 25px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th, td {{ border: 1px solid #cbd5e1; padding: 10px 12px; text-align: center; font-size: 11px; vertical-align: middle; }}
            th {{ background-color: #0284c7; color: white; font-weight: bold; }}
            tr:nth-child(even) {{ background-color: #f8fafc; }}
        </style>
    </head>
    <body>
        <h2>🎓 YKS KOÇLUK — {ogrenci_adi.upper()} KİŞİSEL HAFTALIK DERS PROGRAMI</h2>
        <p>Deniz Yılmaz Gelişim Platformu | {datetime.date.today().strftime('%d.%m.%Y')}</p>
        {df.to_html(index=False, classes='table', border=0)}
    </body>
    </html>
    """
    return html_content.encode('utf-8')

MOTIVASYON_SOZLERI = [
    "🌿 Sakin ol, derin bir nefes al ve adım adım ilerle. Disiplin başarıyı getirir!",
    "🚀 Başarı, her gün ertelemeden tekrarlanan küçük çabaların birikimidir!",
    "🎓 Bugün döktüğün her damla alın teri, hayalindeki okulun kapısını açar!"
]

HAM_DERS_KONULARI = {
    "☕ Mola & Dinlenme Aktivitesi": [
        "Kısa Dinlenme & Çay/Kahve Molası",
        "Zihin Dinlendirme Mola"
    ],
    "🍽️ Yemek Molaları": [
        "Öğle Yemeği Molası",
        "Akşam Yemeği Molası"
    ],
    "📊 Branş Denemeleri": [
        "Matematik Branş Denemesi",
        "Fen Branş Denemesi",
        "Sosyal Branş Denemesi",
        "Türkçe Branş Denemesi",
        "Geometri Branş Denemesi"
    ],
    "👨‍🏫 Özel Ders Türkçe": [
        "Özel Ders Türkçe - Birebir Paragraf & Dil Bilgisi",
        "Özel Ders Türkçe - Soru Çözüm Kampı",
        "Özel Ders Türkçe - Ödev Kontrolü & Tekrar"
    ],
    "👨‍🏫 Özel Ders Matematik": [
        "Özel Ders Matematik - Birebir Konu Anlatımı",
        "Özel Ders Matematik - Soru Çözüm Kampı",
        "Özel Ders Matematik - Ödev Kontrolü & Tekrar",
        "Özel Ders Matematik - Yeni Nesil Soru Analizi"
    ],
    "👨‍🏫 Özel Ders Fizik": [
        "Özel Ders Fizik - Birebir Konu Anlatımı & Deney",
        "Özel Ders Fizik - Soru Çözüm & Formül Pratiği",
        "Özel Ders Fizik - Ödev Kontrolü & Zor Sorular"
    ],
    "👨‍🏫 Özel Ders Kimya": [
        "Özel Ders Kimya - Birebir Konu Anlatımı",
        "Özel Ders Kimya - Soru Çözüm & Hesaplama Pratiği"
    ],
    "👨‍🏫 Özel Ders Biyoloji": [
        "Özel Ders Biyoloji - Birebir Konu Anlatımı & Şekil Analizi",
        "Özel Ders Biyoloji - Soru Çözüm Kampı"
    ],
    "⚡ 📖 Paragraf + 📐 Problem Rutini": [
        "Paragraf Hız Kampı (25 Soru) + Yeni Nesil Problemler (20 Soru)",
        "Sözel Mantık Rutini",
        "Sayı-Kesir Problemleri",
        "Yaş & İşçi Havuz Problemleri",
        "Yüzde-Kar/Zarar & Karışım",
        "Hız & Hareket Problemleri",
        "Grafik & Rutin Olmayan Problemler"
    ],
    "📖 TYT Türkçe": [
        "Sözcükte Anlam", "Cümlede Anlam", "Paragrafta Anlam ve Yapı", 
        "Ses Bilgisi", "Yazım Kuralları", "Noktalama İşaretleri", 
        "Sözcük Türleri", "Fiiller, Ek Fiil ve Fiilimsi", "Cümlenin Ögeleri ve Cümle Çeşitleri", "Anlatım Bozuklukları"
    ],
    "📐 TYT Matematik": [
        "Temel Kavramlar", "Sayı Basamakları", "Bölme ve Bölünebilme", 
        "EBOB - EKOK", "Rasyonel Sayılar", "Basit Eşitsizlikler", 
        "Mutlak Değer", "Üslü İfadeler", "Köklü İfadeler", 
        "Çarpanlara Ayırma", "Oran - Orantı", "Denklem Çözme", 
        "Kümeler ve Kartezyen Çarpım", "Fonksiyonlar", "Veri, Sayma ve Olasılık"
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
        "Sulu Çözeltilerde Dengeler (Asit-Baz / KÇ)", "Elektrokimya", 
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

OSYM_SORU_DAGILIMLARI = {
    "Sözcükte Anlam": "Ort. 2-3 Soru",
    "Cümlede Anlam": "Ort. 2 Soru",
    "Paragrafta Anlam ve Yapı": "Ort. 14-16 Soru",
    "Ses Bilgisi": "Ort. 1 Soru",
    "Yazım Kuralları": "Ort. 2 Soru",
    "Noktalama İşaretleri": "Ort. 2 Soru",
    "Sözcük Türleri": "Ort. 1-2 Soru",
    "Fiiller, Ek Fiil ve Fiilimsi": "Ort. 1 Soru",
    "Cümlenin Ögeleri ve Cümle Çeşitleri": "Ort. 1-2 Soru",
    "Anlatım Bozuklukları": "Ort. 1 Soru",
    
    "Temel Kavramlar": "Ort. 3-4 Soru",
    "Sayı Basamakları": "Ort. 1 Soru",
    "Bölme ve Bölünebilme": "Ort. 1 Soru",
    "EBOB - EKOK": "Ort. 1 Soru",
    "Rasyonel Sayılar": "Ort. 1 Soru",
    "Basit Eşitsizlikler": "Ort. 1 Soru",
    "Mutlak Değer": "Ort. 1 Soru",
    "Üslü İfadeler": "Ort. 1-2 Soru",
    "Köklü İfadeler": "Ort. 1 Soru",
    "Çarpanlara Ayırma": "Ort. 1 Soru",
    "Oran - Orantı": "Ort. 1 Soru",
    "Denklem Çözme": "Ort. 1 Soru",
    "Kümeler ve Kartezyen Çarpım": "Ort. 1 Soru",
    "Fonksiyonlar": "Ort. 2-3 Soru",
    "Veri, Sayma ve Olasılık": "Ort. 3-4 Soru",
    
    "İkinci Dereceden Denklemler & Karmaşık Sayılar": "Ort. 2 Soru",
    "Parabol": "Ort. 1 Soru",
    "Eşitsizlikler": "Ort. 1 Soru",
    "Trigonometri": "Ort. 4 Soru",
    "Logaritma": "Ort. 2 Soru",
    "Diziler": "Ort. 2 Soru",
    "Limit ve Süreklilik": "Ort. 2 Soru",
    "Türev": "Ort. 3-4 Soru",
    "İntegral ve Alan": "Ort. 3-4 Soru"
}

EVRENSEL_DERS_KONULARI = {}
for ders_adi, konu_listesi in HAM_DERS_KONULARI.items():
    genisletilmis = []
    for k in konu_listesi:
        if "Mola" in ders_adi or "Yemek" in ders_adi or "Branş Denemeleri" in ders_adi:
            genisletilmis.append(k)
        else:
            genisletilmis.append(f"{k} — Konu Çalışması")
            genisletilmis.append(f"{k} — Soru Çözümü")
    EVRENSEL_DERS_KONULARI[ders_adi] = genisletilmis

UNIVERSITE_LISTESI = [
    "Acıbadem Mehmet Ali Aydınlar Üniversitesi (İstanbul)", "Adana Alparslan Türkeş Bilim ve Teknoloji Üniversitesi", 
    "Adıyaman Üniversitesi", "Afyon Kocatepe Üniversitesi", "Afyonkarahisar Sağlık Bilimleri Üniversitesi", 
    "Ağrı İbrahim Çeçen Üniversitesi", "Akdeniz Üniversitesi (Antalya)", "Aksaray Üniversitesi", 
    "Alanya Alaaddin Keykubat Üniversitesi (Antalya)", "Altınbaş Üniversitesi (İstanbul)", "Amasya Üniversitesi", 
    "Anadolu Üniversitesi (Eskişehir)", "Ankara Üniversitesi", "Ankara Hacı Bayram Veli Üniversitesi", 
    "Ankara Medipol Üniversitesi", "Ankara Müzik ve Güzel Sanatlar Üniversitesi", "Ankara Sosyal Bilimler Üniversitesi", 
    "Ankara Yıldırım Beyazıt Üniversitesi", "Antalya Bilim Üniversitesi", "Ardahan Üniversitesi", 
    "Artvin Çoruh Üniversitesi", "Atatürk Üniversitesi (Erzurum)", "Atılım Üniversitesi (Ankara)", 
    "Aydın Adnan Menderes Üniversitesi", "Bahçeşehir Üniversitesi (İstanbul)", "Balıkesir Üniversitesi", 
    "Bandırma Onyedi Eylül Üniversitesi (Balıkesir)", "Bartın Üniversitesi", "Batman Üniversitesi", 
    "Bayburt Üniversitesi", "Beykent Üniversitesi (İstanbul)", "Bezm-i Âlem Vakıf Üniversitesi (İstanbul)", 
    "Bilecik Şeyh Edebali Üniversitesi", "Bingöl Üniversitesi", "Bitlis Eren Üniversitesi", 
    "Boğaziçi Üniversitesi (İstanbul)", "Bolu Abant İzzet Baysal Üniversitesi", "Burdur Mehmet Akif Ersoy Üniversitesi", 
    "Bursa Teknik Üniversitesi", "Bursa Uludağ Üniversitesi", "Çağ Üniversitesi (Mersin)", 
    "Çankaya Üniversitesi (Ankara)", "Çanakkale Onsekiz Mart Üniversitesi", "Çankırı Karatekin Üniversitesi", 
    "Çukurova Üniversitesi (Adana)", "Dicle Üniversitesi (Diyarbakır)", "Doğuş Üniversitesi (İstanbul)", 
    "Dokuz Eylül Üniversitesi (İzmir)", "Düzce Üniversitesi", "Ege Üniversitesi (İzmir)", 
    "Erciyes Üniversitesi (Kayseri)", "Erzincan Binali Yıldırım Üniversitesi", "Erzurum Teknik Üniversitesi", 
    "Eskişehir Osmangazi Üniversitesi", "Eskişehir Teknik Üniversitesi", "Fatih Sultan Mehmet Vakıf Üniversitesi (İstanbul)", 
    "Fırat Üniversitesi (Elazığ)", "Galatasaray Üniversitesi (İstanbul)", "Gazi Üniversitesi (Ankara)", 
    "Gaziantep Üniversitesi", "Giresun Üniversitesi", "Gümüşhane Üniversitesi", "Hacettepe Üniversitesi (Ankara)", 
    "Hakkari Üniversitesi", "Haliç Üniversitesi (İstanbul)", "Harran Üniversitesi (Şanlıurfa)", 
    "Hatay Mustafa Kemal Üniversitesi", "Iğdır Üniversitesi", "Isparta Uygulamalı Bilimler Üniversitesi", 
    "İbn Haldun Üniversitesi (İstanbul)", "İhsan Doğramacı Bilkent Üniversitesi (Ankara)", "İnönü Üniversitesi (Malatya)", 
    "İstanbul Üniversitesi", "İstanbul Üniversitesi-Cerrahpaşa", "İstanbul Arel Üniversitesi", 
    "İstanbul Aydın Üniversitesi", "İstanbul Bilgi Üniversitesi", "İstanbul Esenyurt Üniversitesi", 
    "İstanbul Gedik Üniversitesi", "İstanbul Gelişim Üniversitesi", "İstanbul Kültür Üniversitesi", 
    "İstanbul Medeniyet Üniversitesi", "İstanbul Medipol Üniversitesi", "İstanbul Okan Üniversitesi", 
    "İstanbul Rumeli Üniversitesi", "İstanbul Sabahattin Zaim Üniversitesi", "İstanbul Ticaret Üniversitesi", 
    "İstinye Üniversitesi (İstanbul)", "İzmir Bakırçay Üniversitesi", "İzmir Demokrasi Üniversitesi", 
    "İzmir Ekonomi Üniversitesi", "İzmir Katip Çelebi Üniversitesi", "İzmir Yüksek Teknoloji Enstitüsü", 
    "Kadir Has Üniversitesi (İstanbul)", "Kafkas Üniversitesi (Kars)", "Kahramanmaraş Sütçü İmam Üniversitesi", 
    "Karabük Üniversitesi", "Karadeniz Teknik Üniversitesi (Trabzon)", "Karamanoğlu Mehmetbey Üniversitesi (Karaman)", 
    "Kastamonu Üniversitesi", "Kayseri Üniversitesi", "Kırıkkale Üniversitesi", "Kırklareli Üniversitesi", 
    "Kırşehir Ahi Evran Üniversitesi", "Kilis 7 Aralık Üniversitesi", "Kocaeli Üniversitesi", 
    "Kocaeli Sağlık ve Teknoloji Üniversitesi", "Konya Gıda ve Tarım Üniversitesi", "Konya Teknik Üniversitesi", 
    "KTO Karatay Üniversitesi (Konya)", "Kütahya Dumlupınar Üniversitesi", "Kütahya Sağlık Bilimleri Üniversitesi", 
    "Malatya Turgut Özal Üniversitesi", "Manisa Celal Bayar Üniversitesi", "Mardin Artuklu Üniversitesi", 
    "Marmara Üniversitesi (İstanbul)", "Mersin Üniversitesi", "Mimar Sinan Güzel Sanatlar Üniversitesi (İstanbul)", 
    "Muğla Sıtkı Koçman Üniversitesi", "Munzur Üniversitesi (Tunceli)", "Muş Alparslan Üniversitesi", 
    "Necmettin Erbakan Üniversitesi (Konya)", "Nevşehir Hacı Bektaş Veli Üniversitesi", "Niğde Ömer Halisdemir Üniversitesi", 
    "Nuh Naci Yazgan Üniversitesi (Kayseri)", "Ondokuz Mayıs Üniversitesi (Samsun)", "Ordu Üniversitesi", 
    "Orta Doğu Teknik Üniversitesi (ODTÜ - Ankara)", "Osmaniye Korkut Ata Üniversitesi", "Özyeğin Üniversitesi (İstanbul)", 
    "Pamukkale Üniversitesi (Denizli)", "Piri Reis Üniversitesi (İstanbul)", "Recep Tayyip Erdoğan Üniversitesi (Rize)", 
    "Sabancı Üniversitesi (İstanbul)", "Sağlık Bilimleri Üniversitesi (İstanbul)", "Sakarya Üniversitesi", 
    "Sakarya Uygulamalı Bilimler Üniversitesi", "Samsun Üniversitesi", "Sanko Üniversitesi (Gaziantep)", 
    "Selçuk Üniversitesi (Konya)", "Siirt Üniversitesi", "Sinop Üniversitesi", "Sivas Cumhuriyet Üniversitesi", 
    "Süleyman Demirel Üniversitesi (Isparta)", "Şırnak Üniversitesi", "Tarsus Üniversitesi (Mersin)", 
    "TED Üniversitesi (Ankara)", "Tekirdağ Namık Kemal Üniversitesi", "TOBB Ekonomi ve Teknoloji Üniversitesi (Ankara)", 
    "Tokat Gaziosmanpaşa Üniversitesi", "Toros Üniversitesi (Mersin)", "Trabzon Üniversitesi", "Trakya Üniversitesi (Edirne)", 
    "Türk-Alman Üniversitesi (İstanbul)", "Türk Hava Kurumu Üniversitesi (Ankara)", "Ufuk Üniversitesi (Ankara)", 
    "Uşak Üniversitesi", "Üsküdar Üniversitesi (İstanbul)", "Van Yüzüncü Yıl Üniversitesi", 
    "Yalova Üniversitesi", "Yaşar Üniversitesi (İzmir)", "Yeditepe Üniversitesi (İstanbul)", 
    "Yıldız Teknik Üniversitesi (İstanbul)", "Yozgat Bozok Üniversitesi", "Zonguldak Bülent Ecevit Üniversitesi"
]

BOLUM_KATEGORILERI = {
    "SAY (Sayısal)": [
        "Matematik", "Fen Edebiyat Fakültesi Matematik", "Tıp Fakültesi", "Bilgisayar Mühendisliği", "Yapay Zeka ve Veri Mühendisliği", 
        "Elektrik-Elektronik Mühendisliği", "Endüstri Mühendisliği", "Makine Mühendisliği", 
        "İnşaat Mühendisliği", "Yazılım Mühendisliği", "Mimarlık", "Diş Hekimliği Fakültesi", 
        "Eczacılık Fakültesi", "Moleküler Biyoloji ve Genetik", "Fizyoterapi ve Rehabilitasyon", "Hemşirelik"
    ],
    "EA (Eşit Ağırlık)": [
        "Hukuk Fakültesi", "Psikoloji", "İşletme", "İktisat", 
        "Siyaset Bilimi ve Uluslararası İlişkiler", "Yönetim Bilişim Sistemleri", 
        "Rehberlik ve Psikolojik Danışmanlık (PDR)", "Sınıf Öğretmenliği"
    ],
    "SÖZ (Sözel)": [
        "Türk Dili ve Edebiyatı", "Tarih", "Coğrafya", "Gastronomi ve Mutfak Sanatları", 
        "İlahiyat Fakültesi", "Özel Eğitim Öğretmenliği", "Türkçe Öğretmenliği"
    ],
    "DİL (Yabancı Dil)": [
        "İngilizce Öğretmenliği", "Tercümanlık ve Çeviribilim", "İngiliz Dili ve Edebiyatı"
    ]
}

st.markdown("""
<div style="text-align: center; padding: 10px 0 15px 0;">
    <span style="font-size: 42px;">🎓</span>
    <h1 style="margin: 0; font-weight: 800; font-size: 26px;">YKS (TYT/AYT) - LGS KOÇLUK</h1>
    <p style="margin: 0; font-size: 14px; color: #0284c7; font-weight: 700;">DENİZ YILMAZ GELİŞİM PLATFORMU</p>
</div>
""", unsafe_allow_html=True)

link_ogrenci = st.query_params.get("ogrenci", None)

if link_ogrenci:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 18px 24px; border-radius: 16px; margin-bottom: 20px;">
        <h3 style="margin:0; font-size:20px; font-weight:800; color:white !important;">👨‍🏫 Öğretmen Soru İnceleme Ekranı</h3>
        <p style="margin:4px 0 0 0; opacity:0.9; color:white !important;"><strong>{link_ogrenci}</strong> öğrencisinin çözemediği sorular listelenmektedir.</p>
    </div>
    """, unsafe_allow_html=True)
    
    conn_link = get_db_connection()
    df_link_sorular = pd.read_sql_query("SELECT id, tarih, ders, konu, dosya_yolu, dosya_adi FROM yapilamayan_sorular WHERE ad_soyad = ? ORDER BY id DESC", conn_link, params=(link_ogrenci,))
    conn_link.close()

    if df_link_sorular.empty:
        st.info(f"ℹ️ {link_ogrenci} henüz soru yüklemedi.")
    else:
        for _, s_data in df_link_sorular.iterrows():
            st.markdown(f"#### 📌 {s_data['ders']} — {s_data['konu']} <span style='font-size:12px;'>({s_data['tarih']})</span>", unsafe_allow_html=True)
            if os.path.exists(s_data['dosya_yolu']):
                if s_data['dosya_yolu'].lower().endswith(('png', 'jpg', 'jpeg')):
                    st.image(s_data['dosya_yolu'], width=400)
                elif s_data['dosya_yolu'].lower().endswith('.pdf'):
                    st.markdown(pdf_goster_html(s_data['dosya_yolu']), unsafe_allow_html=True)
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
            hatirlanan_ogr = st.query_params.get("hatirla_ogr", None)
            if hatirlanan_ogr:
                conn_h = get_db_connection()
                cur_h = conn_h.cursor()
                cur_h.execute("SELECT ad_soyad FROM ogrenciler WHERE ad_soyad = ? AND onaylandi = 1", (hatirlanan_ogr,))
                if cur_h.fetchone():
                    st.session_state["aktif_ogrenci"] = hatirlanan_ogr
                    aktif_ogr = hatirlanan_ogr
                conn_h.close()

        if not aktif_ogr:
            st.markdown("<h3 style='font-weight:700; font-size:18px;'>👨‍🎓 Öğrenci Giriş & Kayıt Paneli</h3>", unsafe_allow_html=True)
            tab_ogr_login, tab_ogr_register = st.tabs(["🔑 GİRİŞ YAP", "➕ YENİ HESAP OLUŞTUR"])

            with tab_ogr_login:
                with st.form("ogrenci_giris_formu"):
                    login_ad = st.text_input("Adınız ve Soyadınız:").strip().title()
                    # Type "password" Streamlit'in kendi göz ikonunu sağında çıkarır.
                    login_sifre = st.text_input("Şifre / PIN:", type="password")
                    beni_hatirla_ogr = st.checkbox("Beni Hatırla")
                    
                    if st.form_submit_button("Giriş Yap", type="primary", use_container_width=True):
                        if login_ad and login_sifre:
                            conn_l = get_db_connection()
                            cur_l = conn_l.cursor()
                            cur_l.execute("SELECT sifre, onaylandi FROM ogrenciler WHERE ad_soyad = ?", (login_ad,))
                            usr = cur_l.fetchone()
                            conn_l.close()

                            if usr and verify_hash(login_sifre, usr[0]):
                                if usr[1] == 1:
                                    st.session_state["aktif_ogrenci"] = login_ad
                                    if beni_hatirla_ogr:
                                        st.query_params["hatirla_ogr"] = login_ad
                                    else:
                                        if "hatirla_ogr" in st.query_params:
                                            del st.query_params["hatirla_ogr"]
                                    st.rerun()
                                else:
                                    st.warning("⏳ Hesabınız koçunuz tarafından henüz onaylanmamıştır. Lütfen koçunuzun onayını bekleyin.")
                            else:
                                st.error("❌ Hatalı ad veya şifre!")

            with tab_ogr_register:
                with st.form("ogrenci_kayit_formu"):
                    reg_ad = st.text_input("Adınız ve Soyadınız:").strip().title()
                    reg_sifre = st.text_input("Şifre Belirleyin:", type="password")
                    reg_veli_pin = st.text_input("Veli Takip Şifresi Belirleyin:", value="123456")
                    
                    conn_k = get_db_connection()
                    cur_k = conn_k.cursor()
                    cur_k.execute("SELECT kullanici_adi FROM koclar WHERE onaylandi = 1")
                    aktif_koclar_listesi = [k[0] for k in cur_k.fetchall()]
                    conn_k.close()

                    if not aktif_koclar_listesi: aktif_koclar_listesi = ["Deniz Yılmaz"]
                    
                    reg_koc = st.selectbox("Çalışmak İstediğiniz Koçu Seçin:", aktif_koclar_listesi)
                    reg_alan = st.selectbox("Alanınız:", ["SAY (Sayısal)", "EA (Eşit Ağırlık)", "SÖZ (Sözel)", "DİL (Yabancı Dil)"])
                    reg_sinav = st.selectbox("Hazırlanılan Sınav:", ["YKS (TYT + AYT)", "TYT (Sadece TYT)", "LGS (8. Sınıf)"])

                    if st.form_submit_button("Hesabımı Oluştur ve Koç Onayına Gönder", type="primary", use_container_width=True):
                        if reg_ad and reg_sifre:
                            conn_reg = get_db_connection()
                            cur_reg = conn_reg.cursor()
                            cur_reg.execute("SELECT ad_soyad FROM ogrenciler WHERE ad_soyad = ?", (reg_ad,))
                            var_mi = cur_reg.fetchone()
                            if var_mi:
                                st.error(f"⚠️ `{reg_ad}` zaten kayıtlı!")
                                conn_reg.close()
                            else:
                                cur_reg.execute("INSERT INTO ogrenciler (ad_soyad, sifre, veli_pin, alan, sinav_turu, koc_adi, onaylandi) VALUES (?, ?, ?, ?, ?, ?, 0)",
                                               (reg_ad, make_hash(reg_sifre), reg_veli_pin, reg_alan, reg_sinav, reg_koc))
                                conn_reg.commit()
                                conn_reg.close()
                                st.success("🎉 Kaydınız oluşturuldu! Seçtiğiniz koç onayladıktan sonra giriş yapabileceksiniz.")
        else:
            col_o_head1, col_o_head2 = st.columns([0.8, 0.2])
            with col_o_head1:
                conn_inf = get_db_connection()
                cur_inf = conn_inf.cursor()
                cur_inf.execute("SELECT sinav_turu, alan, hedef_uni, hedef_bolum, koc_adi FROM ogrenciler WHERE ad_soyad = ?", (aktif_ogr,))
                r_info = cur_inf.fetchone()
                conn_inf.close()

                ogr_sinav = r_info[0] if r_info else "YKS (TYT + AYT)"
                ogr_alan = r_info[1] if r_info else "SAY (Sayısal)"
                curr_uni = r_info[2] if (r_info and r_info[2]) else "Giresun Üniversitesi"
                curr_bolum = r_info[3] if (r_info and r_info[3]) else "Matematik"
                ogr_kocu = r_info[4] if (r_info and r_info[4]) else "Deniz Yılmaz"
                st.success(f"👤 Aktif Oturum: **{aktif_ogr}** | Koç: **{ogr_kocu}** | Alan: **{ogr_alan}**")
            
            with col_o_head2:
                if st.button("🚪 ÇIKIŞ YAP", key="ogr_logout_btn", use_container_width=True):
                    st.session_state["aktif_ogrenci"] = None
                    if "hatirla_ogr" in st.query_params:
                        del st.query_params["hatirla_ogr"]
                    st.rerun()

            tab_hedef, tab_program, tab_ilerleme, tab_gunluk, tab_deneme, tab_konular = st.tabs([
                "🎯 YÖK ATLAS & ÖSYM",
                "📅 DERS PROGRAMI",
                "✅ İLERLEME TAKİBİ",
                "📝 GÜNLÜK ÇALIŞMA",
                "📊 DENEME YÜKLEME",
                "🗺️ KONU HAKİMİYETİ"
            ])

            with tab_hedef:
                st.markdown(f"<h3 style='font-weight:700; font-size:18px;'>🎯 YÖK Atlas Hedef & Net Analiz Merkezi — {aktif_ogr}</h3>", unsafe_allow_html=True)
                st.caption("🏛️ Üniversitenizi ve bölümünüzü seçerek ÖSYM / YÖK Atlas verilerine göre gereken taban netleri ve başarı sırasını anında görüntüleyin.")

                conn_uni = get_db_connection()
                cur_uni = conn_uni.cursor()
                cur_uni.execute("SELECT DISTINCT universite_adi FROM ozel_universiteler")
                ozel_unis = [r[0] for r in cur_uni.fetchall()]
                conn_uni.close()

                toplam_uni_listesi = sorted(list(set(UNIVERSITE_LISTESI + ozel_unis)))

                col_h_u1, col_h_u2, col_h_u3 = st.columns([1.2, 1.2, 0.8])
                with col_h_u1:
                    u_idx = toplam_uni_listesi.index(curr_uni) if curr_uni in toplam_uni_listesi else 0
                    secilen_hedef_uni = st.selectbox("Hedef Üniversite:", toplam_uni_listesi, index=u_idx)
                
                with col_h_u2:
                    secilen_kategori = st.selectbox("Puan Türü / Kategori:", list(BOLUM_KATEGORILERI.keys()))
                
                conn_bol = get_db_connection()
                cur_bol = conn_bol.cursor()
                cur_bol.execute("SELECT bolum_adi FROM ozel_universiteler WHERE universite_adi = ? AND kategori = ?", (secilen_hedef_uni, secilen_kategori))
                ozel_bolumler = [r[0] for r in cur_bol.fetchall()]
                conn_bol.close()

                toplam_bolum_listesi = sorted(list(set(BOLUM_KATEGORILERI[secilen_kategori] + ozel_bolumler)))

                with col_h_u3:
                    b_idx = toplam_bolum_listesi.index(curr_bolum) if curr_bolum in toplam_bolum_listesi else 0
                    secilen_hedef_bolum = st.selectbox("Bölüm:", toplam_bolum_listesi, index=b_idx)

                conn_det = get_db_connection()
                cur_det = conn_det.cursor()
                cur_det.execute("SELECT taban_net, taban_sira, tyt_net, ayt_net FROM ozel_universiteler WHERE universite_adi = ? AND bolum_adi = ?", (secilen_hedef_uni, secilen_hedef_bolum))
                ozel_kayit = cur_det.fetchone()
                conn_det.close()

                if ozel_kayit:
                    t_net, t_sira, tyt_gerekli, ayt_gerekli = ozel_kayit[0], ozel_kayit[1], ozel_kayit[2], ozel_kayit[3]
                else:
                    if "Matematik" in secilen_hedef_bolum or "Fen Edebiyat" in secilen_hedef_bolum:
                        t_net, t_sira, tyt_gerekli, ayt_gerekli = 75.5, "95.000", 72.0, 45.0
                    else:
                        t_net, t_sira, tyt_gerekli, ayt_gerekli = 85.0, "50.000", 80.0, 52.0

                st.markdown(f"""
                <div class="yok-net-box">
                    <div style="font-size:16px; font-weight:800; margin-bottom:8px;">🏛️ {secilen_hedef_uni} — {secilen_hedef_bolum}</div>
                    <div style="display: flex; gap: 20px; flex-wrap: wrap; margin-top: 10px;">
                        <div style="background: var(--container-bg); padding: 10px 15px; border-radius: 10px; border: 1px solid var(--border-color); flex: 1; min-width: 140px;">
                            <span style="font-size: 11px; font-weight: 700;">YÖK ATLAS TABAN NET</span><br>
                            <span style="font-size: 18px; font-weight: 800; color: #0284c7;">{t_net} Net</span>
                        </div>
                        <div style="background: var(--container-bg); padding: 10px 15px; border-radius: 10px; border: 1px solid var(--border-color); flex: 1; min-width: 140px;">
                            <span style="font-size: 11px; font-weight: 700;">YÖK ATLAS BAŞARI SIRASI</span><br>
                            <span style="font-size: 18px; font-weight: 800; color: #16a34a;">İlk {t_sira}</span>
                        </div>
                        <div style="background: var(--container-bg); padding: 10px 15px; border-radius: 10px; border: 1px solid var(--border-color); flex: 1; min-width: 140px;">
                            <span style="font-size: 11px; font-weight: 700;">GEREKLİ ORTALAMA TYT</span><br>
                            <span style="font-size: 18px; font-weight: 800; color: #9333ea;">~{tyt_gerekli} Net</span>
                        </div>
                        <div style="background: var(--container-bg); padding: 10px 15px; border-radius: 10px; border: 1px solid var(--border-color); flex: 1; min-width: 140px;">
                            <span style="font-size: 11px; font-weight: 700;">GEREKLİ ORTALAMA AYT</span><br>
                            <span style="font-size: 18px; font-weight: 800; color: #ea580c;">~{ayt_gerekli} Net</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button("🚀 Bu Hedefi Profilime Kaydet ve Netlerimi Planla", type="primary", use_container_width=True):
                    conn_up = get_db_connection()
                    cur_up = conn_up.cursor()
                    cur_up.execute("UPDATE ogrenciler SET hedef_uni = ?, hedef_bolum = ?, hedef_net = ? WHERE ad_soyad = ?", 
                                   (secilen_hedef_uni, f"{secilen_hedef_bolum} ({secilen_kategori})", float(t_net), aktif_ogr))
                    conn_up.commit()
                    conn_up.close()
                    st.success(f"🎉 Hedefiniz başarıyla güncellendi: {secilen_hedef_uni} - {secilen_hedef_bolum} ({t_net} Net)!")
                    st.rerun()

            with tab_program:
                st.markdown(f"""
                <div class="program-header-box">
                    <h2 style="margin:0; font-size:22px; font-weight:800; color:white !important;">📅 {aktif_ogr.upper()} — KİŞİSEL HAFTALIK DERS PROGRAMI</h2>
                    <p style="margin:5px 0 0 0; font-size:13px; opacity:0.9; color:white !important;">Koçunuz tarafından özel olarak hazırlanan haftalık çalışma planınız aşağıdadır.</p>
                </div>
                """, unsafe_allow_html=True)

                conn_p = get_db_connection()
                df_p = pd.read_sql_query("SELECT saat_araligi AS 'Saat', pazartesi AS 'Pazartesi', sali AS 'Salı', carsamba AS 'Çarşamba', persembe AS 'Perşembe', cuma AS 'Cuma', cumartesi AS 'Cumartesi', pazar AS 'Pazar' FROM excel_program_matris WHERE ad_soyad = ? ORDER BY saat_araligi ASC", conn_p, params=(aktif_ogr,))
                conn_p.close()

                if not df_p.empty:
                    st.dataframe(df_p, use_container_width=True, height=400)
                    
                    st.markdown("---")
                    st.markdown("#### 📥 Programını Cihazına İndir (PDF / Yazdırılabilir Format)")
                    html_bytes_ogr = html_to_pdf_bytes(df_p, aktif_ogr)
                    st.download_button(
                        label="📥 Programı PDF İndir (.html / Tarayıcıda Aç & Yazdır)",
                        data=html_bytes_ogr,
                        file_name=f"{aktif_ogr}_Haftalik_Ders_Programi.html",
                        mime="text/html",
                        use_container_width=True
                    )
                else:
                    st.info(f"ℹ️ Sevgili {aktif_ogr}, koçun henüz haftalık programını kaydetmedi.")

            with tab_ilerleme:
                st.markdown(f"### ✅ Konu İlerleme, Soru Takibi & ÖSYM Soru Dağılımı — {aktif_ogr}")
                st.caption("📚 Her ders için konuların ÖSYM'de kaç soru getirdiğini görerek çalışmanı planlayabilir, tamamlandığında tik atabilirsin.")

                secilen_takip_ders = st.selectbox("İlerlemesini Görmek / Düzenlemek İstediğiniz Dersi Seçin:", list(HAM_DERS_KONULARI.keys()), key="takip_ders_secim")
                konu_listesi_ogrenci = HAM_DERS_KONULARI[secilen_takip_ders]

                conn_t = get_db_connection()
                cur_t = conn_t.cursor()
                takip_verileri = []
                for konu in konu_listesi_ogrenci:
                    cur_t.execute("SELECT tamamlandi, soru_miktari FROM konu_ilerleme WHERE ad_soyad = ? AND ders = ? AND konu_adi = ?", (aktif_ogr, secilen_takip_ders, konu))
                    res = cur_t.fetchone()
                    t_val = bool(res[0]) if res else False
                    s_val = int(res[1]) if res else 0
                    
                    osym_bilgi = OSYM_SORU_DAGILIMLARI.get(konu, "ÖSYM Ort. 1-2 Soru")
                    
                    takip_verileri.append({
                        "Konu Adı": konu,
                        "ÖSYM Çıkmış Soru Dağılımı": osym_bilgi,
                        "Tamamlandı ✅": t_val,
                        "Çözülen Soru Miktarı": s_val
                    })
                conn_t.close()

                df_takip = pd.DataFrame(takip_verileri)

                with st.form(f"ilerleme_form_{secilen_takip_ders}"):
                    edited_takip = st.data_editor(
                        df_takip,
                        use_container_width=True,
                        hide_index=True,
                        num_rows="fixed",
                        key=f"editor_takip_{secilen_takip_ders}"
                    )
                    if st.form_submit_button("💾 İlerlemeyi Kaydet", type="primary", use_container_width=True):
                        conn_sv = get_db_connection()
                        cur_sv = conn_sv.cursor()
                        for _, row in edited_takip.iterrows():
                            k_adi = row["Konu Adı"]
                            tamam = 1 if row["Tamamlandı ✅"] else 0
                            soru_m = int(row["Çözülen Soru Miktarı"]) if pd.notna(row["Çözülen Soru Miktarı"]) else 0
                            cur_sv.execute("""
                                INSERT INTO konu_ilerleme (ad_soyad, ders, konu_adi, tamamlandi, soru_miktari)
                                VALUES (?, ?, ?, ?, ?)
                                ON CONFLICT(ad_soyad, ders, konu_adi) DO UPDATE SET tamamlandi = ?, soru_miktari = ?
                            """, (aktif_ogr, secilen_takip_ders, k_adi, tamam, soru_m, tamam, soru_m))
                        conn_sv.commit()
                        conn_sv.close()
                        st.success("🎉 İlerlemeniz başarıyla kaydedildi!")
                        st.rerun()

                st.markdown("---")
                st.markdown("#### 📥 İlerleme Tablosunu İndir (CSV / Excel ile açılabilir)")
                conn_csv = get_db_connection()
                df_tum_ilerleme = pd.read_sql_query("SELECT ders AS 'Ders', konu_adi AS 'Konu', CASE WHEN tamamlandi=1 THEN 'Evet' ELSE 'Hayır' END AS 'Tamamlandı', soru_miktari AS 'Soru Miktarı' FROM konu_ilerleme WHERE ad_soyad = ?", conn_csv, params=(aktif_ogr,))
                conn_csv.close()

                if not df_tum_ilerleme.empty:
                    csv_data = df_tum_ilerleme.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Tüm İlerleme Tablosunu İndir",
                        data=csv_data,
                        file_name=f"{aktif_ogr}_Ders_Ilerleme_Tablosu.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

            with tab_gunluk:
                st.markdown(f"### 📝 Günlük Çalışma Girişi (Konu & Dakika Süre Takibi) — {aktif_ogr}")
                s_tarih = st.date_input("Çalışma Tarihi:", datetime.date.today())
                
                sec_alan_giris = st.selectbox("Çalışma Alanınızı Seçiniz:", ["SAY (Sayısal)", "EA (Eşit Ağırlık)", "SÖZ (Sözel)", "DİL (Yabancı Dil)"])
                aktif_giris_dersleri = list(EVRENSEL_DERS_KONULARI.keys())

                with st.form("gunluk_detayli_calisma_formu"):
                    secilen_ders = st.selectbox("Ders Seçin:", aktif_giris_dersleri)
                    konu_listesi_secim = EVRENSEL_DERS_KONULARI.get(secilen_ders, ["Genel Konu Çalışması"])
                    secilen_konu = st.selectbox("Konu Seçin:", konu_listesi_secim)

                    col_gc1, col_gc2, col_gc3 = st.columns(3)
                    with col_gc1: girilen_soru = st.number_input("Çözülen Soru Sayısı:", 0, 500, 20, step=1)
                    with col_gc2: girilen_konu_sure = st.number_input("Konu Anlatımı Süresi (Dakika):", 0, 1440, 45, step=1)
                    with col_gc3: girilen_cozum_sure = st.number_input("Soru Çözümü Süresi (Dakika):", 0, 1440, 45, step=1)

                    if st.form_submit_button("🚀 Çalışmayı Kaydet", type="primary", use_container_width=True):
                        conn_g = get_db_connection()
                        cur_g = conn_g.cursor()
                        cur_g.execute("""
                            INSERT INTO gunluk_calisma (ad_soyad, tarih, ders, konu, soru_sayisi, konu_anlatim_sure, soru_cozum_sure)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (aktif_ogr, str(s_tarih), secilen_ders, secilen_konu, int(girilen_soru), int(girilen_konu_sure), int(girilen_cozum_sure)))
                        conn_g.commit()
                        conn_g.close()
                        st.success(f"🎉 Başarıyla kaydedildi! ({secilen_ders} — {secilen_konu})")

            with tab_deneme:
                st.markdown(f"### 📊 Deneme Sınavı Sonuç Belgesi Yükleme — {aktif_ogr}")
                st.caption("📷 Deneme sınavı sonucunuzu (JPG, PNG veya PDF) buradan yükleyerek koçunuza gönderebilirsiniz.")
                
                with st.form("deneme_yukleme_formu"):
                    dyayin = st.text_input("Deneme Yayın Adı (Örn: 3D Yayınları TYT Deneme):")
                    dnet = st.number_input("Toplam Net:", 0.0, 120.0, 75.0)
                    yuklenen_karne = st.file_uploader("Deneme Sonuç Belgesi (JPG, PNG, PDF):", type=["png", "jpg", "jpeg", "pdf"])
                    
                    if st.form_submit_button("📤 Denemeyi ve Karnemi Koçuma Gönder", type="primary", use_container_width=True) and dyayin:
                        dosya_yolu_db = ""
                        dosya_adi_db = ""
                        if yuklenen_karne is not None:
                            dosya_adi_db = yuklenen_karne.name
                            dosya_yolu_db = os.path.join(KARNE_DIR, f"{datetime.date.today()}_{aktif_ogr}_{dosya_adi_db}")
                            with open(dosya_yolu_db, "wb") as f:
                                f.write(yuklenen_karne.getbuffer())

                        conn_dn = get_db_connection()
                        cur_dn = conn_dn.cursor()
                        cur_dn.execute("""
                            INSERT INTO denemeler (ad_soyad, tarih, yayin, tur, toplam_net, dosya_yolu, dosya_adi, koc_notu)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (aktif_ogr, str(datetime.date.today()), dyayin, "Genel Deneme", float(dnet), dosya_yolu_db, dosya_adi_db, "Koç değerlendirmesi bekleniyor."))
                        conn_dn.commit()
                        conn_dn.close()
                        st.success("🎉 Deneme sonucu ve karne belgeniz başarıyla koçunuza gönderildi!")
                        st.rerun()

                st.markdown("---")
                st.markdown("#### 📋 Geçmiş Deneme Sonuçlarım ve Karnelerim")
                conn_dlist = get_db_connection()
                df_benim_denemeler = pd.read_sql_query("SELECT id, tarih AS 'Tarih', yayin AS 'Yayın', toplam_net AS 'Toplam Net', dosya_yolu, dosya_adi, koc_notu AS 'Koç Notu' FROM denemeler WHERE ad_soyad = ? ORDER BY id DESC", conn_dlist, params=(aktif_ogr,))
                conn_dlist.close()

                if not df_benim_denemeler.empty:
                    for _, drow in df_benim_denemeler.iterrows():
                        st.markdown(f"**{drow['Tarih']}** | {drow['Yayın']} — **Net: {drow['Toplam Net']}** | Not: *{drow['Koç Notu']}*")
                        if drow['dosya_yolu'] and os.path.exists(drow['dosya_yolu']):
                            if drow['dosya_yolu'].lower().endswith(('png', 'jpg', 'jpeg')):
                                st.image(drow['dosya_yolu'], width=300)
                            elif drow['dosya_yolu'].lower().endswith('.pdf'):
                                st.markdown(pdf_goster_html(drow['dosya_yolu']), unsafe_allow_html=True)
                        st.divider()
                else:
                    st.info("ℹ️ Henüz yüklenmiş deneme sınavınız bulunmuyor.")

            with tab_konular:
                st.markdown("### 🗺️ Konu Hakimiyeti Puanlama (1-5)")
                for d_adi, k_list in EVRENSEL_DERS_KONULARI.items():
                    st.markdown(f"**{d_adi}**")
                    for kn in k_list[:3]:
                        st.select_slider(kn, options=[1, 2, 3, 4, 5], value=3, key=f"kp_{aktif_ogr}_{kn}")

    with main_tab2:
        st.markdown("## 👨‍🏫 Koç Yönetim Paneli")
        if "aktif_koc" not in st.session_state: st.session_state["aktif_koc"] = None
        
        if not st.session_state["aktif_koc"]:
            tab_koc_giris, tab_koc_kayit = st.tabs(["🔑 KOÇ GİRİŞİ", "➕ YENİ KOÇ BAŞVURUSU"])
            
            with tab_koc_giris:
                with st.form("koc_giris_formu"):
                    k_ad = st.text_input("Koç Kullanıcı Adı:")
                    k_sif = st.text_input("Şifre:", type="password")
                    if st.form_submit_button("Koç Girişi Yap", type="primary"):
                        conn_kg = get_db_connection()
                        cur_kg = conn_kg.cursor()
                        cur_kg.execute("SELECT sifre, onaylandi FROM koclar WHERE kullanici_adi = ?", (k_ad,))
                        r = cur_kg.fetchone()
                        conn_kg.close()

                        if r and verify_hash(k_sif, r[0]):
                            if r[1] == 1:
                                st.session_state["aktif_koc"] = k_ad
                                st.rerun()
                            else:
                                st.warning("⏳ Koç hesabınız henüz ana koç tarafından onaylanmadı.")
                        else:
                            st.error("Hatalı kullanıcı adı veya şifre!")
                            
            with tab_koc_kayit:
                with st.form("yeni_koc_kayit_formu"):
                    yk_ad = st.text_input("Yeni Koç Kullanıcı Adı Belirle:")
                    yk_sif = st.text_input("Şifre Belirle:", type="password")
                    yk_master = st.text_input("Ana Koç Onay Kodu (Güvenlik Kodu):", type="password")
                    if st.form_submit_button("Koç Kaydı Oluştur", type="primary"):
                        if yk_ad and yk_sif:
                            onay_durum = 1 if yk_master == "Koc123!" else 0
                            conn_kk = get_db_connection()
                            cur_kk = conn_kk.cursor()
                            try:
                                cur_kk.execute("INSERT INTO koclar (kullanici_adi, sifre, onaylandi) VALUES (?, ?, ?)", (yk_ad, make_hash(yk_sif), onay_durum))
                                conn_kk.commit()
                                conn_kk.close()
                                if onay_durum == 1:
                                    st.success("🎉 Koç kaydınız oluşturuldu ve onaylandı! Giriş yapabilirsiniz.")
                                else:
                                    st.success("⏳ Koç başvurunuz alındı. Ana koç onayladıktan sonra giriş yapabileceksiniz.")
                            except sqlite3.IntegrityError:
                                conn_kk.close()
                                st.error("Bu kullanıcı adı zaten alınmış.")
        else:
            col_k_head1, col_k_head2 = st.columns([0.8, 0.2])
            with col_k_head1: st.success(f"👨‍🏫 Aktif Koç: **{st.session_state['aktif_koc']}**")
            with col_k_head2:
                if st.button("🚪 ÇIKIŞ YAP", key="koc_out"):
                    st.session_state["aktif_koc"] = None
                    st.rerun()

            conn_b = get_db_connection()
            cur_b = conn_b.cursor()
            cur_b.execute("SELECT ad_soyad, alan, sinav_turu, koc_adi FROM ogrenciler WHERE onaylandi = 0")
            bekleyen_ogrenciler = cur_b.fetchall()
            conn_b.close()
            
            if bekleyen_ogrenciler:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; padding: 15px 20px; border-radius: 14px; margin-bottom: 20px;">
                    <h3 style="margin:0; font-size:18px; font-weight:800; color:white !important;">🔔 Bildirim: {len(bekleyen_ogrenciler)} Yeni Öğrenci Onay Bekliyor!</h3>
                    <p style="margin:4px 0 0 0; font-size:13px; opacity:0.9; color:white !important;">Aşağıdaki listeden öğrencileri onaylayabilir veya silebilirsiniz (reddedebilirsiniz).</p>
                </div>
                """, unsafe_allow_html=True)

                for b_ogr in bekleyen_ogrenciler:
                    col_bo1, col_bo2, col_bo3, col_bo4, col_bo5 = st.columns([2, 1.5, 1.5, 1, 1])
                    with col_bo1: st.markdown(f"**{b_ogr[0]}**")
                    with col_bo2: st.markdown(f"İstenen Koç: {b_ogr[3]}")
                    with col_bo3: st.markdown(f"Alan: {b_ogr[1]}")
                    with col_bo4:
                        if st.button(f"Onayla ✅", key=f"onay_{b_ogr[0]}"):
                            conn_on = get_db_connection()
                            cur_on = conn_on.cursor()
                            cur_on.execute("UPDATE ogrenciler SET onaylandi = 1 WHERE ad_soyad = ?", (b_ogr[0],))
                            conn_on.commit()
                            conn_on.close()
                            st.success(f"{b_ogr[0]} onaylandı!")
                            st.rerun()
                    with col_bo5:
                        if st.button(f"Sil ❌", key=f"sil_{b_ogr[0]}"):
                            conn_sl = get_db_connection()
                            cur_sl = conn_sl.cursor()
                            cur_sl.execute("DELETE FROM ogrenciler WHERE ad_soyad = ?", (b_ogr[0],))
                            conn_sl.commit()
                            conn_sl.close()
                            st.warning(f"{b_ogr[0]} kaydı silindi.")
                            st.rerun()
                st.divider()

            conn_ogrs = get_db_connection()
            cur_ogrs = conn_ogrs.cursor()
            cur_ogrs.execute("SELECT ad_soyad FROM ogrenciler WHERE koc_adi = ? AND onaylandi = 1", (st.session_state['aktif_koc'],))
            ogrs = [row[0] for row in cur_ogrs.fetchall()]
            conn_ogrs.close()

            if ogrs:
                secilen_ogr = st.selectbox("Yönetilecek Öğrenci:", ogrs)
                
                st.markdown(f"### 📈 {secilen_ogr} — Öğrenci Konu İlerleme ve Soru Durumu")
                conn_ki = get_db_connection()
                df_koc_ilerleme = pd.read_sql_query("SELECT ders AS 'Ders', konu_adi AS 'Konu', CASE WHEN tamamlandi=1 THEN '✅ Tamamlandı' ELSE '⏳ Devam Ediyor' END AS 'Durum', soru_miktari AS 'Çözülen Soru' FROM konu_ilerleme WHERE ad_soyad = ?", conn_ki, params=(secilen_ogr,))
                conn_ki.close()

                if not df_koc_ilerleme.empty:
                    st.dataframe(df_koc_ilerleme, use_container_width=True)
                else:
                    st.info("ℹ️ Öğrenci henüz ilerleme tablosunda işaretleme yapmamış.")

                st.markdown(f"### 📝 {secilen_ogr} — Öğrencinin Günlük Çalışma Kayıtları")
                conn_kc = get_db_connection()
                df_koc_calisma = pd.read_sql_query("SELECT tarih AS 'Tarih', ders AS 'Ders', konu AS 'Konu', soru_sayisi AS 'Soru', konu_anlatim_sure AS 'Konu Süre (dk)', soru_cozum_sure AS 'Çözüm Süre (dk)' FROM gunluk_calisma WHERE ad_soyad = ? ORDER BY id DESC LIMIT 30", conn_kc, params=(secilen_ogr,))
                conn_kc.close()

                if not df_koc_calisma.empty:
                    st.dataframe(df_koc_calisma, use_container_width=True, hide_index=True)
                else:
                    st.info("ℹ️ Öğrenci henüz günlük çalışma kaydı girmemiş.")

                st.markdown(f"### 📊 {secilen_ogr} — Öğrenci Deneme Sonuçları ve Karneleri")
                conn_kdc = get_db_connection()
                df_koc_deneme = pd.read_sql_query("SELECT id, tarih AS 'Tarih', yayin AS 'Yayın', toplam_net AS 'Toplam Net', dosya_yolu, dosya_adi, koc_notu AS 'Koç Notu' FROM denemeler WHERE ad_soyad = ? ORDER BY id DESC", conn_kdc, params=(secilen_ogr,))
                conn_kdc.close()

                if not df_koc_deneme.empty:
                    for _, kd in df_koc_deneme.iterrows():
                        st.markdown(f"**{kd['Tarih']}** | {kd['Yayın']} — **Net: {kd['Toplam Net']}**")
                        if kd['dosya_yolu'] and os.path.exists(kd['dosya_yolu']):
                            if kd['dosya_yolu'].lower().endswith(('png', 'jpg', 'jpeg')):
                                st.image(kd['dosya_yolu'], width=300)
                            elif kd['dosya_yolu'].lower().endswith('.pdf'):
                                st.markdown(pdf_goster_html(kd['dosya_yolu']), unsafe_allow_html=True)
                        
                        with st.form(f"koc_not_form_{kd['id']}"):
                            yeni_koc_notu = st.text_input("Koç Değerlendirme Notu:", value=kd['Koç Notu'])
                            if st.form_submit_button("Notu Güncelle"):
                                conn_kn = get_db_connection()
                                cur_kn = conn_kn.cursor()
                                cur_kn.execute("UPDATE denemeler SET koc_notu = ? WHERE id = ?", (yeni_koc_notu, kd['id']))
                                conn_kn.commit()
                                conn_kn.close()
                                st.success("🎉 Koç notu güncellendi!")
                                st.rerun()
                        st.divider()
                else:
                    st.info("ℹ️ Öğrenci henüz deneme sonucu veya karne yüklememiş.")

                st.divider()
                st.markdown(f"### 🗓️ {secilen_ogr} — Kişiye Özel Haftalık Program Düzenleyici")
                
                tum_dersler_listesi = list(EVRENSEL_DERS_KONULARI.keys())
                saat_secenekleri = [f"{s:02d}" for s in range(7, 24)]
                dakika_secenekleri = [f"{d:02d}" for d in range(0, 60, 5)]
                
                c_saat1, c_dak1, c_saat2, c_dak2, c_gun = st.columns([1.1, 1.1, 1.1, 1.1, 1.6])
                with c_saat1: bas_saat = st.selectbox("Başlangıç Saat:", saat_secenekleri, index=1, key="koc_bas_saat")
                with c_dak1: bas_dakika = st.selectbox("Başlangıç Dakika:", dakika_secenekleri, index=0, key="koc_bas_dakika")
                with c_saat2: bit_saat = st.selectbox("Bitiş Saat:", saat_secenekleri, index=2, key="koc_bit_saat")
                with c_dak2: bit_dakika = st.selectbox("Bitiş Dakika:", dakika_secenekleri, index=0, key="koc_bit_dakika")
                with c_gun: hedef_gun_sec = st.selectbox("Uygulanacak Gün:", ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"], key="dinamik_gun")

                yeni_saat_araligi = f"{bas_saat}:{bas_dakika} - {bit_saat}:{bit_dakika}"

                c_s3, c_s4 = st.columns(2)
                with c_s3: sec_ders_matris = st.selectbox("Ders / Aktivite Seçin:", tum_dersler_listesi, key="dinamik_ders_secim")
                with c_s4: sec_konu_matris = st.selectbox("Alt Konu / Detay Seçin:", EVRENSEL_DERS_KONULARI.get(sec_ders_matris, ["Genel Soru"]), key="dinamik_konu_secim")

                if st.button("📥 Bu Hücreyi Tabloya İşle", type="primary", use_container_width=True):
                     hucre_degeri = f"{sec_ders_matris}\n↳ {sec_konu_matris}"
                     gun_sutun_map = {
                        "Pazartesi": "pazartesi", "Salı": "sali", "Çarşamba": "carsamba",
                        "Perşembe": "persembe", "Cuma": "cuma", "Cumartesi": "cumartesi", "Pazar": "pazar"
                     }
                     t_sutun = gun_sutun_map[hedef_gun_sec]
                     conn_islem = get_db_connection()
                     cur_islem = conn_islem.cursor()
                     cur_islem.execute(f"""
                         INSERT INTO excel_program_matris (ad_soyad, saat_araligi, {t_sutun})
                         VALUES (?, ?, ?)
                         ON CONFLICT(ad_soyad, saat_araligi) DO UPDATE SET {t_sutun} = ?
                     """, (secilen_ogr, yeni_saat_araligi, hucre_degeri, hucre_degeri))
                     conn_islem.commit()
                     conn_islem.close()
                     st.success(f"🎉 {secilen_ogr} için {hedef_gun_sec} günü ({yeni_saat_araligi}) kaydedildi!")
                     st.rerun()

                st.markdown(f"#### 📊 {secilen_ogr} — Canlı Program Tablosu Düzenleyici")
                conn_m = get_db_connection()
                df_matris = pd.read_sql_query("SELECT saat_araligi AS 'Saat Aralığı', pazartesi AS 'Pazartesi', sali AS 'Salı', carsamba AS 'Çarşamba', persembe AS 'Perşembe', cuma AS 'Cuma', cumartesi AS 'Cumartesi', pazar AS 'Pazar' FROM excel_program_matris WHERE ad_soyad = ? ORDER BY saat_araligi ASC", conn_m, params=(secilen_ogr,))
                conn_m.close()
                
                if df_matris.empty:
                    df_matris = pd.DataFrame([{"Saat Aralığı": "08:00 - 09:00", "Pazartesi": "", "Salı": "", "Çarşamba": "", "Perşembe": "", "Cuma": "", "Cumartesi": "", "Pazar": ""}])

                edited_matris = st.data_editor(df_matris, num_rows="dynamic", use_container_width=True, height=450, key=f"excel_matris_editor_{secilen_ogr}")

                if st.button("💾 Tablodaki Tüm Değişiklikleri Kaydet", type="primary", use_container_width=True):
                    conn_sv2 = get_db_connection()
                    cur_sv2 = conn_sv2.cursor()
                    cur_sv2.execute("DELETE FROM excel_program_matris WHERE ad_soyad = ?", (secilen_ogr,))
                    for _, row in edited_matris.iterrows():
                        s_ar = str(row.get("Saat Aralığı", "")).strip()
                        if s_ar and s_ar != "nan":
                            cur_sv2.execute("""
                                INSERT OR REPLACE INTO excel_program_matris (ad_soyad, saat_araligi, pazartesi, sali, carsamba, persembe, cuma, cumartesi, pazar)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    conn_sv2.commit()
                    conn_sv2.close()
                    st.success("🎉 Program güncellendi!")
                    st.rerun()
            else:
                st.info("ℹ️ Sizin koçluğunuz altında onaylanmış öğrenci bulunmuyor.")

    with main_tab3:
        st.markdown("## 👨‍👩‍👧‍👦 Veli Takip Ekranı")
        with st.form("veli_giris_formu"):
            v_ad = st.text_input("Öğrenci Adı ve Soyadı:").strip().title()
            v_sifre = st.text_input("Öğrencinin Verdiği Veli Şifresi (PIN):", type="password")
            veli_giris_buton = st.form_submit_button("Veli Paneline Giriş Yap", type="primary", use_container_width=True)

        if veli_giris_buton:
            if v_ad and v_sifre:
                conn_v = get_db_connection()
                cur_v = conn_v.cursor()
                cur_v.execute("SELECT veli_pin, onaylandi FROM ogrenciler WHERE ad_soyad = ?", (v_ad,))
                ogr_kayit = cur_v.fetchone()
                conn_v.close()

                if ogr_kayit and v_sifre == (ogr_kayit[0] if ogr_kayit[0] else "123456"):
                    if ogr_kayit[1] == 1:
                        st.session_state[f"veli_dogrulanmis_{v_ad}"] = True
                        st.success(f"🔓 Giriş Başarılı! **{v_ad}** adlı öğrencinin paneli açılıyor...")
                        st.rerun()
                    else:
                        st.warning("⏳ Bu öğrencinin hesabı henüz koç tarafından onaylanmamıştır.")
                else:
                    st.error("❌ Hatalı Veli Şifresi veya Öğrenci Adı!")

        giris_yapilan_ogrenciler = [k.replace("veli_dogrulanmis_", "") for k, v in st.session_state.items() if k.startswith("veli_dogrulanmis_") and v == True]
        
        for v_ad in giris_yapilan_ogrenciler:
            st.markdown("---")
            c_vhead1, c_vhead2 = st.columns([0.8, 0.2])
            with c_vhead1: st.success(f"👨‍👩‍👧‍👦 Görüntülenen Öğrenci: **{v_ad}**")
            with c_vhead2:
                if st.button("🔒 Oturumu Kapat", key=f"veli_cikis_{v_ad}"):
                    st.session_state[f"veli_dogrulanmis_{v_ad}"] = False
                    st.rerun()

            conn_vh = get_db_connection()
            cur_vh = conn_vh.cursor()
            cur_vh.execute("SELECT hedef_uni, hedef_bolum, hedef_net FROM ogrenciler WHERE ad_soyad = ?", (v_ad,))
            h_bilgi = cur_vh.fetchone()
            conn_vh.close()

            if h_bilgi:
                st.markdown(f"🎯 **Hedef Üniversite / Bölüm:** {h_bilgi[0]} — {h_bilgi[1]} (Hedef Net: {h_bilgi[2]})")

            st.markdown(f"### 📅 {v_ad.upper()} — Haftalık Ders Programı")
            conn_vp = get_db_connection()
            df_veli_p = pd.read_sql_query("SELECT saat_araligi AS 'Saat', pazartesi AS 'Pazartesi', sali AS 'Salı', carsamba AS 'Çarşamba', persembe AS 'Perşembe', cuma AS 'Cuma', cumartesi AS 'Cumartesi', pazar AS 'Pazar' FROM excel_program_matris WHERE ad_soyad = ? ORDER BY saat_araligi ASC", conn_vp, params=(v_ad,))
            conn_vp.close()

            if not df_veli_p.empty:
                st.dataframe(df_veli_p, use_container_width=True, height=350)
            else:
                st.info("ℹ️ Koç henüz bu öğrenci için haftalık program kaydetmemiş.")

            st.markdown(f"### ✅ Öğrenci Konu İlerleme Durumu")
            conn_vi = get_db_connection()
            df_v_ilerleme = pd.read_sql_query("SELECT ders AS 'Ders', konu_adi AS 'Konu', CASE WHEN tamamlandi=1 THEN '✅ Tamamlandı' ELSE '⏳ Devam Ediyor' END AS 'Durum', soru_miktari AS 'Çözülen Soru' FROM konu_ilerleme WHERE ad_soyad = ?", conn_vi, params=(v_ad,))
            conn_vi.close()

            if not df_v_ilerleme.empty:
                st.dataframe(df_v_ilerleme, use_container_width=True)
            else:
                st.info("ℹ️ Öğrenci henüz ilerleme tablosunda işlem yapmamış.")

            st.markdown(f"### 📝 Öğrencinin Günlük Çalışma Takibi")
            conn_vc = get_db_connection()
            df_v_calisma = pd.read_sql_query("SELECT tarih AS 'Tarih', ders AS 'Ders', konu AS 'Konu', soru_sayisi AS 'Soru', konu_anlatim_sure AS 'Konu Süre (dk)', soru_cozum_sure AS 'Çözüm Süre (dk)' FROM gunluk_calisma WHERE ad_soyad = ? ORDER BY id DESC LIMIT 20", conn_vc, params=(v_ad,))
            conn_vc.close()

            if not df_v_calisma.empty:
                st.dataframe(df_v_calisma, use_container_width=True, hide_index=True)
            else:
                st.info("ℹ️ Öğrenci henüz günlük çalışma kaydı girmemiş.")

            st.markdown(f"### 📊 Deneme Sınavı Sonuçları ve Koç Notları")
            conn_vd = get_db_connection()
            df_v_deneme = pd.read_sql_query("SELECT tarih AS 'Tarih', yayin AS 'Yayın', toplam_net AS 'Toplam Net', koc_notu AS 'Koç Notu' FROM denemeler WHERE ad_soyad = ? ORDER BY id DESC", conn_vd, params=(v_ad,))
            conn_vd.close()

            if not df_v_deneme.empty:
                st.dataframe(df_v_deneme, use_container_width=True, hide_index=True)
            else:
                st.info("ℹ️ Henüz deneme sınavı sonucu yüklenmemiş.")