import streamlit as st
import datetime
import pandas as pd

# Sayfa Ayarları
st.set_page_config(page_title="YKS Çoklu Öğrenci Koçluk Platformu", page_icon="🎓", layout="wide")

# Session State Hazırlığı (Veri Depolama)
if "ogrenciler" not in st.session_state:
    st.session_state["ogrenciler"] = {} # {ogr_id: {sifre, ad, konular, denemeler, gunluk}}

# Koç Şifresi
KOC_SIFRE = "1234"

# Tüm YKS Sayısal Müfredatı
YKS_KONULAR = {
    "📐 Matematik & Geometri": [
        "Temel Kavramlar & Sayılar", "Sayı Basamakları", "Bölme - Bölünebilme", "EBOB - EKOK",
        "Rasyonel Sayılar", "Basit Eşitsizlikler", "Mutlak Değer", "Üslü & Köklü İfadeler",
        "Çarpanlara Ayırma", "Oran - Orantı", "Problem Türleri (Sayı, Kesir, Yaş, Yüzde, Hız)",
        "Mantık & Küme - Kartratezyen Çarpım", "Fonksiyonlar", "2. Dereceden Denklemler",
        "Karmaşık Sayılar", "Polinomlar", "Parabol", "Permütasyon - Kombinasyon - Olasılık",
        "Logaritma", "Diziler", "Trigonometri", "Limit & Süreklilik", "Türev & Uygulamaları",
        "İntegral & Uygulamaları", "Doğruda ve Üçgende Açılar", "Özel Üçgenler (Dik, İkizkenar, Eşkenar)",
        "Üçgende Alan & Açıortay & Kenarortay", "Üçgende Benzerlik", "Çokgenler & Dörtgenler",
        "Çember ve Daire", "Analitik Geometri", "Katı Cisimler (Prizma, Piramit, Küre)"
    ],
    "⚡ Fizik": [
        "Fizik Bilimine Giriş", "Madde ve Özellikleri", "Kütle Özkütle", "Hareket ve Kuvvet",
        "İş, Güç ve Enerji", "Isı ve Sıcaklık", "Genleşme", "Basınç ve Kaldırma Kuvveti",
        "Elektrostatik", "Elektrik Akımı ve Devreler", "Mıknatıs ve Manyetik Alan", "Optik (Yansıma, Kırılma, Mercekler)",
        "Dalgalar (Yay, Su, Ses, Deprem)", "Vektörler & Bağıl Hareket", "Newton'un Hareket Yasaları",
        "Atışlar", "Tork ve Denge", "Ağırlık Merkezi", "Basit Makineler", "Düzgün Çembersel Hareket",
        "Basit Harmonik Hareket", "Açısal Momentum & Kütle Çekim", "Elektriksel Potansiyel & Kuvvet",
        "Manyetizma ve İndüksiyon", "Alternatif Akım & Transformatörler", "Elektromanyetik Dalgalar",
        "Fotoelektrik Olay & Compton", "Özel Görelilik", "Modern Fizik & Teknolojideki Uygulamaları"
    ],
    "🧪 Kimya": [
        "Kimya Bilimi & Atomun Yapısı", "Periyodik Sistem", "Kimyasal Türler Arası Etkileşimler",
        "Maddenin Halleri", "Doğa ve Kimya", "Mol Kavramı", "Kimyasal Tepkimeler ve Hesaplamalar",
        "Karışımlar", "Asitler, Bazlar ve Tuzlar", "Kimya Her Yerde", "Modern Atom Teorisi",
        "Gazlar", "Sıvı Çözeltiler ve Çözünürlük", "Tepkimelerde Enerji", "Tepkimelerde Hız",
        "Kimyasal Denge", "Sulu Çözelti Dengeleri (KÇÇ & Asit-Baz)", "Kimya ve Elektrik (Pil & Elektroliz)",
        "Karbon Kimyasına Giriş", "Organik Kimya (Akan, Alken, Alkin, Alkol, Ester vb.)"
    ],
    "🧬 Biyoloji": [
        "Yaşam Bilimi Biyoloji", "Hücre ve Organeller", "Hücre Zarından Madde Geçişleri",
        "Canlıların Sınıflandırılması", "Hücre Bölünmeleri (Mitoz & Mayoz)", "Kalıtım ve İnsan Genetiği",
        "Ekosistem Ekolojisi & Güncel Çevre Sorunları", "İnsan Fizyolojisi (Sinir, Duyu, Destek-Hareket)",
        "Sindirimi Dolaşım, Solunum, Boşaltım Sistemleri", "Üreme Sistemi ve Gelişme",
        "Komünite ve Popülasyon Ekolojisi", "Nükleik Asitler & Protein Sentezi", "Canlılarda Enerji Dönüşümleri (Fotosentez, Kemosentez, Solunum)",
        "Bitki Biyolojisi (Dokular, Organlar, Taşıma, Büyüme)", "Canlılar ve Çevre"
    ]
}

