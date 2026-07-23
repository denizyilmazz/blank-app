import streamlit as st
import datetime
import sqlite3
import pandas as pd
import random
import base64
import re
import hashlib
import os
import shutil

st.set_page_config(
    page_title="YKS Pro Koçluk Platformu",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🎨 Rahatlatıcı, Huzur Veren ve Odaklanmayı Artıran CSS Teması
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        -webkit-font-smoothing: antialiased;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}

    /* Huzur Veren Pastel Arka Plan */
    .stApp {
        background: linear-gradient(135deg, #f0fdf4 0%, #e0f2fe 50%, #f3e8ff 100%) !important;
        background-attachment: fixed !important;
        color: #0f172a;
    }

    .main .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 1280px !important;
    }

    /* Glassmorphism Sekme Tasarımı */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
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
        padding: 10px 18px;
        font-weight: 700;
        font-size: 13.5px;
        color: #64748b;
        border: none !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .stTabs [data-baseweb="tab"]:hover {
        background-color: rgba(241, 245, 249, 0.9);
        color: #0284c7;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%) !important;
        color: #ffffff !important;
        box-shadow: 0 8px 20px -4px rgba(2, 132, 199, 0.35) !important;
    }

    /* Kart Tasarımları */
    .hero-motivation-card {
        background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 50%, #8b5cf6 100%);
        color: #ffffff;
        padding: 22px 28px;
        border-radius: 20px;
        font-weight: 700;
        box-shadow: 0 12px 30px -5px rgba(14, 165, 233, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.2);
        margin-bottom: 20px;
    }

    .yok-atlas-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 20px;
        border: 1px solid #bae6fd;
        box-shadow: 0 4px 15px rgba(2, 132, 199, 0.08);
        margin-top: 15px;
        margin-bottom: 20px;
    }

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
</style>
""", unsafe_allow_html=True)

SISTEM_YONETICI_KATILIM_KODU = "YKS2026KOC"
DB_FILE = "yks_kocluk.db"

# 🔑 ŞİFRE HASLEME VE DOĞRULAMA (PBKDF2 SHA256)
def make_hash(password: str) -> str:
    salt = "YKS_PRO_SECURE_SALT_2026"
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()

def verify_hash(password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    if password == hashed_password:
        return True
    return make_hash(password) == hashed_password

# 💾 GÜNLÜK VERİTABANI YEDEKLEME SİSTEMİ
def veritabani_gunluk_yedekle():
    try:
        if os.path.exists(DB_FILE):
            os.makedirs("backups", exist_ok=True)
            bugun = datetime.date.today().strftime("%Y%m%d")
            yedek_dosya = os.path.join("backups", f"yks_kocluk_backup_{bugun}.db")
            if not os.path.exists(yedek_dosya):
                shutil.copy2(DB_FILE, yedek_dosya)
    except Exception as e:
        pass

veritabani_gunluk_yedekle()

MOTIVASYON_SOZLERI = [
    "🌿 Sakin ol, derin bir nefes al ve adım adım ilerle. Disiplin başarıyı getirir!",
    "🚀 Başarı, her gün ertelemeden tekrarlanan küçük çabaların birikimidir!",
    "🎓 Bugün döktüğün her damla alın teri, hayalindeki üniversitenin kapısını açar!",
    "💪 Zorluklar, potansiyelini keşfetmen için var olan basamaklardır. Pes etmek yok!",
    "✨ Şimdi odaklan ve çalış, gelecekteki kendin seninle gurur duysun!",
    "🎯 Zirveye giden yolda engel yoktur, sadece kararlılıkla aşılacak hedefler vardır!"
]

# 🏛️ YÖK ATLAS TABAN/TAVAN SIRALAMA VE NET VERİ VERİTABANI
YOK_ATLAS_VERILERI = {
    "İstanbul Teknik Üniversitesi (İTÜ)": {
        "Bilgisayar Mühendisliği": {"taban_sira": "2.150", "tavan_sira": "120", "taban_net": 108.5, "tavan_net": 117.5},
        "Yazılım Mühendisliği": {"taban_sira": "3.100", "tavan_sira": "450", "taban_net": 106.0, "tavan_net": 115.0},
        "Elektrik-Elektronik Mühendisliği": {"taban_sira": "3.800", "tavan_sira": "310", "taban_net": 105.0, "tavan_net": 116.0},
        "Endüstri Mühendisliği": {"taban_sira": "4.500", "tavan_sira": "620", "taban_net": 104.0, "tavan_net": 114.5},
        "Yapay Zeka Mühendisliği": {"taban_sira": "1.850", "tavan_sira": "95", "taban_net": 109.5, "tavan_net": 118.0},
        "Makine Mühendisliği": {"taban_sira": "8.200", "tavan_sira": "1.200", "taban_net": 99.5, "tavan_net": 111.0},
        "Mimarlık": {"taban_sira": "28.500", "tavan_sira": "5.400", "taban_net": 88.0, "tavan_net": 103.5}
    },
    "Boğaziçi Üniversitesi": {
        "Bilgisayar Mühendisliği": {"taban_sira": "290", "tavan_sira": "1", "taban_net": 114.0, "tavan_net": 120.0},
        "Elektrik-Elektronik Mühendisliği": {"taban_sira": "850", "tavan_sira": "15", "taban_net": 112.5, "tavan_net": 119.5},
        "Endüstri Mühendisliği": {"taban_sira": "1.400", "tavan_sira": "80", "taban_net": 110.0, "tavan_net": 118.5},
        "İşletme / İktisat": {"taban_sira": "1.100", "tavan_sira": "45", "taban_net": 108.0, "tavan_net": 117.0}
    },
    "Ortadoğu Teknik Üniversitesi (ODTÜ)": {
        "Bilgisayar Mühendisliği": {"taban_sira": "800", "tavan_sira": "12", "taban_net": 112.0, "tavan_net": 119.5},
        "Elektrik-Elektronik Mühendisliği": {"taban_sira": "1.650", "tavan_sira": "110", "taban_net": 109.5, "tavan_net": 118.0},
        "Havacılık ve Uzay Mühendisliği": {"taban_sira": "3.200", "tavan_sira": "250", "taban_net": 106.5, "tavan_net": 115.5},
        "Endüstri Mühendisliği": {"taban_sira": "2.900", "tavan_sira": "300", "taban_net": 107.0, "tavan_net": 116.0},
        "Makine Mühendisliği": {"taban_sira": "5.400", "tavan_sira": "750", "taban_net": 103.0, "tavan_net": 113.0}
    },
    "Bilkent Üniversitesi": {
        "Bilgisayar Mühendisliği (Burslu)": {"taban_sira": "180", "tavan_sira": "5", "taban_net": 115.0, "tavan_net": 120.0},
        "Elektrik-Elektronik Mühendisliği (Burslu)": {"taban_sira": "450", "tavan_sira": "22", "taban_net": 113.5, "tavan_net": 119.0},
        "Endüstri Mühendisliği (Burslu)": {"taban_sira": "950", "tavan_sira": "65", "taban_net": 111.0, "tavan_net": 118.0},
        "Hukuk Fakültesi (Burslu)": {"taban_sira": "150", "tavan_sira": "8", "taban_net": 109.0, "tavan_net": 116.5}
    },
    "Koç Üniversitesi": {
        "Tıp Fakültesi (Burslu)": {"taban_sira": "75", "tavan_sira": "1", "taban_net": 116.5, "tavan_net": 120.0},
        "Bilgisayar Mühendisliği (Burslu)": {"taban_sira": "110", "tavan_sira": "3", "taban_net": 116.0, "tavan_net": 120.0}
    },
    "Hacettepe Üniversitesi": {
        "Tıp Fakültesi (Türkçe)": {"taban_sira": "1.350", "tavan_sira": "45", "taban_net": 110.5, "tavan_net": 118.5},
        "Tıp Fakültesi (İngilizce)": {"taban_sira": "850", "tavan_sira": "18", "taban_net": 112.0, "tavan_net": 119.0},
        "Diş Hekimliği": {"taban_sira": "18.500", "tavan_sira": "8.200", "taban_net": 93.5, "tavan_net": 104.0},
        "Eczacılık": {"taban_sira": "32.000", "tavan_sira": "15.000", "taban_net": 86.5, "tavan_net": 98.0},
        "Bilgisayar Mühendisliği": {"taban_sira": "3.400", "tavan_sira": "420", "taban_net": 106.0, "tavan_net": 115.0}
    },
    "İstanbul Üniversitesi": {
        "İstanbul Tıp Fakültesi (Çapa)": {"taban_sira": "2.100", "tavan_sira": "150", "taban_net": 109.0, "tavan_net": 117.5},
        "Cerrahpaşa Tıp Fakültesi": {"taban_sira": "2.400", "tavan_sira": "210", "taban_net": 108.5, "tavan_net": 117.0},
        "Hukuk Fakültesi": {"taban_sira": "3.800", "tavan_sira": "450", "taban_net": 98.5, "tavan_net": 110.0},
        "Diş Hekimliği": {"taban_sira": "22.000", "tavan_sira": "11.000", "taban_net": 91.5, "tavan_net": 101.5}
    },
    "Yıldız Teknik Üniversitesi (YTÜ)": {
        "Bilgisayar Mühendisliği": {"taban_sira": "4.800", "tavan_sira": "850", "taban_net": 104.5, "tavan_net": 113.5},
        "Yazılım Mühendisliği": {"taban_sira": "5.900", "tavan_sira": "1.100", "taban_net": 103.0, "tavan_net": 112.0},
        "Yapay Zeka Mühendisliği": {"taban_sira": "4.100", "tavan_sira": "650", "taban_net": 105.5, "tavan_net": 114.0},
        "Endüstri Mühendisliği": {"taban_sira": "9.500", "tavan_sira": "2.100", "taban_net": 98.5, "tavan_net": 109.5},
        "Makine Mühendisliği": {"taban_sira": "18.000", "tavan_sira": "5.200", "taban_net": 93.5, "tavan_net": 104.0}
    }
}

POPULE_UNIVERSITELER = list(YOK_ATLAS_VERILERI.keys())

def sifre_gecerli_mi(sifre):
    if len(sifre) < 6:
        return False, "Şifre en az 6 karakter uzunluğunda olmalıdır!"
    if not re.search(r'[a-zA-ZçğıöşüÇĞİÖŞÜ]', sifre):
        return False, "Şifre en az bir HARF içermelidir!"
    if not re.search(r'\d', sifre):
        return False, "Şifre en az bir RAKAM içermelidir!"
    if not re.search(r'[^\w\s]', sifre):
        return False, "Şifre en az bir NOKTALAMA İŞARETİ veya ÖZEL KARAKTER (!, ?, ., @, vb.) içermelidir!"
    return True, "Şifre geçerli."

def halka_grafik_html(baslik, veri_listesi):
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
    
    return f'''<div style="background-color:#ffffff; padding:22px; border-radius:16px; border:1px solid #e2e8f0; box-shadow:0 4px 15px -3px rgba(0,0,0,0.04); margin-bottom:18px;">
<h4 style="margin-top:0; margin-bottom:18px; color:#0f172a; font-family:sans-serif; text-align:center; font-size:15px; font-weight:700;">{baslik}</h4>
<div style="display:flex; flex-wrap:wrap; align-items:center; justify-content:center; gap:24px;">
<div style="width:140px; height:140px; border-radius:50%; background:conic-gradient({gradient_str}); position:relative; display:flex; align-items:center; justify-content:center; flex-shrink:0; box-shadow:0 4px 12px rgba(0,0,0,0.06);">
<div style="width:84px; height:84px; background:#ffffff; border-radius:50%; display:flex; flex-direction:column; align-items:center; justify-content:center; font-family:sans-serif;">
<span style="font-size:18px; font-weight:800; color:#0f172a;">{toplam}</span>
<span style="font-size:9px; color:#64748b; font-weight:700;">TOPLAM</span>
</div>
</div>
<div style="display:flex; flex-direction:column; justify-content:center;">
{legend_str}
</div>
</div>
</div>'''

# Veritabanı Güvenli Bağlantı (WAL Mode)
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()
cursor.execute("PRAGMA journal_mode=WAL;")

cursor.execute("""
CREATE TABLE IF NOT EXISTS ogrenciler (
    ad_soyad TEXT PRIMARY KEY,
    sifre TEXT,
    koc_adi TEXT DEFAULT '',
    hedef_uni TEXT DEFAULT '',
    hedef_bolum TEXT DEFAULT '',
    hedef_net FLOAT DEFAULT 100.0,
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
conn.commit()

# Varsayılan Koç Hesabı
cursor.execute("SELECT COUNT(*) FROM koclar")
if cursor.fetchone()[0] == 0:
    cursor.execute("INSERT INTO koclar (kullanici_adi, sifre) VALUES (?, ?)", ("koc1", make_hash("Koc123!")))
    conn.commit()

# Veritabanı Şema Güvencesi
for tbl, col, col_def in [
    ("ogrenciler", "koc_adi", "TEXT DEFAULT ''"),
    ("ogrenciler", "hedef_uni", "TEXT DEFAULT ''"),
    ("ogrenciler", "hedef_bolum", "TEXT DEFAULT ''"),
    ("ogrenciler", "hedef_net", "FLOAT DEFAULT 100.0"),
    ("ogrenciler", "program_guncellendi_mi", "INTEGER DEFAULT 0"),
    ("gunluk_calisma", "konu", "TEXT DEFAULT 'Genel Soru Çözümü / Karma'"),
    ("denemeler", "koc_notu", "TEXT DEFAULT ''")
]:
    try:
        cursor.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} {col_def}")
        conn.commit()
    except Exception:
        pass

