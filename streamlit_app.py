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
    page_title="YKS & LGS EVRENSEL KOÇLUK PLATFORMU",
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

@st.cache_data
def mufredat_yukle():
    if os.path.exists("mufredat.csv"):
        try:
            return pd.read_csv("mufredat.csv", sep=";")
        except Exception:
            pass
    return pd.DataFrame(columns=["Grup", "Ders", "Konu"])

def get_ham_mufredat(grup_adi):
    df = mufredat_yukle()
    if df.empty: return {"Örnek Ders": ["Örnek Konu"]}
    df_grup = df[df["Grup"] == grup_adi]
    if df_grup.empty: return {"Genel Ders": ["Genel Konu"]}
    mufredat_dict = {}
    for ders in df_grup["Ders"].unique():
        mufredat_dict[ders] = df_grup[df_grup["Ders"] == ders]["Konu"].tolist()
    return mufredat_dict

def get_evrensel_mufredat(grup_adi):
    ham = get_ham_mufredat(grup_adi)
    evrensel = {}
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

@st.cache_data
def yok_atlas_yukle():
    if os.path.exists("yok_atlas.csv"):
        try:
            return pd.read_csv("yok_atlas.csv", sep=";")
        except Exception:
            pass
    return pd.DataFrame(columns=["Universite", "Bolum", "Kategori", "TabanNet", "TabanSira", "TytNet", "AytNet"])

@st.cache_data
def lgs_hedefler_yukle():
    data = {
        "Il": ["İstanbul", "İstanbul", "Ankara", "Ankara", "İzmir", "Giresun"],
        "LiseTuru": ["Fen Lisesi", "Proje Anadolu Lisesi", "Fen Lisesi", "Proje Anadolu Lisesi", "Fen Lisesi", "Fen Lisesi"],
        "LiseAdi": ["İstanbul Atatürk Fen Lisesi", "Cağaloğlu Anadolu Lisesi", "Ankara Fen Lisesi", "Atatürk Anadolu Lisesi", "İzmir Fen Lisesi", "Giresun Aksu Fen Lisesi"],
        "Yuzdelik Dilim": [0.15, 0.75, 0.20, 1.10, 0.30, 2.50],
        "Taban Puan": [492.5, 485.0, 490.0, 478.0, 488.0, 465.0]
    }
    return pd.DataFrame(data)

def tablo_olustur():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ogrenciler (
        ad_soyad TEXT PRIMARY KEY, sifre TEXT, veli_pin TEXT DEFAULT '123456',
        sinav_turu TEXT DEFAULT 'YKS (TYT + AYT)', alan TEXT DEFAULT 'SAY (Sayısal)',
        hedef_uni TEXT DEFAULT '', hedef_bolum TEXT DEFAULT '', hedef_net FLOAT DEFAULT 80.0,
        hedef_sira TEXT DEFAULT '', koc_adi TEXT DEFAULT '', onaylandi INTEGER DEFAULT 0
    )
    """)
    try:
        cur.execute("ALTER TABLE ogrenciler ADD COLUMN sinif_grubu TEXT DEFAULT '12. Sınıf ve Mezun (2027 YKS)'")
        conn.commit()
    except Exception:
        conn.rollback()
    cur.execute("CREATE TABLE IF NOT EXISTS koclar (kullanici_adi TEXT PRIMARY KEY, sifre TEXT, onaylandi INTEGER DEFAULT 1)")
    cur.execute("CREATE TABLE IF NOT EXISTS gunluk_calisma (id SERIAL PRIMARY KEY, ad_soyad TEXT, tarih TEXT, ders TEXT, konu TEXT, soru_sayisi INTEGER DEFAULT 0, konu_anlatim_sure INTEGER DEFAULT 0, soru_cozum_sure INTEGER DEFAULT 0)")
    cur.execute("CREATE TABLE IF NOT EXISTS konu_ilerleme (ad_soyad TEXT, ders TEXT, konu_adi TEXT, tamamlandi INTEGER DEFAULT 0, soru_miktari INTEGER DEFAULT 0, PRIMARY KEY (ad_soyad, ders, konu_adi))")
    cur.execute("CREATE TABLE IF NOT EXISTS yapilamayan_sorular (id SERIAL PRIMARY KEY, ad_soyad TEXT, tarih TEXT, ders TEXT, konu TEXT, dosya_yolu TEXT, dosya_adi TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS denemeler (id SERIAL PRIMARY KEY, ad_soyad TEXT, tarih TEXT, yayin TEXT, tur TEXT, toplam_net FLOAT, dosya_yolu TEXT DEFAULT '', dosya_adi TEXT DEFAULT '', koc_notu TEXT DEFAULT '')")
    cur.execute("CREATE TABLE IF NOT EXISTS excel_program_matris (ad_soyad TEXT, saat_araligi TEXT, pazartesi TEXT DEFAULT '', sali TEXT DEFAULT '', carsamba TEXT DEFAULT '', persembe TEXT DEFAULT '', cuma TEXT DEFAULT '', cumartesi TEXT DEFAULT '', pazar TEXT DEFAULT '', PRIMARY KEY (ad_soyad, saat_araligi))")
    conn.commit()
    conn.close()

tablo_olustur()

st.markdown("""
<script>
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (prefersDark) { document.documentElement.setAttribute('data-theme', 'dark'); }
    else { document.documentElement.setAttribute('data-theme', 'light'); }
