import streamlit as st
import datetime
import pandas as pd
import sqlite3
import hashlib

# Sayfa Yapılandırması
st.set_page_config(
    page_title="YKS Sayısal Koçluk Platformu",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# SQLite Veritabanı Bağlantı Fonksiyonu
def get_db():
    conn = sqlite3.connect("yks_kocluk.db", check_same_thread=False)
    return conn

# Veritabanı Tablolarını İlklendirme
def init_db():
    conn = get_db()
    c = conn.cursor()
    # Öğrenciler Tablosu
    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            password TEXT
        )
    ''')
    # Günlük Çalışma Kaydı
    c.execute('''
        CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            date TEXT,
            sure REAL,
            paragraf_prob INT,
            mat_geo INT,
            fen INT,
            turkce_sos INT,
            bos_yanlis INT,
            verim INT,
            notlar TEXT
        )
    ''')
    # Deneme Netleri & Karne Kaydı
    c.execute('''
        CREATE TABLE IF NOT EXISTS denemeler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            deneme_turu TEXT,
            deneme_adi TEXT,
            mat REAL,
            fiz REAL,
            kim REAL,
            biy REAL,
            turk REAL,
            sos REAL,
            toplam_net REAL,
            karne_adi TEXT,
            tarih TEXT
        )
    ''')
    # Konu Anlama Dereceleri (1-5 Puan)
    c.execute('''
        CREATE TABLE IF NOT EXISTS topic_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            subject TEXT,
            topic TEXT,
            rating INT,
            UNIQUE(student_id, subject, topic)
        )
    ''')
    # Koç Ödevleri Tablosu
    c.execute('''
        CREATE TABLE IF NOT EXISTS odevler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            ders TEXT,
            detay TEXT,
            son_tarih TEXT,
            durum TEXT DEFAULT 'Bekliyor'
        )
    ''')
    conn.commit()
    conn.close()

init_db()

YKS_KONULARI = {
    "📐 Matematik & Geometri": [
        "Temel Kavramlar & Sayı Basamakları", "Bölme-Bölünebilme & EBOB-EKOK",
        "Rasyonel Sayılar & Basit Eşitsizlikler", "Mutlak Değer & Üslü-Köklü Sayılar",
        "Çarpanlara Ayırma & Oran-Orantı", "Problemler (Sayı, Kesir, Yaş, Yüzde, Hız)",
        "Kümeler, Mantık & Fonksiyonlar", "Polinomlar & 2. Dereceden Denklemler",
        "Karmaşık Sayılar & Parabol", "Permütasyon, Kombinasyon, Olasılık",
        "Trigonometri (TYT & AYT)", "Logaritma & Diziler",
        "Limit & Süreklilik", "Türev ve Uygulamaları", "İntegral ve Uygulamaları",
        "Doğruda ve Üçgende Açılar", "Özel Üçgenler (Dik, İkizkenar, Eşkenar)",
        "Üçgende Alan, Eşlik ve Benzerlik", "Çokgenler ve Dörtgenler",
        "Çember ve Daire", "Analitik Geometri", "Katı Cisimler (Prizma, Piramit, Küre)"
    ],
    "⚡ Fizik": [
        "Fizik Bilimine Giriş & Madde Özellikleri", "Basınç ve Kaldırma Kuvveti",
        "Isı, Sıcaklık ve Genleşme", "Hareket ve Kuvvet", "İş, Güç ve Enerji",
        "Elektrik ve Manyetizma", "Dalgalar & Optik",
        "Vektörler, Tork ve Denge", "Bağıl Hareket & Newton'un Hareket Yasaları",
        "Atışlar & Momentum", "Çembersel Hareket & Harmonik Hareket",
        "Elektriksel Potansiyel & Manyetik Kuvvet", "Alternatif Akım & Transformatörler",
        "Modern Fizik & Atom Fiziği"
    ],
    "🧪 Kimya": [
        "Kimya Bilimi & Atomun Yapısı", "Periyodik Sistem & Etkileşimler",
        "Maddenin Halleri & Kimyanın Temel Kanunları", "Karışımlar, Asitler, Bazlar ve Tuzlar",
        "Modern Atom Teorisi", "Gazlar & Gaz Yasaları",
        "Sıvı Çözeltiler ve Çözünürlük", "Tepkimelerde Enerji & Hız",
        "Kimyasal Denge & Asit-Baz Dengesi", "KÇÇ (Çözünürlük Dengesi)",
        "Kimya ve Elektrik (Piller & Elektroliz)", "Karbon Kimyasına Giriş & Organik Kimya"
    ],
    "🧬 Biyoloji": [
        "Yaşam Bilimi Biyoloji & Hücre", "Canlıların Sınıflandırılması",
        "Hücre Bölünmeleri & Kalıtım", "Ekosistem Ekolojisi",
        "İnsan Fizyolojisi / Sistemler (Sinir, Sindirim, Dolaşım vb.)",
        "Komünite ve Popülasyon Ekolojisi", "Nükleik Asitler & Protein Sentezi",
        "Canlılarda Enerji Dönüşümleri (Fotosentez, Solunum)", "Bitki Biyolojisi"
    ]
}

st.title("🎓 YKS Sayısal Koçluk ve Performans Platformu")

yks_tarihi = datetime.date(2027, 6, 20)
bugun = datetime.date.today()
kalan_gun = (yks_tarihi - bugun).days
st.caption(f"📅 Bugün: {bugun.strftime('%d.%m.%Y')} | ⏳ YKS Maratonuna Kalan: **{max(kalan_gun, 0)} Gün**")
st.divider()

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user_role"] = None
    st.session_state["user_id"] = None
    st.session_state["user_name"] = None

if not st.session_state["logged_in"]:
    st.sidebar.title("🔐 Kullanıcı Girişi")
    giris_turu = st.sidebar.radio("Giriş Türü:", ["👨‍🎓 Öğrenci Girişi / Kayıt", "👨‍🏫 Koç Girişi"])

    if giris_turu == "👨‍🎓 Öğrenci Girişi / Kayıt":
        st.subheader("👨‍🎓 Öğrenci Paneli Girişi")
        islem = st.tabs(["🔑 Giriş Yap", "📝 Yeni Hesap Oluştur"])
        
        with islem[0]:
            student_name = st.text_input("Ad Soyad:", key="login_name")
            student_pin = st.text_input("Şifre / PIN:", type="password", key="login_pin")
            if st.button("Giriş Yap", type="primary"):
                conn = get_db()
                c = conn.cursor()
                hashed_pin = hashlib.sha256(student_pin.encode()).hexdigest()
                c.execute("SELECT id, name FROM students WHERE name = ? AND password = ?", (student_name.strip().title(), hashed_pin))
                res = c.fetchone()
                conn.close()
                if res:
                    st.session_state["logged_in"] = True
                    st.session_state["user_role"] = "Öğrenci"
                    st.session_state["user_id"] = res[0]
                    st.session_state["user_name"] = res[1]
                    st.success(f"Hoş geldin, {res[1]}!")
                    st.rerun()
                else:
                    st.error("❌ Ad Soyad veya Şifre hatalı!")
                    
        with islem[1]:
            new_name = st.text_input("Adınız Soyadınız:", key="reg_name")
            new_pin = st.text_input("Belirleyeceğiniz Şifre / PIN:", type="password", key="reg_pin")
            if st.button("Kayıt Ol ve Giriş Yap"):
                if new_name and new_pin:
                    conn = get_db()
                    c = conn.cursor()
                    try:
                        hashed_pin = hashlib.sha256(new_pin.encode()).hexdigest()
                        formatted_name = new_name.strip().title()
                        c.execute("INSERT INTO students (name, password) VALUES (?, ?)", (formatted_name, hashed_pin))
                        conn.commit()
                        student_id = c.lastrowid
                        conn.close()
                        st.session_state["logged_in"] = True
                        st.session_state["user_role"] = "Öğrenci"
                        st.session_state["user_id"] = student_id
                        st.session_state["user_name"] = formatted_name
                        st.success("✅ Hesabınız veritabanına kaydedildi!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("⚠️ Bu isimde bir öğrenci zaten kayıtlı! Lütfen Giriş Yap sekmesini kullanın.")
                else:
                    st.warning("Lütfen tüm alanları doldurun.")

    else:
        st.subheader("👨‍🏫 Koç / Öğretmen Girişi")
        koc_pin = st.text_input("Koç Giriş Şifresi:", type="password")
        if st.button("Koç Paneline Giriş Yap", type="primary"):
            if koc_pin == "1234":
                st.session_state["logged_in"] = True
                st.session_state["user_role"] = "Koç"
                st.session_state["user_name"] = "Koç / Öğretmen"
                st.success("Giriş Başarılı!")
                st.rerun()
            else:
                st.error("❌ Hatalı Koç Şifresi! (Varsayılan: 1234)")

else:
    c_user, c_out = st.sidebar.columns([2, 1])
    c_user.write(f"👤 **{st.session_state['user_name']}** ({st.session_state['user_role']})")
    if c_out.button("Çıkış"):
        st.session_state["logged_in"] = False
        st.session_state["user_role"] = None
        st.session_state["user_id"] = None
        st.session_state["user_name"] = None
        st.rerun()

    st.sidebar.divider()

    if st.session_state["user_role"] == "Öğrenci":
        tab1, tab2, tab3, tab4 = st.tabs([
            "📝 Günlük Çalışma Girişi", 
            "📊 Deneme Netlerim & Karne", 
            "🗺️ YKS Konu Anlama Derecem", 
            "🎯 Ödevlerim & Koç Notları"
        ])
        
        with tab1:
            st.subheader("📝 Günlük Çalışma & Soru Sayısı Girişi")
            col1, col2 = st.columns(2)
            with col1:
                tarih = st.date_input("Tarih", datetime.date.today())
                sure = st.number_input("Çalışma Süresi (Saat)", 0.0, 16.0, 7.5, 0.5)
                paragraf_prob = st.number_input("Paragraf & Problem (Soru)", 0, value=40, step=5)
                mat_geo = st.number_input("TYT/AYT Mat & Geometri (Soru)", 0, value=60, step=5)
            with col2:
                fen = st.number_input("Fizik, Kimya, Biyoloji (Soru)", 0, value=50, step=5)
                turkce_sos = st.number_input("Türkçe & Sosyal (Soru)", 0, value=30, step=5)
                bos_yanlis = st.number_input("Yapılamayan / Boş Soru Sayısı", 0, value=5, step=1)
                verim = st.slider("Günün Verim Puanı (1-10)", 1, 10, 8)
                
            notlar = st.text_area("Zorlandığın konular / Koçuna iletmek istediğin mesaj:")
            
            if st.button("🚀 Günlük Raporu Kaydet", type="primary", use_container_width=True):
                conn = get_db()
                c = conn.cursor()
                c.execute('''
                    INSERT INTO daily_logs (student_id, date, sure, paragraf_prob, mat_geo, fen, turkce_sos, bos_yanlis, verim, notlar)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (st.session_state["user_id"], str(tarih), sure, paragraf_prob, mat_geo, fen, turkce_sos, bos_yanlis, verim, notlar))
                conn.commit()
                conn.close()
                toplam = paragraf_prob + mat_geo + fen + turkce_sos
                st.success(f"✅ Rapor veritabanına kaydedildi! Toplam Soru: **{toplam}**")

        with tab2:
            st.subheader("📊 Deneme Net Kaydı & Karne Yükleme")
            d_turu = st.selectbox("Deneme Türü", ["TYT Denemesi", "AYT Sayısal Denemesi"])
            d_adi = st.text_input("Deneme Yayını / Adı", placeholder="Örn: 3D Yayınları Türkiye Geneli-1")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                mat = st.number_input("Matematik Net", 0.0, 40.0, 30.0, 0.25)
                fiz = st.number_input("Fizik Net", 0.0, 14.0, 10.0, 0.25)
            with c2:
                kim = st.number_input("Kimya Net", 0.0, 13.0, 10.0, 0.25)
                biy = st.number_input("Biyoloji Net", 0.0, 13.0, 10.0, 0.25)
            with c3:
                turkce = st.number_input("Türkçe Net", 0.0, 40.0, 32.0, 0.25)
                sos_net = st.number_input("Sosyal Net", 0.0, 20.0, 12.0, 0.25)

            if d_turu == "TYT Denemesi":
                toplam_net = turkce + mat + fiz + kim + biy + sos_net
            else:
                toplam_net = mat + fiz + kim + biy
                
            st.metric("🎯 Hesaplanan Toplam Net", f"{toplam_net:.2f}")
            
            karne = st.file_uploader("📄 Deneme Karnesi / Fotoğrafı Yükle (PDF, PNG, JPG):", type=["pdf", "png", "jpg", "jpeg"])
            karne_adi = karne.name if karne is not None else "Dosya Yok"

            if st.button("📈 Deneme Netini ve Karneyi Kaydet", type="primary"):
                conn = get_db()
                c = conn.cursor()
                c.execute('''
                    INSERT INTO denemeler (student_id, deneme_turu, deneme_adi, mat, fiz, kim, biy, turk, sos, toplam_net, karne_adi, tarih)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (st.session_state["user_id"], d_turu, d_adi, mat, fiz, kim, biy, turkce, sos_net, toplam_net, karne_adi, str(datetime.date.today())))
                conn.commit()
                conn.close()
                st.success("✅ Deneme sonucu veritabanına başarıyla aktarıldı!")

            st.divider()
            st.markdown("##### 📜 Geçmiş Deneme Sonuçlarım")
            conn = get_db()
            df_deneme = pd.read_sql_query("SELECT deneme_turu as 'Tür', deneme_adi as 'Deneme', toplam_net as 'Toplam Net', karne_adi as 'Karne Dosyası', tarih as 'Tarih' FROM denemeler WHERE student_id = ?", conn, params=(st.session_state["user_id"],))
            conn.close()
            if not df_deneme.empty:
                st.dataframe(df_deneme, use_container_width=True)
            else:
                st.info("Henüz kaydedilmiş bir deneme bulunmuyor.")

        with tab3:
            st.subheader("🗺️ YKS Konu Anlama Derecelendirmesi")
            st.info("💡 Konuları 1 (Çok Eksiğim Var) ile 5 (Tam Ustalaştım) arasında puanlayın. Koçunuz veritabanından eksiklerinizi anlık görecektir.")

            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT subject, topic, rating FROM topic_ratings WHERE student_id = ?", (st.session_state["user_id"],))
            existing_ratings = {(row[0], row[1]): row[2] for row in c.fetchall()}
            conn.close()

            ders_tabs = st.tabs(list(YKS_KONULARI.keys()))

            for i, (ders_adi, konular) in enumerate(YKS_KONULARI.items()):
                with ders_tabs[i]:
                    st.markdown(f"### {ders_adi}")
                    updated_ratings = {}
                    
                    for konu in konular:
                        col_k, col_p = st.columns([3, 2])
                        col_k.write(f"• **{konu}**")
                        curr_val = existing_ratings.get((ders_adi, konu), 3)
                        rating = col_p.select_slider(
                            f"{konu} Puanı",
                            options=[1, 2, 3, 4, 5],
                            value=curr_val,
                            key=f"rating_{ders_adi}_{konu}",
                            label_visibility="collapsed"
                        )
                        updated_ratings[konu] = rating
                    
                    if st.button(f"💾 {ders_adi} Puanlarımı Kaydet", key=f"btn_{ders_adi}"):
                        conn = get_db()
                        c = conn.cursor()
                        for konu, rat in updated_ratings.items():
                            c.execute('''
                                INSERT INTO topic_ratings (student_id, subject, topic, rating)
                                VALUES (?, ?, ?, ?)
                                ON CONFLICT(student_id, subject, topic) DO UPDATE SET rating=excluded.rating
                            ''', (st.session_state["user_id"], ders_adi, konu, rat))
                        conn.commit()
                        conn.close()
                        st.success(f"✅ {ders_adi} puanlarınız kaydedildi!")

        with tab4:
            st.subheader("🎯 Koçunuzdan Gelen Ödevler ve Notlar")
            conn = get_db()
            df_odev = pd.read_sql_query("SELECT ders as 'Ders', detay as 'Ödev Tanımı', son_tarih as 'Son Tarih', durum as 'Durum' FROM odevler WHERE student_id = ?", conn, params=(st.session_state["user_id"],))
            conn.close()
            
            if not df_odev.empty:
                st.dataframe(df_odev, use_container_width=True)
            else:
                st.info("Atanmış aktif bir ödeviniz bulunmuyor.")

    else:
        st.header("👨‍🏫 Koç / Öğretmen Veritabanı Takip Paneli")
        
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT id, name FROM students ORDER BY name ASC")
        students_list = c.fetchall()
        conn.close()
        
        if not students_list:
            st.warning("⚠️ Veritabanında henüz kayıtlı öğrenci bulunmuyor. Öğrencinizden kayıt olmasını isteyin.")
        else:
            student_dict = {name: sid for sid, name in students_list}
            selected_student_name = st.selectbox("📊 İncelemek İstediğiniz Öğrenciyi Seçin:", list(student_dict.keys()))
            selected_student_id = student_dict[selected_student_name]
            
            st.divider()
            
            ktab1, ktab2, ktab3 = st.tabs([
                "📊 Çalışma & Net Analizi", 
                "⚠️ Zayıf Olduğu Konular (1 ve 2 Puanlar)", 
                "🎯 Ödev Tanımla"
            ])
            
            # KOÇ TAB 1: GENEL METRİKLER
            with ktab1:
                st.subheader(f"📈 {selected_student_name} - Canlı Performans Özeti")
                
                conn = get_db()
                df_logs = pd.read_sql_query("SELECT * FROM daily_logs WHERE student_id = ? ORDER BY date DESC", conn, params=(selected_student_id,))
                df_deneme = pd.read_sql_query("SELECT * FROM denemeler WHERE student_id = ? ORDER BY id DESC", conn, params=(selected_student_id,))
                conn.close()
                
                m1, m2, m3, m4 = st.columns(4)
                toplam_soru = df_logs["paragraf_prob"].sum() + df_logs["mat_geo"].sum() + df_logs["fen"].sum() + df_logs["turkce_sos"].sum() if not df_logs.empty else 0
                ort_sure = df_logs["sure"].mean() if not df_logs.empty else 0.0
                ort_verim = df_logs["verim"].mean() if not df_logs.empty else 0.0
                son_net = df_deneme["toplam_net"].iloc[0] if not df_deneme.empty else 0.0
                
                m1.metric("Toplam Soru", f"{toplam_soru} Soru")
                m2.metric("Ort. Çalışma", f"{ort_sure:.1f} Saat")
                m3.metric("Ort. Verim", f"{ort_verim:.1f} / 10")
                m4.metric("Son Deneme Neti", f"{son_net:.2f}")
                
                st.divider()
                st.write("### 📜 Günlük Çalışma Dökümü")
                if not df_logs.empty:
                    st.dataframe(df_logs[["date", "sure", "paragraf_prob", "mat_geo", "fen", "turkce_sos", "bos_yanlis", "verim", "notlar"]], use_container_width=True)
                else:
                    st.info("Öğrenci henüz günlük çalışma kaydı girmemiş.")

            # KOÇ TAB 2: ZAYIF KONULAR
            with ktab2:
                st.subheader(f"⚠️ {selected_student_name} - Acil Müdahale Gereken Konular")
                conn = get_db()
                df_ratings = pd.read_sql_query("SELECT subject as 'Ders', topic as 'Konu', rating as 'Puan' FROM topic_ratings WHERE student_id = ? AND rating IN (1, 2) ORDER BY rating ASC", conn, params=(selected_student_id,))
                conn.close()
                
                if not df_ratings.empty:
                    st.error(f"🔴 Bu öğrencinin **{len(df_ratings)}** konuda eksik uyarısı bulunmaktadır!")
                    st.dataframe(df_ratings, use_container_width=True)
                else:
                    st.success("✅ Öğrenci 1 veya 2 puan verdiği kritik bir zayıf konu işaretlememiş.")

            # KOÇ TAB 3: ÖDEV VERME
            with ktab3:
                st.subheader(f"🎯 {selected_student_name} İçin Yeni Ödev Ekle")
                o_ders = st.selectbox("Ders", ["Matematik", "Geometri", "Fizik", "Kimya", "Biyoloji", "Paragraf/Problem"])
                o_detay = st.text_area("Ödev Açıklaması / Kitap - Test Detayı")
                o_tarih = st.date_input("Son Teslim Tarihi", datetime.date.today() + datetime.timedelta(days=7))
                
                if st.button("➕ Ödevi Kaydet ve Öğrenciye Gönder", type="primary"):
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("INSERT INTO odevler (student_id, ders, detay, son_tarih) VALUES (?, ?, ?, ?)", (selected_student_id, o_ders, o_detay, str(o_tarih)))
                    conn.commit()
                    conn.close()
                    st.success("✅ Ödev veritabanına eklendi ve öğrencinin paneline aktarıldı!")