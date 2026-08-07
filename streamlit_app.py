import streamlit as st
import datetime
import sqlite3
import pandas as pd
import random
import base64
import hashlib
import os
import io
from urllib.parse import quote
from PIL import Image
import subprocess
import sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl"])
import openpyxl

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

def ilerleme_tablosu_excel_byte(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Ilerleme')
    return output.getvalue()

MOTIVASYON_SOZLERI = [
    "🌿 Sakin ol, derin bir nefes al ve adım adım ilerle. Disiplin başarıyı getirir!",
    "🚀 Başarı, her gün ertelemeden tekrarlanan küçük çabaların birikimidir!",
    "🎓 Bugün döktüğün her damla alın teri, hayalindeki okulun kapısını açar!"
]

HAM_DERS_KONULARI = {
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

EVRENSEL_DERS_KONULARI = {}
for ders_adi, konu_listesi in HAM_DERS_KONULARI.items():
    if "Mola" in ders_adi or "Yürüyüş" in ders_adi or "Yemeği" in ders_adi or "Özel Ders" in ders_adi:
        EVRENSEL_DERS_KONULARI[ders_adi] = konu_listesi
    else:
        genisletilmis = []
        for k in konu_listesi:
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

conn = sqlite3.connect(DB_FILE, check_same_thread=False, timeout=20)
cursor = conn.cursor()
cursor.execute("PRAGMA journal_mode=WAL;")

cursor.execute("""
CREATE TABLE IF NOT EXISTS ogrenciler (
    ad_soyad TEXT PRIMARY KEY,
    sifre TEXT,
    veli_pin TEXT DEFAULT '123456',
    sinav_turu TEXT DEFAULT 'YKS (TYT + AYT)',
    alan TEXT DEFAULT 'SAY (Sayısal)',
    hedef_uni TEXT DEFAULT '',
    hedef_bolum TEXT DEFAULT '',
    hedef_net FLOAT DEFAULT 80.0,
    hedef_sira TEXT DEFAULT ''
)
""")

try:
    cursor.execute("ALTER TABLE ogrenciler ADD COLUMN alan TEXT DEFAULT 'SAY (Sayısal)'")
    conn.commit()
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE ogrenciler ADD COLUMN veli_pin TEXT DEFAULT '123456'")
    conn.commit()
except sqlite3.OperationalError:
    pass

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
cursor.execute("CREATE TABLE IF NOT EXISTS gunluk_calisma (id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT, tarih TEXT, ders TEXT, konu TEXT, soru_sayisi INTEGER DEFAULT 0, konu_anlatim_sure INTEGER DEFAULT 0, soru_cozum_sure INTEGER DEFAULT 0)")
cursor.execute("CREATE TABLE IF NOT EXISTS konu_ilerleme (ad_soyad TEXT, ders TEXT, konu_adi TEXT, tamamlandi INTEGER DEFAULT 0, soru_miktari INTEGER DEFAULT 0, PRIMARY KEY (ad_soyad, ders, konu_adi))")

cursor.execute("CREATE TABLE IF NOT EXISTS yapilamayan_sorular (id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT, tarih TEXT, ders TEXT, konu TEXT, dosya_yolu TEXT, dosya_adi TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS denemeler (id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT, tarih TEXT, yayin TEXT, tur TEXT, toplam_net FLOAT, dosya_yolu TEXT DEFAULT '', dosya_adi TEXT DEFAULT '', koc_notu TEXT DEFAULT '')")
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
            st.markdown(f'<div class="ai-analysis-box">Soru İnceleme Aktif</div>', unsafe_allow_html=True)
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
                    reg_veli_pin = st.text_input("Veli Takip Şifresi Belirleyin (Veli Girişi İçin):", value="123456")
                    reg_alan = st.selectbox("Alanınız:", ["SAY (Sayısal)", "EA (Eşit Ağırlık)", "SÖZ (Sözel)", "DİL (Yabancı Dil)"])
                    reg_sinav = st.selectbox("Hazırlanılan Sınav:", ["YKS (TYT + AYT)", "TYT (Sadece TYT)", "LGS (8. Sınıf)"])

                    if st.form_submit_button("Hesabımı Oluştur", type="primary", use_container_width=True):
                        if reg_ad and reg_sifre:
                            cursor.execute("SELECT ad_soyad FROM ogrenciler WHERE ad_soyad = ?", (reg_ad,))
                            if cursor.fetchone():
                                st.error(f"⚠️ `{reg_ad}` zaten kayıtlı!")
                            else:
                                cursor.execute("INSERT INTO ogrenciler (ad_soyad, sifre, veli_pin, alan, sinav_turu) VALUES (?, ?, ?, ?, ?)",
                                               (reg_ad, make_hash(reg_sifre), reg_veli_pin, reg_alan, reg_sinav))
                                conn.commit()
                                st.session_state["aktif_ogrenci"] = reg_ad
                                st.rerun()
        else:
            col_o_head1, col_o_head2 = st.columns([0.8, 0.2])
            with col_o_head1:
                cursor.execute("SELECT sinav_turu, alan, hedef_uni, hedef_bolum FROM ogrenciler WHERE ad_soyad = ?", (aktif_ogr,))
                r_info = cursor.fetchone()
                ogr_sinav = r_info[0] if r_info else "YKS (TYT + AYT)"
                ogr_alan = r_info[1] if r_info else "SAY (Sayısal)"
                curr_uni = r_info[2] if (r_info and r_info[2]) else "Giresun Üniversitesi"
                curr_bolum = r_info[3] if (r_info and r_info[3]) else "Matematik"
                st.success(f"👤 Aktif Oturum: **{aktif_ogr}** | Alan: **{ogr_alan}** | Sınav: **{ogr_sinav}**")
            
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

                df_p = pd.read_sql_query("SELECT saat_araligi AS 'Saat', pazartesi AS 'Pazartesi', sali AS 'Salı', carsamba AS 'Çarşamba', persembe AS 'Perşembe', cuma AS 'Cuma', cumartesi AS 'Cumartesi', pazar AS 'Pazar' FROM excel_program_matris WHERE ad_soyad = ? ORDER BY saat_araligi ASC", conn, params=(aktif_ogr,))
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
                st.markdown(f"### ✅ Konu İlerleme & Soru Takip Tablosu — {aktif_ogr}")
                st.caption("📚 Her ders için konuları tamamlandığında tik atabilir ve çözdüğünüz soru miktarını yazarak kaydedebilirsiniz.")

                secilen_takip_ders = st.selectbox("İlerlemesini Görmek / Düzenlemek İstediğiniz Dersi Seçin:", list(HAM_DERS_KONULARI.keys()), key="takip_ders_secim")
                konu_listesi_ogrenci = HAM_DERS_KONULARI[secilen_takip_ders]

                takip_verileri = []
                for konu in konu_listesi_ogrenci:
                    cursor.execute("SELECT tamamlandi, soru_miktari FROM konu_ilerleme WHERE ad_soyad = ? AND ders = ? AND konu_adi = ?", (aktif_ogr, secilen_takip_ders, konu))
                    res = cursor.fetchone()
                    t_val = bool(res[0]) if res else False
                    s_val = int(res[1]) if res else 0
                    takip_verileri.append({
                        "Konu Adı": konu,
                        "Tamamlandı ✅": t_val,
                        "Çözülen Soru Miktarı": s_val
                    })

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
                        for _, row in edited_takip.iterrows():
                            k_adi = row["Konu Adı"]
                            tamam = 1 if row["Tamamlandı ✅"] else 0
                            soru_m = int(row["Çözülen Soru Miktarı"]) if pd.notna(row["Çözülen Soru Miktarı"]) else 0
                            cursor.execute("""
                                INSERT INTO konu_ilerleme (ad_soyad, ders, konu_adi, tamamlandi, soru_miktari)
                                VALUES (?, ?, ?, ?, ?)
                                ON CONFLICT(ad_soyad, ders, konu_adi) DO UPDATE SET tamamlandi = ?, soru_miktari = ?
                            """, (aktif_ogr, secilen_takip_ders, k_adi, tamam, soru_m, tamam, soru_m))
                        conn.commit()
                        st.success("🎉 İlerlemeniz başarıyla kaydedildi!")
                        st.rerun()

                st.markdown("---")
                st.markdown("#### 📥 İlerleme Tablosunu İndir (Excel / PDF)")
                df_tum_ilerleme = pd.read_sql_query("SELECT ders AS 'Ders', konu_adi AS 'Konu', CASE WHEN tamamlandi=1 THEN 'Evet' ELSE 'Hayır' END AS 'Tamamlandı', soru_miktari AS 'Soru Miktarı' FROM konu_ilerleme WHERE ad_soyad = ?", conn, params=(aktif_ogr,))
                
                if not df_tum_ilerleme.empty:
                    col_d1, col_d2 = st.columns(2)
                    
                    excel_data = ilerleme_tablosu_excel_byte(df_tum_ilerleme)
                    col_d1.download_button(
                        label="📥 Excel (.xlsx) İndir",
                        data=excel_data,
                        file_name=f"{aktif_ogr}_Ilerleme.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    
                    pdf_html = html_to_pdf_bytes(df_tum_ilerleme, aktif_ogr)
                    col_d2.download_button(
                        label="📥 PDF (.html / Yazdırılabilir) İndir",
                        data=pdf_html,
                        file_name=f"{aktif_ogr}_Ilerleme.html",
                        mime="text/html",
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
                        cursor.execute("""
                            INSERT INTO gunluk_calisma (ad_soyad, tarih, ders, konu, soru_sayisi, konu_anlatim_sure, soru_cozum_sure)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (aktif_ogr, str(s_tarih), secilen_ders, secilen_konu, int(girilen_soru), int(girilen_konu_sure), int(girilen_cozum_sure)))
                        conn.commit()
                        st.success(f"🎉 Başarıyla kaydedildi! ({secilen_ders} — {secilen_konu})")

            with tab_deneme:
                st.markdown(f"### 📊 Deneme Sınavı Sonuç Belgesi Yükleme — {aktif_ogr}")
                with st.form("deneme_yukleme_formu"):
                    dyayin = st.text_input("Deneme Yayın Adı (Örn: 3D Yayınları TYT Deneme):")
                    dnet = st.number_input("Toplam Net:", 0.0, 120.0, 75.0)
                    if st.form_submit_button("📤 Denemeyi Koçuma Gönder", type="primary", use_container_width=True) and dyayin:
                        cursor.execute("""
                            INSERT INTO denemeler (ad_soyad, tarih, yayin, tur, toplam_net, koc_notu)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (aktif_ogr, str(datetime.date.today()), dyayin, "Genel Deneme", float(dnet), "Koç değerlendirmesi bekleniyor."))
                        conn.commit()
                        st.success("🎉 Deneme başarıyla koçunuza gönderildi!")
                        st.rerun()

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
                
                st.markdown(f"### 📈 {secilen_ogr} — Öğrenci Konu İlerleme ve Soru Durumu")
                df_koc_ilerleme = pd.read_sql_query("SELECT ders AS 'Ders', konu_adi AS 'Konu', CASE WHEN tamamlandi=1 THEN '✅ Tamamlandı' ELSE '⏳ Devam Ediyor' END AS 'Durum', soru_miktari AS 'Çözülen Soru' FROM konu_ilerleme WHERE ad_soyad = ?", conn, params=(secilen_ogr,))
                if not df_koc_ilerleme.empty:
                    st.dataframe(df_koc_ilerleme, use_container_width=True)
                else:
                    st.info("ℹ️ Öğrenci henüz ilerleme tablosunda işaretleme yapmamış.")

                st.divider()
                st.markdown(f"### 🗓️ {secilen_ogr} — Kişiye Özel Haftalık Program Oluşturucu")
                
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
                with c_s3: sec_ders_matris = st.selectbox("Ders / Aktivite / Mola Seçin:", tum_dersler_listesi, key="dinamik_ders_secim")
                with c_s4: sec_konu_matris = st.selectbox("Alt Konu / Detay Seçin:", EVRENSEL_DERS_KONULARI.get(sec_ders_matris, ["Genel Soru"]), key="dinamik_konu_secim")

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
                     st.success(f"🎉 {secilen_ogr} için {hedef_gun_sec} günü ({yeni_saat_araligi}) kaydedildi!")
                     st.rerun()

                st.markdown(f"#### 📊 {secilen_ogr} — Canlı Excel Program Tablosu")
                df_matris = pd.read_sql_query("SELECT saat_araligi AS 'Saat Aralığı', pazartesi AS 'Pazartesi', sali AS 'Salı', carsamba AS 'Çarşamba', persembe AS 'Perşembe', cuma AS 'Cuma', cumartesi AS 'Cumartesi', pazar AS 'Pazar' FROM excel_program_matris WHERE ad_soyad = ? ORDER BY saat_araligi ASC", conn, params=(secilen_ogr,))
                
                if df_matris.empty:
                    df_matris = pd.DataFrame([{"Saat Aralığı": "08:00 - 09:00", "Pazartesi": "", "Salı": "", "Çarşamba": "", "Perşembe": "", "Cuma": "", "Cumartesi": "", "Pazar": ""}])

                edited_matris = st.data_editor(df_matris, num_rows="dynamic", use_container_width=True, height=450, key=f"excel_matris_editor_{secilen_ogr}")

                if st.button("💾 Tablodaki Tüm Değişiklikleri Kaydet", type="primary", use_container_width=True):
                    cursor.execute("DELETE FROM excel_program_matris WHERE ad_soyad = ?", (secilen_ogr,))
                    for _, row in edited_matris.iterrows():
                        s_ar = str(row.get("Saat Aralığı", "")).strip()
                        if s_ar and s_ar != "nan":
                            cursor.execute("""
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
                    conn.commit()
                    st.success("🎉 Program güncellendi!")
                    st.rerun()

    with main_tab3:
        st.markdown("## 👨‍👩‍👧‍👦 Veli Takip Ekranı")
        with st.form("veli_giris_formu"):
            v_ad = st.text_input("Öğrenci Adı ve Soyadı:").strip().title()
            v_sifre = st.text_input("Öğrencinin Verdiği Veli Şifresi (PIN):", type="password")
            veli_giris_buton = st.form_submit_button("Veli Paneline Giriş Yap", type="primary", use_container_width=True)

        if veli_giris_buton:
            if v_ad and v_sifre:
                cursor.execute("SELECT veli_pin FROM ogrenciler WHERE ad_soyad = ?", (v_ad,))
                ogr_kayit = cursor.fetchone()
                if ogr_kayit and v_sifre == (ogr_kayit[0] if ogr_kayit[0] else "123456"):
                    st.session_state[f"veli_dogrulanmis_{v_ad}"] = True
                    st.success(f"🔓 Giriş Başarılı! **{v_ad}** adlı öğrencinin paneli açılıyor...")
                    st.rerun()
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

            st.markdown("### ✅ Öğrenci Konu İlerleme Durumu")
            df_v_ilerleme = pd.read_sql_query("SELECT ders AS 'Ders', konu_adi AS 'Konu', CASE WHEN tamamlandi=1 THEN '✅ Tamamlandı' ELSE '⏳ Devam Ediyor' END AS 'Durum', soru_miktari AS 'Çözülen Soru' FROM konu_ilerleme WHERE ad_soyad = ?", conn, params=(v_ad,))
            if not df_v_ilerleme.empty:
                st.dataframe(df_v_ilerleme, use_container_width=True)
            else:
                st.info("ℹ️ Öğrenci henüz ilerleme tablosunda işlem yapmamış.")