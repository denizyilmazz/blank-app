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
    except Exception as e:
        pass

veritabani_gunluk_yedekle()

MOTIVASYON_SOZLERI = [
    "🌿 Sakin ol, derin bir nefes al ve adım adım ilerle. Disiplin başarıyı getirir!",
    "🚀 Başarı, her gün ertelemeden tekrarlanan küçük çabaların birikimidir!",
    "🎓 Bugün döktüğün her damla alın teri, hayalindeki okulun kapısını açar!",
    "💪 Zorluklar, potansiyelini keşfetmen için var olan basamaklardır. Pes etmek yok!",
    "✨ Şimdi odaklan ve çalış, gelecekteki kendin seninle gurur duysun!",
    "🎯 Zirveye giden yolda engel yoktur, sadece kararlılıkla aşılacak hedefler vardır!"
]

# 81 İL LİSTESİ
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

# 🏛️ YÖK ATLAS (YKS) VERİTABANI
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
    "Hacettepe Üniversitesi": {
        "Tıp Fakültesi (Türkçe)": {"taban_sira": "1.350", "tavan_sira": "45", "taban_net": 110.5, "tavan_net": 118.5},
        "Bilgisayar Mühendisliği": {"taban_sira": "3.400", "tavan_sira": "420", "taban_net": 106.0, "tavan_net": 115.0}
    }
}

# 🏫 İLLERE GÖRE LGS NİTELİKLİ LİSELER VERİTABANI
LGS_IL_LISELERI = {
    "İstanbul": {
        "Galatasaray Lisesi": {"taban_puan": "500.0", "yuzdelik": "%0.04", "taban_net": 88.5},
        "İstanbul Lisesi (Erkek Lisesi)": {"taban_puan": "498.5", "yuzdelik": "%0.06", "taban_net": 87.5},
        "Kabataş Erkek Lisesi": {"taban_puan": "496.0", "yuzdelik": "%0.11", "taban_net": 86.5},
        "Atatürk Fen Lisesi": {"taban_puan": "492.5", "yuzdelik": "%0.22", "taban_net": 84.5},
        "Cağaloğlu Anadolu Lisesi": {"taban_puan": "489.0", "yuzdelik": "%0.38", "taban_net": 83.0},
        "Kadıköy Anadolu Lisesi": {"taban_puan": "487.5", "yuzdelik": "%0.47", "taban_net": 82.5},
        "Hüseyin Avni Sözen Anadolu Lisesi": {"taban_puan": "485.0", "yuzdelik": "%0.58", "taban_net": 81.0},
        "Beşiktaş Sakıp Sabancı Anadolu Lisesi": {"taban_puan": "482.0", "yuzdelik": "%0.75", "taban_net": 79.5}
    },
    "Ankara": {
        "Ankara Fen Lisesi": {"taban_puan": "495.0", "yuzdelik": "%0.13", "taban_net": 86.0},
        "Prof. Dr. Aziz Sancar Fen Lisesi": {"taban_puan": "488.5", "yuzdelik": "%0.40", "taban_net": 82.5},
        "Atatürk Anadolu Lisesi": {"taban_puan": "483.0", "yuzdelik": "%0.70", "taban_net": 80.0},
        "Gazi Anadolu Lisesi": {"taban_puan": "478.0", "yuzdelik": "%1.10", "taban_net": 78.0},
        "Ankara Cumhuriyet Fen Lisesi": {"taban_puan": "475.0", "yuzdelik": "%1.35", "taban_net": 76.5}
    },
    "İzmir": {
        "İzmir Fen Lisesi": {"taban_puan": "494.0", "yuzdelik": "%0.16", "taban_net": 85.5},
        "İzmir Atatürk Lisesi": {"taban_puan": "484.0", "yuzdelik": "%0.65", "taban_net": 80.5},
        "Bornova Anadolu Lisesi": {"taban_puan": "479.5", "yuzdelik": "%1.00", "taban_net": 78.5},
        "Buca İnci-Özer Tırnaklı Fen Lisesi": {"taban_puan": "482.0", "yuzdelik": "%0.78", "taban_net": 79.5}
    },
    "Bursa": {
        "Tofaş Fen Lisesi": {"taban_puan": "491.0", "yuzdelik": "%0.30", "taban_net": 84.0},
        "Bursa Anadolu Lisesi": {"taban_puan": "476.0", "yuzdelik": "%1.25", "taban_net": 77.0},
        "Nilüfer IMKB Fen Lisesi": {"taban_puan": "483.0", "yuzdelik": "%0.72", "taban_net": 80.0}
    },
    "Antalya": {
        "Antalya Yusuf Ziya Öner Fen Lisesi": {"taban_puan": "490.0", "yuzdelik": "%0.35", "taban_net": 83.5},
        "Adem-Tolunay Anadolu Lisesi": {"taban_puan": "472.0", "yuzdelik": "%1.60", "taban_net": 75.0}
    },
    "Adana": {
        "Adana Fen Lisesi": {"taban_puan": "489.5", "yuzdelik": "%0.36", "taban_net": 83.0},
        "Adana Anadolu Lisesi": {"taban_puan": "468.0", "yuzdelik": "%2.00", "taban_net": 73.5}
    },
    "Kocaeli": {
        "Kocaeli Fen Lisesi": {"taban_puan": "488.0", "yuzdelik": "%0.45", "taban_net": 82.5},
        "Muammer Dereli Fen Lisesi": {"taban_puan": "477.0", "yuzdelik": "%1.15", "taban_net": 77.5}
    },
    "Konya": {
        "Meram Fen Lisesi": {"taban_puan": "489.0", "yuzdelik": "%0.38", "taban_net": 83.0},
        "Konya Karatay Fen Lisesi": {"taban_puan": "481.0", "yuzdelik": "%0.85", "taban_net": 79.0}
    },
    "Gaziantep": {
        "Vehbi Dinçerler Fen Lisesi": {"taban_puan": "486.0", "yuzdelik": "%0.52", "taban_net": 81.5},
        "Gaziantep Fen Lisesi": {"taban_puan": "482.0", "yuzdelik": "%0.78", "taban_net": 79.5}
    },
    "Kayseri": {
        "Kayseri Fen Lisesi": {"taban_puan": "488.0", "yuzdelik": "%0.45", "taban_net": 82.5},
        "Sümer Fen Lisesi": {"taban_puan": "480.0", "yuzdelik": "%0.92", "taban_net": 78.5}
    }
}

