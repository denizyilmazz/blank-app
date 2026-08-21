import streamlit as st
import datetime
import psycopg2
from psycopg2 import pool
import pandas as pd
import random
import base64
import hashlib
import os
from urllib.parse import quote
from PIL import Image
import shutil
import warnings

# Pandas'ın veritabanı uyarılarını gizliyoruz
warnings.filterwarnings('ignore', category=UserWarning)

st.set_page_config(
    page_title="YKS & LGS KOÇLUK (DENİZ YILMAZ)",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- SADECE KARNE VE BELGELER İÇİN KLASÖR ---
KARNE_DIR = "karne_yuklemeleri"
os.makedirs(KARNE_DIR, exist_ok=True)

# --- SUPABASE BULUT VERİTABANI BAĞLANTISI (IPv4 POOLER) ---
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

# --- DİNAMİK MÜFREDAT OKUYUCU (CSV) ---
@st.cache_data
def mufredat_yukle():
    if os.path.exists("mufredat.csv"):
        try:
            return pd.read_csv("mufredat.csv", sep=";")
        except Exception:
            pass
    # Dosya yoksa veya hatalıysa boş bir şablon döndür
    return pd.DataFrame(columns=["Grup", "Ders", "Konu"])

def get_ham_mufredat(grup_adi):
    df = mufredat_yukle()
    if df.empty: return {"Örnek Ders": ["Örnek Konu (Lütfen mufredat.csv yükleyin)"]}
    df_grup = df[df["Grup"] == grup_adi]
    if df_grup.empty: return {"Genel Ders": ["Genel Konu"]}
    
    mufredat_dict = {}
    for ders in df_grup["Ders"].unique():
        mufredat_dict[ders] = df_grup[df_grup["Ders"] == ders]["Konu"].tolist()
    return mufredat_dict

def get_evrensel_mufredat(grup_adi):
    ham = get_ham_mufredat(grup_adi)
    evrensel = {}
    
    # Ortak molaları her gruba otomatik ekliyoruz
    evrensel["☕ Mola & Dinlenme Aktivitesi"] = ["Kısa Dinlenme & Çay/Kahve Molası", "Zihin Dinlendirme Mola"]
    evrensel["🍽️ Yemek Molaları"] = ["Öğle Yemeği Molası", "Akşam Yemeği Molası"]
    evrensel["📊 Branş Denemeleri"] = ["Genel Branş Denemesi", "Sayısal Branş Denemesi", "Sözel Branş Denemesi"]
    
    for ders, konular in ham.items():
        genisletilmis = []
        for k in konular:
            genisletilmis.append(f"{k} — Konu Çalışması")
            genisletilmis.append(f"{k} — Soru Çözümü")
        evrensel[ders] = genisletilmis
    return evrensel

def tablo_olustur():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Ana Tablolar
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
    
    # Yeni özellik: Sınıf Grubu Sütunu (Eğer veritabanında yoksa hataya düşmeden ekler)
    try:
        cur.execute("ALTER TABLE ogrenciler ADD COLUMN sinif_grubu TEXT DEFAULT '12. Sınıf ve Mezun (2027 YKS)'")
        conn.commit()
    except Exception:
        conn.rollback() # Sütun zaten varsa işlemi güvenle iptal et
        
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
        id SERIAL PRIMARY KEY, ad_soyad TEXT, tarih TEXT, ders TEXT, konu TEXT, 
        soru_sayisi INTEGER DEFAULT 0, konu_anlatim_sure INTEGER DEFAULT 0, soru_cozum_sure INTEGER DEFAULT 0
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS konu_ilerleme (
        ad_soyad TEXT, ders TEXT, konu_adi TEXT, tamamlandi INTEGER DEFAULT 0, 
        soru_miktari INTEGER DEFAULT 0, PRIMARY KEY (ad_soyad, ders, konu_adi)
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
    CREATE TABLE IF NOT EXISTS excel_program_matris (
        ad_soyad TEXT, saat_araligi TEXT, 
        pazartesi TEXT DEFAULT '', sali TEXT DEFAULT '', carsamba TEXT DEFAULT '', 
        persembe TEXT DEFAULT '', cuma TEXT DEFAULT '', cumartesi TEXT DEFAULT '', pazar TEXT DEFAULT '', 
        PRIMARY KEY (ad_soyad, saat_araligi)
    )
    """)
    
    conn.commit()
    conn.close()

tablo_olustur()

# --- CSS VE TEMA AYARLARI ---
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
    html, body, p, label, input, textarea, select, h1, h2, h3, h4, h5, h6 { font-family: 'Plus Jakarta Sans', sans-serif !important; }
    
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
    html, body, p, label, input, textarea, select { color: var(--text-color, #0f172a) !important; }
    #MainMenu, footer, header, .stDeployButton {display: none !important;}
    .stApp { background: var(--bg-gradient) !important; background-attachment: fixed !important; }
    .main .block-container { padding-top: 1rem !important; padding-bottom: 3rem !important; max-width: 1420px !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 6px; background: var(--tab-bg) !important; padding: 8px; border-radius: 16px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05); border: 1px solid var(--border-color) !important; }
    .stTabs [data-baseweb="tab"] { height: 48px; background-color: var(--container-bg) !important; border-radius: 10px; padding: 8px 16px; font-weight: 700 !important; font-size: 13px !important; color: var(--text-color) !important; border: 1px solid var(--border-color) !important; }
    .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%) !important; border: none !important; }
    .stTabs [aria-selected="true"] span, .stTabs [aria-selected="true"] div { color: #ffffff !important; }
    input, textarea, select, div[data-baseweb="select"] { background-color: var(--input-bg) !important; color: var(--input-text) !important; border: 1.5px solid var(--border-color) !important; border-radius: 10px !important; font-weight: 600 !important; }
    div[data-baseweb="select"] > div { background-color: var(--input-bg) !important; color: var(--input-text) !important; }
    div[data-baseweb="select"] span { color: var(--input-text) !important; }
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[data-baseweb="menu"] { background-color: var(--container-bg) !important; }
    div[data-baseweb="popover"] div, li[role="option"], span[data-baseweb="tag"] { color: var(--text-color) !important; background-color: var(--container-bg) !important; }
    li[role="option"]:hover { background-color: #0284c7 !important; color: #ffffff !important; }
    .hero-motivation-card { background: var(--hero-bg) !important; color: #ffffff !important; padding: 20px 24px; border-radius: 20px; font-weight: 700; margin-bottom: 20px; }
    .hero-motivation-card * { color: #ffffff !important; }
    .yok-net-box { background: var(--yok-box-bg) !important; border: 2px solid #3b82f6; border-radius: 16px; padding: 18px 22px; margin-bottom: 15px; }
    .yok-net-box * { color: var(--text-color) !important; }
    .program-header-box { background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%) !important; color: white !important; padding: 20px; border-radius: 16px; margin-bottom: 20px; text-align: center; box-shadow: 0 4px 15px rgba(2, 132, 199, 0.2); }
    .program-header-box * { color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

def make_hash(password: str) -> str:
    salt = "YKS_PRO_SECURE_SALT_2026"
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()

def verify_hash(password: str, hashed_password: str) -> bool:
    if not hashed_password: return False
    if password == hashed_password: return True
    if make_hash(password) == hashed_password: return True
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
        <h2>🎓 DİNAMİK KOÇLUK — {ogrenci_adi.upper()} KİŞİSEL ÇALIŞMA PROGRAMI</h2>
        <p>Deniz Yılmaz Gelişim Platformu | {datetime.date.today().strftime('%d.%m.%Y')}</p>
        {df.to_html(index=False, classes='table', border=0)}
    </body>
    </html>
    """
    return html_content.encode('utf-8')

MOTIVASYON_SOZLERI = [
    "🌿 Sakin ol, derin bir nefes al ve adım adım ilerle. Disiplin başarıyı getirir!",
    "🚀 Başarı, her gün ertelemeden tekrarlanan küçük çabaların birikimidir!",
    "🎓 Bugün döktüğün her damla alın teri, hedeflerine açılan bir kapıdır!"
]

# (Sabit Üniversite listeleri veri boyutunu şişirmemek için küçültüldü, Koç panelinden dinamik güncellenecek)
UNIVERSITE_LISTESI = ["Hedef Seçimi (Veritabanı Güncelleniyor)"]
BOLUM_KATEGORILERI = {"SAY (Sayısal)": ["Bölümler Yükleniyor"], "EA (Eşit Ağırlık)": ["Bölümler Yükleniyor"], "SÖZ (Sözel)": ["Bölümler Yükleniyor"], "LGS Hedef": ["Fen Liseleri", "Anadolu Liseleri"]}

st.markdown("""
<div style="text-align: center; padding: 10px 0 15px 0;">
    <span style="font-size: 42px;">🎓</span>
    <h1 style="margin: 0; font-weight: 800; font-size: 26px;">EVRENSEL KOÇLUK PLATFORMU</h1>
    <p style="margin: 0; font-size: 14px; color: #0284c7; font-weight: 700;">DENİZ YILMAZ</p>
</div>
""", unsafe_allow_html=True)

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
                                st.rerun()
                            else:
                                st.warning("⏳ Hesabınız koçunuz tarafından henüz onaylanmamıştır.")
                        else:
                            st.error("❌ Hatalı ad veya şifre!")

        with tab_ogr_register:
            with st.form("ogrenci_kayit_formu"):
                reg_ad = st.text_input("Adınız ve Soyadınız:").strip().title()
                reg_sifre = st.text_input("Şifre Belirleyin:", type="password")
                reg_veli_pin = st.text_input("Veli Takip Şifresi (PIN):", value="123456")
                
                # Dinamik Grup Listesi (CSV'den çekilir)
                df_gruplar = mufredat_yukle()
                dinamik_gruplar = df_gruplar["Grup"].unique().tolist() if not df_gruplar.empty else ["12. Sınıf ve Mezun (2027 YKS)", "8. Sınıf (LGS)"]
                
                reg_grup = st.selectbox("Sınıfınız / Sınav Grubunuz (Önemli!):", dinamik_gruplar)
                
                conn_k = get_db_connection()
                cur_k = conn_k.cursor()
                cur_k.execute("SELECT kullanici_adi FROM koclar WHERE onaylandi = 1")
                aktif_koclar_listesi = [k[0] for k in cur_k.fetchall()]
                conn_k.close()

                if not aktif_koclar_listesi: aktif_koclar_listesi = ["Deniz Yılmaz"]
                
                reg_koc = st.selectbox("Çalışmak İstediğiniz Koçu Seçin:", aktif_koclar_listesi)
                reg_alan = st.selectbox("Alanınız:", ["SAY (Sayısal)", "EA (Eşit Ağırlık)", "SÖZ (Sözel)", "DİL (Yabancı Dil)", "LGS Ortak Alan"])

                if st.form_submit_button("Hesabımı Oluştur ve Onaya Gönder", type="primary", use_container_width=True):
                    if reg_ad and reg_sifre:
                        conn_reg = get_db_connection()
                        cur_reg = conn_reg.cursor()
                        cur_reg.execute("SELECT ad_soyad FROM ogrenciler WHERE ad_soyad = %s", (reg_ad,))
                        if cur_reg.fetchone():
                            st.error(f"⚠️ `{reg_ad}` zaten kayıtlı!")
                        else:
                            cur_reg.execute("""
                                INSERT INTO ogrenciler (ad_soyad, sifre, veli_pin, alan, sinif_grubu, koc_adi, onaylandi) 
                                VALUES (%s, %s, %s, %s, %s, %s, 0)
                            """, (reg_ad, make_hash(reg_sifre), reg_veli_pin, reg_alan, reg_grup, reg_koc))
                            conn_reg.commit()
                            st.success("🎉 Kaydınız oluşturuldu! Koç onayladıktan sonra giriş yapabileceksiniz.")
                        conn_reg.close()
    else:
        # AKTİF ÖĞRENCİ EKRANI
        conn_inf = get_db_connection()
        cur_inf = conn_inf.cursor()
        cur_inf.execute("SELECT sinav_turu, alan, hedef_uni, hedef_bolum, koc_adi, sinif_grubu FROM ogrenciler WHERE ad_soyad = %s", (aktif_ogr,))
        r_info = cur_inf.fetchone()
        conn_inf.close()

        ogr_alan = r_info[1] if r_info else "SAY"
        ogr_kocu = r_info[4] if r_info else "Deniz Yılmaz"
        ogr_grubu = r_info[5] if (r_info and len(r_info)>5 and r_info[5]) else "12. Sınıf ve Mezun (2027 YKS)"
        
        # SADECE BU ÖĞRENCİYE ÖZEL MÜFREDATI YÜKLE
        OGRENCI_HAM_MUFREDAT = get_ham_mufredat(ogr_grubu)
        OGRENCI_EVRENSEL_MUFREDAT = get_evrensel_mufredat(ogr_grubu)

        col_o_head1, col_o_head2 = st.columns([0.8, 0.2])
        with col_o_head1:
            st.success(f"👤 **{aktif_ogr}** | Grup: **{ogr_grubu}** | Koç: **{ogr_kocu}**")
        with col_o_head2:
            if st.button("🚪 ÇIKIŞ YAP", key="ogr_logout_btn", use_container_width=True):
                st.session_state["aktif_ogrenci"] = None
                if "hatirla_ogr" in st.query_params: del st.query_params["hatirla_ogr"]
                st.rerun()

        tab_program, tab_ilerleme, tab_gunluk, tab_deneme = st.tabs([
            "📅 DERS PROGRAMI",
            "✅ İLERLEME TAKİBİ",
            "📝 GÜNLÜK ÇALIŞMA",
            "📊 DENEME YÜKLEME"
        ])

        with tab_program:
            st.markdown(f"""
            <div class="program-header-box">
                <h2 style="margin:0; font-size:22px; font-weight:800; color:white !important;">📅 {aktif_ogr.upper()} — HAFTALIK DERS PROGRAMI</h2>
                <p style="margin:5px 0 0 0; font-size:13px; opacity:0.9; color:white !important;">Koçunuz tarafından özel olarak hazırlanan haftalık çalışma planınız.</p>
            </div>
            """, unsafe_allow_html=True)

            conn_p = get_db_connection()
            df_p = pd.read_sql_query('SELECT saat_araligi AS "Saat", pazartesi AS "Pazartesi", sali AS "Salı", carsamba AS "Çarşamba", persembe AS "Perşembe", cuma AS "Cuma", cumartesi AS "Cumartesi", pazar AS "Pazar" FROM excel_program_matris WHERE ad_soyad = %s ORDER BY saat_araligi ASC', conn_p.conn, params=(aktif_ogr,))
            conn_p.close()

            if not df_p.empty:
                st.dataframe(df_p, use_container_width=True, height=400)
                html_bytes_ogr = html_to_pdf_bytes(df_p, aktif_ogr)
                st.download_button("📥 Programı İndir (.html / Yazdır)", data=html_bytes_ogr, file_name=f"{aktif_ogr}_Program.html", mime="text/html", use_container_width=True)
            else:
                st.info("ℹ️ Koçun henüz sana özel haftalık programını kaydetmedi.")

        with tab_ilerleme:
            st.markdown(f"### ✅ Konu İlerleme Takibi — ({ogr_grubu})")
            secilen_takip_ders = st.selectbox("İlerlemesini Görmek İstediğiniz Dersi Seçin:", list(OGRENCI_HAM_MUFREDAT.keys()), key="takip_ders_secim")
            konu_listesi_ogrenci = OGRENCI_HAM_MUFREDAT[secilen_takip_ders]

            conn_t = get_db_connection()
            cur_t = conn_t.cursor()
            takip_verileri = []
            for konu in konu_listesi_ogrenci:
                cur_t.execute("SELECT tamamlandi, soru_miktari FROM konu_ilerleme WHERE ad_soyad = %s AND ders = %s AND konu_adi = %s", (aktif_ogr, secilen_takip_ders, konu))
                res = cur_t.fetchone()
                takip_verileri.append({
                    "Konu Adı": konu,
                    "Tamamlandı ✅": bool(res[0]) if res else False,
                    "Çözülen Soru Miktarı": int(res[1]) if res else 0
                })
            conn_t.close()

            df_takip = pd.DataFrame(takip_verileri)

            with st.form(f"ilerleme_form_{secilen_takip_ders}"):
                edited_takip = st.data_editor(df_takip, use_container_width=True, hide_index=True, num_rows="fixed")
                if st.form_submit_button("💾 İlerlemeyi Kaydet", type="primary", use_container_width=True):
                    conn_sv = get_db_connection()
                    cur_sv = conn_sv.cursor()
                    for _, row in edited_takip.iterrows():
                        cur_sv.execute("""
                            INSERT INTO konu_ilerleme (ad_soyad, ders, konu_adi, tamamlandi, soru_miktari)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT(ad_soyad, ders, konu_adi) DO UPDATE SET tamamlandi = EXCLUDED.tamamlandi, soru_miktari = EXCLUDED.soru_miktari
                        """, (aktif_ogr, secilen_takip_ders, row["Konu Adı"], 1 if row["Tamamlandı ✅"] else 0, int(row["Çözülen Soru Miktarı"]) if pd.notna(row["Çözülen Soru Miktarı"]) else 0))
                    conn_sv.commit()
                    conn_sv.close()
                    st.success("🎉 İlerlemeniz başarıyla kaydedildi!")
                    st.rerun()

        with tab_gunluk:
            st.markdown(f"### 📝 Günlük Çalışma Girişi — ({ogr_grubu})")
            s_tarih = st.date_input("Çalışma Tarihi:", datetime.date.today())
            
            with st.form("gunluk_detayli_calisma_formu"):
                secilen_ders = st.selectbox("Çalıştığın Dersi Seç:", list(OGRENCI_EVRENSEL_MUFREDAT.keys()))
                secilen_konu = st.selectbox("Çalıştığın Konu:", OGRENCI_EVRENSEL_MUFREDAT.get(secilen_ders, ["Genel Konu"]))

                col_gc1, col_gc2, col_gc3 = st.columns(3)
                with col_gc1: girilen_soru = st.number_input("Çözülen Soru Sayısı:", 0, 500, 20)
                with col_gc2: girilen_konu_sure = st.number_input("Konu Anlatımı Süresi (Dk):", 0, 1440, 45)
                with col_gc3: girilen_cozum_sure = st.number_input("Soru Çözümü Süresi (Dk):", 0, 1440, 45)

                if st.form_submit_button("🚀 Çalışmayı Kaydet", type="primary", use_container_width=True):
                    conn_g = get_db_connection()
                    cur_g = conn_g.cursor()
                    cur_g.execute("""
                        INSERT INTO gunluk_calisma (ad_soyad, tarih, ders, konu, soru_sayisi, konu_anlatim_sure, soru_cozum_sure)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (aktif_ogr, str(s_tarih), secilen_ders, secilen_konu, int(girilen_soru), int(girilen_konu_sure), int(girilen_cozum_sure)))
                    conn_g.commit()
                    conn_g.close()
                    st.success(f"🎉 Kaydedildi! ({secilen_ders})")

        with tab_deneme:
            st.markdown(f"### 📊 Deneme Sınavı Sonuç Yükleme")
            with st.form("deneme_yukleme_formu"):
                dyayin = st.text_input("Deneme Yayın Adı:")
                dnet = st.number_input("Toplam Net:", 0.0, 120.0, 75.0)
                yuklenen_karne = st.file_uploader("Deneme Sonuç Belgesi (JPG/PDF):", type=["png", "jpg", "jpeg", "pdf"])
                
                if st.form_submit_button("📤 Denemeyi Gönder", type="primary", use_container_width=True) and dyayin:
                    dosya_yolu_db, dosya_adi_db = "", ""
                    if yuklenen_karne is not None:
                        dosya_adi_db = yuklenen_karne.name
                        dosya_yolu_db = os.path.join(KARNE_DIR, f"{datetime.date.today()}_{aktif_ogr}_{dosya_adi_db}")
                        with open(dosya_yolu_db, "wb") as f: f.write(yuklenen_karne.getbuffer())

                    conn_dn = get_db_connection()
                    cur_dn = conn_dn.cursor()
                    cur_dn.execute("""
                        INSERT INTO denemeler (ad_soyad, tarih, yayin, tur, toplam_net, dosya_yolu, dosya_adi, koc_notu)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (aktif_ogr, str(datetime.date.today()), dyayin, "Genel Deneme", float(dnet), dosya_yolu_db, dosya_adi_db, "Bekliyor."))
                    conn_dn.commit()
                    conn_dn.close()
                    st.success("🎉 Deneme sonucu gönderildi!")
                    st.rerun()

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
                    st.error("Hatalı giriş veya onaylanmamış hesap!")
    else:
        col_k_head1, col_k_head2 = st.columns([0.8, 0.2])
        with col_k_head1: st.success(f"👨‍🏫 Aktif Koç: **{st.session_state['aktif_koc']}**")
        with col_k_head2:
            if st.button("🚪 ÇIKIŞ YAP", key="koc_out"):
                st.session_state["aktif_koc"] = None
                st.rerun()

        # Onay Bekleyen Öğrenciler
        conn_b = get_db_connection()
        cur_b = conn_b.cursor()
        cur_b.execute("SELECT ad_soyad, alan, sinif_grubu FROM ogrenciler WHERE onaylandi = 0")
        bekleyen_ogrenciler = cur_b.fetchall()
        conn_b.close()
        
        if bekleyen_ogrenciler:
            st.warning(f"🔔 {len(bekleyen_ogrenciler)} Yeni Öğrenci Onay Bekliyor!")
            for b_ogr in bekleyen_ogrenciler:
                col_bo1, col_bo2, col_bo3, col_bo4 = st.columns([2, 2, 1, 1])
                with col_bo1: st.markdown(f"**{b_ogr[0]}**")
                with col_bo2: st.markdown(f"Sınıfı: {b_ogr[2]}")
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
            
            # SADECE SEÇİLEN ÖĞRENCİYE ÖZEL MÜFREDATI ÇEKİYORUZ!
            conn_ogr_detay = get_db_connection()
            cur_ogr_detay = conn_ogr_detay.cursor()
            cur_ogr_detay.execute("SELECT sinif_grubu FROM ogrenciler WHERE ad_soyad = %s", (secilen_ogr,))
            sec_ogr_grubu = cur_ogr_detay.fetchone()[0]
            conn_ogr_detay.close()
            
            KOC_ICIN_EVRENSEL_MUFREDAT = get_evrensel_mufredat(sec_ogr_grubu)

            st.divider()
            st.markdown(f"### 🗓️ {secilen_ogr} ({sec_ogr_grubu}) — Kişiye Özel Haftalık Program Düzenleyici")
            
            tum_dersler_listesi = list(KOC_ICIN_EVRENSEL_MUFREDAT.keys())
            saat_secenekleri = [f"{s:02d}" for s in range(7, 24)]
            dakika_secenekleri = [f"{d:02d}" for d in range(0, 60, 5)]
            
            c_saat1, c_dak1, c_saat2, c_dak2, c_gun = st.columns([1.1, 1.1, 1.1, 1.1, 1.6])
            with c_saat1: bas_saat = st.selectbox("Başlangıç Saat:", saat_secenekleri, index=1, key="koc_bas_saat")
            with c_dak1: bas_dakika = st.selectbox("Başlangıç Dakika:", dakika_secenekleri, index=0, key="koc_bas_dakika")
            with c_saat2: bit_saat = st.selectbox("Bitiş Saat:", saat_secenekleri, index=2, key="koc_bit_saat")
            with c_dak2: bit_dakika = st.selectbox("Bitiş Dakika:", dakika_secenekleri, index=0, key="koc_bit_dakika")
            with c_gun: hedef_gun_sec = st.selectbox("Uygulanacak Gün:", ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"])

            yeni_saat_araligi = f"{bas_saat}:{bas_dakika} - {bit_saat}:{bit_dakika}"

            c_s3, c_s4 = st.columns(2)
            # DİKKAT: Artık açılır menülerde sadece o öğrencinin sınıf grubuna ait dersler var!
            with c_s3: sec_ders_matris = st.selectbox("Ders / Aktivite Seçin:", tum_dersler_listesi)
            with c_s4: sec_konu_matris = st.selectbox("Alt Konu / Detay Seçin:", KOC_ICIN_EVRENSEL_MUFREDAT.get(sec_ders_matris, ["Genel Soru"]))

            if st.button("📥 Bu Hücreyi Tabloya İşle", type="primary", use_container_width=True):
                 hucre_degeri = f"{sec_ders_matris}\n↳ {sec_konu_matris}"
                 gun_sutun_map = {"Pazartesi": "pazartesi", "Salı": "sali", "Çarşamba": "carsamba", "Perşembe": "persembe", "Cuma": "cuma", "Cumartesi": "cumartesi", "Pazar": "pazar"}
                 t_sutun = gun_sutun_map[hedef_gun_sec]
                 conn_islem = get_db_connection()
                 cur_islem = conn_islem.cursor()
                 cur_islem.execute(f"""
                     INSERT INTO excel_program_matris (ad_soyad, saat_araligi, {t_sutun})
                     VALUES (%s, %s, %s)
                     ON CONFLICT(ad_soyad, saat_araligi) DO UPDATE SET {t_sutun} = EXCLUDED.{t_sutun}
                 """, (secilen_ogr, yeni_saat_araligi, hucre_degeri))
                 conn_islem.commit()
                 conn_islem.close()
                 st.success("Hücre eklendi!")
                 st.rerun()
                 
            st.markdown(f"#### 📊 Canlı Program Tablosu Düzenleyici")
            conn_m = get_db_connection()
            df_matris = pd.read_sql_query('SELECT saat_araligi AS "Saat Aralığı", pazartesi AS "Pazartesi", sali AS "Salı", carsamba AS "Çarşamba", persembe AS "Perşembe", cuma AS "Cuma", cumartesi AS "Cumartesi", pazar AS "Pazar" FROM excel_program_matris WHERE ad_soyad = %s ORDER BY saat_araligi ASC', conn_m.conn, params=(secilen_ogr,))
            conn_m.close()
            
            if df_matris.empty: df_matris = pd.DataFrame([{"Saat Aralığı": "08:00 - 09:00", "Pazartesi": "", "Salı": "", "Çarşamba": "", "Perşembe": "", "Cuma": "", "Cumartesi": "", "Pazar": ""}])
            edited_matris = st.data_editor(df_matris, num_rows="dynamic", use_container_width=True)

            if st.button("💾 Tablodaki Tüm Değişiklikleri Kaydet", type="primary", use_container_width=True):
                conn_sv2 = get_db_connection()
                cur_sv2 = conn_sv2.cursor()
                cur_sv2.execute("DELETE FROM excel_program_matris WHERE ad_soyad = %s", (secilen_ogr,))
                for _, row in edited_matris.iterrows():
                    s_ar = str(row.get("Saat Aralığı", "")).strip()
                    if s_ar and s_ar != "nan":
                        cur_sv2.execute("""
                            INSERT INTO excel_program_matris (ad_soyad, saat_araligi, pazartesi, sali, carsamba, persembe, cuma, cumartesi, pazar)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (secilen_ogr, s_ar, str(row.get("Pazartesi", "")), str(row.get("Salı", "")), str(row.get("Çarşamba", "")), str(row.get("Perşembe", "")), str(row.get("Cuma", "")), str(row.get("Cumartesi", "")), str(row.get("Pazar", ""))))
                conn_sv2.commit()
                conn_sv2.close()
                st.success("🎉 Program güncellendi!")
                st.rerun()

with main_tab3:
    st.markdown("## 👨‍👩‍👧‍👦 Veli Takip Ekranı (Bakım Aşamasında)")
    st.info("Bu ekran dinamik formata geçiriliyor.")