</script>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    html, body, p, label, input, textarea, select, h1, h2, h3, h4, h5, h6 { font-family: 'Plus Jakarta Sans', sans-serif !important; }
    @media (prefers-color-scheme: dark) {
        :root { --bg-gradient: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #020617 100%); --text-color: #f8fafc; --container-bg: #1e293b; --border-color: #334155; --input-bg: #0f172a; --input-text: #f8fafc; --tab-bg: #1e293b; --yok-box-bg: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); --hero-bg: linear-gradient(135deg, #0284c7 0%, #4f46e5 50%, #7c3aed 100%); }
    }
    @media (prefers-color-scheme: light) {
        :root { --bg-gradient: linear-gradient(135deg, #f0fdf4 0%, #e0f2fe 50%, #f3e8ff 100%); --text-color: #0f172a; --container-bg: #ffffff; --border-color: #cbd5e1; --input-bg: #ffffff; --input-text: #0f172a; --tab-bg: #ffffff; --yok-box-bg: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); --hero-bg: linear-gradient(135deg, #0ea5e9 0%, #6366f1 50%, #8b5cf6 100%); }
    }
    html, body, p, label, input, textarea, select { color: var(--text-color, #0f172a) !important; }
    #MainMenu, footer, header, .stDeployButton {display: none !important;}
    .stApp { background: var(--bg-gradient) !important; background-attachment: fixed !important; }
    .main .block-container { padding-top: 1rem !important; padding-bottom: 3rem !important; max-width: 1420px !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 6px; background: var(--tab-bg) !important; padding: 8px; border-radius: 16px; border: 1px solid var(--border-color) !important; }
    .stTabs [data-baseweb="tab"] { height: 48px; background-color: var(--container-bg) !important; border-radius: 10px; padding: 8px 16px; font-weight: 700 !important; font-size: 13px !important; color: var(--text-color) !important; border: 1px solid var(--border-color) !important; }
    .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%) !important; border: none !important; }
    .stTabs [aria-selected="true"] span, .stTabs [aria-selected="true"] div { color: #ffffff !important; }
    input, textarea, select, div[data-baseweb="select"] { background-color: var(--input-bg) !important; color: var(--input-text) !important; border: 1.5px solid var(--border-color) !important; border-radius: 10px !important; font-weight: 600 !important; }
    .hero-motivation-card { background: var(--hero-bg) !important; color: #ffffff !important; padding: 20px 24px; border-radius: 20px; font-weight: 700; margin-bottom: 20px; }
    .hero-motivation-card * { color: #ffffff !important; }
    .yok-net-box { background: var(--yok-box-bg) !important; border: 2px solid #3b82f6; border-radius: 16px; padding: 18px 22px; margin-bottom: 15px; }
    .yok-net-box * { color: var(--text-color) !important; }
    .program-header-box { background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%) !important; color: white !important; padding: 20px; border-radius: 16px; margin-bottom: 20px; text-align: center; }
    .program-header-box * { color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

def make_hash(password: str) -> str:
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), "YKS_PRO_SECURE_SALT_2026".encode('utf-8'), 100000).hex()

def verify_hash(password: str, hashed_password: str) -> bool:
    if not hashed_password: return False
    if password == hashed_password: return True
    if make_hash(password) == hashed_password: return True
    return False

def pdf_goster_html(pdf_path):
    try:
        with open(pdf_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode('utf-8')
        return f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="550" style="border-radius:12px; border:1px solid #cbd5e1;"></iframe>'
    except Exception:
        return "<p style='color:red;'>PDF okunamadı.</p>"

def html_to_pdf_bytes(df, ogrenci_adi):
    return f"""
    <!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8"><title>{ogrenci_adi}</title></head>
    <body style="font-family: Arial; padding: 25px;">
        <h2 style="text-align: center; color: #0284c7;">🎓 {ogrenci_adi.upper()} ÇALIŞMA PROGRAMI</h2>
        {df.to_html(index=False, classes='table', border=0)}
    </body></html>
    """.encode('utf-8')

MOTIVASYON_SOZLERI = [
    "🌿 Sakin ol, derin bir nefes al ve adım adım ilerle. Disiplin başarıyı getirir!",
    "🚀 Başarı, her gün ertelemeden tekrarlanan küçük çabaların birikimidir!"
]

st.markdown("""
<div style="text-align: center; padding: 10px 0 15px 0;">
    <span style="font-size: 42px;">🎓</span>
    <h1 style="margin: 0; font-weight: 800; font-size: 26px;">EVRENSEL KOÇLUK PLATFORMU</h1>
    <p style="margin: 0; font-size: 14px; color: #0284c7; font-weight: 700;">DENİZ YILMAZ</p>
</div>
""", unsafe_allow_html=True)

main_tab1, main_tab2, main_tab3 = st.tabs(["👨‍🎓 ÖĞRENCİ PANELİ", "👨‍🏫 KOÇ YÖNETİM PANELİ", "👨‍👩‍👧‍👦 VELİ TAKİP EKRANI"])

with main_tab1:
    if "motivasyon_goster" not in st.session_state: st.session_state["motivasyon_goster"] = True
    if "motivasyon_sozu" not in st.session_state: st.session_state["motivasyon_sozu"] = random.choice(MOTIVASYON_SOZLERI)
        
    if st.session_state["motivasyon_goster"]:
        col_m1, col_m2 = st.columns([0.9, 0.1])
        with col_m1:
            st.markdown(f'<div class="hero-motivation-card"><div style="font-size:11px; letter-spacing:2px; font-weight:800; margin-bottom:4px;">⚡ GÜNÜN MOTİVASYONU</div><div style="font-size:16px; font-weight:800;">"{st.session_state["motivasyon_sozu"]}"</div></div>', unsafe_allow_html=True)
        with col_m2:
            if st.button("❌", key="kapat_m"): st.session_state["motivasyon_goster"] = False; st.rerun()
    
    aktif_ogr = st.session_state.get("aktif_ogrenci", None)
    if not aktif_ogr and "hatirla_ogr" in st.query_params:
        aktif_ogr = st.query_params["hatirla_ogr"]
        st.session_state["aktif_ogrenci"] = aktif_ogr

    if not aktif_ogr:
        tab_log, tab_reg = st.tabs(["🔑 GİRİŞ YAP", "➕ YENİ HESAP OLUŞTUR"])
        with tab_log:
            with st.form("ogr_giris"):
                lad = st.text_input("Ad Soyad:").strip().title()
                lsif = st.text_input("Şifre:", type="password")
                hatirla = st.checkbox("Beni Hatırla")
                if st.form_submit_button("Giriş Yap", type="primary", use_container_width=True):
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute("SELECT sifre, onaylandi FROM ogrenciler WHERE ad_soyad = %s", (lad,))
                    res = cur.fetchone()
                    conn.close()
                    if res and verify_hash(lsif, res[0]) and res[1] == 1:
                        st.session_state["aktif_ogrenci"] = lad
                        if hatirla: st.query_params["hatirla_ogr"] = lad
                        st.rerun()
                    else:
                        st.error("Hatalı giriş veya onaylanmamış hesap!")
        with tab_reg:
            with st.form("ogr_kayit"):
                rad = st.text_input("Ad Soyad:").strip().title()
                rsif = st.text_input("Şifre Belirle:", type="password")
                rpin = st.text_input("Veli PIN:", value="123456")
                
                df_g = mufredat_yukle()
                gruplar = df_g["Grup"].unique().tolist() if not df_g.empty else ["12. Sınıf ve Mezun (2027 YKS)", "8. Sınıf (LGS)"]
                rgrup = st.selectbox("Sınıfınız / Grubunuz:", gruplar)
                
                conn_k = get_db_connection()
                cur_k = conn_k.cursor()
                cur_k.execute("SELECT kullanici_adi FROM koclar WHERE onaylandi = 1")
                koclar = [k[0] for k in cur_k.fetchall()]
                conn_k.close()
                if not koclar: koclar = ["Deniz Yılmaz"]
                rkoc = st.selectbox("Koçunuz:", koclar)
                ralan = st.selectbox("Alan / Kategori:", ["SAY", "EA", "SÖZ", "DİL", "LGS Ortak"])

                if st.form_submit_button("Kayıt Ol", type="primary", use_container_width=True):
                    if rad and rsif:
                        conn = get_db_connection()
                        cur = conn.cursor()
                        cur.execute("INSERT INTO ogrenciler (ad_soyad, sifre, veli_pin, alan, sinif_grubu, koc_adi, onaylandi) VALUES (%s, %s, %s, %s, %s, %s, 0)",
                                    (rad, make_hash(rsif), rpin, ralan, rgrup, rkoc))
                        conn.commit()
                        conn.close()
                        st.success("Kayıt oluşturuldu, koç onayı bekleniyor.")
    else:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT koc_adi, sinif_grubu FROM ogrenciler WHERE ad_soyad = %s", (aktif_ogr,))
        inf = cur.fetchone()
        conn.close()
        
        ogrupu = inf[1] if (inf and len(inf)>1 and inf[1]) else "12. Sınıf ve Mezun (2027 YKS)"
        
        col_h1, col_h2 = st.columns([0.8, 0.2])
        with col_h1: st.success(f"👤 **{aktif_ogr}** | Grup: **{ogrupu}**")
        with col_h2:
            if st.button("Çıkış Yap", use_container_width=True):
                st.session_state["aktif_ogrenci"] = None
                if "hatirla_ogr" in st.query_params: del st.query_params["hatirla_ogr"]
                st.rerun()

        tab_hedef, tab_program, tab_ilerleme, tab_gunluk, tab_deneme = st.tabs([
            "🎯 HEDEF & NET MERKEZİ", "📅 DERS PROGRAMI", "✅ İLERLEME", "📝 ÇALIŞMA", "📊 DENEME"
        ])

        with tab_hedef:
            if "LGS" in ogrupu:
                st.markdown("### 🎯 LGS Lise Hedef & Yüzdelik Dilim Merkezi")
                df_lgs = lgs_hedefler_yukle()
                col_l1, col_l2, col_l3 = st.columns(3)
                with col_l1: sec_il = st.selectbox("İl Seçin:", df_lgs["Il"].unique().tolist())
                with col_l2: sec_tur = st.selectbox("Lise Türü:", df_lgs[df_lgs["Il"]==sec_il]["LiseTuru"].unique().tolist())
                with col_l3: sec_lise = st.selectbox("Okul Adı:", df_lgs[(df_lgs["Il"]==sec_il)&(df_lgs["LiseTuru"]==sec_tur)]["LiseAdi"].unique().tolist())
                
                lise_satir = df_lgs[df_lgs["LiseAdi"] == sec_lise].iloc[0]
                st.markdown(f"""
                <div class="yok-net-box">
                    <h4 style="margin:0 0 10px 0;">🏫 {sec_lise}</h4>
                    <p><b>Hedef Taban Yüzdelik Dilim:</b> %{lise_satir['Yuzdelik Dilim']}</p>
                    <p><b>Hedef Taban Puan:</b> {lise_satir['Taban Puan']} Puan</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Bu Lise Hedefini Kaydet", type="primary", use_container_width=True):
                    conn = get_db_connection()
                    conn.cursor().execute("UPDATE ogrenciler SET hedef_uni = %s, hedef_bolum = %s WHERE ad_soyad = %s", (sec_il, sec_lise, aktif_ogr))
                    conn.commit()
                    conn.close()
                    st.success("LGS hedefiniz kaydedildi!")
            else:
                st.markdown("### 🎯 YÖK Atlas Üniversite & Bölüm Hedef Merkezi")
                df_yok = yok_atlas_yukle()
                if df_yok.empty:
                    st.warning("yok_atlas.csv dosyası eksik veya boş.")
                else:
                    col_y1, col_y2, col_y3 = st.columns(3)
                    with col_y1: u_list = df_yok["Universite"].unique().tolist(); suni = st.selectbox("Üniversite:", u_list)
                    with col_y2: k_list = df_yok[df_yok["Universite"]==suni]["Kategori"].unique().tolist(); skat = st.selectbox("Kategori:", k_list)
                    with col_y3: b_list = df_yok[(df_yok["Universite"]==suni)&(df_yok["Kategori"]==skat)]["Bolum"].unique().tolist(); sbol = st.selectbox("Bölüm:", b_list)
                    
                    satir = df_yok[(df_yok["Universite"]==suni)&(df_yok["Kategori"]==skat)&(df_yok["Bolum"]==sbol)].iloc[0]
                    st.markdown(f"""
                    <div class="yok-net-box">
                        <h4>🏛️ {suni} — {sbol}</h4>
                        <p><b>YÖK Atlas Taban Net:</b> {satir['TabanNet']} Net | <b>Sıra:</b> İlk {satir['TabanSira']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("Üniversite Hedefini Kaydet", type="primary", use_container_width=True):
                        conn = get_db_connection()
                        conn.cursor().execute("UPDATE ogrenciler SET hedef_uni = %s, hedef_bolum = %s WHERE ad_soyad = %s", (suni, sbol, aktif_ogr))
                        conn.commit()
                        conn.close()
                        st.success("YKS hedefiniz kaydedildi!")

        with tab_program:
            st.markdown('<div class="program-header-box"><h2>📅 Haftalık Program</h2></div>', unsafe_allow_html=True)
            conn = get_db_connection()
            df_p = pd.read_sql_query('SELECT saat_araligi AS "Saat", pazartesi AS "Pazartesi", sali AS "Salı", carsamba AS "Çarşamba", persembe AS "Perşembe", cuma AS "Cuma", cumartesi AS "Cumartesi", pazar AS "Pazar" FROM excel_program_matris WHERE ad_soyad = %s ORDER BY saat_araligi ASC', conn.conn, params=(aktif_ogr,))
            conn.close()
            if not df_p.empty:
                st.dataframe(df_p, use_container_width=True)
                st.download_button("Programı İndir", html_to_pdf_bytes(df_p, aktif_ogr), file_name=f"{aktif_ogr}_program.html", mime="text/html", use_container_width=True)
            else:
                st.info("Programınız henüz hazırlanmadı.")

        with tab_ilerleme:
            st.markdown("### ✅ Konu İlerleme")
            ham_m = get_ham_mufredat(ogrupu)
            ders_sec = st.selectbox("Ders Seç:", list(ham_m.keys()))
            konular = ham_m[ders_sec]
            
            conn = get_db_connection()
            cur = conn.cursor()
            veri = []
            for k in konular:
                cur.execute("SELECT tamamlandi, soru_miktari FROM konu_ilerleme WHERE ad_soyad = %s AND ders = %s AND konu_adi = %s", (aktif_ogr, ders_sec, k))
                r = cur.fetchone()
                veri.append({"Konu": k, "Tamamlandı ✅": bool(r[0]) if r else False, "Soru": int(r[1]) if r else 0})
            conn.close()
            
            df_t = pd.DataFrame(veri)
            with st.form("form_t"):
                ed_t = st.data_editor(df_t, use_container_width=True, hide_index=True)
                if st.form_submit_button("İlerlemeyi Kaydet", type="primary", use_container_width=True):
                    conn = get_db_connection()
                    cur = conn.cursor()
                    for _, row in ed_t.iterrows():
                        cur.execute("INSERT INTO konu_ilerleme (ad_soyad, ders, konu_adi, tamamlandi, soru_miktari) VALUES (%s, %s, %s, %s, %s) ON CONFLICT(ad_soyad, ders, konu_adi) DO UPDATE SET tamamlandi = EXCLUDED.tamamlandi, soru_miktari = EXCLUDED.soru_miktari",
                                    (aktif_ogr, ders_sec, row["Konu"], 1 if row["Tamamlandı ✅"] else 0, int(row["Soru"])))
                    conn.commit()
                    conn.close()
                    st.success("Kaydedildi!")
                    st.rerun()

        with tab_gunluk:
            st.markdown("### 📝 Günlük Çalışma Girişi")
            evr_m = get_evrensel_mufredat(ogrupu)
            with st.form("g_form"):
                dtarih = st.date_input("Tarih:", datetime.date.today())
                gders = st.selectbox("Ders:", list(evr_m.keys()))
                gkonu = st.selectbox("Konu:", evr_m.get(gders, ["Genel"]))
                gsoru = st.number_input("Soru Sayısı:", 0, 500, 20)
                gkons = st.number_input("Konu Anlatım (Dk):", 0, 1440, 45)
                gcozs = st.number_input("Soru Çözüm (Dk):", 0, 1440, 45)
                if st.form_submit_button("Çalışmayı Kaydet", type="primary", use_container_width=True):
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute("INSERT INTO gunluk_calisma (ad_soyad, tarih, ders, konu, soru_sayisi, konu_anlatim_sure, soru_cozum_sure) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                                (aktif_ogr, str(dtarih), gders, gkonu, gsoru, gkons, gcozs))
                    conn.commit()
                    conn.close()
                    st.success("Çalışma eklendi!")

        with tab_deneme:
            st.markdown("### 📊 Deneme Yükle")
            with st.form("dn_form"):
                dyayin = st.text_input("Yayın Adı:")
                dnet = st.number_input("Net:", 0.0, 500.0, 75.0)
                yuklenen_karne = st.file_uploader("Sonuç Belgesi (JPG/PDF):", type=["png", "jpg", "jpeg", "pdf"])
                if st.form_submit_button("Gönder", type="primary", use_container_width=True) and dyayin:
                    dosya_yolu_db = ""
                    if yuklenen_karne is not None:
                        dosya_yolu_db = os.path.join(KARNE_DIR, f"{datetime.date.today()}_{aktif_ogr}_{yuklenen_karne.name}")
                        with open(dosya_yolu_db, "wb") as f: f.write(yuklenen_karne.getbuffer())
                    conn = get_db_connection()
                    conn.cursor().execute("INSERT INTO denemeler (ad_soyad, tarih, yayin, tur, toplam_net, dosya_yolu) VALUES (%s, %s, %s, %s, %s, %s)", (aktif_ogr, str(datetime.date.today()), dyayin, "Genel", dnet, dosya_yolu_db))
                    conn.commit()
                    conn.close()
                    st.success("Deneme kaydedildi!")

with main_tab2:
    st.markdown("## 👨‍🏫 Koç Yönetim Paneli")
    if "aktif_koc" not in st.session_state: st.session_state["aktif_koc"] = None
    
    if not st.session_state["aktif_koc"]:
        with st.form("koc_giris"):
            kad = st.text_input("Koç Kullanıcı Adı:")
            ksif = st.text_input("Şifre:", type="password")
            if st.form_submit_button("Giriş Yap", type="primary"):
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("SELECT sifre FROM koclar WHERE kullanici_adi = %s", (kad,))
                res = cur.fetchone()
                conn.close()
                if res and verify_hash(ksif, res[0]):
                    st.session_state["aktif_koc"] = kad
                    st.rerun()
                else:
                    st.error("Hatalı koç şifresi!")
    else:
        col_kk1, col_kk2 = st.columns([0.8, 0.2])
        with col_kk1: st.success(f"👨‍🏫 Koç: **{st.session_state['aktif_koc']}**")
        with col_kk2:
            if st.button("Çıkış", use_container_width=True): st.session_state["aktif_koc"] = None; st.rerun()
            
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT ad_soyad, sinif_grubu FROM ogrenciler WHERE onaylandi = 0")
        bekleyen = cur.fetchall()
        conn.close()
        
        if bekleyen:
            st.warning(f"🔔 {len(bekleyen)} öğrenci onay bekliyor!")
            for b in bekleyen:
                col_b1, col_b2, col_b3 = st.columns([3, 1, 1])
                with col_b1: st.write(f"**{b[0]}** ({b[1]})")
                with col_b2:
                    if st.button("Onayla", key=f"onay_{b[0]}"):
                        conn = get_db_connection()
                        conn.cursor().execute("UPDATE ogrenciler SET onaylandi = 1 WHERE ad_soyad = %s", (b[0],))
                        conn.commit()
                        conn.close()
                        st.rerun()
                with col_b3:
                    if st.button("Sil", key=f"sil_{b[0]}"):
                        conn = get_db_connection()
                        conn.cursor().execute("DELETE FROM ogrenciler WHERE ad_soyad = %s", (b[0],))
                        conn.commit()
                        conn.close()
                        st.rerun()

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT ad_soyad FROM ogrenciler WHERE koc_adi = %s AND onaylandi = 1", (st.session_state['aktif_koc'],))
        ogrs = [o[0] for o in cur.fetchall()]
        conn.close()

        if ogrs:
            s_ogr = st.selectbox("Öğrenci Seç:", ogrs)
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT sinif_grubu FROM ogrenciler WHERE ad_soyad = %s", (s_ogr,))
            s_grup = cur.fetchone()[0]
            conn.close()
            
            evr_muf = get_evrensel_mufredat(s_grup)
            
            st.markdown(f"### 🗓️ {s_ogr} ({s_grup}) — Haftalık Program Düzenleyici")
            with st.form("prog_duzenle"):
                gun = st.selectbox("Gün:", ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"])
                saat = st.selectbox("Saat Aralığı:", ["08:00 - 09:00", "09:00 - 10:00", "10:00 - 11:00", "11:00 - 12:00", "13:00 - 14:00", "14:00 - 15:00", "15:00 - 16:00", "16:00 - 17:00", "17:00 - 18:00", "19:00 - 20:00", "20:00 - 21:00"])
                ders_sec = st.selectbox("Ders:", list(evr_muf.keys()))
                konu_sec = st.selectbox("Konu:", evr_muf.get(ders_sec, ["Genel"]))
                
                if st.form_submit_button("Program Satırını Güncelle", type="primary", use_container_width=True):
                    sutun_map = {"Pazartesi": "pazartesi", "Salı": "sali", "Çarşamba": "carsamba", "Perşembe": "persembe", "Cuma": "cuma", "Cumartesi": "cumartesi", "Pazar": "pazar"}
                    sutun = sutun_map[gun]
                    deger = f"{ders_sec}\n↳ {konu_sec}"
                    
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute(f"INSERT INTO excel_program_matris (ad_soyad, saat_araligi, {sutun}) VALUES (%s, %s, %s) ON CONFLICT(ad_soyad, saat_araligi) DO UPDATE SET {sutun} = EXCLUDED.{sutun}",
                                (s_ogr, saat, deger))
                    conn.commit()
                    conn.close()
                    st.success("Program hücresi güncellendi!")
                    st.rerun()

            st.markdown(f"### 📊 {s_ogr} — Denemeler ve Çalışma Kayıtları")
            conn = get_db_connection()
            df_dn = pd.read_sql_query('SELECT tarih AS "Tarih", yayin AS "Yayın", toplam_net AS "Net", koc_notu AS "Koç Notu" FROM denemeler WHERE ad_soyad = %s', conn.conn, params=(s_ogr,))
            conn.close()
            if not df_dn.empty: st.dataframe(df_dn, use_container_width=True)
            else: st.info("Öğrencinin deneme kaydı yok.")

with main_tab3:
    st.markdown("## 👨‍👩‍👧‍👦 Veli Takip Ekranı")
    with st.form("v_giris"):
        vad = st.text_input("Öğrenci Adı:").strip().title()
        vpin = st.text_input("Veli PIN:", type="password")
        if st.form_submit_button("Veli Paneli Aç", type="primary", use_container_width=True):
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT veli_pin, onaylandi FROM ogrenciler WHERE ad_soyad = %s", (vad,))
            vrow = cur.fetchone()
            conn.close()
            if vrow and vpin == vrow[0] and vrow[1] == 1:
                st.session_state[f"veli_OK_{vad}"] = True
                st.success(f"Veli girişi başarılı: {vad}")
                st.rerun()
            else:
                st.error("Hatalı öğrenci adı veya Veli PIN!")