GENEL_DEFAULT_LISE = {
    "İl Nitelikli Fen Lisesi (Genel Taban)": {"taban_puan": "450.0", "yuzdelik": "%2.50", "taban_net": 72.0},
    "İl Nitelikli Anadolu Lisesi (Genel Taban)": {"taban_puan": "410.0", "yuzdelik": "%6.00", "taban_net": 62.0},
    "İl Nitelikli Proje İmam Hatip / Meslek Lisesi": {"taban_puan": "370.0", "yuzdelik": "%12.00", "taban_net": 52.0}
}

# 📖 DERS & KONU SÖZLÜKLERİ
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

LGS_KONULAR = {
    "📖 LGS Türkçe": ["Fiilimsiler", "Sözcükte Anlam", "Cümlede Anlam", "Paragrafta Anlam ve Yapı", "Cümlenin Ögeleri", "Metin Türleri ve Söz Sanatları", "Yazım Kuralları", "Noktalama İşaretleri", "Sözel Mantık ve Görsel Okuma"],
    "📐 LGS Matematik": ["Çarpanlar ve Katlar", "Üslü İfadeler", "Kareköklü İfadeler", "Veri Analizi", "Basit Olayların Olma Olasılığı", "Cebirsel İfadeler ve Özdeşlikler", "Birinci Dereceden Bir Bilinmeyenli Denklemler", "Eşitsizlikler", "Üçgenler", "Eşlik ve Benzerlik", "Dönüşüm Geometrisi", "Geometrik Cisimler"],
    "🧪 LGS Fen Bilimleri": ["Mevsimler ve İklim", "DNA ve Genetik Kod", "Basınç", "Madde ve Endüstri", "Basit Makineler", "Enerji Dönüşümleri ve Çevre Bilimi", "Elektrik Yükleri ve Elektrik Enerjisi"],
    "📜 LGS İnkılap Tarihi": ["Bir Kahraman Doğuyor", "Milli Uyanış: Bağımsızlık Yolunda Atılan Adımlar", "Milli Bir Destan: Ya Ölüm Ya Kalıcılık", "Atatürkçülük ve Çağdaşlaşan Türkiye", "Demokratikleşme Çabaları", "Atatürk Dönemi Dış Politika", "Atatürk'ün Ölümü ve Sonrası"],
    "🕌 LGS Din Kültürü": ["Kader İnancı", "Zekat ve Sadaka", "Din ve Hayat", "Hz. Muhammed'in (S.A.V.) Örnekliği", "Kur'an-ı Kerim ve Özellikleri"],
    "🇬🇧 LGS İngilizce": ["Friendship", "Teen Life", "In The Kitchen", "On The Phone", "The Internet", "Adventures", "Tourism", "Chores", "Science", "Natural Forces"]
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
        if deger <= 0: continue
        yuzde = (deger / toplam) * 100
        sonraki_yuzde = mevcut_yuzde + yuzde
        gradient_parcalari.append(f"{renk} {mevcut_yuzde:.1f}% {sonraki_yuzde:.1f}%")
        mevcut_yuzde = sonraki_yuzde
        
        item_str = f'<div style="display:flex; align-items:center; margin-bottom:8px; font-size:13.5px;"><span style="width:12px; height:12px; background-color:{renk}; border-radius:50%; display:inline-block; margin-right:10px;"></span><span style="color:#475569; font-weight:600;">{etiket}:</span>&nbsp;<span style="color:#0f172a; font-weight:700;">{deger} Adet</span>&nbsp;<span style="color:#94a3b8; font-size:11.5px;">(%{yuzde:.1f})</span></div>'
        legend_html.append(item_str)
        
    gradient_str = ", ".join(gradient_parcalari)
    legend_str = "".join(legend_html)
    
    return f'''<div style="background-color:#ffffff; padding:22px; border-radius:16px; border:1px solid #e2e8f0; box-shadow:0 4px 15px -3px rgba(0,0,0,0.04); margin-bottom:18px;">
<h4 style="margin-top:0; margin-bottom:18px; color:#0f172a; text-align:center; font-size:15px; font-weight:700;">{baslik}</h4>
<div style="display:flex; flex-wrap:wrap; align-items:center; justify-content:center; gap:24px;">
<div style="width:140px; height:140px; border-radius:50%; background:conic-gradient({gradient_str}); position:relative; display:flex; align-items:center; justify-content:center;">
<div style="width:84px; height:84px; background:#ffffff; border-radius:50%; display:flex; flex-direction:column; align-items:center; justify-content:center;">
<span style="font-size:18px; font-weight:800; color:#0f172a;">{toplam}</span>
<span style="font-size:9px; color:#64748b; font-weight:700;">TOPLAM</span>
</div>
</div>
<div>{legend_str}</div>
</div>
</div>'''

conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()
cursor.execute("PRAGMA journal_mode=WAL;")

cursor.execute("""
CREATE TABLE IF NOT EXISTS ogrenciler (
    ad_soyad TEXT PRIMARY KEY,
    sifre TEXT,
    sinav_turu TEXT DEFAULT 'YKS (TYT)',
    hedef_il TEXT DEFAULT 'İstanbul',
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

# Şema Güvencesi Migrasyonları
for tbl, col, col_def in [
    ("ogrenciler", "sinav_turu", "TEXT DEFAULT 'YKS (TYT)'"),
    ("ogrenciler", "hedef_il", "TEXT DEFAULT 'İstanbul'"),
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

giris_turu = st.sidebar.radio("Giriş Paneli Seçin:", ["👨‍🎓 ÖĞRENCİ GİRİŞİ", "👨‍🏫 KOÇ GİRİŞİ"])

# ==================== ÖĞRENCİ PANELİ ====================
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
        "📝 GÜNLÜK ÇALIŞMA",
        "📊 DENEMELER & GELİŞİM",
        "🗺️ KONU HAKİMİYETİ"
    ])
    
    # --- TAB 1: ÖĞRENCİ GİRİŞ / KAYIT ---
    with tab_giris:
        st.markdown("<h3 style='font-weight:700; font-size:18px; color:#1e293b;'>Öğrenci Hesabı Girişi / Kaydı</h3>", unsafe_allow_html=True)
        cursor.execute("SELECT kullanici_adi FROM koclar")
        koc_listesi = [r[0] for r in cursor.fetchall()] or ["koc1"]
            
        with st.form("ogrenci_giris_kayit_formu"):
            col1, col2, col3, col4 = st.columns(4)
            with col1: ad_soyad = st.text_input("Adınız ve Soyadınız:").strip().title()
            with col2: sifre = st.text_input("Şifreniz / PIN:", type="password")
            with col3: sinav_turu = st.selectbox("🎓 Hazırlanılan Sınav:", ["YKS (TYT)", "LGS (8. Sınıf)"])
            with col4: secilen_koc = st.selectbox("👨‍🏫 Sorumlu Koçunuz:", koc_listesi)
            ogr_giris_btn = st.form_submit_button("Giriş Yap / Hesabı Oluştur", type="primary", use_container_width=True)
            
        if ogr_giris_btn:
            if ad_soyad and sifre:
                cursor.execute("SELECT sifre, koc_adi, sinav_turu FROM ogrenciler WHERE ad_soyad = ?", (ad_soyad,))
                user = cursor.fetchone()
                if user is None:
                    cursor.execute("INSERT INTO ogrenciler (ad_soyad, sifre, sinav_turu, koc_adi) VALUES (?, ?, ?, ?)", (ad_soyad, make_hash(sifre), sinav_turu, secilen_koc))
                    conn.commit()
                    st.success(f"🎉 Hoş geldin {ad_soyad}! Profilin [{sinav_turu} - {secilen_koc} koçluğunda] oluşturuldu.")
                    st.session_state["aktif_ogrenci"] = ad_soyad
                else:
                    if verify_hash(sifre, user[0]):
                        cursor.execute("UPDATE ogrenciler SET koc_adi = ?, sinav_turu = ? WHERE ad_soyad = ?", (secilen_koc, sinav_turu, ad_soyad))
                        conn.commit()
                        st.success(f"🔓 Giriş başarılı! Hoş geldin {ad_soyad} ({sinav_turu}).")
                        st.session_state["aktif_ogrenci"] = ad_soyad
                    else:
                        st.error("Hatalı şifre!")
            else:
                st.warning("Lütfen tüm alanları doldurunuz.")
                
    aktif_ogr = st.session_state.get("aktif_ogrenci", None)
    
    if not aktif_ogr:
        st.info("ℹ️ İşlem yapmak için lütfen ilk sekmeden 'Giriş / Kayıt' yapın.")
    else:
        cursor.execute("SELECT sinav_turu, hedef_il FROM ogrenciler WHERE ad_soyad = ?", (aktif_ogr,))
        r_info = cursor.fetchone()
        ogr_sinav = r_info[0] if r_info else "YKS (TYT)"
        m_il = r_info[1] if (r_info and r_info[1]) else "İstanbul"
        
        st.sidebar.success(f"👤 Aktif Öğrenci: **{aktif_ogr}** ({ogr_sinav})")
        
        # 🔔 PROGRAM GÜNCELLEME UYARISI
        cursor.execute("SELECT program_guncellendi_mi FROM ogrenciler WHERE ad_soyad = ?", (aktif_ogr,))
        p_row = cursor.fetchone()
        if p_row and p_row[0] == 1:
            st.warning("🔔 **DERS PROGRAMI GÜNCELLEMESİ:** Koçunuz haftalık ders programınızda yeni düzenlemeler yaptı! 'Haftalık Ders Programı' sekmesinden inceleyebilirsiniz.")
            if st.button("✅ Programı İnceledim / Bildirimi Kapat", type="secondary"):
                cursor.execute("UPDATE ogrenciler SET program_guncellendi_mi = 0 WHERE ad_soyad = ?", (aktif_ogr,))
                conn.commit()
                st.rerun()

        AKTIF_KONULAR = TYT_KONULAR if ogr_sinav == "YKS (TYT)" else LGS_KONULAR
        AKTIF_DERSLER = list(AKTIF_KONULAR.keys())

        # --- TAB 2: HEDEF TAKİBİ (İLLERE GÖRE DİNAMİK LGS / YKS) ---
        with tab_hedef:
            st.markdown(f"<h3 style='font-weight:700; font-size:18px;'>🎯 {ogr_sinav} Hedef Okul Takip Area — {aktif_ogr}</h3>", unsafe_allow_html=True)
            cursor.execute("SELECT hedef_uni, hedef_bolum, hedef_net, hedef_il FROM ogrenciler WHERE ad_soyad = ?", (aktif_ogr,))
            h_data = cursor.fetchone() or ("", "", 100.0, "İstanbul")

            if ogr_sinav == "YKS (TYT)":
                secilen_uni = st.selectbox("🏛️ Hedeflenen Üniversite:", POPULE_UNIVERSITELER, index=POPULE_UNIVERSITELER.index(h_data[0]) if h_data[0] in POPULE_UNIVERSITELER else 0)
                mevcut_bolumler = list(YOK_ATLAS_VERILERI[secilen_uni].keys())
                secilen_bolum = st.selectbox("🎓 Hedeflenen Bölüm:", mevcut_bolumler, index=mevcut_bolumler.index(h_data[1]) if h_data[1] in mevcut_bolumler else 0)
                
                atlas_bilgi = YOK_ATLAS_VERILERI[secilen_uni][secilen_bolum]
                otomatik_taban_net = atlas_bilgi["taban_net"]
                secilen_il = "Türkiye Genel"
                
                st.markdown(f"""
                <div class="target-card">
                    <h4 style="margin-top:0; color:#0284c7;">🏛️ YÖK Atlas Verileri ({secilen_uni} - {secilen_bolum})</h4>
                    <div style="display:flex; justify-content:space-around; flex-wrap:wrap; gap:10px;">
                        <div><strong>📉 Taban Sıralama:</strong> {atlas_bilgi['taban_sira']}.</div>
                        <div><strong>🏆 Tavan Sıralama:</strong> {atlas_bilgi['tavan_sira']}.</div>
                        <div><strong>🎯 Taban TYT Net:</strong> {atlas_bilgi['taban_net']} Net</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # 81 İL SEÇİMLİ LGS MODÜLÜ
                secilen_il = st.selectbox("🗺️ Hedeflediğiniz İli Seçin (81 İl):", ILLER_LISTESI, index=ILLER_LISTESI.index(h_data[3]) if h_data[3] in ILLER_LISTESI else 39)
                
                # Seçilen İlin Liselerini Hazırlama
                il_liseleri_dict = LGS_IL_LISELERI.get(secilen_il, GENEL_DEFAULT_LISE)
                il_lise_listesi = list(il_liseleri_dict.keys()) + ["✏️ Diğer / Manuel Lise Gir"]
                
                secilen_uni = st.selectbox(f"🏫 {secilen_il} İline Ait Nitelikli Liseler:", il_lise_listesi)
                secilen_bolum = "LGS Lise Hedefi"

                if secilen_uni in il_liseleri_dict:
                    lise_bilgi = il_liseleri_dict[secilen_uni]
                    otomatik_taban_net = lise_bilgi["taban_net"]
                    st.markdown(f"""
                    <div class="target-card">
                        <h4 style="margin-top:0; color:#0284c7;">🏫 LGS Nitelikli Lise Verileri ({secilen_il} - {secilen_uni})</h4>
                        <div style="display:flex; justify-content:space-around; flex-wrap:wrap; gap:10px;">
                            <div><strong>📉 LGS Taban Puan:</strong> {lise_bilgi['taban_puan']} Puan</div>
                            <div><strong>📊 Yüzdelik Dilim:</strong> {lise_bilgi['yuzdelik']}</div>
                            <div><strong>🎯 Gerekli Toplam LGS Net:</strong> {lise_bilgi['taban_net']} Net / 90</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    secilen_uni = st.text_input("Manuel Lise Adını Giriniz:", value="Özel Hedef Lise")
                    otomatik_taban_net = 70.0

            with st.form("hedef_kaydet_form"):
                col_h1, col_h2 = st.columns(2)
                with col_h1: st.text_input("Gerekli Taban Net (Otomatik):", value=f"{otomatik_taban_net} Net", disabled=True)
                with col_h2: ozel_hedef_net = st.number_input("Kendi Net Hedefinizi Özelleştirin:", 10.0, 120.0, float(otomatik_taban_net), 1.0)
                
                if st.form_submit_button("🎯 Hedefimi Kaydet", type="primary", use_container_width=True):
                    cursor.execute("UPDATE ogrenciler SET hedef_uni = ?, hedef_bolum = ?, hedef_net = ?, hedef_il = ? WHERE ad_soyad = ?", (secilen_uni, secilen_bolum, float(ozel_hedef_net), secilen_il, aktif_ogr))
                    conn.commit()
                    st.success("🎉 Hedef kaydedildi!")
                    st.rerun()

            # Deneme Analizi
            cursor.execute("SELECT MAX(toplam_net), MIN(toplam_net) FROM denemeler WHERE ad_soyad = ?", (aktif_ogr,))
            d_min_max = cursor.fetchone()
            max_net = d_min_max[0] if (d_min_max and d_min_max[0] is not None) else 0.0
            min_net = d_min_max[1] if (d_min_max and d_min_max[1] is not None) else 0.0
            hedef_net_val = float(h_data[2]) if (h_data[2] and h_data[2] > 0) else otomatik_taban_net

            st.divider()
            st.markdown("<h4 style='font-weight:700; font-size:17px; color:#0f172a;'>🏆 En Yüksek ve En Düşük Denemelerinize Göre Hedef Analizi</h4>", unsafe_allow_html=True)
            
            if max_net > 0:
                st.markdown("<h5 style='font-weight:700; color:#0284c7; margin-top:15px;'>🔥 En Yüksek Deneme Performansı (Zirve)</h5>", unsafe_allow_html=True)
                oran_max = min(1.0, max_net / hedef_net_val)
                st.markdown(f"**Target Net:** `{hedef_net_val}` Net | **En Yüksek Netiniz:** `{max_net}` Net")
                st.progress(oran_max)
                st.markdown(f"📈 **Zirve Nete Göre Ulaşma Oranı: %{(oran_max*100):.1f}**")

                st.markdown("<br/>", unsafe_allow_html=True)
                st.markdown("<h5 style='font-weight:700; color:#475569;'>🛡️ En Düşük Deneme Performansı (Taban)</h5>", unsafe_allow_html=True)
                oran_min = min(1.0, min_net / hedef_net_val)
                st.markdown(f"**Target Net:** `{hedef_net_val}` Net | **En Düşük Netiniz:** `{min_net}` Net")
                st.progress(oran_min)
                st.markdown(f"📈 **En Düşük Nete Göre Ulaşma Oranı: %{(oran_min*100):.1f}**")
            else:
                st.info("ℹ️ Henüz kaydedilmiş bir deneme sonucunuz bulunmuyor.")

        # --- TAB 3: DERS PROGRAMI ---
        with tab_program:
            st.markdown("<h3 style='font-weight:700; font-size:18px;'>📅 Sorumlu Koçunuz Tarafından Hazırlanan Haftalık Ders Programı</h3>", unsafe_allow_html=True)
            df_prog = pd.read_sql_query("SELECT gun, saat_araligi, aktivite_turu, ders, detay_aciklama FROM haftalik_program WHERE ad_soyad = ? ORDER BY id ASC", conn, params=(aktif_ogr,))
            
            if df_prog.empty:
                st.info("ℹ️ Koçunuz henüz size özel bir çalışma programı tanımlamadı.")
            else:
                st.dataframe(df_prog, use_container_width=True)
                html_table = df_prog.to_html(index=False, classes="styled-table")
                html_prog_page = f"""
                <div style="font-family: Arial, sans-serif; padding:25px; border:2px solid #0284c7; border-radius:12px; background:#fff;">
                    <div style="text-align:center; border-bottom:2px solid #e2e8f0; padding-bottom:10px; margin-bottom:15px;">
                        <h2 style="color:#0284c7; margin:0;">🎓 YKS-LGS KOÇLUK (DENİZ YILMAZ)</h2>
                        <h4 style="color:#475569; margin:5px 0 0 0;">👨‍🎓 {aktif_ogr} ({ogr_sinav}) - HAFTALIK DERS PROGRAMI</h4>
                        <p style="color:#64748b; font-size:12px; margin:4px 0 0 0;">Tarih: {datetime.date.today().strftime('%d.%m.%Y')}</p>
                    </div>
                    {html_table}
                </div>
                """
                b64_p = base64.b64encode(html_prog_page.encode('utf-8')).decode('utf-8')
                href_p = f'<a href="data:text/html;charset=utf-8;base64,{b64_p}" download="{aktif_ogr}_Haftalik_Ders_Programi.html" style="display:inline-block; padding:10px 20px; background-color:#10b981; color:white; text-decoration:none; border-radius:10px; font-weight:bold;">📄 Haftalık Programı Yazdır / PDF İndir</a>'
                st.markdown(href_p, unsafe_allow_html=True)

        # --- TAB 4: GÜNLÜK ÇALIŞMA ---
        with tab_gunluk:
            st.markdown(f"<h3 style='font-weight:700; font-size:18px;'>📝 Günlük Çalışma Girişi — {aktif_ogr} ({ogr_sinav})</h3>", unsafe_allow_html=True)
            
            c_top1, c_top2, c_top3 = st.columns([1, 1, 1])
            with c_top1: tarih_giris = st.date_input("Çalışma Tarihi", datetime.date.today())
            with c_top2: sure_giris = st.number_input("Bugünkü Toplam Çalışma Süresi (Saat)", 0.0, 16.0, 6.0, 0.5)
            with c_top3: verim_giris = st.slider("Günün Verim Puanı (1-10)", 1, 10, 8)
                
            not_giris = st.text_area("Bugün zorlandığın detaylar / Koçuna iletmek istediğin çalışma notu:", height=70)
            
            st.divider()
            st.markdown("<h4 style='font-weight:700; font-size:16px;'>📚 Ders ve Konu Bazlı Soru Analizi Girişi</h4>", unsafe_allow_html=True)
            
            ders_sekmeleri = st.tabs(AKTIF_DERSLER)
            ders_verileri = {}

            for idx, ders_adi in enumerate(AKTIF_DERSLER):
                with ders_sekmeleri[idx]:
                    secilen_konu = st.selectbox(
                        f"Çalıştığınız Konu ({ders_adi}):",
                        options=["Genel Soru Çözümü / Karma"] + AKTIF_KONULAR[ders_adi],
                        key=f"konu_select_{ders_adi}"
                    )
                    
                    c1, c2, c3, c4 = st.columns(4)
                    with c1: toplam_s = st.number_input(f"Toplam Soru ({ders_adi})", 0, 500, 0, key=f"top_{ders_adi}")
                    with c2: dogru_s = st.number_input(f"Doğru ({ders_adi})", 0, 500, 0, key=f"dog_{ders_adi}")
                    with c3: yanlis_s = st.number_input(f"Yanlış ({ders_adi})", 0, 500, 0, key=f"yan_{ders_adi}")
                    with c4: bos_s = st.number_input(f"Boş ({ders_adi})", 0, 500, 0, key=f"bos_{ders_adi}")
                    
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
                    st.success("🎉 Çalışmalarınız başarıyla kaydedildi!")

            st.divider()
            df_analiz = pd.read_sql_query("SELECT ders, SUM(toplam_soru) as toplam, SUM(dogru) as d, SUM(yanlis) as y, SUM(bos) as b FROM gunluk_calisma WHERE ad_soyad = ? GROUP BY ders", conn, params=(aktif_ogr,))
            if not df_analiz.empty and df_analiz["toplam"].sum() > 0:
                top_d, top_y, top_b = int(df_analiz["d"].sum()), int(df_analiz["y"].sum()), int(df_analiz["b"].sum())
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    renkler = ['#0284c7', '#0ea5e9', '#38bdf8', '#818cf8', '#6366f1', '#10b981']
                    st.markdown(halka_grafik_html("🍩 Derslere Göre Soru Dağılımı", [(row["ders"], int(row["toplam"]), renkler[idx % len(renkler)]) for idx, row in df_analiz[df_analiz["toplam"] > 0].reset_index().iterrows()]), unsafe_allow_html=True)
                with col_g2:
                    st.markdown(halka_grafik_html("🎯 Toplam Doğru / Yanlış / Boş Oranı", [("Doğru 🟢", top_d, "#10b981"), ("Yanlış 🔴", top_y, "#ef4444"), ("Boş 🟡", top_b, "#f59e0b")]), unsafe_allow_html=True)

        # --- TAB 5: DENEMELER & GELİŞİM ---
        with tab_deneme:
            st.markdown(f"<h3 style='font-weight:700; font-size:18px;'>📊 Deneme Sonuçları & Karne Yükleme ({ogr_sinav})</h3>", unsafe_allow_html=True)
            with st.form("deneme_yukle_formu"):
                col_d1, col_d2, col_d3 = st.columns(3)
                with col_d1: yayin = st.text_input("Deneme Adı / Yayın:")
                with col_d2: d_tur = st.selectbox("Deneme Türü:", [f"{ogr_sinav} Genel Denemesi", f"{ogr_sinav} Branş Denemesi"])
                with col_d3: toplam_net = st.number_input("Toplam Netiniz:", 0.0, 120.0, 70.0)
                karne_dosya = st.file_uploader("📄 Deneme Karnesi Yükle:", type=["pdf", "png", "jpg"])
                if st.form_submit_button("Deneme Karnesini Kaydet", type="primary", use_container_width=True) and yayin:
                    cursor.execute("INSERT INTO denemeler (ad_soyad, tarih, yayin, tur, toplam_net, dosya_adi, koc_notu) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                   (aktif_ogr, str(datetime.date.today()), yayin, d_tur, float(toplam_net), karne_dosya.name if karne_dosya else "Dosya Yok", ''))
                    conn.commit()
                    st.success("🎉 Deneme sonucu kaydedildi!")

            st.divider()
            df_net_trend = pd.read_sql_query("SELECT tarih, toplam_net, yayin FROM denemeler WHERE ad_soyad = ? ORDER BY id ASC", conn, params=(aktif_ogr,))
            if not df_net_trend.empty:
                st.line_chart(df_net_trend.set_index("tarih")["toplam_net"])

        # --- TAB 6: KONU HAKİMİYETİ ---
        with tab_konular:
            st.markdown(f"<h3 style='font-weight:700; font-size:18px;'>🗺️ {ogr_sinav} Ders Ders Konu Hakimiyet Puanlaması (1 - 5)</h3>", unsafe_allow_html=True)
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

# ==================== KOÇ PANELİ ====================
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
            
            cursor.execute("SELECT sinav_turu, hedef_uni, hedef_bolum, hedef_net, hedef_il FROM ogrenciler WHERE ad_soyad = ?", (secilen_ogr,))
            k_info = cursor.fetchone()
            s_turu = k_info[0] if k_info else "YKS (TYT)"
            
            K_DERSLER = list(TYT_KONULAR.keys()) if s_turu == "YKS (TYT)" else list(LGS_KONULAR.keys())

            st.info(f"🎓 **Öğrenci Kategori:** `{s_turu}` | **Hedef Okul:** {k_info[1] if k_info else ''} ({k_info[4] if k_info else ''}) | **Hedef Net:** {k_info[3] if k_info else ''}")

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
                    with cp5: p_detay = st.text_input("Açıklama / Soru Sayısı / Konu:", placeholder="Ör: Paragraf 30 Soru + Matematik Problem")
                    
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
                sil_id = st.selectbox("Silmek istediğiniz ID:", df_koc_prog["id"].tolist())
                if st.button("🗑️ Seçilen Aktiviteyi Sil", type="secondary"):
                    cursor.execute("DELETE FROM haftalik_program WHERE id = ?", (sil_id,))
                    cursor.execute("UPDATE ogrenciler SET program_guncellendi_mi = 1 WHERE ad_soyad = ?", (secilen_ogr,))
                    conn.commit()
                    st.rerun()

            st.divider()
            st.markdown(f"### 📊 Öğrenci Analiz Raporu & Deneme Değerlendirme")
            df_deneme = pd.read_sql_query("SELECT id, tarih, yayin, tur, toplam_net, dosya_adi, koc_notu FROM denemeler WHERE ad_soyad = ?", conn, params=(secilen_ogr,))
            
            if not df_deneme.empty:
                st.dataframe(df_deneme, use_container_width=True)
                deneme_secenekleri = {row['id']: f"ID: {row['id']} - {row['tarih']} | {row['yayin']} - Net: {row['toplam_net']}" for _, row in df_deneme.iterrows()}
                secilen_deneme_id = st.selectbox("Değerlendirilecek Deneme:", options=list(deneme_secenekleri.keys()), format_func=lambda x: deneme_secenekleri[x])
                deneme_row = df_deneme[df_deneme['id'] == secilen_deneme_id].iloc[0]

                df_zayif = pd.read_sql_query("SELECT konu_adi FROM konu_puanlari WHERE ad_soyad = ? AND puan IN (1, 2)", conn, params=(secilen_ogr,))
                z_str = ", ".join(df_zayif['konu_adi'].tolist()) if not df_zayif.empty else "Acil müdahale gereken konu bulunmamaktadır."

                if st.button("🤖 Otomatik AI Analiz Taslağı Üret", use_container_width=True):
                    st.session_state[f"temp_not_{secilen_deneme_id}"] = (
                        f"📌 {deneme_row['yayin']} Değerlendirmesi ({s_turu}):\n"
                        f"• Net: {deneme_row['toplam_net']} Net.\n"
                        f"• Hedef Okul: {k_info[1] if k_info else ''}\n"
                        f"• Tespit Edilen Zayıf Konular: {z_str}\n\n"
                        f"💡 Deniz Yılmaz Koçluk Tavsiyesi:\n"
                        f"1. Eksik konulardan günlük en az 30 soru çözülmeli.\n"
                        f"2. Yanlış yapılan soruların çözümleri tekrar incelenmeli."
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
                        <p><strong>📑 Deneme:</strong> {deneme_row['yayin']} | <strong>Net:</strong> {deneme_row['toplam_net']}</p>
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