import streamlit as st
import datetime
import psycopg2
from psycopg2 import pool
import pandas as pd
import random
import base64
import hashlib
import os
import warnings

warnings.filterwarnings('ignore', category=UserWarning)

st.set_page_config(
    page_title="YKS (TYT/AYT) - LGS KOÇLUK (DENİZ YILMAZ)",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

KARNE_DIR = "karne_yuklemeleri"
os.makedirs(KARNE_DIR, exist_ok=True)

SUPABASE_URI = "postgresql://postgres.ypftcgbwgcctaeljsvxf:DenizMelis160625.@aws-0-eu-central-1.pooler.supabase.com:6543/postgres"

@st.cache_resource
def get_connection_pool():
    return pool.ThreadedConnectionPool(1, 20, SUPABASE_URI)

class PooledConnection:
    def __init__(self, db_pool):
        self._pool = db_pool
        self.conn = self._pool.getconn()
    def close(self):
        self._pool.putconn(self.conn)
    def __getattr__(self, item):
        return getattr(self.conn, item)

def get_db_connection():
    return PooledConnection(get_connection_pool())

def tablo_olustur():
    conn = get_db_connection()
    cur = conn.cursor()
    
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
    try:
        cur.execute("ALTER TABLE ogrenciler ADD COLUMN IF NOT EXISTS sinif_grubu TEXT DEFAULT '12. Sınıf ve Mezun (2027 YKS)'")
        conn.commit()
    except Exception:
        conn.rollback()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ozel_universiteler (
        id SERIAL PRIMARY KEY,
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
    cur.execute("""
    CREATE TABLE IF NOT EXISTS gunluk_calisma (
        id SERIAL PRIMARY KEY, 
        ad_soyad TEXT, 
        tarih TEXT, 
        ders TEXT, 
        konu TEXT, 
        soru_sayisi INTEGER DEFAULT 0, 
        konu_anlatim_sure INTEGER DEFAULT 0, 
        soru_cozum_sure INTEGER DEFAULT 0
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS konu_ilerleme (
        ad_soyad TEXT, ders TEXT, konu_adi TEXT, 
        tamamlandi INTEGER DEFAULT 0, soru_miktari INTEGER DEFAULT 0, 
        PRIMARY KEY (ad_soyad, ders, konu_adi)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS yapilamayan_sorular (
        id SERIAL PRIMARY KEY, ad_soyad TEXT, tarih TEXT, ders TEXT, konu TEXT, dosya_yolu TEXT, dosya_adi TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS denemeler (
        id SERIAL PRIMARY KEY, ad_soyad TEXT, tarih TEXT, yayin TEXT, tur TEXT, 
        toplam_net FLOAT, dosya_yolu TEXT DEFAULT '', dosya_adi TEXT DEFAULT '', koc_notu TEXT DEFAULT ''
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS konu_puanlari (
        ad_soyad TEXT, konu_adi TEXT, puan INTEGER, PRIMARY KEY (ad_soyad, konu_adi)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS excel_program_matris (
        ad_soyad TEXT, 
        hafta_baslangici TEXT DEFAULT '2026-09-07', 
        saat_araligi TEXT, 
        pazartesi TEXT DEFAULT '', sali TEXT DEFAULT '', carsamba TEXT DEFAULT '', 
        persembe TEXT DEFAULT '', cuma TEXT DEFAULT '', cumartesi TEXT DEFAULT '', pazar TEXT DEFAULT ''
    )
    """)
    try:
        cur.execute("ALTER TABLE excel_program_matris ADD COLUMN IF NOT EXISTS hafta_baslangici TEXT DEFAULT '2026-09-07'")
        cur.execute("ALTER TABLE excel_program_matris DROP CONSTRAINT IF EXISTS excel_program_matris_pkey;")
        cur.execute("ALTER TABLE excel_program_matris ADD PRIMARY KEY (ad_soyad, hafta_baslangici, saat_araligi);")
        conn.commit()
    except Exception:
        conn.rollback()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS program_dosyalari (
        id SERIAL PRIMARY KEY, ad_soyad TEXT, yukleyen TEXT, tarih TEXT, dosya_yolu TEXT, dosya_adi TEXT
    )
    """)
    
    conn.commit()
    conn.close()

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
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, p, label, input, textarea, select, h1, h2, h3, h4, h5, h6 {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-gradient: linear-gradient(135deg, #090d16 0%, #111827 50%, #030712 100%);
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
            --bg-gradient: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 50%, #e2e8f0 100%);
            --text-color: #0f172a;
            --container-bg: #ffffff;
            --border-color: #e2e8f0;
            --input-bg: #ffffff;
            --input-text: #0f172a;
            --tab-bg: #ffffff;
            --yok-box-bg: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            --hero-bg: linear-gradient(135deg, #0284c7 0%, #6366f1 50%, #8b5cf6 100%);
        }
    }

    html, body, p, label, input, textarea, select {
        color: var(--text-color, #0f172a) !important;
    }

    #MainMenu, footer, header, .stDeployButton {display: none !important;}

    .stApp {
        background: var(--bg-gradient) !important;
        background-attachment: fixed !important;
    }

    .main .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 4rem !important;
        max-width: 1420px !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: var(--tab-bg, #ffffff) !important;
        padding: 10px;
        border-radius: 20px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.08);
        border: 1.5px solid var(--border-color, #cbd5e1) !important;
    }

    .stTabs [data-baseweb="tab"] {
        height: 52px;
        background-color: var(--container-bg, #ffffff) !important;
        border-radius: 14px;
        padding: 10px 20px;
        font-weight: 700 !important;
        font-size: 13.5px !important;
        color: var(--text-color, #0f172a) !important;
        border: 1px solid var(--border-color, #cbd5e1) !important;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%) !important;
        border: none !important;
        box-shadow: 0 8px 20px rgba(2, 132, 199, 0.35);
    }

    .stTabs [aria-selected="true"] span, .stTabs [aria-selected="true"] div {
        color: #ffffff !important;
    }

    input, textarea, select, div[data-baseweb="select"] {
        background-color: var(--input-bg, #ffffff) !important;
        color: var(--input-text, #0f172a) !important;
        border: 1.8px solid var(--border-color, #cbd5e1) !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
    }

    .hero-motivation-card {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #db2777 100%) !important;
        color: #ffffff !important;
        padding: 26px 30px;
        border-radius: 24px;
        font-weight: 700;
        margin-bottom: 24px;
        box-shadow: 0 15px 35px -10px rgba(124, 58, 237, 0.5);
    }

    .hero-motivation-card * {
        color: #ffffff !important;
    }

    .yok-net-box {
        background: var(--yok-box-bg) !important;
        border: 2.5px solid #3b82f6;
        border-radius: 20px;
        padding: 22px 26px;
        margin-bottom: 20px;
    }
    
    .yok-net-box * {
        color: var(--text-color, #0f172a) !important;
    }

    .program-header-box {
        background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%) !important;
        color: white !important;
        padding: 24px;
        border-radius: 20px;
        margin-bottom: 24px;
        text-align: center;
        box-shadow: 0 10px 25px rgba(2, 132, 199, 0.25);
    }
    
    .program-header-box * {
        color: #ffffff !important;
    }

    .renkli-kart-1 {
        background: linear-gradient(135deg, #0284c7 0%, #0ea5e9 100%);
        color: white;
        padding: 20px;
        border-radius: 18px;
        box-shadow: 0 8px 20px rgba(2, 132, 199, 0.25);
        text-align: center;
    }
    .renkli-kart-2 {
        background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
        color: white;
        padding: 20px;
        border-radius: 18px;
        box-shadow: 0 8px 20px rgba(124, 58, 237, 0.25);
        text-align: center;
    }
    .renkli-kart-3 {
        background: linear-gradient(135deg, #059669 100%, #10b981 100%);
        color: white;
        padding: 20px;
        border-radius: 18px;
        box-shadow: 0 8px 20px rgba(5, 150, 105, 0.25);
        text-align: center;
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
        return f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="550" type="application/pdf" style="border-radius:16px; border:1px solid #cbd5e1;"></iframe>'
    except Exception:
        return "<p style='color:red;'>PDF dosyası okunamadı.</p>"

def html_to_pdf_bytes(df, ogrenci_adi):
    html_content = f"""
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <title>{ogrenci_adi} - Ders Programı</title>
        <style>
            @media print {{
                body {{ padding: 0; }}
                button {{ display: none; }}
            }}
            body {{ font-family: 'Plus Jakarta Sans', Helvetica, Arial, sans-serif; padding: 30px; color: #0f172a; }}
            h2 {{ text-align: center; color: #0284c7; margin-bottom: 5px; }}
            p {{ text-align: center; color: #64748b; font-size: 12px; margin-bottom: 25px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; border-radius: 8px; overflow: hidden; }}
            th, td {{ border: 1px solid #cbd5e1; padding: 10px 12px; text-align: center; font-size: 11px; vertical-align: middle; }}
            th {{ background-color: #0284c7; color: white; font-weight: bold; }}
            tr:nth-child(even) {{ background-color: #f8fafc; }}
        </style>
    </head>
    <body>
        <h2>🎓 YKS KOÇLUK — {ogrenci_adi.upper()} DERS PROGRAMI</h2>
        <p>Deniz Yılmaz Gelişim Platformu | {datetime.date.today().strftime('%d.%m.%Y')}</p>
        {df.to_html(index=False, classes='table', border=0)}
        <div style="text-align: center; margin-top: 30px;">
            <button onclick="window.print()" style="background: #0284c7; color: white; border: none; padding: 12px 24px; font-size: 14px; font-weight: bold; border-radius: 8px; cursor: pointer;">🖨️ PDF Olarak Kaydet / Yazdır</button>
        </div>
    </body>
    </html>
    """
    return html_content.encode('utf-8')

def haftalik_program_toplu_pdf_bytes(df_full, ogrenci_adi):
    df_n = df_full.copy()
    df_n.columns = [str(c).strip().lower() for c in df_n.columns]
    
    saat_col = "saat_araligi" if "saat_araligi" in df_n.columns else ("saat" if "saat" in df_n.columns else df_n.columns[0])

    gunler = [
        ("Pazartesi", "pazartesi"),
        ("Salı", "sali"),
        ("Çarşamba", "carsamba"),
        ("Perşembe", "persembe"),
        ("Cuma", "cuma"),
        ("Cumartesi", "cumartesi"),
        ("Pazar", "pazar")
    ]
    
    gun_htmls = ""
    for g_adi, g_col in gunler:
        if g_col in df_n.columns:
            df_g = df_n[[saat_col, g_col]].copy()
            df_g = df_g[df_g[g_col].notna() & (df_g[g_col].astype(str).str.strip() != "")]
            if not df_g.empty:
                df_g.columns = ["Saat Aralığı", "Ders / Aktivite"]
                table_html = df_g.to_html(index=False, classes='table', border=0)
                gun_htmls += f"""
                <div style="margin-bottom: 25px;">
                    <h3 style="color: #0284c7; border-bottom: 2px solid #0284c7; padding-bottom: 5px; margin-bottom: 10px;">📌 {g_adi}</h3>
                    {table_html}
                </div>
                """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <title>{ogrenci_adi} - Toplu Haftalık Ders Programı</title>
        <style>
            @media print {{
                body {{ padding: 0; }}
                button {{ display: none; }}
            }}
            body {{ font-family: 'Plus Jakarta Sans', Helvetica, Arial, sans-serif; padding: 30px; color: #0f172a; }}
            h2 {{ text-align: center; color: #0284c7; margin-bottom: 5px; }}
            h3 {{ font-size: 14px; margin-top: 20px; }}
            p {{ text-align: center; color: #64748b; font-size: 12px; margin-bottom: 25px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 5px; border-radius: 8px; overflow: hidden; margin-bottom: 15px; }}
            th, td {{ border: 1px solid #cbd5e1; padding: 8px 12px; text-align: center; font-size: 11px; vertical-align: middle; }}
            th {{ background-color: #0284c7; color: white; font-weight: bold; }}
            tr:nth-child(even) {{ background-color: #f8fafc; }}
        </style>
    </head>
    <body>
        <h2>🎓 YKS KOÇLUK — {ogrenci_adi.upper()} TOPLU HAFTALIK DERS PROGRAMI</h2>
        <p>Deniz Yılmaz Gelişim Sistemleri | {datetime.date.today().strftime('%d.%m.%Y')}</p>
        {gun_htmls}
        <div style="text-align: center; margin-top: 30px;">
            <button onclick="window.print()" style="background: #0284c7; color: white; border: none; padding: 12px 24px; font-size: 14px; font-weight: bold; border-radius: 8px; cursor: pointer;">🖨️ PDF Olarak Kaydet / Yazdır</button>
        </div>
    </body>
    </html>
    """
    return html_content.encode('utf-8')

def calisma_raporu_html(df, ogrenci_adi, periyot_adi):
    return f"""
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <title>{ogrenci_adi} - Çalışma Raporu</title>
        <style>
            @media print {{
                body {{ padding: 0; }}
                button {{ display: none; }}
            }}
            body {{ font-family: 'Plus Jakarta Sans', Helvetica, Arial, sans-serif; padding: 30px; color: #0f172a; }}
            h2 {{ text-align: center; color: #0284c7; margin-bottom: 5px; }}
            p {{ text-align: center; color: #64748b; font-size: 12px; margin-bottom: 25px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; border-radius: 8px; overflow: hidden; }}
            th, td {{ border: 1px solid #cbd5e1; padding: 10px 12px; text-align: center; font-size: 11px; vertical-align: middle; }}
            th {{ background-color: #0284c7; color: white; font-weight: bold; }}
            tr:nth-child(even) {{ background-color: #f8fafc; }}
        </style>
    </head>
    <body>
        <h2>📊 {ogrenci_adi.upper()} — {periyot_adi.upper()} ÇALIŞMA RAPORU</h2>
        <p>Deniz Yılmaz Gelişim Platformu | Rapor Tarihi: {datetime.date.today().strftime('%d.%m.%Y')}</p>
        {df.to_html(index=False, classes='table', border=0)}
        <div style="text-align: center; margin-top: 30px;">
            <button onclick="window.print()" style="background: #0284c7; color: white; border: none; padding: 12px 24px; font-size: 14px; font-weight: bold; border-radius: 8px; cursor: pointer;">🖨️ PDF Olarak Kaydet / Yazdır</button>
        </div>
    </body>
    </html>
    """.encode('utf-8')

MOTIVASYON_SOZLERI = [
    "🌿 Sakin ol, derin bir nefes al ve adım adım ilerle. Disiplin başarıyı getirir!",
    "🚀 Başarı, her gün ertelemeden tekrarlanan küçük çabaların birikimidir!",
    "🎓 Bugün döktüğün her damla alın teri, hayalindeki okulun kapısını açar!"
]

HAM_DERS_KONULARI = {
    "🌅 Günlük Rutinler": [
        "Paragraf 25 Soru + Problem 20 Soru"
    ],
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
    "👨‍🏫 Özel Ders": [
        "Özel Ders - Birebir Konu Anlatımı",
        "Özel Ders - Soru Çözüm Kampı",
        "Özel Ders - Ödev Kontrolü & Tekrar"
    ],
    "📖 TYT Türkçe": [
        "Sözcükte Anlam",
        "Cümlede Anlam",
        "Paragrafta Anlam ve Yapı",
        "Ses Bilgisi",
        "Yazım Kuralları",
        "Noktalama İşaretleri",
        "Sözcük Türleri (İsim, Sıfat, Zamir, Zarf, Edat, Bağlaç)",
        "Fiiller, Ek Fiil ve Fiilimsi",
        "Cümlenin Ögeleri",
        "Cümle Çeşitleri",
        "Anlatım Bozuklukları"
    ],
    "📐 TYT Matematik": [
        "Temel Kavramlar ve Sayı Kümeleri",
        "Sayı Basamakları",
        "Bölme ve Bölünebilme",
        "EBOB - EKOK",
        "Rasyonel Sayılar",
        "Basit Eşitsizlikler",
        "Mutlak Değer",
        "Üslü İfadeler",
        "Köklü İfadeler",
        "Çarpanlara Ayırma",
        "Oran - Orantı",
        "Denklem Çözme",
        "Problemler (Sayı, Kesir, Yaş, İşçi, Hız, Yüzde, Karışım, Grafik)",
        "Kümeler ve Kartezyen Çarpım",
        "Mantık",
        "Fonksiyonlar",
        "Polinomlar",
        "Veri, Sayma ve Olasılık"
    ],
    "📏 TYT Geometri": [
        "Doğruda ve Üçgende Açılar",
        "Özel Üçgenler (Dik, İkizkenar, Eşkenar)",
        "Üçgende Açıortay, Kenarortay ve Benzerlik",
        "Üçgende Alan ve Açı-Kenar Bağıntıları",
        "Çokgenler ve Dörtgenler",
        "Özel Dörtgenler (Paralelkenar, Eşkenar Dörtgen, Dikdörtgen, Kare, Yamuk)",
        "Çember ve Daire",
        "Katı Cisimler (Prizma, Piramit, Silindir, Koni, Küre)",
        "Analitik Geometri (Nokta ve Doğru Analitiği)"
    ],
    "⚡ TYT Fizik": [
        "Fizik Bilimine Giriş",
        "Madde ve Özellikleri",
        "Basınç ve Kaldırma Kuvveti",
        "Isı, Sıcaklık ve Genleşme",
        "Hareket ve Kuvvet (Newton Yasaları)",
        "İş, Güç ve Enerji",
        "Elektrostatik ve Elektrik Akımı",
        "Manyetizma",
        "Dalgalar",
        "Optik"
    ],
    "🧪 TYT Kimya": [
        "Kimya Bilimi",
        "Atom ve Periyodik Sistem",
        "Türler Arası Etkileşimler",
        "Maddenin Halleri",
        "Kimyanın Temel Kanunları ve Kimyasal Hesaplamalar",
        "Karışımlar",
        "Asitler, Bazlar ve Tuzlar",
        "Kimya Her Yerde"
    ],
    "🧬 TYT Biyoloji": [
        "Canlıların Ortak Özellikleri ve Temel Bileşenler",
        "Hücre ve Organelleri",
        "Madde Geçişleri",
        "Hücre Bölünmeleri (Mitoz ve Mayoz)",
        "Kalıtım ve Evrim",
        "Ekoloji"
    ],
    "📜 TYT Tarih": [
        "Tarih Bilimi",
        "İlk Çağ Medeniyetleri",
        "İslamiyet Tarihi ve Uygarlığı",
        "Türklerin İslamiyet'i Kabulü ve İlk Türk Devletleri",
        "Osmanlı Devleti Kuruluş ve Yükselme",
        "Osmanlı Kültür ve Medeniyeti",
        "Milli Mücadele Dönemi",
        "Atatürk İnkılap ve İlkeleri"
    ],
    "🌍 TYT Coğrafya": [
        "Doğa ve İnsan & Harita Bilgisi",
        "Dünyanın Şekli ve Hareketleri",
        "İklim Bilgisi",
        "İç ve Dış Kuvvetler",
        "Nüfus ve Yerleşme",
        "Ulaşım Yolları ve Göç",
        "Afetler"
    ],
    "🧠 TYT Felsefe": [
        "Felsefeyi Tanıma",
        "Bilgi Felsefesi (Epistemoloji)",
        "Varlık Felsefesi (Ontoloji)",
        "Ahlak Felsefesi",
        "Din, Siyaset ve Sanat Felsefesi"
    ],
    "🕌 TYT Din Kültürü": [
        "İnanç",
        "İbadet",
        "Ahlak ve Değerler",
        "Hz. Muhammed'in Hayatı, Örnekliği ve Hz. Muhammed",
        "Vahiy ve Akıl"
    ],
    "📐 AYT Matematik": [
        "İkinci Dereceden Denklemler ve Karmaşık Sayılar",
        "Parabol",
        "İkinci Dereceden Eşitsizlikler",
        "Logaritma",
        "Diziler",
        "Trigonometri",
        "Limit ve Süreklilik",
        "Türev",
        "İntegral ve Alan"
    ],
    "📏 AYT Geometri": [
        "Çemberin Analitik İncelenmesi",
        "Dönüşüm Geometrisi",
        "Trigonometri Geometri Uygulamaları"
    ],
    "⚡ AYT Fizik": [
        "Vektörler ve Bağıl Hareket",
        "Dinamik (Newton'ın Hareket Yasaları)",
        "Bir Boyutta ve İki Boyutta Sabit İvmeli Hareket (Atışlar)",
        "İş, Güç ve Enerji (AYT)",
        "İtme ve Çizgisel Momentum",
        "Tork, Denge ve Kütle Merkezi",
        "Basit Makineler",
        "Elektriksel Kuvvet, Elektrik Alan ve Potansiyel",
        "Sığalar (Kondansatörler)",
        "Manyetik Alan ve Manyetik Kuvvet",
        "İndüksiyon, Özindüksiyon ve Alternatif Akım",
        "Çembersel Hareket ve Kepler Yasaları",
        "Basit Harmonik Hareket",
        "Dalga Mekaniği (Girişim, Kırınım) ve Elektromanyetik Dalgalar",
        "Atom Fiziği, Radyoaktivite ve Modern Fizik"
    ],
    "🧪 AYT Kimya": [
        "Modern Atom Teorisi",
        "Gazlar",
        "Sıvı Çözeltiler ve Koligatif Özellikler",
        "Kimyasal Tepkimelerde Enerji",
        "Kimyasal Tepkimelerde Hız",
        "Kimyasal Denge",
        "Sulu Çözeltilerde Denge (Asit-Baz ve KÇ)",
        "Elektrokimya (Piller ve Elektroliz)",
        "Organik Kimyaya Giriş",
        "Hidrokarbonlar",
        "Fonksiyonel Gruplar ve Organik Bileşikler"
    ],
    "🧬 AYT Biyoloji": [
        "Sinir Sistemi ve Endokrin Sistem",
        "Duyu Organları",
        "Destek ve Hareket Sistemi",
        "Sindirim, Dolaşım ve Solunum Sistemi",
        "Boşaltım Sistemi ve Üreme Sistemi",
        "Nükleik Asitler ve Protein Sentezi",
        "Fotosentez ve Kemosentez",
        "Hücresel Solunum",
        "Bitki Biyolojisi",
        "Canlılar ve Çevre (Ekoloji AYT)"
    ],
    "📖 AYT Türk Dili ve Edebiyatı": [
        "İslamiyet Öncesi Türk Edebiyatı ve Geçiş Dönemi",
        "Halk Edebiyatı",
        "Divan Edebiyatı",
        "Tanzimat Dönemi Edebiyatı",
        "Servet-i Fünun ve Fecr-i Âti Edebiyatı",
        "Milli Edebiyat Dönemi",
        "Cumhuriyet Dönemi Şiir",
        "Cumhuriyet Dönemi Roman ve Hikaye",
        "Tiyatro, Mektup, Anı, Makale ve Söyleşi"
    ],
    "📜 AYT Tarih": [
        "Dünya Gücü Osmanlı (1453-1600)",
        "Arayış Yılları (17. Yüzyıl)",
        "18. Yüzyılda Değişim ve Diplomasi",
        "En Uzun Yüzyıl (19. Yüzyıl)",
        "20. Yüzyılda Osmanlı Devleti",
        "I. Dünya Savaşı ve Mondros",
        "Kurtuluş Savaşı Hazırlık Dönemi",
        "I. TBMM Dönemi ve Kurtuluş Savaşı Muharebeleri",
        "Atatürkçülük ve Türk İnkılabı",
        "İki Savaş Arası Dönem (1929 Krizi vb.)",
        "II. Dünya Savaşı Dönemi ve Soğuk Savaş"
    ],
    "🌍 AYT Coğrafya": [
        "Ekosistem ve Madde Döngüleri",
        "Biyomlar",
        "Türkiye'nin Su ve Toprak Varlığı",
        "Geçmişten Geleceğe Şehir ve Ekonomi",
        "Türkiye Ekonomisi (Tarım, Maden, Sanayi, Ulaşım)",
        "Türkiye'nin Jeopolitik Konumu",
        "Küresel ve Bölgesel Örgütler",
        "Çevre Sorunları ve Küresel İklim Değişikliği"
    ]
}

OSYM_SORU_DAGILIMLARI = {
    "Paragraf 25 Soru + Problem 20 Soru": "Günlük Alışkanlık",
    "Sözcükte Anlam": "Ort. 2-3 Soru",
    "Cümlede Anlam": "Ort. 2 Soru",
    "Paragrafta Anlam ve Yapı": "Ort. 14-16 Soru",
    "Ses Bilgisi": "Ort. 1 Soru",
    "Yazım Kuralları": "Ort. 2 Soru",
    "Noktalama İşaretleri": "Ort. 2 Soru",
    "Temel Kavramlar ve Sayı Kümeleri": "Ort. 3-4 Soru",
    "Sayı Basamakları": "Ort. 1 Soru",
    "Bölme ve Bölünebilme": "Ort. 1 Soru",
    "EBOB - EKOK": "Ort. 1 Soru",
    "Rasyonel Sayılar": "Ort. 1 Soru",
    "Basit Eşitsizlikler": "Ort. 1 Soru",
    "Mutlak Değer": "Ort. 1 Soru",
    "Üslü İfadeler": "Ort. 1-2 Soru",
    "Köklü İfadeler": "Ort. 1 Soru",
    "Fonksiyonlar": "Ort. 2-3 Soru",
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
        if "Mola" in ders_adi or "Yemek" in ders_adi or "Branş Denemeleri" in ders_adi or "Günlük Rutinler" in ders_adi:
            genisletilmis.append(k)
        else:
            genisletilmis.append(f"{k} — Konu Çalışması")
            genisletilmis.append(f"{k} — Soru Çözümü")
    EVRENSEL_DERS_KONULARI[ders_adi] = genisletilmis

UNIVERSITE_LISTESI = [
    "Acıbadem Mehmet Ali Aydınlar Üniversitesi (İstanbul)", "Adana Alparslan Türkeş Bilim ve Teknoloji Üniversitesi", 
    "Adıyaman Üniversitesi", "Afyon Kocatepe Üniversitesi", "Afyonkarahisar Sağlık Bilimleri Üniversitesi", 
    "Akdeniz Üniversitesi (Antalya)", "Ankara Üniversitesi", "Atatürk Üniversitesi (Erzurum)", 
    "Boğaziçi Üniversitesi (İstanbul)", "Bursa Uludağ Üniversitesi", "Çukurova Üniversitesi (Adana)", 
    "Dokuz Eylül Üniversitesi (İzmir)", "Ege Üniversitesi (İzmir)", "Fırat Üniversitesi (Elazığ)", 
    "Galatasaray Üniversitesi (İstanbul)", "Gazi Üniversitesi (Ankara)", "Giresun Üniversitesi", 
    "Hacettepe Üniversitesi (Ankara)", "İhsan Doğramacı Bilkent Üniversitesi (Ankara)", "İstanbul Üniversitesi", 
    "İstanbul Üniversitesi-Cerrahpaşa", "İstanbul Teknik Üniversitesi (İTÜ)", "Koç Üniversitesi (İstanbul)", 
    "Marmara Üniversitesi (İstanbul)", "Orta Doğu Teknik Üniversitesi (ODTÜ - Ankara)", "Yıldız Teknik Üniversitesi (İstanbul)"
]

BOLUM_KATEGORILERI = {
    "SAY (Sayısal)": [
        "Matematik", "Tıp Fakültesi", "Bilgisayar Mühendisliği", "Elektrik-Elektronik Mühendisliği", 
        "Endüstri Mühendisliği", "Makine Mühendisliği", "Yazılım Mühendisliği", "Mimarlık", 
        "Diş Hekimliği Fakültesi", "Eczacılık Fakültesi", "Hemşirelik"
    ],
    "EA (Eşit Ağırlık)": [
        "Hukuk Fakültesi", "Psikoloji", "İşletme", "İktisat", 
        "Yönetim Bilişim Sistemleri", "Rehberlik ve Psikolojik Danışmanlık (PDR)", "Sınıf Öğretmenliği"
    ],
    "SÖZ (Sözel)": [
        "Türk Dili ve Edebiyatı", "Tarih", "Gastronomi ve Mutfak Sanatları", "İlahiyat Fakültesi", "Türkçe Öğretmenliği"
    ],
    "DİL (Yabancı Dil)": [
        "İngilizce Öğretmenliği", "Tercümanlık ve Çeviribilim", "İngiliz Dili ve Edebiyatı"
    ]
}

st.markdown("""
<div style="text-align: center; padding: 15px 0 20px 0;">
    <span style="font-size: 48px; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.15));">🎓</span>
    <h1 style="margin: 5px 0 0 0; font-weight: 800; font-size: 28px; background: linear-gradient(135deg, #0284c7 0%, #4f46e5 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">YKS (TYT/AYT) & LGS KOÇLUK PLATFORMU</h1>
    <p style="margin: 5px 0 0 0; font-size: 14px; color: #0284c7; font-weight: 700; letter-spacing: 1px;">DENİZ YILMAZ GELİŞİM SİSTEMİ</p>
</div>
""", unsafe_allow_html=True)

link_ogrenci = st.query_params.get("ogrenci", None)

if link_ogrenci:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 20px 26px; border-radius: 20px; margin-bottom: 24px; box-shadow: 0 10px 25px rgba(16, 185, 129, 0.25);">
        <h3 style="margin:0; font-size:20px; font-weight:800; color:white !important;">👨‍🏫 Öğretmen Soru İnceleme Ekranı</h3>
        <p style="margin:6px 0 0 0; opacity:0.95; color:white !important;"><strong>{link_ogrenci}</strong> öğrencisinin çözemediği sorular listelenmektedir.</p>
    </div>
    """, unsafe_allow_html=True)
    
    conn_link = get_db_connection()
    df_link_sorular = pd.read_sql_query('SELECT id, tarih, ders, konu, dosya_yolu, dosya_adi FROM yapilamayan_sorular WHERE ad_soyad = %s ORDER BY id DESC', conn_link.conn, params=(link_ogrenci,))
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
                    <div style="font-size:11px; letter-spacing:2px; font-weight:800; color:rgba(255,255,255,0.85); margin-bottom:6px;">⚡ GÜNÜN MOTİVASYON MESAJI</div>
                    <div style="font-size:17px; font-weight:800;">"{st.session_state['motivasyon_sozu']}"</div>
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
                cur_h.execute("SELECT ad_soyad FROM ogrenciler WHERE ad_soyad = %s AND onaylandi = 1", (hatirlanan_ogr,))
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
                    login_sifre = st.text_input("Şifre / PIN:", type="password")
                    beni_hatirla_ogr = st.checkbox("Beni Hatırla")
                    
                    if st.form_submit_button("Giriş Yap", type="primary", use_container_width=True):
                        if login_ad and login_sifre:
                            conn_l = get_db_connection()
                            cur_l = conn_l.cursor()
                            cur_l.execute("SELECT sifre, onaylandi FROM ogrenciler WHERE ad_soyad = %s", (login_ad,))
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
                                    st.warning("⏳ Hesabınız koçunuz tarafından henüz onaylanmamıştır.")
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
                            cur_reg.execute("SELECT ad_soyad FROM ogrenciler WHERE ad_soyad = %s", (reg_ad,))
                            var_mi = cur_reg.fetchone()
                            if var_mi:
                                st.error(f"⚠️ `{reg_ad}` zaten kayıtlı!")
                                conn_reg.close()
                            else:
                                cur_reg.execute("INSERT INTO ogrenciler (ad_soyad, sifre, veli_pin, alan, sinav_turu, koc_adi, onaylandi) VALUES (%s, %s, %s, %s, %s, %s, 0)",
                                               (reg_ad, make_hash(reg_sifre), reg_veli_pin, reg_alan, reg_sinav, reg_koc))
                                conn_reg.commit()
                                conn_reg.close()
                                st.success("🎉 Kaydınız oluşturuldu! Seçtiğiniz koç onayladıktan sonra giriş yapabileceksiniz.")
        else:
            col_o_head1, col_o_head2 = st.columns([0.8, 0.2])
            with col_o_head1:
                conn_inf = get_db_connection()
                cur_inf = conn_inf.cursor()
                cur_inf.execute("SELECT sinav_turu, alan, hedef_uni, hedef_bolum, koc_adi FROM ogrenciler WHERE ad_soyad = %s", (aktif_ogr,))
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
                st.caption("🏛️ Üniversitenizi ve bölümünüzü seçerek ÖSYM / YÖK Atlas verilerine göre gereken taban netleri ve başarı sırasını görüntüleyin.")

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
                cur_bol.execute("SELECT bolum_adi FROM ozel_universiteler WHERE universite_adi = %s AND kategori = %s", (secilen_hedef_uni, secilen_kategori))
                ozel_bolumler = [r[0] for r in cur_bol.fetchall()]
                conn_bol.close()

                toplam_bolum_listesi = sorted(list(set(BOLUM_KATEGORILERI[secilen_kategori] + ozel_bolumler)))

                with col_h_u3:
                    b_idx = toplam_bolum_listesi.index(curr_bolum) if curr_bolum in toplam_bolum_listesi else 0
                    secilen_hedef_bolum = st.selectbox("Bölüm:", toplam_bolum_listesi, index=b_idx)

                conn_det = get_db_connection()
                cur_det = conn_det.cursor()
                cur_det.execute("SELECT taban_net, taban_sira, tyt_net, ayt_net FROM ozel_universiteler WHERE universite_adi = %s AND bolum_adi = %s", (secilen_hedef_uni, secilen_hedef_bolum))
                ozel_kayit = cur_det.fetchone()
                conn_det.close()

                if ozel_kayit:
                    t_net, t_sira, tyt_gerekli, ayt_gerekli = ozel_kayit[0], ozel_kayit[1], ozel_kayit[2], ozel_kayit[3]
                else:
                    t_net, t_sira, tyt_gerekli, ayt_gerekli = 85.0, "50.000", 80.0, 52.0

                st.markdown(f"""
                <div class="yok-net-box">
                    <div style="font-size:16px; font-weight:800; margin-bottom:8px;">🏛️ {secilen_hedef_uni} — {secilen_hedef_bolum}</div>
                    <div style="display: flex; gap: 20px; flex-wrap: wrap; margin-top: 10px;">
                        <div style="background: var(--container-bg); padding: 10px 15px; border-radius: 12px; border: 1px solid var(--border-color); flex: 1; min-width: 140px;">
                            <span style="font-size: 11px; font-weight: 700;">YÖK ATLAS TABAN NET</span><br>
                            <span style="font-size: 18px; font-weight: 800; color: #0284c7;">{t_net} Net</span>
                        </div>
                        <div style="background: var(--container-bg); padding: 10px 15px; border-radius: 12px; border: 1px solid var(--border-color); flex: 1; min-width: 140px;">
                            <span style="font-size: 11px; font-weight: 700;">YÖK ATLAS BAŞARI SIRASI</span><br>
                            <span style="font-size: 18px; font-weight: 800; color: #16a34a;">İlk {t_sira}</span>
                        </div>
                        <div style="background: var(--container-bg); padding: 10px 15px; border-radius: 12px; border: 1px solid var(--border-color); flex: 1; min-width: 140px;">
                            <span style="font-size: 11px; font-weight: 700;">GEREKLİ ORTALAMA TYT</span><br>
                            <span style="font-size: 18px; font-weight: 800; color: #9333ea;">~{tyt_gerekli} Net</span>
                        </div>
                        <div style="background: var(--container-bg); padding: 10px 15px; border-radius: 12px; border: 1px solid var(--border-color); flex: 1; min-width: 140px;">
                            <span style="font-size: 11px; font-weight: 700;">GEREKLİ ORTALAMA AYT</span><br>
                            <span style="font-size: 18px; font-weight: 800; color: #ea580c;">~{ayt_gerekli} Net</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button("🚀 Bu Hedefi Profilime Kaydet ve Netlerimi Planla", type="primary", use_container_width=True):
                    conn_up = get_db_connection()
                    cur_up = conn_up.cursor()
                    cur_up.execute("UPDATE ogrenciler SET hedef_uni = %s, hedef_bolum = %s, hedef_net = %s WHERE ad_soyad = %s", 
                                   (secilen_hedef_uni, f"{secilen_hedef_bolum} ({secilen_kategori})", float(t_net), aktif_ogr))
                    conn_up.commit()
                    conn_up.close()
                    st.success(f"🎉 Hedefiniz başarıyla güncellendi: {secilen_hedef_uni} - {secilen_hedef_bolum} ({t_net} Net)!")
                    st.rerun()

            with tab_program:
                st.markdown(f"""
                <div class="program-header-box">
                    <h2 style="margin:0; font-size:22px; font-weight:800; color:white !important;">📅 {aktif_ogr.upper()} — DERS PROGRAMI MERKEZİ</h2>
                    <p style="margin:5px 0 0 0; font-size:13px; opacity:0.9; color:white !important;">Bu haftanın programını ve günlük derslerinizi buradan takip edebilirsiniz.</p>
                </div>
                """, unsafe_allow_html=True)

                bugun_tarih = datetime.date.today()
                bu_hafta_pazartesi = bugun_tarih - datetime.timedelta(days=bugun_tarih.weekday())
                secilen_hafta_str = str(bu_hafta_pazartesi)

                ogr_prog_alt_secim = st.radio("Program Görünümü:", ["☀️ Bugünün Programı", "📅 Tüm Haftalık Program"], horizontal=True, key="ogr_prog_alt_secim_key")

                gun_indexleri = {0: "pazartesi", 1: "sali", 2: "carsamba", 3: "persembe", 4: "cuma", 5: "cumartesi", 6: "pazar"}
                gun_isimleri_tr = {0: "Pazartesi", 1: "Salı", 2: "Çarşamba", 3: "Perşembe", 4: "Cuma", 5: "Cumartesi", 6: "Pazar"}
                bugun_idx = bugun_tarih.weekday()
                bugun_kolun = gun_indexleri[bugun_idx]
                bugun_adi_str = gun_isimleri_tr[bugun_idx]

                if ogr_prog_alt_secim == "☀️ Bugünün Programı":
                    st.markdown(f"#### ☀️ Bugün ({bugun_adi_str} - {bugun_tarih.strftime('%d.%m.%Y')}) Programı")
                    
                    df_bugun = pd.DataFrame(columns=["Saat Aralığı", "Ders / Aktivite"])
                    try:
                        conn_bugun = get_db_connection()
                        query_bugun = f'SELECT saat_araligi AS "Saat Aralığı", {bugun_kolun} AS "Ders / Aktivite" FROM excel_program_matris WHERE ad_soyad = %s AND hafta_baslangici = %s AND {bugun_kolun} IS NOT NULL AND {bugun_kolun} != \'\' ORDER BY saat_araligi ASC'
                        df_bugun = pd.read_sql_query(query_bugun, conn_bugun.conn, params=(aktif_ogr, secilen_hafta_str))
                        conn_bugun.close()
                    except Exception:
                        pass

                    if not df_bugun.empty:
                        st.dataframe(df_bugun, use_container_width=True, hide_index=True)
                        
                        st.markdown("---")
                        st.markdown("#### 📥 Bugünün Programını İndir")
                        html_bytes_bugun = html_to_pdf_bytes(df_bugun, f"{aktif_ogr} - {bugun_adi_str}")
                        st.download_button(
                            label="📥 Bugünün Programını PDF İndir (.html / Tarayıcıda Aç & Yazdır)",
                            data=html_bytes_bugun,
                            file_name=f"{aktif_ogr}_{bugun_adi_str}_Bugunun_Programi.html",
                            mime="text/html",
                            use_container_width=True
                        )
                    else:
                        st.info(f"ℹ️ Bu hafta ({secilen_hafta_str} haftası) için bugün ({bugun_adi_str}) planlanmış ders bulunmuyor.")
                else:
                    st.markdown(f"#### 📅 Bu Haftanın Programı ({secilen_hafta_str} Haftası)")
                    try:
                        conn_p = get_db_connection()
                        df_p_full = pd.read_sql_query('SELECT saat_araligi, pazartesi, sali, carsamba, persembe, cuma, cumartesi, pazar FROM excel_program_matris WHERE ad_soyad = %s AND hafta_baslangici = %s ORDER BY saat_araligi ASC', conn_p.conn, params=(aktif_ogr, secilen_hafta_str))
                        conn_p.close()
                    except Exception:
                        df_p_full = pd.DataFrame()

                    if not df_p_full.empty:
                        haftanin_gunleri = [
                            ("Pazartesi", "pazartesi"),
                            ("Salı", "sali"),
                            ("Çarşamba", "carsamba"),
                            ("Perşembe", "persembe"),
                            ("Cuma", "cuma"),
                            ("Cumartesi", "cumartesi"),
                            ("Pazar", "pazar")
                        ]
                        
                        temiz_haftalik_tablolar = {}
                        for g_adi, g_col in haftanin_gunleri:
                            df_g = df_p_full[["saat_araligi", g_col]].copy()
                            df_g = df_g[df_g[g_col].notna() & (df_g[g_col].astype(str).str.strip() != "")]
                            if not df_g.empty:
                                df_g.columns = ["Saat Aralığı", "Ders / Aktivite"]
                                temiz_haftalik_tablolar[g_adi] = df_g

                        if temiz_haftalik_tablolar:
                            for g_adi, df_g in temiz_haftalik_tablolar.items():
                                st.markdown(f"##### 📌 {g_adi}")
                                st.dataframe(df_g, use_container_width=True, hide_index=True)
                                st.markdown("")
                            
                            st.markdown("---")
                            html_bytes_ogr = haftalik_program_toplu_pdf_bytes(df_p_full, aktif_ogr)
                            st.download_button(
                                label="📥 Bu Haftanın Programını Toplu PDF Olarak İndir / Yazdır",
                                data=html_bytes_ogr,
                                file_name=f"{aktif_ogr}_Haftalik_Ders_Programi.html",
                                mime="text/html",
                                use_container_width=True
                            )
                        else:
                            st.info(f"ℹ️ Sevgili {aktif_ogr}, koçun henüz bu hafta için ders eklemedi.")
                    else:
                        st.info(f"ℹ️ Sevgili {aktif_ogr}, koçun henüz bu hafta için program kaydetmedi.")

            with tab_ilerleme:
                st.markdown(f"### ✅ Konu İlerleme, Soru Takibi & ÖSYM Soru Dağılımı — {aktif_ogr}")
                secilen_takip_ders = st.selectbox("İlerlemesini Görmek / Düzenlemek İstediğiniz Dersi Seçin:", list(HAM_DERS_KONULARI.keys()), key="takip_ders_secim")
                konu_listesi_ogrenci = HAM_DERS_KONULARI[secilen_takip_ders]

                conn_t = get_db_connection()
                cur_t = conn_t.cursor()
                takip_verileri = []
                for konu in konu_listesi_ogrenci:
                    cur_t.execute("SELECT tamamlandi, soru_miktari FROM konu_ilerleme WHERE ad_soyad = %s AND ders = %s AND konu_adi = %s", (aktif_ogr, secilen_takip_ders, konu))
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
                                VALUES (%s, %s, %s, %s, %s)
                                ON CONFLICT(ad_soyad, ders, konu_adi) DO UPDATE SET tamamlandi = EXCLUDED.tamamlandi, soru_miktari = EXCLUDED.soru_miktari
                            """, (aktif_ogr, secilen_takip_ders, k_adi, tamam, soru_m))
                        conn_sv.commit()
                        conn_sv.close()
                        st.success("🎉 İlerlemeniz başarıyla kaydedildi!")
                        st.rerun()

            with tab_gunluk:
                st.markdown(f"### 📝 Günlük Çalışma Girişi — {aktif_ogr}")
                s_tarih = st.date_input("Çalışma Tarihi:", datetime.date.today(), key="gunluk_tarih_inp")
                
                aktif_giris_dersleri = list(EVRENSEL_DERS_KONULARI.keys())

                secilen_ders = st.selectbox("Ders Seçin:", aktif_giris_dersleri, key="gunluk_ders_secim")
                konu_listesi_secim = EVRENSEL_DERS_KONULARI.get(secilen_ders, ["Genel Konu Çalışması"])
                secilen_konu = st.selectbox("Konu Seçin:", konu_listesi_secim, key="gunluk_konu_secim")

                col_gc1, col_gc2, col_gc3 = st.columns(3)
                with col_gc1: girilen_soru = st.number_input("Çözülen Soru Sayısı:", 0, 500, 20, step=1, key="gunluk_soru_inp")
                with col_gc2: girilen_konu_sure = st.number_input("Konu Anlatımı Süresi (Dakika):", 0, 1440, 45, step=1, key="gunluk_konu_sure_inp")
                with col_gc3: girilen_cozum_sure = st.number_input("Soru Çözümü Süresi (Dakika):", 0, 1440, 45, step=1, key="gunluk_cozum_sure_inp")

                if st.button("🚀 Çalışmayı Kaydet", type="primary", use_container_width=True, key="gunluk_kaydet_btn"):
                    conn_g = get_db_connection()
                    cur_g = conn_g.cursor()
                    cur_g.execute("""
                        INSERT INTO gunluk_calisma (ad_soyad, tarih, ders, konu, soru_sayisi, konu_anlatim_sure, soru_cozum_sure)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (aktif_ogr, str(s_tarih), secilen_ders, secilen_konu, int(girilen_soru), int(girilen_konu_sure), int(girilen_cozum_sure)))
                    conn_g.commit()
                    conn_g.close()
                    st.success(f"🎉 Başarıyla kaydedildi! ({secilen_ders} — {secilen_konu})")
                    st.rerun()

                # --- YENİ EKLENEN ÖZELLİK: Yanlış/Hatalı Kaydı Silme ---
                st.markdown("---")
                st.markdown("#### 🗑️ Son Çalışma Kayıtlarım ve Hatalı Giriş Silme")
                conn_del_q = get_db_connection()
                df_son_calismalar = pd.read_sql_query('SELECT id, tarih, ders, konu, soru_sayisi FROM gunluk_calisma WHERE ad_soyad = %s ORDER BY id DESC LIMIT 15', conn_del_q.conn, params=(aktif_ogr,))
                conn_del_q.close()

                if not df_son_calismalar.empty:
                    kayit_secenekleri = []
                    for _, r_row in df_son_calismalar.iterrows():
                        k_str = f"ID: {r_row['id']} | Tarih: {r_row['tarih']} | Ders: {r_row['ders']} | Konu: {r_row['konu']} (Soru: {r_row['soru_sayisi']})"
                        kayit_secenekleri.append((r_row['id'], k_str))

                    secilen_sil_kayit = st.selectbox("Silmek İstediğiniz Kaydı Seçin:", options=[k[1] for k in kayit_secenekleri], key="silinecek_kayit_secim")
                    
                    if st.button("🗑️ Seçilen Yanlış Kaydı Sil", type="secondary", use_container_width=True):
                        secilen_id = None
                        for kid, ktext in kayit_secenekleri:
                            if ktext == secilen_sil_kayit:
                                secilen_id = kid
                                break
                        
                        if secilen_id:
                            conn_del = get_db_connection()
                            cur_del = conn_del.cursor()
                            cur_del.execute("DELETE FROM gunluk_calisma WHERE id = %s AND ad_soyad = %s", (secilen_id, aktif_ogr))
                            conn_del.commit()
                            conn_del.close()
                            st.success("🎉 Seçilen çalışma kaydı başarıyla silindi!")
                            st.rerun()
                else:
                    st.info("ℹ️ Henüz silinebilecek bir çalışma kaydı bulunmuyor.")

            with tab_deneme:
                st.markdown(f"### 📊 Deneme Sınavı Sonuç Belgesi Yükleme — {aktif_ogr}")
                with st.form("deneme_yukleme_formu"):
                    dyayin = st.text_input("Deneme Yayın Adı:")
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
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (aktif_ogr, str(datetime.date.today()), dyayin, "Genel Deneme", float(dnet), dosya_yolu_db, dosya_adi_db, "Koç değerlendirmesi bekleniyor."))
                        conn_dn.commit()
                        conn_dn.close()
                        st.success("🎉 Deneme sonucu ve karne belgeniz koçunuza gönderildi!")
                        st.rerun()

            with tab_konular:
                st.markdown(f"### 🗺️ Konu Hakimiyeti Puanlama (1-5) — {aktif_ogr}")
                for d_adi, k_list in HAM_DERS_KONULARI.items():
                    st.markdown(f"**{d_adi}**")
                    for kn in k_list[:2]:
                        st.select_slider(kn, options=[1, 2, 3, 4, 5], value=3, key=f"kp_{aktif_ogr}_{kn}")

    with main_tab2:
        st.markdown("## 👨‍🏫 Koç Yönetim Paneli")
        if "aktif_koc" not in st.session_state: st.session_state["aktif_koc"] = None
        
        if not st.session_state["aktif_koc"]:
            with st.form("koc_giris_formu"):
                k_ad = st.text_input("Koç Kullanıcı Adı:")
                k_sif = st.text_input("Şifre:", type="password")
                if st.form_submit_button("Koç Girişi Yap", type="primary"):
                    conn_kg = get_db_connection()
                    cur_kg = conn_kg.cursor()
                    cur_kg.execute("SELECT sifre, onaylandi FROM koclar WHERE kullanici_adi = %s", (k_ad,))
                    r = cur_kg.fetchone()
                    conn_kg.close()

                    if r and verify_hash(k_sif, r[0]):
                        st.session_state["aktif_koc"] = k_ad
                        st.rerun()
                    else:
                        st.error("Hatalı kullanıcı adı veya şifre!")
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
                st.warning(f"🔔 {len(bekleyen_ogrenciler)} Yeni Öğrenci Onay Bekliyor!")
                for b_ogr in bekleyen_ogrenciler:
                    col_bo1, col_bo2, col_bo3, col_bo4 = st.columns([2, 1, 1, 1])
                    with col_bo1: st.markdown(f"**{b_ogr[0]}**")
                    with col_bo2: st.markdown(f"Alan: {b_ogr[1]}")
                    with col_bo3:
                        if st.button(f"Onayla ✅", key=f"onay_{b_ogr[0]}"):
                            conn_on = get_db_connection()
                            conn_on.cursor().execute("UPDATE ogrenciler SET onaylandi = 1 WHERE ad_soyad = %s", (b_ogr[0],))
                            conn_on.commit()
                            conn_on.close()
                            st.rerun()
                    with col_bo4:
                        if st.button(f"Sil ❌", key=f"sil_{b_ogr[0]}"):
                            conn_sl = get_db_connection()
                            conn_sl.cursor().execute("DELETE FROM ogrenciler WHERE ad_soyad = %s", (b_ogr[0],))
                            conn_sl.commit()
                            conn_sl.close()
                            st.rerun()
                st.divider()

            conn_ogrs = get_db_connection()
            cur_ogrs = conn_ogrs.cursor()
            cur_ogrs.execute("SELECT ad_soyad FROM ogrenciler WHERE koc_adi = %s AND onaylandi = 1", (st.session_state['aktif_koc'],))
            ogrs = [row[0] for row in cur_ogrs.fetchall()]
            conn_ogrs.close()

            if ogrs:
                secilen_ogr = st.selectbox("Yönetilecek Öğrenci:", ogrs)
                
                st.markdown(f"### 📈 {secilen_ogr} — Öğrenci İlerleme ve Çalışma Takibi")
                conn_ki = get_db_connection()
                df_koc_ilerleme = pd.read_sql_query('SELECT ders AS "Ders", konu_adi AS "Konu", CASE WHEN tamamlandi=1 THEN \'✅ Tamamlandı\' ELSE \'⏳ Devam Ediyor\' END AS "Durum", soru_miktari AS "Çözülen Soru" FROM konu_ilerleme WHERE ad_soyad = %s', conn_ki.conn, params=(secilen_ogr,))
                conn_ki.close()

                if not df_koc_ilerleme.empty:
                    st.dataframe(df_koc_ilerleme, use_container_width=True)
                else:
                    st.info("ℹ️ Öğrenci henüz ilerleme tablosunda işaretleme yapmamış.")

                st.markdown(f"### 📝 {secilen_ogr} — Günlük, Haftalık ve Aylık Çalışma Takibi & Raporlama")
                
                rapor_periyodu = st.radio("Rapor Görünüm Periyodu Seçin:", ["Günlük (Tarih Bazlı)", "Haftalık", "Aylık", "Tüm Zamanlar"], horizontal=True, key="koc_rapor_periyot_unique")

                conn_kc = get_db_connection()
                df_koc_calisma = pd.read_sql_query('SELECT tarih, ders, konu, soru_sayisi AS "Soru", konu_anlatim_sure AS "Konu Süre (dk)", soru_cozum_sure AS "Çözüm Süre (dk)" FROM gunluk_calisma WHERE ad_soyad = %s ORDER BY tarih DESC', conn_kc.conn, params=(secilen_ogr,))
                conn_kc.close()

                if not df_koc_calisma.empty:
                    df_koc_calisma["tarih_dt"] = pd.to_datetime(df_koc_calisma["tarih"], errors="coerce")
                    bugun = pd.Timestamp(datetime.date.today())

                    if rapor_periyodu == "Günlük (Tarih Bazlı)":
                        secilen_gun = st.date_input("İncelenecek Tarihi Seçin:", datetime.date.today(), key="koc_gun_secim_unique")
                        df_filtrelenmis = df_koc_calisma[df_koc_calisma["tarih_dt"].dt.date == secilen_gun].copy()
                        periyot_etiket = f"{secilen_gun} Tarihli Günlük"
                    elif rapor_periyodu == "Haftalık":
                        hafta_basi = bugun - pd.Timedelta(days=7)
                        df_filtrelenmis = df_koc_calisma[df_koc_calisma["tarih_dt"] >= hafta_basi].copy()
                        periyot_etiket = "Son 7 Günlük Haftalık"
                    elif rapor_periyodu == "Aylık":
                        ay_basi = bugun - pd.Timedelta(days=30)
                        df_filtrelenmis = df_koc_calisma[df_koc_calisma["tarih_dt"] >= ay_basi].copy()
                        periyot_etiket = "Son 30 Günlük Aylık"
                    else:
                        df_filtrelenmis = df_koc_calisma.copy()
                        periyot_etiket = "Tüm Zamanlar"

                    if not df_filtrelenmis.empty:
                        gosterilecek_df = df_filtrelenmis[["tarih", "ders", "konu", "Soru", "Konu Süre (dk)", "Çözüm Süre (dk)"]].rename(columns={"tarih": "Tarih", "ders": "Ders", "konu": "Konu"})
                        
                        toplam_soru = gosterilecek_df["Soru"].sum()
                        toplam_konu_sure = gosterilecek_df["Konu Süre (dk)"].sum()
                        toplam_cozum_sure = gosterilecek_df["Çözüm Süre (dk)"].sum()
                        toplam_saat = round((toplam_konu_sure + toplam_cozum_sure) / 60, 1)

                        cm1, cm2, cm3 = st.columns(3)
                        with cm1:
                            st.markdown(f'<div class="renkli-kart-1"><div style="font-size:12px; font-weight:700; opacity:0.9;">TOPLAM ÇÖZÜLEN SORU</div><div style="font-size:26px; font-weight:800; margin-top:5px;">{int(toplam_soru):,}</div></div>', unsafe_allow_html=True)
                        with cm2:
                            st.markdown(f'<div class="renkli-kart-2"><div style="font-size:12px; font-weight:700; opacity:0.9;">TOPLAM ÇALIŞMA SÜRESİ</div><div style="font-size:26px; font-weight:800; margin-top:5px;">{toplam_saat} Saat</div></div>', unsafe_allow_html=True)
                        with cm3:
                            st.markdown(f'<div class="renkli-kart-3"><div style="font-size:12px; font-weight:700; opacity:0.9;">TOPLAM KAYIT ADEDİ</div><div style="font-size:26px; font-weight:800; margin-top:5px;">{len(gosterilecek_df)}</div></div>', unsafe_allow_html=True)

                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown("#### 📈 Ders Bazlı Soru Dağılımı ve İlerleme")
                        ders_soru_df = gosterilecek_df.groupby("Ders")["Soru"].sum().reset_index()
                        
                        for _, drow in ders_soru_df.iterrows():
                            d_adi = drow["Ders"]
                            d_soru = int(drow["Soru"])
                            max_s = int(ders_soru_df["Soru"].max()) if not ders_soru_df.empty else 1
                            yuzde = float(d_soru / max_s) if max_s > 0 else 0.0
                            
                            st.markdown(f"**{d_adi}** — `{d_soru} Soru`")
                            st.progress(yuzde)

                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown("#### 📋 Ayrıntılı Çalışma Listesi")
                        st.dataframe(gosterilecek_df, use_container_width=True, hide_index=True)

                        rapor_bytes = calisma_raporu_html(gosterilecek_df, secilen_ogr, periyot_etiket)
                        st.download_button(
                            label=f"📥 Bu {periyot_etiket} Raporu PDF / HTML Olarak İndir",
                            data=rapor_bytes,
                            file_name=f"{secilen_ogr}_{periyot_etiket.replace(' ', '_')}_Calisma_Raporu.html",
                            mime="text/html",
                            key="koc_indir_button_unique",
                            use_container_width=True
                        )
                    else:
                        st.warning(f"⚠️ Seçilen {rapor_periyodu.lower()} aralığında kayıt bulunamadı.")
                else:
                    st.info("ℹ️ Öğrenci henüz günlük çalışma kaydı girmemiş.")

                st.markdown(f"### 📊 {secilen_ogr} — Deneme Sınavları ve Koç Notları")
                conn_kdc = get_db_connection()
                df_koc_deneme = pd.read_sql_query('SELECT id, tarih AS "Tarih", yayin AS "Yayın", toplam_net AS "Toplam Net", dosya_yolu, dosya_adi, koc_notu AS "Koç Notu" FROM denemeler WHERE ad_soyad = %s ORDER BY id DESC', conn_kdc.conn, params=(secilen_ogr,))
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
                            yeni_koc_notu = st.text_input("Koç Değerlendirme Notu:", value=kd['Koç Notu'] if kd['Koç Notu'] else "", key=f"koc_not_inp_{kd['id']}")
                            if st.form_submit_button("Notu Güncelle"):
                                conn_kn = get_db_connection()
                                cur_kn = conn_kn.cursor()
                                cur_kn.execute("UPDATE denemeler SET koc_notu = %s WHERE id = %s", (yeni_koc_notu, kd['id']))
                                conn_kn.commit()
                                conn_kn.close()
                                st.success("🎉 Koç notu güncellendi!")
                                st.rerun()
                        st.divider()
                else:
                    st.info("ℹ️ Öğrenci henüz deneme sonucu veya karne yüklememiş.")

                st.divider()
                st.markdown(f"### 🗓️ {secilen_ogr} — Kişiye Özel Haftalık Program Düzenleyici")

                bugun_koc = datetime.date.today()
                varsayilan_pazartesi = bugun_koc - datetime.timedelta(days=bugun_koc.weekday())
                koc_hafta_secim = st.date_input("Düzenlenecek Haftanın Pazartesi Tarihi:", value=varsayilan_pazartesi, key="koc_hafta_tarih_secim")
                koc_hafta_str = str(koc_hafta_secim)

                with st.expander("🔄 Geçmiş Haftadan Program Kopyala (Şablon Kullan)", expanded=False):
                    conn_havuz = get_db_connection()
                    cur_hav = conn_havuz.cursor()
                    cur_hav.execute("SELECT DISTINCT hafta_baslangici FROM excel_program_matris WHERE ad_soyad = %s ORDER BY hafta_baslangici DESC", (secilen_ogr,))
                    mevcut_haftalar = [r[0] for r in cur_hav.fetchall()]
                    conn_havuz.close()

                    if mevcut_haftalar:
                        kopyalanacak_hafta = st.selectbox("Hangi Haftanın Programı Kopyalansın?", mevcut_haftalar, key="kopya_kaynak_hafta")
                        if st.button("Seçilen Haftayı Aktif Haftaya Kopyala", key="hafta_kopyala_islem"):
                            if kopyalanacak_hafta != koc_hafta_str:
                                conn_cp = get_db_connection()
                                cur_cp = conn_cp.cursor()
                                cur_cp.execute("SELECT saat_araligi, pazartesi, sali, carsamba, persembe, cuma, cumartesi, pazar FROM excel_program_matris WHERE ad_soyad = %s AND hafta_baslangici = %s", (secilen_ogr, kopyalanacak_hafta))
                                kaynak_satirlar = cur_cp.fetchall()
                                
                                for row in kaynak_satirlar:
                                    s_ar, pz, sl, cr, pr, cm, cmt, pzr = row
                                    cur_cp.execute("""
                                        INSERT INTO excel_program_matris (ad_soyad, hafta_baslangici, saat_araligi, pazartesi, sali, carsamba, persembe, cuma, cumartesi, pazar)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                        ON CONFLICT (ad_soyad, hafta_baslangici, saat_araligi) DO UPDATE SET
                                        pazartesi = EXCLUDED.pazartesi, sali = EXCLUDED.sali, carsamba = EXCLUDED.carsamba, 
                                        persembe = EXCLUDED.persembe, cuma = EXCLUDED.cuma, cumartesi = EXCLUDED.cumartesi, pazar = EXCLUDED.pazar
                                    """, (secilen_ogr, koc_hafta_str, s_ar, pz, sl, cr, pr, cm, cmt, pzr))
                                conn_cp.commit()
                                conn_cp.close()
                                st.success(f"🎉 {kopyalanacak_hafta} haftasının programı başarıyla {koc_hafta_str} haftasına kopyalandı!")
                                st.rerun()
                            else:
                                st.warning("⚠️ Kaynak hafta ile hedef hafta aynı olamaz!")
                    else:
                        st.info("ℹ️ Kopyalanabilecek geçmiş hafta kaydı bulunmuyor.")

                with st.expander("✨ Gün Bazlı Özel Saat & Hazır Tablo (Excel/CSV) Yükleme ve PDF İndir", expanded=True):
                    
                    conn_kpdf = get_db_connection()
                    df_kpdf = pd.read_sql_query('SELECT saat_araligi AS "Saat", pazartesi AS "Pazartesi", sali AS "Salı", carsamba AS "Çarşamba", persembe AS "Perşembe", cuma AS "Cuma", cumartesi AS "Cumartesi", pazar AS "Pazar" FROM excel_program_matris WHERE ad_soyad = %s AND hafta_baslangici = %s ORDER BY saat_araligi ASC', conn_kpdf.conn, params=(secilen_ogr, koc_hafta_str))
                    conn_kpdf.close()

                    if not df_kpdf.empty:
                        koc_pdf_bytes = haftalik_program_toplu_pdf_bytes(df_kpdf, secilen_ogr)
                        st.download_button(
                            label=f"📥 {secilen_ogr} Öğrencisinin Bu Hafta ({koc_hafta_str}) Programını Toplu PDF Olarak İndir",
                            data=koc_pdf_bytes,
                            file_name=f"{secilen_ogr}_{koc_hafta_str}_Haftalik_Program.html",
                            mime="text/html",
                            key=f"koc_down_pdf_{secilen_ogr}",
                            use_container_width=True
                        )
                        st.markdown("---")

                    st.markdown("#### 1️⃣ Güne Özel Saat & Ders Ekleme")
                    gb_gun = st.selectbox("Gün Seçin:", ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"], key="gb_gun_secim")
                    gb_saat = st.text_input("Bu Güne Özel Saat Aralığı (Örn: 09:30 - 11:00):", value="09:30 - 11:00", key="gb_saat_inp")
                    
                    tum_dersler_listesi = list(EVRENSEL_DERS_KONULARI.keys())
                    gb_ders = st.selectbox("Ders / Aktivite:", tum_dersler_listesi, key="gb_ders_inp")
                    gb_konu = st.selectbox("Alt Konu / Detay:", EVRENSEL_DERS_KONULARI.get(gb_ders, ["Genel Soru"]), key="gb_konu_inp")

                    if st.button("Seçilen Güne Bu Saati ve Dersi İşle", type="primary", key="gb_kaydet_btn"):
                        gun_col_map = {"Pazartesi": "pazartesi", "Salı": "sali", "Çarşamba": "carsamba", "Perşembe": "persembe", "Cuma": "cuma", "Cumartesi": "cumartesi", "Pazar": "pazar"}
                        col_adi = gun_col_map[gb_gun]
                        hucre_metin = f"{gb_ders}\n↳ {gb_konu}"
                        
                        conn_gb = get_db_connection()
                        cur_gb = conn_gb.cursor()
                        cur_gb.execute(f"""
                            INSERT INTO excel_program_matris (ad_soyad, hafta_baslangici, saat_araligi, {col_adi})
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (ad_soyad, hafta_baslangici, saat_araligi) DO UPDATE SET {col_adi} = EXCLUDED.{col_adi}
                        """, (secilen_ogr, koc_hafta_str, gb_saat, hucre_metin))
                        conn_gb.commit()
                        conn_gb.close()
                        st.success(f"🎉 {koc_hafta_str} haftası {gb_gun} günü için {gb_saat} saatine ders başarıyla eklendi!")
                        st.rerun()

                    st.markdown("---")
                    st.markdown("#### 2️⃣ Hazır Excel / CSV Tablosu Yükle")
                    st.caption(f"💡 {koc_hafta_str} haftası için hazır program tablosu yükleyebilirsiniz.")
                    yuklenen_prog_dosya = st.file_uploader("Ders programı dosyası seçin:", type=["xlsx", "csv"], key=f"prog_upl_{secilen_ogr}")
                    if yuklenen_prog_dosya is not None:
                        try:
                            if yuklenen_prog_dosya.name.endswith('.csv'):
                                df_yuklenen = pd.read_csv(yuklenen_prog_dosya)
                            else:
                                df_yuklenen = pd.read_excel(yuklenen_prog_dosya)
                            
                            df_yuklenen.columns = [str(c).strip() for c in df_yuklenen.columns]
                            if "Saat Aralığı" in df_yuklenen.columns or "Saat" in df_yuklenen.columns:
                                saat_kolonu = "Saat Aralığı" if "Saat Aralığı" in df_yuklenen.columns else "Saat"
                                conn_upl = get_db_connection()
                                cur_upl = conn_upl.cursor()
                                cur_upl.execute("DELETE FROM excel_program_matris WHERE ad_soyad = %s AND hafta_baslangici = %s", (secilen_ogr, koc_hafta_str))
                                for _, r_u in df_yuklenen.iterrows():
                                    s_ar_u = str(r_u.get(saat_kolonu, "")).strip()
                                    if s_ar_u and s_ar_u != "nan":
                                        cur_upl.execute("""
                                            INSERT INTO excel_program_matris (ad_soyad, hafta_baslangici, saat_araligi, pazartesi, sali, carsamba, persembe, cuma, cumartesi, pazar)
                                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                        """, (
                                            secilen_ogr, koc_hafta_str, s_ar_u,
                                            str(r_u.get("Pazartesi", "") if pd.notna(r_u.get("Pazartesi")) else ""),
                                            str(r_u.get("Salı", "") if pd.notna(r_u.get("Salı")) else ""),
                                            str(r_u.get("Çarşamba", "") if pd.notna(r_u.get("Çarşamba")) else ""),
                                            str(r_u.get("Perşembe", "") if pd.notna(r_u.get("Perşembe")) else ""),
                                            str(r_u.get("Cuma", "") if pd.notna(r_u.get("Cuma")) else ""),
                                            str(r_u.get("Cumartesi", "") if pd.notna(r_u.get("Cumartesi")) else ""),
                                            str(r_u.get("Pazar", "") if pd.notna(r_u.get("Pazar")) else "")
                                        ))
                                conn_upl.commit()
                                conn_upl.close()
                                st.success(f"🎉 {koc_hafta_str} haftası program tablosu başarıyla yüklendi!")
                                st.rerun()
                            else:
                                st.error("❌ Yüklenen dosyada 'Saat Aralığı' veya 'Saat' sütunu bulunamadı!")
                        except Exception as e:
                            st.error(f"❌ Dosya okunurken hata oluştu: {e}")

                st.markdown(f"#### 📊 {secilen_ogr} — Canlı Program Tablosu Düzenleyici ({koc_hafta_str} Haftası)")
                conn_m = get_db_connection()
                df_matris = pd.read_sql_query('SELECT saat_araligi AS "Saat Aralığı", pazartesi AS "Pazartesi", sali AS "Salı", carsamba AS "Çarşamba", persembe AS "Perşembe", cuma AS "Cuma", cumartesi AS "Cumartesi", pazar AS "Pazar" FROM excel_program_matris WHERE ad_soyad = %s AND hafta_baslangici = %s ORDER BY saat_araligi ASC', conn_m.conn, params=(secilen_ogr, koc_hafta_str))
                conn_m.close()
                
                if df_matris.empty:
                    df_matris = pd.DataFrame([{"Saat Aralığı": "08:00 - 09:00", "Pazartesi": "", "Salı": "", "Çarşamba": "", "Perşembe": "", "Cuma": "", "Cumartesi": "", "Pazar": ""}])

                edited_matris = st.data_editor(df_matris, num_rows="dynamic", use_container_width=True, height=450, key=f"excel_matris_editor_{secilen_ogr}_{koc_hafta_str}")

                if st.button("💾 Tablodaki Tüm Değişiklikleri Kaydet", type="primary", use_container_width=True, key="koc_matris_kaydet_btn"):
                    conn_sv2 = get_db_connection()
                    cur_sv2 = conn_sv2.cursor()
                    cur_sv2.execute("DELETE FROM excel_program_matris WHERE ad_soyad = %s AND hafta_baslangici = %s", (secilen_ogr, koc_hafta_str))
                    for _, row in edited_matris.iterrows():
                        s_ar = str(row.get("Saat Aralığı", "")).strip()
                        if s_ar and s_ar != "nan":
                            cur_sv2.execute("""
                                INSERT INTO excel_program_matris (ad_soyad, hafta_baslangici, saat_araligi, pazartesi, sali, carsamba, persembe, cuma, cumartesi, pazar)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (ad_soyad, hafta_baslangici, saat_araligi) DO UPDATE SET
                                pazartesi = EXCLUDED.pazartesi, sali = EXCLUDED.sali, carsamba = EXCLUDED.carsamba, 
                                persembe = EXCLUDED.persembe, cuma = EXCLUDED.cuma, cumartesi = EXCLUDED.cumartesi, pazar = EXCLUDED.pazar
                            """, (
                                secilen_ogr, koc_hafta_str, s_ar,
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
                    st.success(f"🎉 {koc_hafta_str} haftası programı güncellendi!")
                    st.rerun()

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
                cur_v.execute("SELECT veli_pin, onaylandi FROM ogrenciler WHERE ad_soyad = %s", (v_ad,))
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
            cur_vh.execute("SELECT hedef_uni, hedef_bolum, hedef_net FROM ogrenciler WHERE ad_soyad = %s", (v_ad,))
            h_bilgi = cur_vh.fetchone()
            conn_vh.close()

            if h_bilgi:
                st.markdown(f"🎯 **Hedef Üniversite / Bölüm:** {h_bilgi[0]} — {h_bilgi[1]} (Hedef Net: {h_bilgi[2]})")

            st.markdown(f"### 📅 {v_ad.upper()} — Haftalık Ders Programı")
            
            bugun_v_tarih = datetime.date.today()
            veli_hafta_pazartesi = bugun_v_tarih - datetime.timedelta(days=bugun_v_tarih.weekday())
            veli_hafta_str = str(veli_hafta_pazartesi)

            conn_vp = get_db_connection()
            df_veli_p = pd.read_sql_query('SELECT saat_araligi AS "Saat", pazartesi AS "Pazartesi", sali AS "Salı", carsamba AS "Çarşamba", persembe AS "Perşembe", cuma AS "Cuma", cumartesi AS "Cumartesi", pazar AS "Pazar" FROM excel_program_matris WHERE ad_soyad = %s AND hafta_baslangici = %s ORDER BY saat_araligi ASC', conn_vp.conn, params=(v_ad, veli_hafta_str))
            conn_vp.close()

            if not df_veli_p.empty:
                st.dataframe(df_veli_p, use_container_width=True, height=350)
            else:
                st.info(f"ℹ️ Koç henüz bu hafta ({veli_hafta_str}) için haftalık program kaydetmemiş.")

            st.markdown(f"### ✅ Konu İlerleme Durumu")
            conn_vi = get_db_connection()
            df_v_ilerleme = pd.read_sql_query('SELECT ders AS "Ders", konu_adi AS "Konu", CASE WHEN tamamlandi=1 THEN \'✅ Tamamlandı\' ELSE \'⏳ Devam Ediyor\' END AS "Durum", soru_miktari AS "Çözülen Soru" FROM konu_ilerleme WHERE ad_soyad = %s', conn_vi.conn, params=(v_ad,))
            conn_vi.close()

            if not df_v_ilerleme.empty:
                st.dataframe(df_v_ilerleme, use_container_width=True)
            else:
                st.info("ℹ️ Öğrenci henüz ilerleme tablosunda işlem yapmamış.")

            st.markdown(f"### 📝 Günlük, Haftalık ve Aylık Çalışma Takibi & Raporlama")
            rapor_periyodu_v = st.radio("Veli Rapor Görünüm Periyodu Seçin:", ["Günlük (Tarih Bazlı)", "Haftalık", "Aylık", "Tüm Zamanlar"], horizontal=True, key="veli_rapor_periyot_unique")

            conn_vc = get_db_connection()
            df_v_calisma = pd.read_sql_query('SELECT tarih, ders, konu, soru_sayisi AS "Soru", konu_anlatim_sure AS "Konu Süre (dk)", soru_cozum_sure AS "Çözüm Süre (dk)" FROM gunluk_calisma WHERE ad_soyad = %s ORDER BY tarih DESC', conn_vc.conn, params=(v_ad,))
            conn_vc.close()

            if not df_v_calisma.empty:
                df_v_calisma["tarih_dt"] = pd.to_datetime(df_v_calisma["tarih"], errors="coerce")
                bugun_v = pd.Timestamp(datetime.date.today())

                if rapor_periyodu_v == "Günlük (Tarih Bazlı)":
                    secilen_gun_v = st.date_input("İncelenecek Tarihi Seçin:", datetime.date.today(), key="veli_gun_secim_unique")
                    df_filtrelenmis_v = df_v_calisma[df_v_calisma["tarih_dt"].dt.date == secilen_gun_v].copy()
                    periyot_etiket_v = f"{secilen_gun_v} Tarihli Günlük"
                elif rapor_periyodu_v == "Haftalık":
                    hafta_basi_v = bugun_v - pd.Timedelta(days=7)
                    df_filtrelenmis_v = df_v_calisma[df_v_calisma["tarih_dt"] >= hafta_basi_v].copy()
                    periyot_etiket_v = "Son 7 Günlük Haftalık"
                elif rapor_periyodu_v == "Aylık":
                    ay_basi_v = bugun_v - pd.Timedelta(days=30)
                    df_filtrelenmis_v = df_v_calisma[df_v_calisma["tarih_dt"] >= ay_basi_v].copy()
                    periyot_etiket_v = "Son 30 Günlük Aylık"
                else:
                    df_filtrelenmis_v = df_v_calisma.copy()
                    periyot_etiket_v = "Tüm Zamanlar"

                if not df_filtrelenmis_v.empty:
                    gosterilecek_df_v = df_filtrelenmis_v[["tarih", "ders", "konu", "Soru", "Konu Süre (dk)", "Çözüm Süre (dk)"]].rename(columns={"tarih": "Tarih", "ders": "Ders", "konu": "Konu"})
                    
                    toplam_soru_v = gosterilecek_df_v["Soru"].sum()
                    toplam_konu_sure_v = gosterilecek_df_v["Konu Süre (dk)"].sum()
                    toplam_cozum_sure_v = gosterilecek_df_v["Çözüm Süre (dk)"].sum()
                    toplam_saat_v = round((toplam_konu_sure_v + toplam_cozum_sure_v) / 60, 1)

                    vm1, vm2, vm3 = st.columns(3)
                    with vm1:
                        st.markdown(f'<div class="renkli-kart-1"><div style="font-size:12px; font-weight:700; opacity:0.9;">TOPLAM ÇÖZÜLEN SORU</div><div style="font-size:26px; font-weight:800; margin-top:5px;">{int(toplam_soru_v):,}</div></div>', unsafe_allow_html=True)
                    with vm2:
                        st.markdown(f'<div class="renkli-kart-2"><div style="font-size:12px; font-weight:700; opacity:0.9;">TOPLAM ÇALIŞMA SÜRESİ</div><div style="font-size:26px; font-weight:800; margin-top:5px;">{toplam_saat_v} Saat</div></div>', unsafe_allow_html=True)
                    with vm3:
                        st.markdown(f'<div class="renkli-kart-3"><div style="font-size:12px; font-weight:700; opacity:0.9;">TOPLAM KAYIT ADEDİ</div><div style="font-size:26px; font-weight:800; margin-top:5px;">{len(gosterilecek_df_v)}</div></div>', unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("#### 📈 Ders Bazlı Soru Dağılımı")
                    ders_soru_df_v = gosterilecek_df_v.groupby("Ders")["Soru"].sum().reset_index()
                    
                    for _, vdrow in ders_soru_df_v.iterrows():
                        vd_adi = vdrow["Ders"]
                        vd_soru = int(vdrow["Soru"])
                        vmax_s = int(ders_soru_df_v["Soru"].max()) if not ders_soru_df_v.empty else 1
                        vyuzde = float(vd_soru / vmax_s) if vmax_s > 0 else 0.0
                        
                        st.markdown(f"**{vd_adi}** — `{vd_soru} Soru`")
                        st.progress(vyuzde)

                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("#### 📋 Çalışma Listesi")
                    st.dataframe(gosterilecek_df_v, use_container_width=True, hide_index=True)

                    rapor_bytes_v = calisma_raporu_html(gosterilecek_df_v, v_ad, periyot_etiket_v)
                    st.download_button(
                        label=f"📥 Bu {periyot_etiket_v} Raporu PDF / HTML Olarak İndir",
                        data=rapor_bytes_v,
                        file_name=f"{v_ad}_{periyot_etiket_v.replace(' ', '_')}_Calisma_Raporu.html",
                        mime="text/html",
                        key="veli_indir_button_unique",
                        use_container_width=True
                    )
                else:
                    st.warning(f"⚠️ Seçilen {rapor_periyodu_v.lower()} aralığında kayıt bulunamadı.")
            else:
                st.info("ℹ️ Öğrenci henüz günlük çalışma kaydı girmemiş.")

            st.markdown(f"### 📊 Deneme Sınavı Sonuçları ve Koç Notları")
            conn_vd = get_db_connection()
            df_v_deneme = pd.read_sql_query('SELECT tarih AS "Tarih", yayin AS "Yayın", toplam_net AS "Toplam Net", koc_notu AS "Koç Notu" FROM denemeler WHERE ad_soyad = %s ORDER BY id DESC', conn_vd.conn, params=(v_ad,))
            conn_vd.close()

            if not df_v_deneme.empty:
                st.dataframe(df_v_deneme, use_container_width=True, hide_index=True)
            else:
                st.info("ℹ️ Henüz deneme sınavı sonucu yüklenmemiş.")