# --- YAN MENÜ: GİRİŞ PANELİ ---
st.sidebar.title("🎓 YKS Koçluk Platformu")
giris_turu = st.sidebar.radio("Giriş Türü Seçin:", ["👨‍🎓 Öğrenci Girişi / Kayıt", "👨‍🏫 Koç Girişi"])

# ----------------------------------------------------
# 1. ÖĞRENCİ PANELİ
# ----------------------------------------------------
if giris_turu == "👨‍🎓 Öğrenci Girişi / Kayıt":
    st.title("👨‍🎓 Öğrenci Paneli")
    
    tab_giris, tab_soru, tab_deneme, tab_konu = st.tabs([
        "🔑 Giriş / Kayıt", "📝 Günlük Çalışma", "📊 Deneme & Karne Analizi", "🗺️ Konu Derecelendirme"
    ])
    
    with tab_giris:
        st.subheader("Öğrenci Hesabı")
        ad_soyad = st.text_input("Adınız ve Soyadınız:").strip().title()
        sifre = st.text_input("Şifreniz / PIN:", type="password")
        
        if st.button("Giriş Yap / Hesabı Aktif Et"):
            if ad_soyad and sifre:
                if ad_soyad not in st.session_state["ogrenciler"]:
                    st.session_state["ogrenciler"][ad_soyad] = {
                        "sifre": sifre,
                        "konular": {},
                        "denemeler": [],
                        "gunluk": []
                    }
                    st.success(f"Hoş geldin {ad_soyad}! Yeni profilin başarıyla oluşturuldu.")
                else:
                    if st.session_state["ogrenciler"][ad_soyad]["sifre"] == sifre:
                        st.success(f"Hoş geldin {ad_soyad}! Başarıyla giriş yapıldı.")
                    else:
                        st.error("Hatalı şifre! Lütfen kontrol edin.")
                st.session_state["aktif_ogrenci"] = ad_soyad
            else:
                st.warning("Lütfen adınız soyadınız ve şifrenizi girin.")
                
    aktif_ogr = st.session_state.get("aktif_ogrenci", None)
    
    if not aktif_ogr:
        st.info("⚠️ İşlem yapmak için lütfen önce 'Giriş / Kayıt' sekmesinden hesabınıza giriş yapın.")
    else:
        # GÜNLÜK ÇALIŞMA SEKMESİ
        with tab_soru:
            st.subheader(f"📝 Günlük Çalışma Girişi - ({aktif_ogr})")
            col1, col2 = st.columns(2)
            with col1:
                tarih = st.date_input("Tarih", datetime.date.today())
                sure = st.number_input("Çalışma Süresi (Saat)", 0.0, 16.0, 7.5, 0.5)
                paragraf_prob = st.number_input("Paragraf & Problem (Soru)", 0, 200, 40)
                mat_geo = st.number_input("TYT Mat & Geometri (Soru)", 0, 300, 50)
            with col2:
                fen = st.number_input("TYT Fen Bilimleri (Soru)", 0, 200, 40)
                turkce_sos = st.number_input("TYT Türkçe & Sosyal (Soru)", 0, 200, 30)
                verim = st.slider("Günün Verim Puanı (1-10)", 1, 10, 8)
            notlar = st.text_area("Zorlandığın konular / Koçuna iletmek istediğin not:")
            
            if st.button("🚀 Günlük Raporu Kaydet"):
                toplam = paragraf_prob + mat_geo + fen + turkce_sos
                veri = {"tarih": tarih, "sure": sure, "toplam_soru": toplam, "verim": verim, "not": notlar}
                st.session_state["ogrenciler"][aktif_ogr]["gunluk"].append(veri)
                st.success(f"Tebrikler {aktif_ogr}! {toplam} soru kaydı koç paneline iletildi.")

        # DENEME & KARNE YÜKLEME SEKMESİ
        with tab_deneme:
            st.subheader("📊 Deneme Sonucu Kaydı & PDF/Görsel Karne Yükleme")
            st.caption("Deneme sonuçlarını ve karne dosyanı yükle, sistem otomatik eksik analizi çıkarsın.")
            
            yayin = st.text_input("Deneme Yayını / Adı (Örn: 3D TYT Genəl Deneme-1):")
            d_turu = st.selectbox("Deneme Türü:", ["TYT Denemesi", "AYT Sayısal Denemesi", "Matematik Branş Denemesi", "Fen Branş Denemesi"])
            
            c1, c2, c3 = st.columns(3)
            with c1:
                mat_net = st.number_input("Matematik Neti:", 0.0, 40.0, 28.5)
                fiz_net = st.number_input("Fizik Neti:", 0.0, 14.0, 9.0)
            with c2:
                kim_net = st.number_input("Kimya Neti:", 0.0, 14.0, 10.5)
                biy_net = st.number_input("Biyoloji Neti:", 0.0, 14.0, 8.0)
            with c3:
                turk_net = st.number_input("Türkçe Neti (Varsa):", 0.0, 40.0, 31.0)
                sos_net = st.number_input("Sosyal Neti (Varsa):", 0.0, 20.0, 13.0)
                
            toplam_net = mat_net + fiz_net + kim_net + biy_net + turk_net + sos_net
            st.metric("Hesaplanan Toplam Net:", f"{toplam_net:.2f}")
            
            # PDF / Görsel Yükleyici
            karne_dosyasi = st.file_uploader("📄 Deneme Karnesi / Fotoğrafı Yükle (PDF, PNG, JPG):", type=["pdf", "png", "jpg", "jpeg"])
            
            if karne_dosyasi is not None:
                st.info(f"📎 **Yüklenen Dosya:** `{karne_dosyasi.name}` (Koç kontrolüne hazır)")

            if st.button("📥 Denemeyi ve Karneyi Kaydet"):
                deneme_kayit = {
                    "tarih": datetime.date.today(),
                    "yayin": yayin,
                    "tur": d_turu,
                    "toplam_net": toplam_net,
                    "detay": {"Matematik": mat_net, "Fizik": fiz_net, "Kimya": kim_net, "Biyoloji": biy_net},
                    "dosya_adi": karne_dosyasi.name if karne_dosyasi else "Dosya Yüklenmedi"
                }
                st.session_state["ogrenciler"][aktif_ogr]["denemeler"].append(deneme_kayit)
                st.success("Deneme sonucu ve analizi başarıyla kaydedildi!")
                
                # Otomatik Eksik Analiz Motoru
                st.divider()
                st.subheader("💡 Sistem Otomatik Eksik Analiz Raporu")
                
                if mat_net < 30 and d_turu == "TYT Denemesi":
                    st.warning("⚠️ **Matematik Uyarısı:** Netin 30'un altında. Problem ve Geometri ivmesini artırmalı, süre yönetimini gözden geçirmelisin.")
                if fiz_net < 10:
                    st.warning("⚠️ **Fizik Uyarısı:** Fizik netin hedef seviyenin gerisinde. Optik ve Elektrik konularında konu tekrarları yapman önerilir.")
                if toplam_net >= 90:
                    st.balloons()
                    st.success("🌟 **Mükemmel Performans:** Net seviyen Sayısal İlk 5.000 hedefiyle tam uyumlu gidiyor!")

        # KONU DERECELENDİRME SEKMESİ
        with tab_konu:
            st.subheader("🗺️ YKS Konu Anlama Derecelendirmesi")
            st.info("Her ders için kendini 1 (Çok Eksiğim Var) ile 5 (Tamamen Ustalaştım) arasında puanla.")
            
            for ders, konular in YKS_KONULAR.items():
                with st.expander(f"📚 {ders} Konuları"):
                    for kn in konular:
                        mevcut_puan = st.session_state["ogrenciler"][aktif_ogr]["konular"].get(kn, 3)
                        yeni_puan = st.select_slider(
                            f"**{kn}**",
                            options=[1, 2, 3, 4, 5],
                            value=mevcut_puan,
                            format_func=lambda x: {1: "1 - Çok Zayıf 🔴", 2: "2 - Eksikler Var 🟠", 3: "3 - Orta 🟡", 4: "4 - İyi 🟢", 5: "5 - Tam Usta 🔵"}[x],
                            key=f"{aktif_ogr}_{kn}"
                        )
                        st.session_state["ogrenciler"][aktif_ogr]["konular"][kn] = yeni_puan
            st.success("Konu hakimiyet durumların güncellendi!")

