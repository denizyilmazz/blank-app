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
        padding: 18px 22px;
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

    .program-header-box {
        background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%);
        color: white;
        padding: 20px;
        border-radius: 16px;
        margin-bottom: 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(2, 132, 199, 0.2);
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

HAM_DERS_KONULARI = {
    "📐 Matematik Özel Ders": [
        "Matematik Özel Ders - Konu Anlatımı & Föyler",
        "Matematik Özel Ders - Soru Çözüm Kampı",
        "Matematik Özel Ders - Ödev Kontrolü & Tekrar",
        "Matematik Özel Ders - Yeni Nesil Soru Analizi"
    ],
    "⚡ Fizik Özel Ders": [
        "Fizik Özel Ders - Konu Anlatımı & Deney/Simülasyon",
        "Fizik Özel Ders - Soru Çözüm & Formül Pratiği",
        "Fizik Özel Ders - Ödev Kontrolü & Zor Sorular"
    ],
    "🧪 Kimya Özel Ders": [
        "Kimya Özel Ders - Konu Anlatımı",
        "Kimya Özel Ders - Soru Çözüm & Hesaplama Pratiği"
    ],
    "🧬 Biyoloji Özel Ders": [
        "Biyoloji Özel Ders - Konu Anlatımı & Şekil Analizi",
        "Biyoloji Özel Ders - Soru Çözüm Kampı"
    ],
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
        "Paragraf Hız Kampı (25 Soru)", "Sözel Mantık Rutini", 
        "Yeni Nesil Problemler (20 Soru)", "Sayı-Kesir Problemleri", 
        "Yaş & İşçi Havuz Problemleri", "Yüzde-Kar/Zarar & Karışım", 
        "Hız & Hareket Problemleri", "Grafik & Rutin Olmayan Problemler"
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

YKS_KAPSAMLI_DERS_KONULAR = {}
for k, v_list in HAM_DERS_KONULARI.items():
    if "Özel Ders" in k or "Mola" in k or "Yürüyüş" in k or "Yemeği" in k:
        YKS_KAPSAMLI_DERS_KONULAR[k] = v_list
    else:
        genisletilmis_liste = []
        for konu in v_list:
            genisletilmis_liste.append(f"{konu} — Konu Çalışması")
            genisletilmis_liste.append(f"{konu} — Soru Çözümü")
        YKS_KAPSAMLI_DERS_KONULAR[k] = genisletilmis_liste

TYT_KONULAR = {
    "⚡ 📖 Paragraf + 📐 Problem Rutini": ["Paragraf — Konu Çalışması", "Paragraf — Soru Çözümü", "Problem — Konu Çalışması", "Problem — Soru Çözümü"],
    "📖 TYT Türkçe": ["Sözcükte Anlam — Konu Çalışması", "Sözcükte Anlam — Soru Çözümü"],
    "📐 TYT Matematik": ["Temel Kavramlar — Konu Çalışması", "Temel Kavramlar — Soru Çözümü"]
}

AYT_KONULAR = {
    "📐 AYT Matematik": ["Polinomlar — Konu Çalışması", "Polinomlar — Soru Çözümü"]
}

LGS_KONULAR = {
    "📖 LGS Türkçe (20 Soru)": ["Fiilimsiler — Konu Çalışması", "Fiilimsiler — Soru Çözümü"],
    "📐 LGS Matematik (20 Soru)": ["Çarpanlar ve Katlar — Konu Çalışması", "Çarpanlar ve Katlar — Soru Çözümü"]
}

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

cursor.execute("""
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

st.markdown("""
<div style="text-align: center; padding: 10px 0 15px 0;">
    <span style="font-size: 42px;">🎓</span>
    <h1 style="margin: 0; font-weight: 800; font-size: 26px; color: #0f172a;">YKS (TYT/AYT) - LGS KOÇLUK</h1>
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
            hatirlanan_ogr = st.query_params.get("hatirla_ogr", None)
            if hatirlanan_ogr:
                cursor.execute("SELECT ad_soyad FROM ogrenciler WHERE ad_soyad = ?", (hatirlanan_ogr,))
                if cursor.fetchone():
                    st.session_state["aktif_ogrenci"] = hatirlanan_ogr
                    aktif_ogr = hatirlanan_ogr

        if not aktif_ogr:
            st.markdown("<h3 style='font-weight:700; font-size:18px;'>👨‍🎓 Öğrenci Giriş & Kayıt Paneli</h3>", unsafe_allow_html=True)
            tab_ogr_login, tab_ogr_register = st.tabs(["🔑 GİRİŞ YAP", "➕ YENİ HESAP OLUŞTUR"])

            with tab_ogr_login:
                with st.form("ogrenci_giris_formu"):
                    login_ad = st.text_input("Adınız ve Soyadınız:").strip().title()
                    login_sifre = st.text_input("Şifre / PIN:", type="password")
                    beni_hatirla_ogr = st.checkbox("Beni Hatırla")
                    if st.form_submit_button("Giriş Yap", type="primary", use_container_width=True):
                        if login_ad and login_sifre:
                            cursor.execute("SELECT sifre FROM ogrenciler WHERE ad_soyad = ?", (login_ad,))
                            usr = cursor.fetchone()
                            if usr and verify_hash(login_sifre, usr[0]):
                                st.session_state["aktif_ogrenci"] = login_ad
                                if beni_hatirla_ogr:
                                    st.query_params["hatirla_ogr"] = login_ad
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
                cursor.execute("SELECT sinav_turu, hedef_uni, hedef_bolum FROM ogrenciler WHERE ad_soyad = ?", (aktif_ogr,))
                r_info = cursor.fetchone()
                ogr_sinav = r_info[0] if r_info else "TYT (Sadece TYT Çalışması)"
                curr_uni = r_info[1] if (r_info and r_info[1]) else "Giresun Üniversitesi"
                curr_bolum = r_info[2] if (r_info and r_info[2]) else "Matematik"
                st.success(f"👤 Aktif Oturum: **{aktif_ogr}** | Sınav Modu: **{ogr_sinav}**")
            
            with col_o_head2:
                if st.button("🚪 ÇIKIŞ YAP", key="ogr_logout_btn", use_container_width=True):
                    st.session_state["aktif_ogrenci"] = None
                    if "hatirla_ogr" in st.query_params:
                        del st.query_params["hatirla_ogr"]
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
                st.markdown(f"<h3 style='font-weight:700; font-size:18px;'>🎯 YÖK Atlas Hedef & Net Analiz Merkezi — {aktif_ogr}</h3>", unsafe_allow_html=True)
                st.caption("🏛️ Üniversitenizi ve bölümünüzü seçerek ÖSYM / YÖK Atlas verilerine göre gereken taban netleri ve başarı sırasını anında görüntüleyin.")

                cursor.execute("SELECT DISTINCT universite_adi FROM ozel_universiteler")
                ozel_unis = [r[0] for r in cursor.fetchall()]
                toplam_uni_listesi = sorted(list(set(UNIVERSITE_LISTESI + ozel_unis)))

                col_h_u1, col_h_u2, col_h_u3 = st.columns([1.2, 1.2, 0.8])
                with col_h_u1:
                    u_idx = toplam_uni_listesi.index(curr_uni) if curr_uni in toplam_uni_listesi else 0
                    secilen_hedef_uni = st.selectbox("Hedef Üniversite:", toplam_uni_listesi, index=u_idx)
                
                with col_h_u2:
                    secilen_kategori = st.selectbox("Puan Türü / Kategori:", list(BOLUM_KATEGORILERI.keys()))
                
                cursor.execute("SELECT bolum_adi FROM ozel_universiteler WHERE universite_adi = ? AND kategori = ?", (secilen_hedef_uni, secilen_kategori))
                ozel_bolumler = [r[0] for r in cursor.fetchall()]
                toplam_bolum_listesi = sorted(list(set(BOLUM_KATEGORILERI[secilen_kategori] + ozel_bolumler)))

                with col_h_u3:
                    b_idx = toplam_bolum_listesi.index(curr_bolum) if curr_bolum in toplam_bolum_listesi else 0
                    secilen_hedef_bolum = st.selectbox("Bölüm:", toplam_bolum_listesi, index=b_idx)

                cursor.execute("SELECT taban_net, taban_sira, tyt_net, ayt_net FROM ozel_universiteler WHERE universite_adi = ? AND bolum_adi = ?", (secilen_hedef_uni, secilen_hedef_bolum))
                ozel_kayit = cursor.fetchone()

                if ozel_kayit:
                    t_net, t_sira, tyt_gerekli, ayt_gerekli = ozel_kayit[0], ozel_kayit[1], ozel_kayit[2], ozel_kayit[3]
                else:
                    if "Matematik" in secilen_hedef_bolum or "Fen Edebiyat" in secilen_hedef_bolum:
                        t_net, t_sira, tyt_gerekli, ayt_gerekli = 75.5, "95.000", 72.0, 45.0
                    else:
                        t_net, t_sira, tyt_gerekli, ayt_gerekli = 85.0, "50.000", 80.0, 52.0

                st.markdown(f"""
                <div class="yok-net-box">
                    <div style="font-size:16px; font-weight:800; color:#1e40af; margin-bottom:8px;">🏛️ {secilen_hedef_uni} — {secilen_hedef_bolum}</div>
                    <div style="display: flex; gap: 20px; flex-wrap: wrap; margin-top: 10px;">
                        <div style="background: white; padding: 10px 15px; border-radius: 10px; border: 1px solid #93c5fd; flex: 1; min-width: 140px;">
                            <span style="font-size: 11px; color: #64748b; font-weight: 700;">YÖK ATLAS TABAN NET</span><br>
                            <span style="font-size: 18px; font-weight: 800; color: #0284c7;">{t_net} Net</span>
                        </div>
                        <div style="background: white; padding: 10px 15px; border-radius: 10px; border: 1px solid #93c5fd; flex: 1; min-width: 140px;">
                            <span style="font-size: 11px; color: #64748b; font-weight: 700;">YÖK ATLAS BAŞARI SIRASI</span><br>
                            <span style="font-size: 18px; font-weight: 800; color: #16a34a;">İlk {t_sira}</span>
                        </div>
                        <div style="background: white; padding: 10px 15px; border-radius: 10px; border: 1px solid #93c5fd; flex: 1; min-width: 140px;">
                            <span style="font-size: 11px; color: #64748b; font-weight: 700;">GEREKLİ ORTALAMA TYT</span><br>
                            <span style="font-size: 18px; font-weight: 800; color: #9333ea;">~{tyt_gerekli} Net</span>
                        </div>
                        <div style="background: white; padding: 10px 15px; border-radius: 10px; border: 1px solid #93c5fd; flex: 1; min-width: 140px;">
                            <span style="font-size: 11px; color: #64748b; font-weight: 700;">GEREKLİ ORTALAMA AYT</span><br>
                            <span style="font-size: 18px; font-weight: 800; color: #ea580c;">~{ayt_gerekli} Net</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button("🚀 Bu Hedefi Profilime Kaydet ve Netlerimi Planla", type="primary", use_container_width=True):
                    cursor.execute("UPDATE ogrenciler SET hedef_uni = ?, hedef_bolum = ?, hedef_net = ? WHERE ad_soyad = ?", 
                                   (secilen_hedef_uni, f"{secilen_hedef_bolum} ({secilen_kategori})", float(t_net), aktif_ogr))
                    conn.commit()
                    st.success(f"🎉 Hedefiniz başarıyla güncellendi: {secilen_hedef_uni} - {secilen_hedef_bolum} ({t_net} Net)!")
                    st.rerun()

            with tab_program:
                st.markdown(f"""
                <div class="program-header-box">
                    <h2 style="margin:0; font-size:22px; font-weight:800; color:white !important;">📅 {aktif_ogr.upper()} — KİŞİSEL HAFTALIK DERS PROGRAMI</h2>
                    <p style="margin:5px 0 0 0; font-size:13px; opacity:0.9; color:white !important;">Koçunuz tarafından özel olarak hazırlanan haftalık çalışma planınız aşağıdadır.</p>
                </div>
                """, unsafe_allow_html=True)

                df_p = pd.read_sql_query("SELECT saat_araligi AS 'Saat', pazartesi AS 'Pazartesi', sali AS 'Salı', carsamba AS 'Çarşamba', persembe AS 'Perşembe', cuma AS 'Cuma', cumartesi AS 'Cumartesi', pazar AS 'Pazar' FROM excel_program_matris WHERE ad_soyad = ?", conn, params=(aktif_ogr,))
                if not df_p.empty:
                    st.dataframe(df_p, use_container_width=True, height=400)
                    
                    st.markdown("---")
                    st.markdown("#### 📥 Programını Cihazına İndir")
                    csv_data = df_p.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Programı İndir (.csv)",
                        data=csv_data,
                        file_name=f"{aktif_ogr}_Haftalik_Ders_Programi.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                else:
                    st.info(f"ℹ️ Sevgili {aktif_ogr}, koçun henüz haftalık programını kaydetmedi. Kaydedildiği an burada görünecektir.")

                df_dosyalar = pd.read_sql_query("SELECT dosya_adi, dosya_yolu FROM program_dosyalari WHERE ad_soyad = ?", conn, params=(aktif_ogr,))
                for _, f_row in df_dosyalar.iterrows():
                    if os.path.exists(f_row['dosya_yolu']):
                        with open(f_row['dosya_yolu'], "rb") as fb:
                            st.download_button(f"📥 Ekstra Dosya: {f_row['dosya_adi']}", data=fb, file_name=f_row['dosya_adi'])

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
                st.markdown(f"### 📊 Denemeler & Yapay Zeka Koç Analizi — {aktif_ogr}")
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
            hatirlanan_koc = st.query_params.get("hatirla_koc", None)
            if hatirlanan_koc:
                cursor.execute("SELECT kullanici_adi FROM koclar WHERE kullanici_adi = ?", (hatirlanan_koc,))
                if cursor.fetchone():
                    st.session_state["aktif_koc"] = hatirlanan_koc

        if not st.session_state["aktif_koc"]:
            with st.form("koc_giris"):
                k_ad = st.text_input("Koç Kullanıcı Adı:")
                k_sif = st.text_input("Şifre:", type="password")
                beni_hatirla_koc = st.checkbox("Beni Hatırla", key="bh_koc")
                if st.form_submit_button("Giriş Yap", type="primary"):
                    cursor.execute("SELECT sifre FROM koclar WHERE kullanici_adi = ?", (k_ad,))
                    r = cursor.fetchone()
                    if r and verify_hash(k_sif, r[0]):
                        st.session_state["aktif_koc"] = k_ad
                        if beni_hatirla_koc:
                            st.query_params["hatirla_koc"] = k_ad
                        st.rerun()
                    else: st.error("Hatalı!")
        else:
            if st.button("🚪 ÇIKIŞ YAP", key="koc_out"):
                st.session_state["aktif_koc"] = None
                if "hatirla_koc" in st.query_params:
                    del st.query_params["hatirla_koc"]
                st.rerun()

            with st.expander("➕ Sistemde Olmayan Üniversite / Bölüm Ekle (Özel Tanımlama)"):
                with st.form("ozel_uni_ekle_form"):
                    st.markdown("**Listede bulamadığınız üniversite ve bölümü ekleyerek anında hedef olarak seçilmesini sağlayabilirsiniz.**")
                    y_uni = st.text_input("Üniversite Adı (Örn: Giresun Üniversitesi):").strip()
                    y_bolum = st.text_input("Bölüm Adı (Örn: Fen Edebiyat Fakültesi Matematik):").strip()
                    y_kat = st.selectbox("Puan Türü:", ["SAY (Sayısal)", "EA (Eşit Ağırlık)", "SÖZ (Sözel)", "DİL (Yabancı Dil)"])
                    c_n1, c_n2, c_n3, c_n4 = st.columns(4)
                    with c_n1: y_tnet = st.number_input("Taban Net:", 0.0, 120.0, 75.0, 0.5)
                    with c_n2: y_tsira = st.text_input("Başarı Sırası:", value="95.000")
                    with c_n3: y_tyt = st.number_input("Gerekli TYT:", 0.0, 120.0, 70.0, 0.5)
                    with c_n4: y_ayt = st.number_input("Gerekli AYT:", 0.0, 80.0, 45.0, 0.5)

                    if st.form_submit_button("💾 Üniversite / Bölümü Kaydet", type="primary", use_container_width=True):
                        if y_uni and y_bolum:
                            cursor.execute("""
                                INSERT INTO ozel_universiteler (universite_adi, bolum_adi, kategori, taban_net, taban_sira, tyt_net, ayt_net)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (y_uni, y_bolum, y_kat, y_tnet, y_tsira, y_tyt, y_ayt))
                            conn.commit()
                            st.success(f"🎉 '{y_uni} - {y_bolum}' başarıyla sisteme eklendi!")
                            st.rerun()
                        else:
                            st.error("⚠️ Üniversite ve bölüm adını boş bırakmayın!")

            cursor.execute("SELECT ad_soyad FROM ogrenciler")
            ogrs = [row[0] for row in cursor.fetchall()]
            if ogrs:
                secilen_ogr = st.selectbox("Yönetilecek Öğrenci:", ogrs)
                
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

                st.divider()
                st.markdown(f"### 🗓️ {secilen_ogr} — Kişiye Özel Haftalık Program Oluşturucu")
                st.caption("⚡ Ders seçtiğinizde alt konular 'Konu Çalışması' ve 'Soru Çözümü' olarak anında güncellenir. Kaydettiğiniz an öğrenci panelinde kişiye özel olarak görünür.")

                tum_dersler_listesi = list(YKS_KAPSAMLI_DERS_KONULAR.keys())
                
                c_s1, c_s2 = st.columns(2)
                with c_s1:
                    yeni_saat_araligi = st.text_input("Saat Dilimi:", value="09:00 - 10:00", key="dinamik_saat")
                with c_s2:
                    hedef_gun_sec = st.selectbox("Uygulanacak Gün:", ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"], key="dinamik_gun")
                
                c_s3, c_s4 = st.columns(2)
                with c_s3:
                    sec_ders_matris = st.selectbox("Ders / Aktivite Seçin:", tum_dersler_listesi, key="dinamik_ders_secim")
                
                mevcut_alt_konular = YKS_KAPSAMLI_DERS_KONULAR.get(sec_ders_matris, ["Genel Soru"])
                
                with c_s4:
                    sec_konu_matris = st.selectbox("Alt Konu / Detay Seçin:", mevcut_alt_konular, key="dinamik_konu_secim")

                if st.button("📥 Bu Hücreyi Tabloya İşle", type="primary", use_container_width=True):
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
                     st.success(f"🎉 {secilen_ogr} için {hedef_gun_sec} günü ({yeni_saat_araligi}) başarıyla kaydedildi ve öğrenci paneline eklendi!")
                     st.rerun()

                st.markdown(f"#### 📊 {secilen_ogr} — Canlı Excel Program Tablosu")
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
                    st.success(f"🎉 {secilen_ogr} adlı öğrencinin haftalık programı güncellendi ve paneline yansıtıldı!")

                st.markdown("#### 📥 Öğrencinin Programını İndir")
                df_koc_ind = pd.read_sql_query("SELECT saat_araligi AS 'Saat', pazartesi AS 'Pazartesi', sali AS 'Salı', carsamba AS 'Çarşamba', persembe AS 'Perşembe', cuma AS 'Cuma', cumartesi AS 'Cumartesi', pazar AS 'Pazar' FROM excel_program_matris WHERE ad_soyad = ?", conn, params=(secilen_ogr,))
                if not df_koc_ind.empty:
                    csv_data_koc = df_koc_ind.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Programı İndir (.csv)",
                        data=csv_data_koc,
                        file_name=f"{secilen_ogr}_Ders_Programi.csv",
                        mime="text/csv",
                        use_container_width=True,
                        key="koc_csv_ind"
                    )

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
                sec_ogr_adi_link = locals().get('secilen_ogr', 'Öğrenci')
                host_url = "https://blank-app-mtyl8rm3xgtksm5qer7qng.streamlit.app"
                share_url = f"{host_url}/?ogrenci={quote(sec_ogr_adi_link)}"
                st.markdown(f"### 💬 {sec_ogr_adi_link} WhatsApp Paylaşım Linki")
                st.code(share_url, language="text")
                st.link_button("💬 WhatsApp İle Gönder", f"https://api.whatsapp.com/send?text={quote(f'Soru linki: {share_url}')}")

    with main_tab3:
        st.markdown("## 👨‍👩‍👧‍👦 Veli Takip Ekranı")
        st.caption("Öğrencinin adını yazarak haftalık ders programını, günlük çözülen soru ve süre bilgilerini, ve deneme sonuçlarını detaylıca takip edebilirsiniz.")
        
        v_ad = st.text_input("Takip Edilecek Öğrenci Adı ve Soyadı:").strip().title()
        if v_ad:
            cursor.execute("SELECT ad_soyad FROM ogrenciler WHERE ad_soyad = ?", (v_ad,))
            if cursor.fetchone():
                st.success(f"🔍 **{v_ad}** adlı öğrencinin takip raporu yükleniyor...")
                
                # 1. HAFTALIK DERS PROGRAMI
                st.markdown("### 📅 Haftalık Ders Programı")
                df_veli_prog = pd.read_sql_query("SELECT saat_araligi AS 'Saat', pazartesi AS 'Pazartesi', sali AS 'Salı', carsamba AS 'Çarşamba', persembe AS 'Perşembe', cuma AS 'Cuma', cumartesi AS 'Cumartesi', pazar AS 'Pazar' FROM excel_program_matris WHERE ad_soyad = ?", conn, params=(v_ad,))
                if not df_veli_prog.empty:
                    st.dataframe(df_veli_prog, use_container_width=True)
                else:
                    st.info("ℹ️ Bu öğrenci için henüz haftalık ders programı oluşturulmamış.")

                st.divider()

                # 2. BUGÜNKÜ ÇÖZÜLEN SORU VE SÜRE BİLGİSİ
                bugun_str = str(datetime.date.today())
                st.markdown(f"### ⏱️ Bugünkü Çalışma Özeti ({bugun_str})")
                df_veli_gunluk = pd.read_sql_query("SELECT ders, konu, toplam_soru, sure, verim FROM gunluk_calisma WHERE ad_soyad = ? AND tarih = ?", conn, params=(v_ad, bugun_str))
                if not df_veli_gun_luk := df_veli_gunluk.empty:
                    pass
                if not df_veli_gunluk.empty:
                    toplam_bugun_soru = df_veli_gunluk['toplam_soru'].sum()
                    toplam_bugun_sure = df_veli_gunluk['sure'].sum()
                    
                    col_v1, col_v2 = st.columns(2)
                    with col_v1:
                        st.metric("🎯 Bugün Toplam Çözülen Soru", f"{toplam_bugun_soru} Soru")
                    with col_v2:
                        st.metric("⏳ Bugün Toplam Çalışma Süresi", f"{toplam_bugun_sure} Saat")
                    
                    st.dataframe(df_veli_gunluk, use_container_width=True)
                else:
                    st.info("ℹ️ Öğrenci bugün henüz günlük çalışma kaydı girmemiş.")

                st.divider()

                # 3. DENEME SONUÇLARI VE KOÇ ANALİZLERİ
                st.markdown("### 📊 Deneme Sınavı Sonuçları ve Yapay Zeka Koç Raporları")
                df_veli_deneme = pd.read_sql_query("SELECT tarih, yayin, toplam_net, koc_notu FROM denemeler WHERE ad_soyad = ? ORDER BY id DESC", conn, params=(v_ad,))
                if not df_veli_deneme.empty:
                    for _, d_row in df_veli_deneme.iterrows():
                        st.markdown(f"""
                        <div class="calc-card">
                            <strong>📌 {d_row['yayin']} — Toplam Net: {d_row['toplam_net']}</strong> <span style="font-size:12px; color:#64748b;">({d_row['tarih']})</span>
                            <div class="ai-analysis-box">{d_row['koc_notu']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("ℹ️ Öğrenci henüz kayıtlı deneme sonucu bulunmuyor.")

            else:
                st.error(f"❌ `{v_ad}` adında kayıtlı bir öğrenci bulunamadı. Lütfen tam adını kontrol edin.")