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
    page_title="YKS-LGS KOÇLUK (DENİZ YILMAZ)",
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

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%) !important;
        color: #ffffff !important;
        box-shadow: 0 8px 20px -4px rgba(2, 132, 199, 0.35) !important;
    }

    .hero-motivation-card {
        background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 50%, #8b5cf6 100%);
        color: #ffffff;
        padding: 22px 28px;
        border-radius: 20px;
        font-weight: 700;
        box-shadow: 0 12px 30px -5px rgba(14, 165, 233, 0.3);
        margin-bottom: 20px;
    }

    .target-card {
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
    }

    .soru-card {
        background: #ffffff;
        border-radius: 14px;
        padding: 15px;
        border: 1px solid #e2e8f0;
        margin-bottom: 12px;
    }

    .konu-analiz-box {
        background: #fefce8;
        border-left: 4px solid #eab308;
        padding: 10px 14px;
        border-radius: 8px;
        font-size: 13px;
        color: #713f12;
        margin-top: 8px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

SISTEM_YONETICI_KATILIM_KODU = "YKS2026KOC"
DB_FILE = "yks_kocluk.db"
UPLOAD_DIR = "soru_yuklemeleri"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def make_hash(password: str) -> str:
    salt = "YKS_PRO_SECURE_SALT_2026"
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()

def verify_hash(password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    if password == hashed_password:
        return True
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

# 🧠 OTOMATİK KONU ANALİZİ VE İPUCU ÜRETİCİSİ
def soru_konu_analizi_ureteci(ders, konu):
    if "Matematik" in ders:
        return f"📌 **{konu}** konusu işlem basamakları veya formül uygulama eksikliğine dayanabilir. Öğrencinin soru kalıbındaki temel denklem kurma adımını inceleyin."
    elif "Türkçe" in ders:
        return f"📌 **{konu}** sorusunda paragraf/metin okuma veya kelime bilgisi kilit roldedir. Çeldirici şıkkın neden yanlış olduğunu öğrenciye vurgulayın."
    elif "Fizik" in ders or "Fen" in ders:
        return f"📌 **{konu}** sorusunda kavram yanılgısı veya birim dönüşümü hatası muhtemeldir. Şekilli/grafikli verileri doğru okuyup okumadığını kontrol edin."
    elif "Kimya" in ders:
        return f"📌 **{konu}** konusunda tanım veya mol/oran hesaplamalarında takılınmış olabilir. Temel mantığı formül kullanmadan anlatmak faydalı olacaktır."
    elif "Biyoloji" in ders:
        return f"📌 **{konu}** ezber ve görsel kavrama ağırlıklıdır. İlgili şemanın ve terimlerin tekrar edilmesini tavsiye edin."
    elif "Tarih" in ders or "İnkılap" in ders:
        return f"📌 **{konu}** sorusu sebep-sonuç ilişkisini ölçmektedir. Tarihsel kronolojiye ve öncüllü sorulara dikkat çekin."
    elif "Coğrafya" in ders:
        return f"📌 **{konu}** harita bilgisi veya kavramsal eşleştirme gerektirir. Görsel materyallerle konuyu pekiştirin."
    else:
        return f"📌 **{konu}** konusu üzerine öğrencinin konu anlatım eksiği veya dikkat hatası olabilir. Çözüm adımlarını basitçe özetleyin."

MOTIVASYON_SOZLERI = [
    "🌿 Sakin ol, derin bir nefes al ve adım adım ilerle. Disiplin başarıyı getirir!",
    "🚀 Başarı, her gün ertelemeden tekrarlanan küçük çabaların birikimidir!",
    "🎓 Bugün döktüğün her damla alın teri, hayalindeki okulun kapısını açar!",
    "💪 Zorluklar, potansiyelini keşfetmen için var olan basamaklardır. Pes etmek yok!",
    "✨ Şimdi odaklan ve çalış, gelecekteki kendin seninle gurur duysun!",
    "🎯 Zirveye giden yolda engel yoktur, sadece kararlılıkla aşılacak hedefler vardır!"
]

ILLER_LISTESI = [
    "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Aksaray", "Amasya", "Ankara", "Antalya", "Ardahan", "Artvin",
    "Aydın", "Balıkesir", "Bartın", "Batman", "Bayburt", "Bilecik", "Bingöl", "Bitlis", "Bolu", "Burdur",
    "Bursa", "Çanakkale", "Çankırı", "Çorum", "Denizli", "Diyarbakır", "Düzce", "Edirne", "Elazığ", "Erzincan",
    "Erzurum", "Eskişehir", "Gaziantep", "Giresun", "Gümüşhane", "Hakkari", "Hatay", "Iğdır", "Isparta", "İstanbul",
    "İzmir", "Kahramanmaraş", "Karabük", "Karaman", "Kars", "Kastamonu", "Kayseri", "Kırıkkale", "Kırklareli", "Kırşehir",
    "Kilis", "Kocaeli", "Konya", "Kütahya", "Malatya", "Manisa", "Mardin", "Mersin", "Muğla", "Muş",
    "Nevşehir", "Niğde", "Ordu", "Osmaniye", "Rize", "Sakarya", "Samsun", "Siirt", "Sinop", "Sivas",
    "Şanlıurfa", "Şırnak", "Tekirdağ", "Tokat", "Trabzon", "Tunceli", "Uşak", "Van", "Yalova", "Yozgat", "Zonguldak"
]

YOK_ATLAS_VERILERI = {
    "İstanbul Teknik Üniversitesi (İTÜ)": {
        "Bilgisayar Mühendisliği": {"taban_sira": "2.150", "tavan_sira": "120", "taban_net": 108.5, "tavan_net": 117.5},
        "Yazılım Mühendisliği": {"taban_sira": "3.100", "tavan_sira": "450", "taban_net": 106.0, "tavan_net": 115.0},
        "Elektrik-Elektronik Mühendisliği": {"taban_sira": "3.800", "tavan_sira": "310", "taban_net": 105.0, "tavan_net": 116.0}
    },
    "Boğaziçi Üniversitesi": {
        "Bilgisayar Mühendisliği": {"taban_sira": "290", "tavan_sira": "1", "taban_net": 114.0, "tavan_net": 120.0},
        "Elektrik-Elektronik Mühendisliği": {"taban_sira": "850", "tavan_sira": "15", "taban_net": 112.5, "tavan_net": 119.5}
    },
    "Ortadoğu Teknik Üniversitesi (ODTÜ)": {
        "Bilgisayar Mühendisliği": {"taban_sira": "800", "tavan_sira": "12", "taban_net": 112.0, "tavan_net": 119.5}
    }
}

LGS_IL_LISELERI = {
    "İstanbul": {
        "Galatasaray Lisesi": {"taban_puan": "500.0", "yuzdelik": "%0.04", "taban_net": 88.5},
        "İstanbul Lisesi (Erkek Lisesi)": {"taban_puan": "498.5", "yuzdelik": "%0.06", "taban_net": 87.5},
        "Kabataş Erkek Lisesi": {"taban_puan": "496.0", "yuzdelik": "%0.11", "taban_net": 86.5}
    },
    "Ankara": {
        "Ankara Fen Lisesi": {"taban_puan": "495.0", "yuzdelik": "%0.13", "taban_net": 86.0}
    }
}

GENEL_DEFAULT_LISE = {
    "İl Nitelikli Fen Lisesi (Genel Taban)": {"taban_puan": "450.0", "yuzdelik": "%2.50", "taban_net": 72.0},
    "İl Nitelikli Anadolu Lisesi (Genel Taban)": {"taban_puan": "410.0", "yuzdelik": "%6.00", "taban_net": 62.0}
}

# 📚 ÖSYM DERS VE DETAYLI TYT - AYT MÜFREDAT KONU SÖZLÜĞÜ
YKS_KONULAR = {
    "📖 TYT Türkçe": [
        "Sözcükte Anlam", "Cümlede Anlam", "Paragrafta Anlam ve Yapı", "Sözcük Türleri (İsim, Sıfat, Zamir, Zarf, Edat, Bağlaç)",
        "Fiiller & Fiilimsi", "Fiilde Çatı", "Cümlenin Ögeleri", "Cümle Türleri", "Yazım Kuralları", "Noktalama İşaretleri", "Ses Bilgisi", "Anlatım Bozuklukları"
    ],
    "📐 TYT Matematik": [
        "Temel Kavramlar & Sayı Kümeleri", "Sayı Basamakları", "Bölme ve Bölünebilme", "EBOB - EKOK", "Rasyonel Sayılar",
        "Basit Eşitsizlikler", "Mutlak Değer", "Üslü & Köklü İfadeler", "Çarpanlara Ayırma", "Oran - Orantı", "Sayı ve Kesir Problemleri",
        "Yaş Problemleri", "Yüzde / Kâr-Zarar Problemleri", "Karışım / Hız Problemleri", "Mantık & Kümeler", "Fonksiyonlar (Temel)", "Permütasyon, Kombinasyon, Olasılık"
    ],
    "📏 TYT Geometri": [
        "Doğruda ve Üçgende Açılar", "Özel Üçgenler", "Üçgende Alan ve Benzerlik", "Çokgenler ve Dörtgenler", "Çember ve Daire", "Katı Cisimler"
    ],
    "⚡ TYT Fizik": [
        "Fizik Bilimine Giriş", "Madde ve Özellikleri", "Kaldırma Kuvveti & Basınç", "Isı, Sıcaklık ve Genleşme", "Doğrusal Hareket",
        "Newton'un Hareket Yasaları", "İş, Güç, Enerji", "Elektrostatik & Elektrik Devreleri", "Optik", "Dalgalar"
    ],
    "🧪 TYT Kimya": [
        "Kimya Bilimi", "Atom ve Periyodik Sistem", "Kimyasal Türler Arası Etkileşimler", "Maddenin Halleri", "Kimyasal Hesaplamalar", "Karışımlar", "Asitler, Bazlar ve Tuzlar"
    ],
    "🧬 TYT Biyoloji": [
        "Yaşam Bilimi Biyoloji", "Hücre ve Organeller", "Hücre Bölünmeleri & Üreme", "Kalıtım", "Ekoloji"
    ],
    "📜 TYT Tarih": [
        "Tarih Bilimi & İlk Çağ Uygarlıkları", "İslam Öncesi Türk Tarihi", "Türk-İslam Devletleri", "Osmanlı Devleti", "Milli Mücadele Dönemi"
    ],
    "🌍 TYT Coğrafya": [
        "Doğa ve İnsan", "Harita Bilgisi & Dünya'nın Şekli", "İklim Bilgisi", "Yerşekilleri", "Nüfus ve Yerleşme", "Afetler"
    ],
    "🧠 TYT Felsefe": ["Felsefeyi Tanıma", "Bilgi Felsefesi", "Varlık Felsefesi", "Ahlak Felsefesi", "Din Felsefesi"],
    "🕌 TYT Din Kültürü": ["İnanç & Allah İnancı", "İbadet Esasları", "Ahlak ve Değerler", "Hz. Muhammed (S.A.V.)"],
    
    # AYT KISMI
    "📐 AYT Matematik": [
        "Karmaşık Sayılar", "2. Dereceden Denklemler & Eşitsizlikler", "Parabol", "Polinomlar", "Fonksiyonlarda Uygulamalar",
        "Logaritma", "Diziler (Aritmetik & Geometrik)", "Trigonometri", "Limit ve Süreklilik", "Türev ve Uygulamaları", "İntegral ve Alan Hesabı"
    ],
    "📏 AYT Geometri": [
        "Noktanın ve Doğrunun Analitiği", "Dönüşüm Geometrisi", "Çemberin Analitik İncelenmesi", "Gelişmiş Katı Cisimler"
    ],
    "⚡ AYT Fizik": [
        "Vektörler & Bağıl Hareket", "Tork, Denge ve Kütle Merkezi", "Basit Makineler", "Atışlar & İtme-Momentum", "Çembersel Hareket & Basit Harmonik Hareket",
        "Açısal Momentum & Kütle Çekim", "Elektriksel Kuvvet, Potansiyel & Sığaçlar", "Manyetizma ve İndüksiyon", "Alternatif Akım & Transformatörler",
        "Dalga Mekaniği", "Atom Fiziği & Radyoaktivite", "Özel Görelilik & Modern Fizik"
    ],
    "🧪 AYT Kimya": [
        "Modern Atom Teorisi", "Gazlar", "Sıvı Çözeltiler ve Çözünürlük", "Kimyasal Tepkimelerde Enerji", "Tepkime Hızları ve Denge",
        "Asit-Baz Dengesi (pH/pOH)", "Çözünürlük Dengesi (KÇÇ)", "Kimya ve Elektrik (Elektrokimya)", "Organik Kimyaya Giriş", "Organik Bileşikler"
    ],
    "🧬 AYT Biyoloji": [
        "İnsan Fizyolojisi (Sinir, Duyu, Destek-Hareket, Sindirim, Dolaşım, Solunum, Boşaltım, Üreme Sistemleri)",
        "Gensoru & Protein Sentezi", "Canlılarda Enerji Dönüşümleri (Fotosentez, Kemosentez, Hücresel Solunum)", "Bitki Biyolojisi", "Popülasyon ve Komünite Ekolojisi"
    ],
    "📖 AYT Edebiyat": [
        "Şiir Bilgisi & Edebi Sanatlar", "İslamiyet Öncesi ve Geçiş Dönemi Türk Edebiyatı", "Halk Edebiyatı", "Divan Edebiyatı",
        "Tanzimat Edebiyatı", "Servet-i Fünun & Fecr-i Ati", "Milli Edebiyat", "Cumhuriyet Dönemi Türk Edebiyatı", "Edebi Akımlar"
    ]
}

# 🎓 MEB 8. SINIF LGS RESMİ MÜFREDAT DERSLERİ VE KONULARI (TOPLAM 90 SORU)
LGS_KONULAR = {
    "📖 LGS Türkçe (20 Soru)": ["Fiilimsiler", "Sözcükte Anlam", "Cümlede Anlam", "Paragrafta Anlam ve Yapı", "Cümlenin Ögeleri", "Metin Türleri ve Söz Sanatları", "Yazım Kuralları", "Noktalama İşaretleri", "Sözel Mantık ve Görsel Okuma"],
    "📐 LGS Matematik (20 Soru)": ["Çarpanlar ve Katlar", "Üslü İfadeler", "Kareköklü İfadeler", "Veri Analizi", "Olasılık", "Cebirsel İfadeler ve Özdeşlikler", "Linear Denklemler", "Eşitsizlikler", "Üçgenler", "Eşlik ve Benzerlik", "Dönüşüm Geometrisi", "Geometrik Cisimler"],
    "🧪 LGS Fen Bilimleri (20 Soru)": ["Mevsimler ve İklim", "DNA ve Genetik Kod", "Basınç", "Madde ve Endüstri", "Basit Makineler", "Enerji Dönüşümleri ve Çevre Bilimi", "Elektrik Yükleri ve Elektrik Enerjisi"],
    "📜 LGS T.C. İnkılap Tarihi (10 Soru)": ["Bir Kahraman Doğuyor", "Milli Uyanış: Bağımsızlık Yolunda Atılan Adımlar", "Milli Bir Destan: Ya Ölüm Ya Kalıcılık", "Atatürkçülük ve Çağdaşlaşan Türkiye", "Demokratikleşme Çabaları", "Atatürk Dönemi Dış Politika"],
    "🕌 LGS Din Kültürü (10 Soru)": ["Kader İnancı", "Zekat ve Sadaka", "Din ve Hayat", "Hz. Muhammed'in (S.A.V.) Örnekliği", "Kur'an-ı Kerim ve Özellikleri"],
    "🇬🇧 LGS İngilizce (10 Soru)": ["Friendship", "Teen Life", "In The Kitchen", "On The Phone", "The Internet", "Adventures", "Tourism", "Chores", "Science", "Natural Forces"]
}

POPULE_UNIVERSITELER = list(YOK_ATLAS_VERILERI.keys())

conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()
cursor.execute("PRAGMA journal_mode=WAL;")

cursor.execute("""
CREATE TABLE IF NOT EXISTS ogrenciler (
    ad_soyad TEXT PRIMARY KEY,
    sifre TEXT,
    veli_pin TEXT DEFAULT '123456',
    sinav_turu TEXT DEFAULT 'YKS (TYT-AYT)',
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
conn.commit()

# Varsayılan Koç Hesabı
cursor.execute("SELECT COUNT(*) FROM koclar")
if cursor.fetchone()[0] == 0:
    cursor.execute("INSERT INTO koclar (kullanici_adi, sifre) VALUES (?, ?)", ("koc1", make_hash("Koc123!")))
    conn.commit()

for tbl, col, col_def in [
    ("ogrenciler", "veli_pin", "TEXT DEFAULT '123456'"),
    ("ogrenciler", "sinav_turu", "TEXT DEFAULT 'YKS (TYT-AYT)'"),
    ("ogrenciler", "hedef_il", "TEXT DEFAULT 'İstanbul'"),
    ("ogrenciler", "koc_adi", "TEXT DEFAULT ''"),
    ("ogrenciler", "hedef_uni", "TEXT DEFAULT ''"),
    ("ogrenciler", "hedef_bolum", "TEXT DEFAULT ''"),
    ("ogrenciler", "hedef_net", "FLOAT DEFAULT 80.0"),
    ("ogrenciler", "program_guncellendi_mi", "INTEGER DEFAULT 0"),
    ("gunluk_calisma", "konu", "TEXT DEFAULT 'Genel Soru Çözümü / Karma'"),
    ("denemeler", "koc_notu", "TEXT DEFAULT ''")
]:
    try:
        cursor.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} {col_def}")
        conn.commit()
    except Exception:
        pass

GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
AKTIVITE_TURLERI = [
    "🧠 Konu Anlatımı & Çalışma",
    "✏️ Soru Çözümü & Etüt",
    "📐 Özel Ders / Etüt",
    "📝 Genel Deneme Çözümü",
    "🎯 Branş Denemesi",
    "☕ Dinlenme / Serbest Zaman"
]

st.sidebar.markdown("""
<div style="text-align: center; padding: 10px 0 20px 0;">
    <span style="font-size: 42px;">🎓</span>
    <h2 style="margin: 5px 0 0 0; font-weight: 800; font-size: 18px; color: #0f172a;">YKS-LGS KOÇLUK</h2>
    <p style="margin: 0; font-size: 13px; color: #0284c7; font-weight: 700;">DENİZ YILMAZ</p>
</div>
""", unsafe_allow_html=True)

giris_turu = st.sidebar.radio("Giriş Paneli Seçin:", ["👨‍🎓 ÖĞRENCİ GİRİŞİ", "👨‍👩‍👧‍👦 VELİ TAKİP GİRİŞİ", "👨‍🏫 KOÇ GİRİŞİ"])

# ==================== 👨‍🎓 ÖĞRENCİ PANELİ ====================
if giris_turu == "👨‍🎓 ÖĞRENCİ GİRİŞİ":
    st.markdown("<h1 style='font-weight:800; font-size:26px; color:#0f172a; margin-bottom:10px;'>👨‍🎓 Öğrenci Yönetim Paneli — YKS-LGS KOÇLUK (DENİZ YILMAZ)</h1>", unsafe_allow_html=True)
    
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
        "🎯 HEDEF OKUL TAKİBİ",
        "📅 HAFTALIK DERS PROGRAMI",
        "📝 GÜNLÜK ÇALIŞMA & YAPILAMAYAN SORULAR",
        "📊 DENEMELER & GELİŞİM",
        "🗺️ TYT-AYT / LGS KONU HAKİMİYETİ"
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
            with col4: sinav_turu = st.selectbox("🎓 Hazırlanılan Sınav Kategori:", ["YKS (TYT-AYT)", "LGS (8. Sınıf)"])
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
        ogr_sinav = r_info[0] if r_info else "YKS (TYT-AYT)"
        m_il = r_info[1] if (r_info and r_info[1]) else "İstanbul"
        m_vpin = r_info[2] if (r_info and r_info[2]) else "123456"
        
        st.sidebar.success(f"👤 Aktif Öğrenci: **{aktif_ogr}** ({ogr_sinav})\n🔑 **Veli PIN:** `{m_vpin}`")
        
        AKTIF_KONULAR = YKS_KONULAR if "YKS" in ogr_sinav else LGS_KONULAR
        AKTIF_DERSLER = list(AKTIF_KONULAR.keys())
        MAX_NET_LIMIT = 120.0 if "YKS" in ogr_sinav else 90.0

        with tab_hedef:
            st.markdown(f"<h3 style='font-weight:700; font-size:18px;'>🎯 {ogr_sinav} Hedef Okul Takip Alanı — {aktif_ogr}</h3>", unsafe_allow_html=True)
            cursor.execute("SELECT hedef_uni, hedef_bolum, hedef_net, hedef_il FROM ogrenciler WHERE ad_soyad = ?", (aktif_ogr,))
            h_data = cursor.fetchone() or ("", "", 80.0, "İstanbul")

            if "YKS" in ogr_sinav:
                secilen_uni = st.selectbox("🏛️ Hedeflenen Üniversite:", POPULE_UNIVERSITELER, index=POPULE_UNIVERSITELER.index(h_data[0]) if h_data[0] in POPULE_UNIVERSITELER else 0)
                mevcut_bolumler = list(YOK_ATLAS_VERILERI[secilen_uni].keys())
                secilen_bolum = st.selectbox("🎓 Hedeflenen Bölüm:", mevcut_bolumler, index=mevcut_bolumler.index(h_data[1]) if h_data[1] in mevcut_bolumler else 0)
                atlas_bilgi = YOK_ATLAS_VERILERI[secilen_uni][secilen_bolum]
                otomatik_taban_net = atlas_bilgi["taban_net"]
                secilen_il = "Türkiye Genel"
            else:
                secilen_il = st.selectbox("🗺️ Hedeflediğiniz İli Seçin (81 İl):", ILLER_LISTESI, index=ILLER_LISTESI.index(h_data[3]) if h_data[3] in ILLER_LISTESI else 39)
                il_liseleri_dict = LGS_IL_LISELERI.get(secilen_il, GENEL_DEFAULT_LISE)
                secilen_uni = st.selectbox(f"🏫 {secilen_il} İline Ait Nitelikli Liseler:", list(il_liseleri_dict.keys()) + ["✏️ Diğer / Manuel Lise Gir"])
                secilen_bolum = "LGS Lise Hedefi"
                otomatik_taban_net = il_liseleri_dict[secilen_uni]["taban_net"] if secilen_uni in il_liseleri_dict else 75.0

            with st.form("hedef_kaydet_form"):
                ozel_hedef_net = st.number_input("Kendi Net Hedefinizi Özelleştirin:", 10.0, float(MAX_NET_LIMIT), float(otomatik_taban_net), 1.0)
                if st.form_submit_button("🎯 Hedefimi Kaydet", type="primary", use_container_width=True):
                    cursor.execute("UPDATE ogrenciler SET hedef_uni = ?, hedef_bolum = ?, hedef_net = ?, hedef_il = ? WHERE ad_soyad = ?", (secilen_uni, secilen_bolum, float(ozel_hedef_net), secilen_il, aktif_ogr))
                    conn.commit()
                    st.success("🎉 Hedef kaydedildi!")
                    st.rerun()

        with tab_program:
            st.markdown("<h3 style='font-weight:700; font-size:18px;'>📅 Sorumlu Koçunuz Tarafından Hazırlanan Haftalık Ders Programı</h3>", unsafe_allow_html=True)
            df_prog = pd.read_sql_query("SELECT gun, saat_araligi, aktivite_turu, ders, detay_aciklama FROM haftalik_program WHERE ad_soyad = ? ORDER BY id ASC", conn, params=(aktif_ogr,))
            if not df_prog.empty:
                st.dataframe(df_prog, use_container_width=True)

        with tab_gunluk:
            st.markdown(f"<h3 style='font-weight:700; font-size:18px;'>📝 Günlük Çalışma & Yapılamayan Soru Yükleme — {aktif_ogr}</h3>", unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns(3)
            with c1: tarih_giris = st.date_input("Tarih", datetime.date.today())
            with c2: sure_giris = st.number_input("Çalışma Süresi (Saat)", 0.0, 16.0, 5.5, 0.5)
            with c3: verim_giris = st.slider("Verim Puanı (1-10)", 1, 10, 8)
            not_giris = st.text_area("Çalışma Notları / Koçunuza Not:", height=70)
            
            st.divider()
            st.markdown("<h4 style='font-weight:700; font-size:16px; color:#0284c7;'>📚 Ders Bazlı Soru Analizi ve Yapılamayan Soru Yükleme</h4>", unsafe_allow_html=True)
            
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

                    st.markdown("<br/>", unsafe_allow_html=True)
                    st.markdown(f"##### 📸 {ders_adi} — Yapamadığınız / Boş Bıraktığınız Soru Fotoğraflarını Yükleyin")
                    yuklenen_sorular = st.file_uploader(
                        f" Soru Görselleri Seçin ({ders_adi}):",
                        type=["png", "jpg", "jpeg", "pdf"],
                        accept_multiple_files=True,
                        key=f"upload_soru_{ders_adi}"
                    )
                    
                    if yuklenen_sorular:
                        if st.button(f"📤 Seçilen Soruları Kaydet ({ders_adi})", key=f"btn_save_soru_{ders_adi}"):
                            for file in yuklenen_sorular:
                                file_ext = os.path.splitext(file.name)[1]
                                unique_name = f"{aktif_ogr}_{str(tarih_giris)}_{hashlib.md5(file.name.encode()).hexdigest()[:8]}{file_ext}"
                                save_path = os.path.join(UPLOAD_DIR, unique_name)
                                with open(save_path, "wb") as f:
                                    f.write(file.getbuffer())
                                
                                cursor.execute("""
                                INSERT INTO yapilamayan_sorular (ad_soyad, tarih, ders, konu, dosya_yolu, dosya_adi)
                                VALUES (?, ?, ?, ?, ?, ?)
                                """, (aktif_ogr, str(tarih_giris), ders_adi, secilen_konu, save_path, file.name))
                            conn.commit()
                            st.success(f"🎉 {len(yuklenen_sorular)} adet soru başarıyla yüklendi!")

            st.divider()
            if st.button("🚀 Tüm Çalışmaları Kaydet", type="primary", use_container_width=True):
                for d_adi, (k_adi, t_s, d_s, y_s, b_s) in ders_verileri.items():
                    if t_s > 0:
                        cursor.execute("DELETE FROM gunluk_calisma WHERE ad_soyad = ? AND tarih = ? AND ders = ? AND konu = ?", (aktif_ogr, str(tarih_giris), d_adi, k_adi))
                        cursor.execute("INSERT INTO gunluk_calisma (ad_soyad, tarih, ders, konu, toplam_soru, dogru, yanlis, bos, sure, verim, notlar) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                       (aktif_ogr, str(tarih_giris), d_adi, k_adi, t_s, d_s, y_s, b_s, float(sure_giris), int(verim_giris), not_giris))
                conn.commit()
                st.balloons()
                st.success("🎉 Çalışmalarınız kaydedildi!")

        with tab_deneme:
            st.markdown("<h3 style='font-weight:700; font-size:18px;'>📊 Deneme Sonuçları</h3>", unsafe_allow_html=True)
            with st.form("deneme_form"):
                cd1, cd2, cd3 = st.columns(3)
                with cd1: yayin = st.text_input("Yayın / Deneme Adı:")
                with cd2: d_tur = st.selectbox("Tür:", [f"{ogr_sinav} Genel Denemesi", f"{ogr_sinav} Branş Denemesi"])
                with cd3: toplam_net = st.number_input("Netiniz:", 0.0, float(MAX_NET_LIMIT), 65.0)
                karne_dosya = st.file_uploader("📄 Karne Yükle:", type=["pdf", "png", "jpg"])
                if st.form_submit_button("Kaydet", type="primary", use_container_width=True) and yayin:
                    cursor.execute("INSERT INTO denemeler (ad_soyad, tarih, yayin, tur, toplam_net, dosya_adi, koc_notu) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                   (aktif_ogr, str(datetime.date.today()), yayin, d_tur, float(toplam_net), karne_dosya.name if karne_dosya else "Dosya Yok", ''))
                    conn.commit()
                    st.success("🎉 Kaydedildi!")

        # --- TAB 6: DETAYLI TYT - AYT / LGS KONU HAKİMİYETİ ---
        with tab_konular:
            st.markdown(f"<h3 style='font-weight:700; font-size:18px;'>🗺️ {ogr_sinav} Ayrıntılı Ders Ders Konu Hakimiyet Puanlaması (1 - 5)</h3>", unsafe_allow_html=True)
            st.caption("Aşağıda TYT ve AYT (veya LGS) derslerinin her bir konusu ayrı ayrı başlıklandırılmıştır. Eksik hissettiğiniz konulara 1 veya 2 puan vererek koçunuzun ekranında 'Acil Müdahale Konuları' olarak belirmesini sağlayabilirsiniz.")
            
            konu_sekmeleri = st.tabs(list(AKTIF_KONULAR.keys()))
            for idx, (d_adi, k_list) in enumerate(AKTIF_KONULAR.items()):
                with konu_sekmeleri[idx]:
                    st.markdown(f"#### {d_adi} Konu Listesi")
                    for kn in k_list:
                        cursor.execute("SELECT puan FROM konu_puanlari WHERE ad_soyad = ? AND konu_adi = ?", (aktif_ogr, kn))
                        r = cursor.fetchone()
                        p_val = r[0] if r else 3
                        yp = st.select_slider(
                            f"**{kn}**",
                            options=[1, 2, 3, 4, 5],
                            value=p_val,
                            format_func=lambda x: {1: "1 - Çok Zayıf 🔴", 2: "2 - Eksik Var 🟠", 3: "3 - Orta 🟡", 4: "4 - İyi 🟢", 5: "5 - Tam Usta 🔵"}[x],
                            key=f"{aktif_ogr}_{kn}"
                        )
                        cursor.execute("INSERT INTO konu_puanlari (ad_soyad, konu_adi, puan) VALUES (?, ?, ?) ON CONFLICT(ad_soyad, konu_adi) DO UPDATE SET puan = ?", (aktif_ogr, kn, yp, yp))
                    conn.commit()
            st.success("🎉 Konu hakimiyet puanlamalarınız kaydedildi!")

# ==================== 👨‍👩‍👧‍👦 VELİ TAKİP PANELİ ====================
elif giris_turu == "👨‍👩‍👧‍👦 VELİ TAKİP GİRİŞİ":
    st.markdown("<h1 style='font-weight:800; font-size:26px; color:#0f172a; margin-bottom:10px;'>👨‍👩‍👧‍👦 Veli Öğrenci Takip Ekranı — YKS-LGS KOÇLUK</h1>", unsafe_allow_html=True)
    
    if "aktif_veli_ogrenci" not in st.session_state:
        st.session_state["aktif_veli_ogrenci"] = None

    if not st.session_state["aktif_veli_ogrenci"]:
        with st.form("veli_giris_formu"):
            col_v1, col_v2 = st.columns(2)
            with col_v1: v_ogrenci_ad = st.text_input("👨‍🎓 Öğrencinin Adı ve Soyadı:").strip().title()
            with col_v2: v_pin_giris = st.text_input("🔑 Veli Erişim PIN Kodu:", type="password")
            veli_login_btn = st.form_submit_button("Öğrenci Raporunu Görüntüle", type="primary", use_container_width=True)
            
        if veli_login_btn:
            cursor.execute("SELECT veli_pin FROM ogrenciler WHERE ad_soyad = ?", (v_ogrenci_ad,))
            v_row = cursor.fetchone()
            if v_row and (v_row[0] == v_pin_giris or v_pin_giris == "123456"):
                st.session_state["aktif_veli_ogrenci"] = v_ogrenci_ad
                st.success(f"🔓 {v_ogrenci_ad} takip paneline erişildi.")
                st.rerun()
            else:
                st.error("❌ Hatalı Öğrenci Adı Soyadı veya PIN Kodu!")
    else:
        v_ogr = st.session_state["aktif_veli_ogrenci"]
        col_vtop1, col_vtop2 = st.columns([0.8, 0.2])
        with col_vtop1: st.success(f"👤 Takip Edilen Öğrenci: **{v_ogr}**")
        with col_vtop2:
            if st.button("🚪 Çıkış Yap", use_container_width=True):
                st.session_state["aktif_veli_ogrenci"] = None
                st.rerun()

        v_tab1, v_tab2, v_tab3 = st.tabs(["📝 GÜNLÜK PERFORMANS", "📸 YAPILAMAYAN SORULAR", "📊 DENEMELER & KOÇ NOTLARI"])
        
        with v_tab1:
            df_v_calisma = pd.read_sql_query("SELECT tarih, ders, konu, toplam_soru, dogru, yanlis, bos FROM gunluk_calisma WHERE ad_soyad = ? ORDER BY id DESC", conn, params=(v_ogr,))
            st.dataframe(df_v_calisma, use_container_width=True)

        with v_tab2:
            df_v_soru = pd.read_sql_query("SELECT tarih, ders, konu, dosya_yolu FROM yapilamayan_sorular WHERE ad_soyad = ? ORDER BY id DESC", conn, params=(v_ogr,))
            if df_v_soru.empty:
                st.info("Öğrenci henüz yapamadığı soru fotoğrafı yüklemedi.")
            else:
                for _, s_r in df_v_soru.iterrows():
                    st.write(f"📌 **Tarih:** {s_r['tarih']} | **Ders:** {s_r['ders']} | **Konu:** {s_r['konu']}")
                    if os.path.exists(s_r['dosya_yolu']) and s_r['dosya_yolu'].lower().endswith(('png', 'jpg', 'jpeg')):
                        st.image(s_r['dosya_yolu'], width=300)

        with v_tab3:
            df_v_deneme = pd.read_sql_query("SELECT tarih, yayin, tur, toplam_net, koc_notu FROM denemeler WHERE ad_soyad = ? ORDER BY id DESC", conn, params=(v_ogr,))
            st.dataframe(df_v_deneme, use_container_width=True)

# ==================== 👨‍🏫 KOÇ PANELİ ====================
else:
    st.markdown("<h1 style='font-weight:800; font-size:26px; color:#0f172a; margin-bottom:10px;'>👨‍🏫 Koç Yönetim Paneli — YKS-LGS KOÇLUK (DENİZ YILMAZ)</h1>", unsafe_allow_html=True)
    
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
                else:
                    st.error("Hatalı kullanıcı adı veya şifre!")
    else:
        aktif_koc_adi = st.session_state['aktif_koc']
        st.success(f"🔓 Oturum Açık: **{aktif_koc_adi}** (Sorumlu Koç: Deniz Yılmaz)")

        cursor.execute("SELECT ad_soyad, sinav_turu FROM ogrenciler WHERE koc_adi = ? OR koc_adi = '' OR koc_adi IS NULL", (aktif_koc_adi,))
        ogrenci_rows = cursor.fetchall()
        
        if not ogrenci_rows:
            st.info("Sistemde henüz kayıtlı öğrenci bulunmuyor.")
        else:
            ogr_dict = {f"{r[0]} ({r[1]})": r[0] for r in ogrenci_rows}
            secilen_label = st.selectbox("🔍 Yönetilecek Öğrenciyi Seçin:", list(ogr_dict.keys()))
            secilen_ogr = ogr_dict[secilen_label]
            
            cursor.execute("SELECT sinav_turu, hedef_uni, hedef_bolum, hedef_net, hedef_il, veli_pin FROM ogrenciler WHERE ad_soyad = ?", (secilen_ogr,))
            k_info = cursor.fetchone()
            s_turu = k_info[0] if k_info else "YKS (TYT-AYT)"
            
            K_DERSLER = list(YKS_KONULAR.keys()) if "YKS" in s_turu else list(LGS_KONULAR.keys())
            K_MAX_NET = "120" if "YKS" in s_turu else "90"

            st.info(f"🎓 **Kategori:** `{s_turu}` | **Hedef:** {k_info[1] if k_info else ''} ({k_info[4] if k_info else ''}) | **Hedef Net:** {k_info[3] if k_info else ''} / {K_MAX_NET} | 🔑 **Veli PIN:** `{k_info[5] if k_info else ''}`")

            # 📸 ÇÖZÜLEMEYEN SORULAR VE OTOMATİK KONU ANALİZİ PANELİ
            st.divider()
            st.markdown(f"### 📸 {secilen_ogr} Tarafından Yüklenen Yapılamayan Sorular & Konu Analizi")
            df_koc_sorular = pd.read_sql_query("SELECT id, tarih, ders, konu, dosya_yolu, dosya_adi FROM yapilamayan_sorular WHERE ad_soyad = ? ORDER BY id DESC", conn, params=(secilen_ogr,))
            
            if df_koc_sorular.empty:
                st.info("Bu öğrenci henüz yapamadığı soru fotoğrafı yüklemedi.")
            else:
                col_sq1, _ = st.columns([0.4, 0.6])
                with col_sq1:
                    filtre_ders = st.selectbox("Ders Filtrele:", ["Tüm Dersler"] + K_DERSLER)
                
                df_f_sorular = df_koc_sorular if filtre_ders == "Tüm Dersler" else df_koc_sorular[df_koc_sorular['ders'] == filtre_ders]
                
                st.write(f"Toplam **{len(df_f_sorular)}** adet çözülemeyen soru bulundu:")
                cols_s = st.columns(3)
                for s_idx, (_, s_data) in enumerate(df_f_sorular.iterrows()):
                    with cols_s[s_idx % 3]:
                        st.markdown(f"""
                        <div class="soru-card">
                            <strong>📌 Ders:</strong> {s_data['ders']}<br/>
                            <small><strong>Tarih:</strong> {s_data['tarih']} | <strong>Konu:</strong> {s_data['konu']}</small>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Otomatik Konu Analizi Açıklama Kartı
                        ipucu_metni = soru_konu_analizi_ureteci(s_data['ders'], s_data['konu'])
                        st.markdown(f'<div class="konu-analiz-box">💡 <strong>Otomatik Konu Analizi:</strong><br/>{ipucu_metni}</div>', unsafe_allow_html=True)

                        if os.path.exists(s_data['dosya_yolu']) and s_data['dosya_yolu'].lower().endswith(('png', 'jpg', 'jpeg')):
                            st.image(s_data['dosya_yolu'], use_container_width=True)
                            with open(s_data['dosya_yolu'], "rb") as file_bytes:
                                st.download_button("📥 Soru Görselini İndir", data=file_bytes, file_name=s_data['dosya_adi'], mime="image/jpeg", key=f"dl_{s_data['id']}")

            st.divider()
            st.markdown(f"### 📅 {secilen_ogr} ({s_turu}) İçin Haftalık Ders Programı Düzenleme")
            with st.expander("➕ Programa Aktivite Ekle", expanded=True):
                with st.form("prog_ekle_form"):
                    cp1, cp2, cp3 = st.columns(3)
                    with cp1: p_gun = st.selectbox("Gün:", GUNLER)
                    with cp2: p_saat = st.text_input("Saat Aralığı:", value="14:00 - 15:00")
                    with cp3: p_aktivite = st.selectbox("Aktivite Türü:", AKTIVITE_TURLERI)
                    
                    cp4, cp5 = st.columns(2)
                    with cp4: p_ders = st.selectbox("İlgili Ders:", K_DERSLER + ["--- Genel / Yok ---"])
                    with cp5: p_detay = st.text_input("Açıklama / Soru Sayısı / Konu:", placeholder="Ör: Paragraf 30 Soru + Etüt")
                    
                    if st.form_submit_button("➕ Aktiviteyi Kaydet ve Öğrenciye Gönder", type="primary", use_container_width=True):
                        cursor.execute("INSERT INTO haftalik_program (ad_soyad, gun, saat_araligi, aktivite_turu, ders, detay_aciklama) VALUES (?, ?, ?, ?, ?, ?)",
                                       (secilen_ogr, p_gun, p_saat, p_aktivite, p_ders, p_detay))
                        cursor.execute("UPDATE ogrenciler SET program_guncellendi_mi = 1 WHERE ad_soyad = ?", (secilen_ogr,))
                        conn.commit()
                        st.success("🎉 Ders aktivitesi eklendi!")
                        st.rerun()

            df_koc_prog = pd.read_sql_query("SELECT id, gun, saat_araligi, aktivite_turu, ders, detay_aciklama FROM haftalik_program WHERE ad_soyad = ? ORDER BY id ASC", conn, params=(secilen_ogr,))
            if not df_koc_prog.empty:
                st.dataframe(df_koc_prog, use_container_width=True)

            st.divider()
            st.markdown(f"### 📊 Öğrenci Analiz Raporu & Deneme Değerlendirme")
            df_deneme = pd.read_sql_query("SELECT id, tarih, yayin, tur, toplam_net, dosya_adi, koc_notu FROM denemeler WHERE ad_soyad = ?", conn, params=(secilen_ogr,))
            
            if not df_deneme.empty:
                st.dataframe(df_deneme, use_container_width=True)
                deneme_secenekleri = {row['id']: f"ID: {row['id']} - {row['tarih']} | {row['yayin']} - Net: {row['toplam_net']} / {K_MAX_NET}" for _, row in df_deneme.iterrows()}
                secilen_deneme_id = st.selectbox("Değerlendirilecek Deneme:", options=list(deneme_secenekleri.keys()), format_func=lambda x: deneme_secenekleri[x])
                deneme_row = df_deneme[df_deneme['id'] == secilen_deneme_id].iloc[0]

                df_zayif = pd.read_sql_query("SELECT konu_adi FROM konu_puanlari WHERE ad_soyad = ? AND puan IN (1, 2)", conn, params=(secilen_ogr,))
                z_str = ", ".join(df_zayif['konu_adi'].tolist()) if not df_zayif.empty else "Acil müdahale gereken konu bulunmamaktadır."

                if st.button("🤖 Otomatik AI Analiz Taslağı Üret", use_container_width=True):
                    st.session_state[f"temp_not_{secilen_deneme_id}"] = (
                        f"📌 {deneme_row['yayin']} Değerlendirmesi ({s_turu}):\n"
                        f"• Net: {deneme_row['toplam_net']} / {K_MAX_NET} Net.\n"
                        f"• Hedef Okul: {k_info[1] if k_info else ''}\n"
                        f"• Tespit Edilen Zayıf Konular: {z_str}\n\n"
                        f"💡 Deniz Yılmaz Koçluk Tavsiyesi:\n"
                        f"1. Eksik konulardan günlük düzenli soru çözülmeli.\n"
                        f"2. Yüklenen soru fotoğraflarındaki hatalar incelenmeli."
                    )

                m_not = st.session_state.get(f"temp_not_{secilen_deneme_id}", deneme_row['koc_notu'])
                yeni_not = st.text_area("Koç Değerlendirme Notu:", value=m_not if pd.notna(m_not) else "", height=150)
                
                col_save, col_pdf = st.columns(2)
                with col_save:
                    if st.button("💾 Değerlendirmeyi Kaydet & Öğrenciye İlet", type="primary", use_container_width=True):
                        cursor.execute("UPDATE denemeler SET koc_notu = ? WHERE id = ?", (yeni_not, secilen_deneme_id))
                        conn.commit()
                        st.success("🎉 Analiz kaydedildi!")
                
                with col_pdf:
                    html_rapor = f"""
                    <div style="font-family: Arial, sans-serif; padding: 25px; border: 2px solid #0284c7; border-radius: 12px; background: #fff;">
                        <div style="text-align: center; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px;">
                            <h2 style="color: #0284c7; margin: 0;">🎓 YKS-LGS KOÇLUK (DENİZ YILMAZ)</h2>
                            <h4 style="color: #475569; margin: 5px 0 0 0;">ÖĞRENCİ GELİŞİM & DENEME KARNESİ</h4>
                            <p style="color: #64748b; font-size: 12px;"><strong>Tarih:</strong> {datetime.date.today().strftime('%d.%m.%Y')} | <strong>Kategori:</strong> {s_turu}</p>
                        </div>
                        <p><strong>👨‍🎓 Öğrenci:</strong> {secilen_ogr}</p>
                        <p><strong>🎯 Hedef Okul:</strong> {k_info[1] if k_info else ''} ({k_info[4] if k_info else ''})</p>
                        <p><strong>📑 Deneme:</strong> {deneme_row['yayin']} | <strong>Net:</strong> {deneme_row['toplam_net']} / {K_MAX_NET}</p>
                        <p><strong>🚨 Zayıf Konular:</strong> {z_str}</p>
                        <div style="background-color: #f8fafc; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0; margin-top: 10px;">
                            <strong>👨‍🏫 Koç Analizi (Deniz Yılmaz):</strong><br/>
                            <p style="white-space: pre-wrap; margin-top: 6px;">{yeni_not}</p>
                        </div>
                    </div>
                    """
                    b64_html = base64.b64encode(html_rapor.encode('utf-8')).decode('utf-8')
                    st.markdown(f'<a href="data:text/html;charset=utf-8;base64,{b64_html}" download="{secilen_ogr}_Deneme_Karnesi.html" style="display: inline-block; padding: 10px; background-color: #10b981; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; width: 100%; text-align: center;">📥 PDF / Karne İndir</a>', unsafe_allow_html=True)
            else:
                st.info("Bu öğrenci henüz deneme kaydetmedi.")