# ----------------------------------------------------
# 2. KOÇ PANELİ
# ----------------------------------------------------
else:
    st.title("👨‍🏫 Koç Analiz ve Takip Paneli")
    koc_sifre_giris = st.sidebar.text_input("Koç Şifresi:", type="password")
    
    if koc_sifre_giris != KOC_SIFRE:
        st.warning("🔒 Koç paneline erişmek için sol menüden koç şifrenizi girin. (Varsayılan: 1234)")
    else:
        st.success("🔓 Koç Paneli Yetkisi Doğrulandı.")
        
        tum_ogrenciler = list(st.session_state["ogrenciler"].keys())
        
        if not tum_ogrenciler:
            st.info("Henüz sisteme kayıtlı bir öğrenci bulunmuyor.")
        else:
            secilen_ogr = st.selectbox("🔍 İncelemek İstediğiniz Öğrenciyi Seçin:", tum_ogrenciler)
            ogr_veri = st.session_state["ogrenciler"][secilen_ogr]
            
            st.divider()
            st.header(f"📊 Öğrenci Raporu: {secilen_ogr}")
            
            k1, k2, k3 = st.columns(3)
            k1.metric("Toplam Girilen Çalışma", f"{len(ogr_veri['gunluk'])} Gün")
            k2.metric("Girilmiş Deneme Sayısı", f"{len(ogr_veri['denemeler'])} Adet")
            
            # Kırmızı Alarm Veren Zayıf Konular (1 veya 2 Puan Alanlar)
            zayif_konular = [k for k, v in ogr_veri["konular"].items() if v in [1, 2]]
            k3.metric("🔴 Acil Müdahale Gereken Konu", f"{len(zayif_konular)} Konu")
            
            # Zayıf Konular Listesi
            if zayif_konular:
                with st.expander("🚨 Öğrencinin 1 ve 2 Puan Verdiği Zayıf Konular (Ödev Listesi)"):
                    for zk in zayif_konular:
                        st.write(f"- ⚠️ **{zk}** (Puan: {ogr_veri['konular'][zk]})")
            
            # Deneme Karneleri ve Dosyalar
            st.subheader("📑 Yüklenen Denemeler ve Karne Dosyaları")
            if ogr_veri["denemeler"]:
                df_deneme = pd.DataFrame(ogr_veri["denemeler"])
                st.dataframe(df_deneme[["tarih", "yayin", "tur", "toplam_net", "dosya_adi"]], use_container_width=True)
            else:
                st.info("Öğrenci henüz deneme sonucu veya karne dosyası yüklememiş.")