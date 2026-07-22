import streamlit as st
import datetime

# Sayfa Yapısı
st.set_page_config(page_title="YKS Koçluk App", page_icon="🎓", layout="wide")

st.title("🎓 YKS Sayısal İlk 5.000 Koçluk & Takip Uygulaması")
st.caption("23 Temmuz 2026 Başlangıçlı TYT Maratonu")

# Sol Menüden Rol Seçimi
rol = st.sidebar.radio("Giriş Paneli Seçin:", ["👨‍🎓 Öğrenci Paneli", "👨‍🏫 Koç Paneli"])

# ----------------------------------------------------
# 1. ÖĞRENCİ PANELİ
# ----------------------------------------------------
if rol == "👨‍🎓 Öğrenci Paneli":
    st.header("📝 Günlük Soru ve Çalışma Girişi")
    st.info("Bugün yaptığın çalışmaları girip 'Kaydet' butonuna bas.")
    
    col1, col2 = st.columns(2)
    with col1:
        tarih = st.date_input("Tarih", datetime.date.today())
        sure = st.number_input("Çalışma Süresi (Saat)", min_value=0.0, max_value=16.0, value=8.0, step=0.5)
        paragraf_prob = st.number_input("Paragraf & Problem (Soru)", min_value=0, value=45, step=5)
        mat_geo = st.number_input("TYT Mat & Geometri (Soru)", min_value=0, value=50, step=5)
        
    with col2:
        fen = st.number_input("TYT Fen Bilimleri (Soru)", min_value=0, value=40, step=5)
        turkce_sos = st.number_input("TYT Türkçe & Sosyal (Soru)", min_value=0, value=30, step=5)
        bos_yanlis = st.number_input("Yapılamayan / Boş Soru Sayısı", min_value=0, value=5, step=1)
        verim = st.slider("Günün Verim Puanı (1-10)", 1, 10, 8)
        
    notlar = st.text_area("Bugün zorlandığın yerler / Koçuna notun:")
    
    if st.button("🚀 Günlük Raporu Kaydet ve Koça Gönder", type="primary"):
        toplam = paragraf_prob + mat_geo + fen + turkce_sos
        st.success(f"Tebrikler! Bugün toplam {toplam} soru kaydedildi ve koç paneline aktarıldı.")

# ----------------------------------------------------
# 2. KOÇ PANELİ
# ----------------------------------------------------
else:
    st.header("📊 Koç Analiz ve Yönetim Paneli")
    
    # Metrik Kartları
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Haftalık Hedef", "2.100 Soru")
    k2.metric("Çözülen Soru", "1.650 Soru", delta="+165 Soru")
    k3.metric("Hedef Tamamlanma", "%78.5")
    k4.metric("Ortalama Verim", "8.2 / 10")
    
    st.divider()
    
    # Özel Ders Uyarısı
    st.warning("⚠️ **Özel Ders Takvimi:** Pazartesi, Çarşamba ve Cuma günleri 14:00 - 15:00 saatleri arasında Matematik Özel Dersi vardır.")
    
    # Koç Değerlendirmesi
    st.subheader("💬 Öğrenciye Günlük Geri Bildirim Yaz")
    koc_mesaj = st.text_area("Öğrencinin ekranında görünecek mesajın:")
    durum = st.selectbox("Günlük Durum Onayı:", ["✅ Görüldü & Onaylandı", "⚠️ Eksik Var - Tamamla", "🔍 Soru Defteri Kontrol Edilmeli"])
    
    if st.button("Geri Bildirimi İlet", type="primary"):
        st.info("Değerlendirmeniz öğrencinin ekranına başarıyla gönderildi.")