TYT_KONULAR = {
    "📖 TYT Türkçe": ["Sözcükte Anlam", "Cümlede Anlam", "Paragraf", "Yazım Kuralları", "Noktalama İşaretleri", "Dil Bilgisi", "Metin Türleri"],
    "📐 TYT Matematik": ["Temel Kavramlar", "Sayı Basamakları", "Bölme - Bölünebilme", "EBOB - EKOK", "Rasyonel Sayılar", "Basit Eşitsizlikler", "Mutlak Değer", "Üslü & Köklü İfadeler", "Çarpanlara Ayırma", "Oran - Orantı", "Problemler (Sayı, Kesir, Yaş, Yüzde, Hız)", "Fonksiyonlar", "2. Dereceden Denklemler", "Polinomlar", "Mantık & Küme", "Permütasyon - Kombinasyon - Olasılık"],
    "📏 TYT Geometri": ["Doğruda ve Üçgende Açılar", "Özel Üçgenler", "Üçgende Alan & Benzerlik", "Çokgenler & Dörtgenler", "Çember ve Daire", "Analitik Geometri", "Katı Cisimler"],
    "⚡ TYT Fizik": ["Fizik Bilimine Giriş", "Madde ve Özellikleri", "Kuvvet ve Hareket", "İş, Güç, Enerji", "Isı ve Sıcaklık", "Basınç ve Kaldırma Kuvveti", "Elektrostatik & Elektrik", "Optik", "Dalgalar"],
    "🧪 TYT Kimya": ["Kimya Bilimi & Atom", "Periyodik Sistem", "Türler Arası Etkileşimler", "Maddenin Halleri", "Mol Kavramı & Tepkimeler", "Karışımlar", "Asit, Baz, Tuz"],
    "🧬 TYT Biyoloji": ["Yaşam Bilimi Biyoloji", "Hücre ve Organeller", "Hücre Bölünmeleri", "Kalıtım", "Ekoloji"],
    "📜 TYT Tarih": ["Tarih Bilimine Giriş", "İlk Çağ Uygarlıkları", "İslam Öncesi Türk Tarihi", "İslam Tarihi ve Uygarlığı", "Türk İslam Devletleri", "Osmanlı Devleti Kuruluş & Yükselme", "Milli Mücadele & İnkılap Tarihi"],
    "🌍 TYT Coğrafya": ["Doğa ve İnsan", "Dünya'nın Şekli ve Hareketleri", "Coğrafi Konum & Harita Bilgisi", "İklim Bilgisi & İklim Tipleri", "Yerin Şekillenmesi", "Beşeri Sistemler & Nüfus", "Afetler ve Çevre"],
    "🧠 TYT Felsefe": ["Felsefeyi Tanıma", "Felsefi Düşünce & Sorgulama", "Bilgi Felsefesi (Epistemoloji)", "Varlık Felsefesi (Ontoloji)", "Ahlak Felsefesi (Etik)", "Sanat Felsefesi", "Din Felsefesi"],
    "🕌 TYT Din Kültürü": ["İnanç & Allah İnancı", "İbadet ve Esasları", "Ahlak ve Değerler", "Hz. Muhammed (S.A.V.) ve Gençlik", "Vahiy ve Akıl", "İslam ve Bilim"]
}

DERSLER = list(TYT_KONULAR.keys())
GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
AKTIVITE_TURLERI = [
    "🧠 Konu Anlatımı & Çalışma",
    "✏️ Soru Çözümü & Etüt",
    "📐 Matematik Özel Ders",
    "📝 TYT Genel Denemesi",
    "🎯 TYT Branş Denemesi",
    "☕ Dinlenme / Serbest Zaman"
]

st.sidebar.markdown("""
<div style="text-align: center; padding: 10px 0 20px 0;">
    <span style="font-size: 42px;">🎓</span>
    <h2 style="margin: 5px 0 0 0; font-weight: 800; font-size: 20px; color: #0f172a;">YKS Pro Koçluk</h2>
    <p style="margin: 0; font-size: 12px; color: #0284c7; font-weight: 600;">Hedef & Gelişim Platformu</p>
</div>
""", unsafe_allow_html=True)

giris_turu = st.sidebar.radio("Giriş Paneli Seçin:", ["👨‍🎓 ÖĞRENCİ GİRİŞİ", "👨‍🏫 KOÇ GİRİŞİ"])

# ==================== ÖĞRENCİ PANELİ ====================
if giris_turu == "👨‍🎓 ÖĞRENCİ GİRİŞİ":
    st.markdown("<h1 style='font-weight:800; font-size:28px; color:#0f172a; margin-bottom:10px;'>👨‍🎓 Öğrenci Yönetim Paneli</h1>", unsafe_allow_html=True)
    
    if "motivasyon_goster" not in st.session_state: st.session_state["motivasyon_goster"] = True
    if "motivasyon_sozu" not in st.session_state: st.session_state["motivasyon_sozu"] = random.choice(MOTIVASYON_SOZLERI)
        
    if st.session_state["motivasyon_goster"]:
        m_col1, m_col2 = st.columns([0.9, 0.1])
        with m_col1:
            st.markdown(f'''
            <div class="hero-motivation-card">
                <div style="font-size:11px; letter-spacing:2px; font-weight:800; color:rgba(255,255,255,0.85); margin-bottom:6px;">⚡ GÜNÜN MOTİVASYON MESAJI</div>
                <div style="font-size:18px; font-weight:800;">"{st.session_state['motivasyon_sozu']}"</div>
            </div>
            ''', unsafe_allow_html=True)
        with m_col2:
            if st.button("❌ KAPAT", key="kapat_motivasyon", use_container_width=True):
                st.session_state["motivasyon_goster"] = False
                st.rerun()
    
    tab_giris, tab_hedef, tab_program, tab_gunluk, tab_deneme, tab_konular = st.tabs([
        "🔑 GİRİŞ / KAYIT",
        "🎯 YÖK ATLAS HEDEF TAKİBİ",
        "📅 HAFTALIK DERS PROGRAMI",
        "📝 GÜNLÜK ÇALIŞMA",
        "📊 DENEMELER & GELİŞİM",
        "🗺️ TYT KONU HAKİMİYETİ"
    ])
    
    # --- TAB 1: ÖĞRENCİ GİRİŞ / KAYIT ---
    with tab_giris:
        st.markdown("<h3 style='font-weight:700; font-size:18px; color:#1e293b;'>Öğrenci Hesabı Girişi / Kaydı</h3>", unsafe_allow_html=True)
        cursor.execute("SELECT kullanici_adi FROM koclar")
        koc_listesi = [r[0] for r in cursor.fetchall()] or ["koc1"]
            
        with st.form("ogrenci_giris_kayit_formu"):
            col1, col2, col3 = st.columns(3)
            with col1: ad_soyad = st.text_input("Adınız ve Soyadınız:").strip().title()
            with col2: sifre = st.text_input("Şifreniz / PIN:", type="password")
            with col3: secilen_koc = st.selectbox("👨‍🏫 Sorumlu Koçunuzu Seçin:", koc_listesi)
            ogr_giris_btn = st.form_submit_button("Giriş Yap / Hesabı Oluştur", type="primary", use_container_width=True)
            
        if ogr_giris_btn:
            if ad_soyad and sifre:
                cursor.execute("SELECT sifre, koc_adi FROM ogrenciler WHERE ad_soyad = ?", (ad_soyad,))
                user = cursor.fetchone()
                if user is None:
                    cursor.execute("INSERT INTO ogrenciler (ad_soyad, sifre, koc_adi) VALUES (?, ?, ?)", (ad_soyad, make_hash(sifre), secilen_koc))
                    conn.commit()
                    st.success(f"🎉 Hoş geldin {ad_soyad}! Profilin ({secilen_koc} koçluğunda) oluşturuldu.")
                    st.session_state["aktif_ogrenci"] = ad_soyad
                else:
                    if verify_hash(sifre, user[0]):
                        cursor.execute("UPDATE ogrenciler SET koc_adi = ? WHERE ad_soyad = ?", (secilen_koc, ad_soyad))
                        conn.commit()
                        st.success(f"🔓 Başarıyla giriş yapıldı! Hoş geldin {ad_soyad}.")
                        st.session_state["aktif_ogrenci"] = ad_soyad
                    else:
                        st.error("Hatalı şifre!")
            else:
                st.warning("Lütfen tüm alanları doldurunuz.")
                
    aktif_ogr = st.session_state.get("aktif_ogrenci", None)
    
    if not aktif_ogr:
        st.info("ℹ️ İşlem yapmak için lütfen ilk sekmeden 'Giriş / Kayıt' yapın.")
    else:
        st.sidebar.success(f"👤 Aktif Öğrenci: **{aktif_ogr}**")
        
        # 🔔 PROGRAM GÜNCELLEME UYARISI BİLDİRİMİ
        cursor.execute("SELECT program_guncellendi_mi FROM ogrenciler WHERE ad_soyad = ?", (aktif_ogr,))
        p_row = cursor.fetchone()
        if p_row and p_row[0] == 1:
            st.warning("🔔 **DERS PROGRAMI GÜNCELLEMESİ:** Sorumlu koçunuz haftalık ders programınızda yeni düzenlemeler yaptı! Aşağıdaki 'Haftalık Ders Programı' sekmesinden inceleyebilirsiniz.")
            if st.button("✅ Programı İnceledim / Bildirimi Kapat", type="secondary"):
                cursor.execute("UPDATE ogrenciler SET program_guncellendi_mi = 0 WHERE ad_soyad = ?", (aktif_ogr,))
                conn.commit()
                st.rerun()

        # --- TAB 2: YÖK ATLAS HEDEF TAKİBİ ---
        with tab_hedef:
            st.markdown(f"<h3 style='font-weight:700; font-size:18px; color:#1e293b;'>🎯 YÖK Atlas Üniversite & Bölüm Hedef Alanı — {aktif_ogr}</h3>", unsafe_allow_html=True)
            
            cursor.execute("SELECT hedef_uni, hedef_bolum, hedef_net FROM ogrenciler WHERE ad_soyad = ?", (aktif_ogr,))
            h_data = cursor.fetchone() or ("", "", 100.0)
            
            secilen_uni = st.selectbox("🏛️ Hedeflenen Üniversiteyi Seçin:", POPULE_UNIVERSITELER, index=POPULE_UNIVERSITELER.index(h_data[0]) if h_data[0] in POPULE_UNIVERSITELER else 0)
            
            mevcut_bolumler = list(YOK_ATLAS_VERILERI[secilen_uni].keys())
            secilen_bolum = st.selectbox("🎓 Hedeflenen Bölümü Seçin:", mevcut_bolumler, index=mevcut_bolumler.index(h_data[1]) if h_data[1] in mevcut_bolumler else 0)
            
            atlas_bilgi = YOK_ATLAS_VERILERI[secilen_uni][secilen_bolum]
            otomatik_taban_net = atlas_bilgi["taban_net"]
            
            st.markdown(f"""
            <div class="yok-atlas-card">
                <h4 style="margin-top:0; color:#0284c7; font-size:16px;">🏛️ YÖK Atlas Resmi Taban & Tavan Verileri ({secilen_uni} - {secilen_bolum})</h4>
                <div style="display:flex; justify-content:space-around; flex-wrap:wrap; gap:15px; margin-top:10px;">
                    <div><strong>📉 Taban Sıralama (Son Giren):</strong> <span style="color:#2563eb; font-weight:800;">{atlas_bilgi['taban_sira']}.</span></div>
                    <div><strong>🏆 Tavan Sıralama (1. Giren):</strong> <span style="color:#10b981; font-weight:800;">{atlas_bilgi['tavan_sira']}.</span></div>
                    <div><strong>🎯 Gerekli Taban TYT Net:</strong> <span style="color:#0284c7; font-weight:800;">{atlas_bilgi['taban_net']} Net</span></div>
                    <div><strong>🔥 Tavan TYT Net:</strong> <span style="color:#8b5cf6; font-weight:800;">{atlas_bilgi['tavan_net']} Net</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.form("hedef_kaydet_form"):
                col_h1, col_h2 = st.columns(2)
                with col_h1:
                    st.text_input("Seçilen YÖK Atlas Taban Neti (Otomatik Geldi):", value=f"{otomatik_taban_net} Net", disabled=True)
                with col_h2:
                    ozel_hedef_net = st.number_input("Kendi TYT Net Hedefinizi Özelleştirin (İsteğe Bağlı):", 40.0, 120.0, float(otomatik_taban_net), 1.0)
                
                if st.form_submit_button("🎯 Bu Hedefi Profilime Kaydet", type="primary", use_container_width=True):
                    cursor.execute("UPDATE ogrenciler SET hedef_uni = ?, hedef_bolum = ?, hedef_net = ? WHERE ad_soyad = ?", (secilen_uni, secilen_bolum, float(ozel_hedef_net), aktif_ogr))
                    conn.commit()
                    st.success(f"🎉 Hedefiniz ({secilen_uni} - {secilen_bolum}) başarıyla kaydedildi!")
                    st.rerun()

            # En Yüksek ve En Düşük Deneme Netlerini Çekme
            cursor.execute("SELECT MAX(toplam_net), MIN(toplam_net) FROM denemeler WHERE ad_soyad = ?", (aktif_ogr,))
            d_min_max = cursor.fetchone()
            max_net = d_min_max[0] if (d_min_max and d_min_max[0] is not None) else 0.0
            min_net = d_min_max[1] if (d_min_max and d_min_max[1] is not None) else 0.0
            hedef_net_val = float(h_data[2]) if (h_data[2] and h_data[2] > 0) else otomatik_taban_net

            st.divider()
            st.markdown("<h4 style='font-weight:700; font-size:16px; color:#334155;'>🏆 En Yüksek ve En Düşük Denemelerinize Göre Hedef Analizi</h4>", unsafe_allow_html=True)
            
            if max_net > 0:
                hedef_sub_tab1, hedef_sub_tab2 = st.tabs([
                    "🔥 EN YÜKSEK DENEME PERFORMANSI (ZİRVE)",
                    "🛡️ EN DÜŞÜK DENEME PERFORMANSI (TABAN)"
                ])

                # 🥇 EN YÜKSEK DENEME SEKMESİ
                with hedef_sub_tab1:
                    oran_max = min(1.0, max_net / hedef_net_val)
                    yuzde_max = oran_max * 100
                    st.markdown(f"**YÖK Atlas Hedef Net:** `{hedef_net_val}` Net | **En Yüksek Deneme Netiniz:** `{max_net}` Net")
                    st.progress(oran_max)
                    st.markdown(f"📈 **En Yüksek Nete Göre Hedefe Ulaşma Oranı: %{yuzde_max:.1f}**")
                    
                    fark_max = hedef_net_val - max_net
                    if fark_max <= 0:
                        st.balloons()
                        st.success(f"🔥 İNANILMAZ! En yüksek deneme netin ({max_net} Net) ile {secilen_uni} hedefini aştın! Potansiyelin burada, hep burayı hedefle!")
                    elif fark_max <= 10:
                        st.info(f"🚀 Zirve performansın hedefine ramak kala! Hedefe sadece **{fark_max:.1f} Net** kaldı. Sen bu neti yapabiliyorsun, başarmak elinde!")
                    else:
                        st.info(f"💪 En yüksek netine göre hedefe ulaşmak için **{fark_max:.1f} Net** gerekiyor. Zirveni daha da yukarı taşımak için eksikleri kapatmaya devam!")

                # 🛡️ EN DÜŞÜK DENEME SEKMESİ
                with hedef_sub_tab2:
                    oran_min = min(1.0, min_net / hedef_net_val)
                    yuzde_min = oran_min * 100
                    st.markdown(f"**YÖK Atlas Hedef Net:** `{hedef_net_val}` Net | **En Düşük Deneme Netiniz:** `{min_net}` Net")
                    st.progress(oran_min)
                    st.markdown(f"📈 **En Düşük Nete Göre Hedef Ulaşma Oranı: %{yuzde_min:.1f}**")
                    
                    fark_min = hedef_net_val - min_net
                    if fark_min <= 0:
                        st.balloons()
                        st.success(f"🛡️ MÜKEMMEL! En kötü günündeki deneme netin ({min_net} Net) bile {secilen_uni} hedefini karşılıyor! Sisteminiz çok sağlam!")
                    else:
                        st.warning(f"⚠️ En düşük denemendeki taban netin ile hedef arasındaki fark: **{fark_min:.1f} Net**. Kötü geçen sınav günlerinde bile netini korumak için dip net seviyeni yukarı çekmeliyiz!")

            else:
                st.info("ℹ️ Henüz kaydedilmiş bir deneme sonucunuz bulunmuyor. Denemelerinizi girdikçe en yüksek ve en düşük netlerinize göre analizler burada görüntülenecektir.")

        # --- TAB 3: DERS PROGRAMI (KOÇ TARAFINDAN GİRİLEN) ---
        with tab_program:
            st.markdown("<h3 style='font-weight:700; font-size:18px; color:#1e293b;'>📅 Sorumlu Koçunuz Tarafından Hazırlanan Haftalık Ders Programı</h3>", unsafe_allow_html=True)
            
            df_prog = pd.read_sql_query("SELECT gun, saat_araligi, aktivite_turu, ders, detay_aciklama FROM haftalik_program WHERE ad_soyad = ? ORDER BY id ASC", conn, params=(aktif_ogr,))
            
            if df_prog.empty:
                st.info("ℹ️ Sorumlu koçunuz henüz size özel bir çalışma programı tanımlamadı. Koçunuz programı girdiğinde doğrudan burada görüntülenecektir.")
            else:
                st.dataframe(df_prog, use_container_width=True)
                
                # PDF / Çıktı Alma Alanı
                html_table = df_prog.to_html(index=False, classes="styled-table")
                html_prog_page = f"""
                <div style="font-family: Arial, sans-serif; padding:25px; border:2px solid #0284c7; border-radius:12px; background:#fff; color:#0f172a;">
                    <h2 style="color:#0284c7; text-align:center; margin-bottom:5px;">🎓 {aktif_ogr} - HAFTALIK YKS DERS PROGRAMI</h2>
                    <p style="text-align:center; color:#64748b; font-size:13px; margin-top:0;">Tarih: {datetime.date.today().strftime('%d.%m.%Y')}</p>
                    <hr style="border:1px solid #e2e8f0; margin-bottom:20px;"/>
                    {html_table}
                </div>
                """
                b64_p = base64.b64encode(html_prog_page.encode('utf-8')).decode('utf-8')
                href_p = f'<a href="data:text/html;charset=utf-8;base64,{b64_p}" download="{aktif_ogr}_Haftalik_Ders_Programi.html" style="display:inline-block; padding:10px 20px; background-color:#10b981; color:white; text-decoration:none; border-radius:10px; font-weight:bold;">📄 Haftalık Programı Yazdır / PDF İndir</a>'
                st.markdown(href_p, unsafe_allow_html=True)

        # --- TAB 4: GÜNLÜK ÇALIŞMA ---
        with tab_gunluk:
            st.markdown(f"<h3 style='font-weight:700; font-size:18px; color:#1e293b;'>📝 Günlük Çalışma Girişi — {aktif_ogr}</h3>", unsafe_allow_html=True)
            
            c_top1, c_top2, c_top3 = st.columns([1, 1, 1])
            with c_top1: tarih_giris = st.date_input("Çalışma Tarihi", datetime.date.today())
            with c_top2: sure_giris = st.number_input("Bugünkü Toplam Çalışma Süresi (Saat)", 0.0, 16.0, 7.5, 0.5)
            with c_top3: verim_giris = st.slider("Günün Verim Puanı (1-10)", 1, 10, 8)
                
            not_giris = st.text_area("Bugün zorlandığın detaylar / Koçuna iletmek istediğin çalışma notu:", height=80)
            
            st.divider()
            st.markdown("<h4 style='font-weight:700; font-size:16px; color:#334155;'>📚 Ders ve Konu Bazlı Soru Analizi Girişi</h4>", unsafe_allow_html=True)
            
            ders_sekmeleri = st.tabs(DERSLER)
            ders_verileri = {}

            for idx, ders_adi in enumerate(DERSLER):
                with ders_sekmeleri[idx]:
                    secilen_konu = st.selectbox(
                        f"Çalıştığınız Konu ({ders_adi}):",
                        options=["Genel Soru Çözümü / Karma"] + TYT_KONULAR[ders_adi],
                        key=f"konu_select_{ders_adi}"
                    )
                    
                    c1, c2, c3, c4 = st.columns(4)
                    with c1: toplam_s = st.number_input(f"Toplam Soru ({ders_adi})", 0, 500, 0, key=f"top_{ders_adi}")
                    with c2: dogru_s = st.number_input(f"Doğru ({ders_adi})", 0, 500, 0, key=f"dog_{ders_adi}")
                    with c3: yanlis_s = st.number_input(f"Yanlış ({ders_adi})", 0, 500, 0, key=f"yan_{ders_adi}")
                    with c4: bos_s = st.number_input(f"Boş ({ders_adi})", 0, 500, 0, key=f"bos_{ders_adi}")
                        
                    if dogru_s + yanlis_s + bos_s > toplam_s:
                        st.error(f"⚠️ {ders_adi}: Doğru + Yanlış + Boş sayısı Toplam Soru sayısından fazla olamaz!")
                    
                    ders_verileri[ders_adi] = (secilen_konu, toplam_s, dogru_s, yanlis_s, bos_s)

            if st.button("🚀 Tüm Ders ve Konu Çalışmalarını Kaydet", type="primary", use_container_width=True):
                yeni_kayit = False
                for d_adi, (k_adi, t_s, d_s, y_s, b_s) in ders_verileri.items():
                    if t_s > 0:
                        yeni_kayit = True
                        cursor.execute("DELETE FROM gunluk_calisma WHERE ad_soyad = ? AND tarih = ? AND ders = ? AND konu = ?", (aktif_ogr, str(tarih_giris), d_adi, k_adi))
                        cursor.execute("""
                        INSERT INTO gunluk_calisma (ad_soyad, tarih, ders, konu, toplam_soru, dogru, yanlis, bos, sure, verim, notlar)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (aktif_ogr, str(tarih_giris), d_adi, k_adi, t_s, d_s, y_s, b_s, float(sure_giris), int(verim_giris), not_giris))
                        conn.commit()
                
                if yeni_kayit:
                    st.balloons()
                    st.success("🎉 TEBRİKLER HEDEFİNE 1 ADIM DAHA YAKLAŞTIN!")
                else:
                    st.warning("Lütfen kaydetmeden önce en az bir dersten soru sayısı giriniz.")

            st.divider()
            st.markdown(f"<h4 style='font-weight:700; font-size:16px; color:#1e293b;'>📈 Anlık Soru ve Başarı Grafikleri — {aktif_ogr}</h4>", unsafe_allow_html=True)
            
            df_analiz = pd.read_sql_query("SELECT ders, SUM(toplam_soru) as toplam, SUM(dogru) as d, SUM(yanlis) as y, SUM(bos) as b FROM gunluk_calisma WHERE ad_soyad = ? GROUP BY ders", conn, params=(aktif_ogr,))
            
            if df_analiz.empty or df_analiz["toplam"].sum() == 0:
                st.info("📊 Henüz soru verisi bulunmuyor.")
            else:
                top_d, top_y, top_b = int(df_analiz["d"].sum()), int(df_analiz["y"].sum()), int(df_analiz["b"].sum())
                col_g1, col_g2 = st.columns(2)
                
                with col_g1:
                    df_filtr = df_analiz[df_analiz["toplam"] > 0]
                    renkler = ['#0284c7', '#0ea5e9', '#38bdf8', '#818cf8', '#6366f1', '#4f46e5', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6']
                    ders_v_list = [(row["ders"], int(row["toplam"]), renkler[idx % len(renkler)]) for idx, row in df_filtr.reset_index().iterrows()]
                    st.markdown(halka_grafik_html("🍩 Derslere Göre Soru Dağılımı", ders_v_list), unsafe_allow_html=True)

                with col_g2:
                    dyb_verileri = [("Doğru 🟢", top_d, "#10b981"), ("Yanlış 🔴", top_y, "#ef4444"), ("Boş 🟡", top_b, "#f59e0b")]
                    st.markdown(halka_grafik_html("🎯 Toplam Doğru / Yanlış / Boş Oranı", dyb_verileri), unsafe_allow_html=True)

        # --- TAB 5: DENEMELER & GELİŞİM ---
        with tab_deneme:
            st.markdown("<h3 style='font-weight:700; font-size:18px; color:#1e293b;'>📊 Deneme Sonuçları & Karne Yükleme</h3>", unsafe_allow_html=True)
            
            with st.form("deneme_yukle_formu"):
                col_d1, col_d2, col_d3 = st.columns(3)
                with col_d1: yayin = st.text_input("Deneme Adı / Yayın:")
                with col_d2: d_tur = st.selectbox("Deneme Türü:", ["TYT Genel Denemesi", "TYT Branş Denemesi"])
                with col_d3: toplam_net = st.number_input("Toplam Netiniz:", 0.0, 120.0, 75.0)
                    
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
                st.success("🎉 Deneme sonucu kaydedildi!")

            st.divider()
            st.markdown("<h4 style='font-weight:700; font-size:16px; color:#1e293b;'>📈 Zaman İçindeki Net Gelişim Grafiğiniz</h4>", unsafe_allow_html=True)
            df_net_trend = pd.read_sql_query("SELECT tarih, toplam_net, yayin FROM denemeler WHERE ad_soyad = ? ORDER BY id ASC", conn, params=(aktif_ogr,))
            
            if not df_net_trend.empty:
                st.line_chart(df_net_trend.set_index("tarih")["toplam_net"])
            else:
                st.info("Henüz zaman grafiği gösterecek kadar deneme verisi girilmedi.")

            st.divider()
            st.markdown("<h4 style='font-weight:700; font-size:16px; color:#1e293b;'>📋 Geçmiş Denemeleriniz ve Koçunuzun Değerlendirmeleri</h4>", unsafe_allow_html=True)
            df_ogr_deneme = pd.read_sql_query("SELECT tarih, yayin, tur, toplam_net, dosya_adi, koc_notu FROM denemeler WHERE ad_soyad = ? ORDER BY id DESC", conn, params=(aktif_ogr,))
            if df_ogr_deneme.empty:
                st.info("Henüz kaydedilmiş bir deneme sonucunuz bulunmuyor.")
            else:
                for idx, row in df_ogr_deneme.iterrows():
                    with st.expander(f"📌 {row['tarih']} — {row['yayin']} ({row['tur']}) | Net: {row['toplam_net']}"):
                        st.write(f"**Karne Dosyası:** {row['dosya_adi']}")
                        if row['koc_notu'] and str(row['koc_notu']).strip() != '':
                            st.markdown(f"""
                            <div class="coach-feedback-card">
                                <strong>👨‍🏫 Koçunuzun Deneme Analizi ve Notu:</strong><br/>
                                <div style="margin-top: 6px; white-space: pre-wrap;">{row['koc_notu']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.info("👨‍🏫 Koçunuz henüz bu deneme için analiz notu eklemedi.")

        # --- TAB 6: TYT KONU HAKİMİYETİ ---
        with tab_konular:
            st.markdown("<h3 style='font-weight:700; font-size:18px; color:#1e293b;'>🗺️ TYT Ders Ders Konu Hakimiyet Puanlaması (1 - 5)</h3>", unsafe_allow_html=True)
            st.caption("1 ve 2 puan alan konular koç paneline 'Acil Müdahale Konuları' olarak aktarılır.")
            
            konu_sekmeleri = st.tabs(list(TYT_KONULAR.keys()))
            
            for idx, (d_adi, k_list) in enumerate(TYT_KONULAR.items()):
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

# ==================== KOÇ PANELİ ====================
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

        with koc_tab_giris:
            st.markdown("<h3 style='font-weight:700; font-size:18px;'>👨‍🏫 Koç Girişi</h3>", unsafe_allow_html=True)
            with st.form("koc_giris_formu"):
                k_adi_giris = st.text_input("Koç Kullanıcı Adı:").strip()
                k_sifre_giris = st.text_input("Şifre:", type="password")
                giris_btn = st.form_submit_button("Koç Paneline Giriş Yap", type="primary", use_container_width=True)
                
            if giris_btn:
                cursor.execute("SELECT sifre FROM koclar WHERE kullanici_adi = ?", (k_adi_giris,))
                row = cursor.fetchone()
                if row and verify_hash(k_sifre_giris, row[0]):
                    st.session_state["aktif_koc"] = k_adi_giris
                    st.success(f"🔓 Hoş geldiniz Sayın Koç {k_adi_giris}!")
                    st.rerun()
                else:
                    st.error("Hatalı kullanıcı adı veya şifre!")

        with koc_tab_kayit:
            st.markdown("<h3 style='font-weight:700; font-size:18px;'>📝 Yeni Koç Hesabı Oluştur</h3>", unsafe_allow_html=True)
            st.markdown(f"""
            <div class="info-security-card">
                🛡️ Katılım Kodu: <code>{SISTEM_YONETICI_KATILIM_KODU}</code> | Şifre en az 6 karakter, 1 harf, 1 rakam ve 1 özel karakter içermelidir.
            </div>
            """, unsafe_allow_html=True)
            
            with st.form("koc_kayit_formu"):
                katilim_kodu_input = st.text_input("🔑 Yönetici Katılım Kodu:", type="password")
                yeni_k_adi = st.text_input("Yeni Koç Kullanıcı Adı:").strip()
                yeni_k_sifre = st.text_input("Şifre:", type="password")
                yeni_k_sifre_tekrar = st.text_input("Şifre Tekrarı:", type="password")
                kaydet_btn = st.form_submit_button("Koç Hesabını Kaydet", type="primary", use_container_width=True)
            
            if kaydet_btn:
                if katilim_kodu_input != SISTEM_YONETICI_KATILIM_KODU:
                    st.error("❌ Hatalı Katılım Kodu!")
                elif yeni_k_sifre != yeni_k_sifre_tekrar:
                    st.error("Şifreler uyuşmuyor!")
                else:
                    gecerli, mesaj = sifre_gecerli_mi(yeni_k_sifre)
                    if not gecerli:
                        st.error(f"⚠️ {mesaj}")
                    else:
                        cursor.execute("INSERT INTO koclar (kullanici_adi, sifre) VALUES (?, ?)", (yeni_k_adi, make_hash(yeni_k_sifre)))
                        conn.commit()
                        st.success(f"🎉 Koç hesabı ({yeni_k_adi}) başarıyla oluşturuldu!")

        with koc_tab_sifre:
            st.markdown("<h3 style='font-weight:700; font-size:18px;'>🔒 Şifre Değiştir</h3>", unsafe_allow_html=True)
            with st.form("koc_sifre_degistir_formu"):
                s_k_adi = st.text_input("Kullanıcı Adınız:").strip()
                eski_sifre = st.text_input("Mevcut Şifreniz:", type="password")
                yeni_sifre = st.text_input("Yeni Şifreniz:", type="password")
                yeni_sifre_tekrar = st.text_input("Yeni Şifre Tekrarı:", type="password")
                sifre_guncelle_btn = st.form_submit_button("Şifreyi Güncelle", use_container_width=True)
            
            if sifre_guncelle_btn:
                cursor.execute("SELECT sifre FROM koclar WHERE kullanici_adi = ?", (s_k_adi,))
                row = cursor.fetchone()
                if not row or not verify_hash(eski_sifre, row[0]):
                    st.error("Mevcut şifre hatalı!")
                elif yeni_sifre != yeni_sifre_tekrar:
                    st.error("Yeni şifreler uyuşmuyor!")
                else:
                    cursor.execute("UPDATE koclar SET sifre = ? WHERE kullanici_adi = ?", (make_hash(yeni_sifre), s_k_adi))
                    conn.commit()
                    st.success("🎉 Şifreniz güncellendi!")

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
            st.info(f"👨‍🏫 Sayın Koç {aktif_koc_adi}, sistemde henüz kayıtlı öğrenciniz bulunmuyor.")
        else:
            secilen_ogr = st.selectbox(f"🔍 Yönetilecek Öğrenciyi Seçin ({len(ogrenciler)} Kayıtlı Öğrenci):", ogrenciler)
            
            cursor.execute("SELECT hedef_uni, hedef_bolum, hedef_net FROM ogrenciler WHERE ad_soyad = ?", (secilen_ogr,))
            h_info = cursor.fetchone()
            if h_info and h_info[0]:
                st.info(f"🎯 **Öğrenci YÖK Atlas Hedefi:** {h_info[0]} - {h_info[1]} (Hedef Taban Net: {h_info[2]})")
            
            st.divider()
            st.markdown(f"### 📅 {secilen_ogr} İçin Haftalık Ders Programı Oluşturma & Düzenleme")
            
            with st.expander("➕ Programa Yeni Etüt / Ders / Deneme Saati Ekle", expanded=True):
                with st.form("prog_ekle_form"):
                    cp1, cp2, cp3 = st.columns(3)
                    with cp1: p_gun = st.selectbox("Gün:", GUNLER)
                    with cp2: p_saat = st.text_input("Saat Aralığı (Ör: 14:00 - 15:00):", value="14:00 - 15:00")
                    with cp3: p_aktivite = st.selectbox("Aktivite Türü:", AKTIVITE_TURLERI)
                    
                    cp4, cp5 = st.columns(2)
                    with cp4: p_ders = st.selectbox("İlgili Ders:", DERSLER + ["--- Genel / Yok ---"])
                    with cp5: p_detay = st.text_input("Konu Anlatımı / Soru Sayısı / Detay Açıklama:", placeholder="Ör: Paragraf 40 Soru + Matematik Problem")
                    
                    if st.form_submit_button("➕ Bu Aktiviteyi Program Tablosuna Ekle", type="primary", use_container_width=True):
                        cursor.execute("""
                        INSERT INTO haftalik_program (ad_soyad, gun, saat_araligi, aktivite_turu, ders, detay_aciklama)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """, (secilen_ogr, p_gun, p_saat, p_aktivite, p_ders, p_detay))
                        cursor.execute("UPDATE ogrenciler SET program_guncellendi_mi = 1 WHERE ad_soyad = ?", (secilen_ogr,))
                        conn.commit()
                        st.success("🎉 Ders aktivitesi eklendi ve öğrenciye bildirim gönderildi!")
                        st.rerun()

            df_koc_prog = pd.read_sql_query("SELECT id, gun, saat_araligi, aktivite_turu, ders, detay_aciklama FROM haftalik_program WHERE ad_soyad = ? ORDER BY id ASC", conn, params=(secilen_ogr,))
            if not df_koc_prog.empty:
                st.markdown("#### 📋 Öğrencinin Aktif Ders Programı")
                st.dataframe(df_koc_prog, use_container_width=True)
                
                sil_id = st.selectbox("Silmek istediğiniz aktivitenin ID numarasını seçin:", df_koc_prog["id"].tolist())
                if st.button("🗑️ Seçilen Ders Aktivitesini Programdan Sil", type="secondary"):
                    cursor.execute("DELETE FROM haftalik_program WHERE id = ?", (sil_id,))
                    cursor.execute("UPDATE ogrenciler SET program_guncellendi_mi = 1 WHERE ad_soyad = ?", (secilen_ogr,))
                    conn.commit()
                    st.success("Aktivite silindi ve program güncellendi!")
                    st.rerun()
            else:
                st.info("Bu öğrenci için henüz program aktivitesi girilmedi.")

            st.divider()
            st.markdown(f"<h2 style='font-weight:800; font-size:22px; color:#0f172a;'>📊 Öğrenci Analiz Raporu: {secilen_ogr}</h2>", unsafe_allow_html=True)
            
            st.markdown("<h4 style='font-weight:700; font-size:16px; color:#334155;'>📚 Ders & Konu Bazlı Soru Dağılımı</h4>", unsafe_allow_html=True)
            df_gunluk = pd.read_sql_query("SELECT id, tarih, ders, konu, toplam_soru, dogru, yanlis, bos, sure, verim, notlar FROM gunluk_calisma WHERE ad_soyad = ?", conn, params=(secilen_ogr,))
            
            if not df_gunluk.empty:
                st.dataframe(df_gunluk, use_container_width=True)
            else:
                st.info("Bu öğrenci henüz soru verisi girmedi.")
                
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
                            f"• YÖK Atlas Hedefi: {h_info[0] if h_info else ''} ({h_info[2] if h_info else ''} Net)\n"
                            f"• Tespit Edilen Zayıf Konular: {zayif_str}\n\n"
                            f"💡 Sorumlu Koç ({aktif_koc_adi}) Tavsiyesi & Çalışma Planı:\n"
                            f"1. Zayıf tespit edilen konulardan haftalık en az 40'ar soru çözülmeli.\n"
                            f"2. Matematik özel dersindeki örnek sorular tekrar edilmeli.\n"
                            f"3. Zamana karşı süre tutularak TYT branş denemesi çözülmeli."
                        )
                        st.session_state[f"temp_not_{secilen_deneme_id}"] = otomatik_not
                        st.success("🤖 Otomatik analiz taslağı üretildi!")

                mevcut_koc_notu = st.session_state.get(f"temp_not_{secilen_deneme_id}", deneme_row['koc_notu'])
                if pd.isna(mevcut_koc_notu): mevcut_koc_notu = ""

                yeni_koc_notu = st.text_area("Koç Değerlendirmesi (Onaylamak için kaydedin):", value=mevcut_koc_notu, height=180, key=f"koc_not_input_{secilen_deneme_id}")
                
                col_save, col_pdf = st.columns(2)
                with col_save:
                    if st.button("💾 Değerlendirmeyi Onayla ve Öğrenciye İlet", type="primary", use_container_width=True):
                        cursor.execute("UPDATE denemeler SET koc_notu = ? WHERE id = ?", (yeni_koc_notu, secilen_deneme_id))
                        conn.commit()
                        st.success("🎉 Deneme analiz notu öğrenci paneline gönderildi!")
                
                with col_pdf:
                    st.markdown("##### 📄 Yazdırılabilir / PDF Rapor Karnesi")
                    html_rapor = f"""
                    <div style="font-family: 'Segoe UI', Arial, sans-serif; padding: 25px; border: 2px solid #0284c7; border-radius: 12px; background-color: #ffffff; color: #0f172a;">
                        <div style="text-align: center; border-bottom: 2px solid #e2e8f0; padding-bottom: 12px; margin-bottom: 18px;">
                            <h2 style="color: #0284c7; margin: 0; font-size: 22px;">🎓 YKS ÖĞRENCİ GELİŞİM & DENEME KARNESİ</h2>
                            <p style="color: #64748b; margin: 6px 0 0 0; font-size: 13px;"><strong>Tarih:</strong> {datetime.date.today().strftime('%d.%m.%Y')} | <strong>Koç:</strong> {aktif_koc_adi}</p>
                        </div>
                        <p style="font-size: 14px;"><strong>👨‍🎓 Öğrenci Adı Soyadı:</strong> {secilen_ogr}</p>
                        <p style="font-size: 14px;"><strong>🎯 YÖK Atlas Hedefi:</strong> {h_info[0] if h_info else ''} - {h_info[1] if h_info else ''}</p>
                        <p style="font-size: 14px;"><strong>📑 Deneme Adı / Yayın:</strong> {deneme_row['yayin']} ({deneme_row['tur']})</p>
                        <p style="font-size: 14px;"><strong>🎯 Toplam Net:</strong> <span style="font-size: 18px; color: #0284c7; font-weight: bold;">{deneme_row['toplam_net']} Net</span></p>
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
                st.success("✨ Öğrencinin acil müdahale gerektiren zayıf konusu bulunmuyor.")