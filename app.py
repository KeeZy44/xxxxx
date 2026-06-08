import streamlit as st
import pandas as pd
import sqlite3
import datetime
from groq import Groq
import re

# Sayfa Ayarları
st.set_page_config(page_title="Mehmet Ali - Pro Fitness Hub V6", layout="wide")

# Groq API Şifresi
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

st.title("🏋️ Mehmet Ali - Pro Fitness Komuta Merkezi (V6)")
st.markdown("Salon İmkânlarına Göre Özelleştirilmiş ve Sırt & Kol Günü Güçlendirilmiş Canlı Program")

# --- GELİŞMİŞ YEREL VERİTABANI FONKSİYONLARI ---
def veritabanini_hazirla():
    conn = sqlite3.connect('fitness_kocum.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS gunluk_kayitlar
                 (tarih TEXT, mesaj_tipi TEXT, kullanici_mesaji TEXT, ai_hesabi TEXT, 
                  kalori INTEGER, protein INTEGER, karb INTEGER, yag INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS profil_ayarlari
                 (id INTEGER PRIMARY KEY, boy INTEGER, kilo REAL, yas INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS kilo_gecmisi
                 (tarih TEXT UNIQUE, kilo REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS adim_takip
                 (tarih TEXT UNIQUE, adim_sayisi INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS pr_rekorlar
                 (hareket_adi TEXT PRIMARY KEY, rekor_kilo REAL, tarih TEXT)''')
    conn.commit()
    conn.close()

def profil_getir():
    conn = sqlite3.connect('fitness_kocum.db')
    c = conn.cursor()
    c.execute("SELECT boy, kilo, yas FROM profil_ayarlari WHERE id = 1")
    res = c.fetchone()
    conn.close()
    if res:
        return res[0], res[1], res[2]
    return 180, 80.0, 20

def profil_kaydet(boy, kilo, yas):
    conn = sqlite3.connect('fitness_kocum.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO profil_ayarlari (id, boy, kilo, yas) VALUES (1, ?, ?, ?)", (boy, kilo, yas))
    bugun_str = datetime.date.today().strftime("%Y-%m-%d")
    c.execute("INSERT OR REPLACE INTO kilo_gecmisi (tarih, kilo) VALUES (?, ?)", (bugun_str, kilo))
    conn.commit()
    conn.close()

def local_veri_kaydet(mesaj_tipi, kullanici_mesaji, ai_hesabi, kalori=0, protein=0, karb=0, yag=0):
    try:
        conn = sqlite3.connect('fitness_kocum.db')
        c = conn.cursor()
        tarih = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO gunluk_kayitlar VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                  (tarih, mesaj_tipi, kullanici_mesaji, ai_hesabi, kalori, protein, karb, yag))
        conn.commit()
        conn.close()
    except:
        pass

veritabanini_hazirla()

# --- SOL PANEL: KALICI PROFİL VE ÖLÇÜMLER ---
st.sidebar.header("👤 Güncel Durum")
v_boy, v_kilo, v_yas = profil_getir()

boy = st.sidebar.number_input("Boy (cm):", value=v_boy, step=1)
kilo = st.sidebar.number_input("Kilo (kg):", value=v_kilo, step=0.1)
yas = st.sidebar.number_input("Yaş:", value=v_yas, step=1)

if st.sidebar.button("💾 Kiloyu ve Profili Kaydet"):
    profil_kaydet(boy, kilo, yas)
    st.sidebar.success("Profil ve Kilo Geçmişi Güncellendi!")
    st.rerun()

# Hedefler
bmh = (10 * kilo) + (6.25 * boy) - (5 * yas) + 5
hedef_kalori = int(bmh * 1.375 - 500)
hedef_protein = int(kilo * 2.2)
hedef_adim = 10000

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Günlük Hedeflerin")
st.sidebar.metric(label="Alman Gereken Kalori", value=f"{hedef_kalori} kcal")
st.sidebar.metric(label="Gerekli Protein", value=f"{hedef_protein} g")

# --- ANLIK ÖĞÜN & ADIM EKLEME ALANI ---
st.sidebar.markdown("---")
st.sidebar.subheader("🍽️ Yapay Zekaya Öğün Ekle")
yeni_ogun = st.sidebar.text_area("Ne yedin?", placeholder="Örn: 200g tavuk göğsü, 1 kase pilav...", key="web_ogun_input")

if st.sidebar.button("Koça Gönder & Kaydet"):
    if yeni_ogun:
        with st.spinner("Demir Koç hesaplıyor..."):
            try:
                sistem_komutu = "Sen Mehmet Ali'nin fitness koçusun. Girdileri analiz et ve net bir şekilde 'Kalori: X kcal', 'Protein: Y gram' formatında yanıt üret."
                completion = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "system", "content": sistem_komutu}, {"role": "user", "content": yeni_ogun}],
                    temperature=0.3,
                )
                ai_cevabi = completion.choices[0].message.content
                kalori, protein = 0, 0
                k_match = re.search(r'Kalori:\s*(\d+)', ai_cevabi, re.IGNORECASE)
                p_match = re.search(r'Protein:\s*(\d+)', ai_cevabi, re.IGNORECASE)
                if k_match: kalori = int(k_match.group(1))
                if p_match: protein = int(p_match.group(1))
                
                local_veri_kaydet("Beslenme", yeni_ogun, ai_cevabi, kalori, protein, 0, 0)
                st.sidebar.success("Kaydedildi!")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Hata: {e}")

st.sidebar.markdown("---")
st.sidebar.subheader("👣 iPhone Adım Girişi")
bugunku_adim = st.sidebar.number_input("Bugün kaç adım attın?", min_value=0, step=500, value=0)
if st.sidebar.button("👟 Adımı Kaydet"):
    try:
        conn = sqlite3.connect('fitness_kocum.db')
        c = conn.cursor()
        bugun_str = datetime.date.today().strftime("%Y-%m-%d")
        c.execute("INSERT OR REPLACE INTO adim_takip (tarih, adim_sayisi) VALUES (?, ?)", (bugun_str, bugunku_adim))
        conn.commit()
        conn.close()
        st.sidebar.success("Adım başarıyla işlendi!")
        st.rerun()
    except:
        pass

# --- GÜNLÜK VERİLERİ ÇEKME FONKSİYONLARI ---
def gunluk_verileri_yukle():
    try:
        conn = sqlite3.connect('fitness_kocum.db')
        bugun_str = datetime.datetime.now().strftime("%Y-%m-%d")
        df = pd.read_sql_query("SELECT * FROM gunluk_kayitlar WHERE tarih LIKE ?", conn, params=(f"{bugun_str}%",))
        
        beslenme_df = df[df['mesaj_tipi'] == 'Beslenme']
        al_kalori = beslenme_df['kalori'].sum() if not beslenme_df.empty else 0
        al_protein = beslenme_df['protein'].sum() if not beslenme_df.empty else 0
        
        c = conn.cursor()
        c.execute("SELECT adim_sayisi FROM adim_takip WHERE tarih = ?", (bugun_str,))
        adim_res = c.fetchone()
        al_adim = adim_res[0] if adim_res else 0
        conn.close()
        
        return al_kalori, al_protein, al_adim
    except:
        return 0, 0, 0

alınan_kalori, alınan_protein, alınan_adim = gunluk_verileri_yukle()

# --- MERKEZİ SEKME SİSTEMİ ---
tab_program, tab_kilo, tab_rekorlar = st.tabs(["📊 Günlük Durum & Program", "📈 Haftalık Kilo Takibi", "🏆 PR Rekor Defterim"])

# --- TAB 1: GÜNLÜK DURUM VE ANTRENMAN ---
with tab_program:
    st.subheader("📈 Günlük İlerleme Durumu")
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.write(f"🍗 Protein Tüketimi ({alınan_protein}g / {hedef_protein}g)")
        st.progress(min(alınan_protein / max(hedef_protein, 1), 1.0))
    with col_m2:
        st.write(f"🔥 Kalori Alımı ({alınan_kalori} kcal / {hedef_kalori} kcal)")
        st.progress(min(alınan_kalori / max(hedef_kalori, 1), 1.0))
    with col_m3:
        st.write(f"👣 Günlük Kardiyo / Adım ({alınan_adim} / {hedef_adim})")
        st.progress(min(alınan_adim / hedef_adim, 1.0))

    st.markdown("---")
    with st.expander("🚨 ÖNEMLİ ANTRENMAN KURALLARI & TEKNİKLER"):
        st.markdown("**• Isınma:** 10 dk hafif yürüyüş + eklem hareketleri.")
        st.markdown("**• Kardiyo:** Sonunda 15 dk (10 eğim, 5 hız).")
        st.markdown("**• Dinlenme:** Set arası 2-3 dk, hareket arası 1 dk.")
        st.markdown("**• RPT:** İlk set en ağır. Sonraki setlerde ağırlığı %10 düşür, tekrarı artır.")
        st.markdown("**• Rest-Pause (RP):** Set bitince 15 sn dinlen, +3-5 tekrar daha yap (3 kez tekrarla).")

    st.subheader("📅 Haftalık Salon Programı")
    secilen_gun = st.selectbox(
        "Hangi günün programına bakacaksın?",
        ["Pazartesi (1. Gün: Göğüs & Omuz)", "Salı/Çarşamba (2. Gün: Sırt & Komple Kol)", "Cuma (3. Gün: Üst Vücut Hipertrofi)", "Dinlenme Günü"]
    )

    if secilen_gun == "Pazartesi (1. Gün: Göğüs & Omuz)":
        st.markdown("### 🔴 1. GÜN: GÖĞÜS & OMUZ (Pazartesi)")
        st.info("🏋️ **1. Olympic Flat Bench Press**\n\n* **Ekipman:** Flat Bench | **Set/Tekrar:** 3 x 6-8-10 | **Teknik:** RPT (RIR 1-2)")
        st.info("🏋️ **2. Incline Dumbbell Press VEYA Ayarlanabilir Makine**\n\n* **Ekipman:** İncline Bench / Ayarlı Makine | **Set/Tekrar:** 3 x 8-10 | **Teknik:** Kontrollü Negatif")
        st.info("🏋️ **3. Plate-Loaded Shoulder Press**\n\n* **Ekipman:** Shoulder Machine | **Set/Tekrar:** 3 x 8-10 | **Teknik:** RP (Son Set)")
        st.info("🏋️ **4. Dumbbell Lateral Raise**\n\n* **Ekipman:** Dumbbell | **Set/Tekrar:** 3 x 12-15 | **Teknik:** RP (Son Set)")
        st.info("🏋️ **5. Seated Pec Deck Fly (Oturarak Göğüs Fly Makinesi)**\n\n* **Ekipman:** Fly Makinesi | **Set/Tekrar:** 3 x 12-15 | **Teknik:** Squeeze (Sıkıştır)")
        st.info("🏋️ **6. Cable Pushdown**\n\n* **Ekipman:** Cable Station | **Set/Tekrar:** 3 x 12 | **Teknik:** RP (Son Set)")

    elif secilen_gun == "Salı/Çarşamba (2. Gün: Sırt & Komple Kol)":
        st.markdown("### 🟢 2. GÜN: SIRT & KOMPLE KOL (Ön ve Arka Kol Odaklı)")
        
        # Sırt Blokları
        st.success("💪 **1. Hammer Pull-Down**\n\n* **Ekipman:** Pull-Down Machine | **Set/Tekrar:** 3 x 6-8-10 | **Teknik:** RPT (Sırt Genişliği)")
        st.success("💪 **2. Plate-Loaded Row**\n\n* **Ekipman:** Row Machine | **Set/Tekrar:** 3 x 8-10 | **Teknik:** Kalınlık İçin Kürekleri Sıkıştır")
        st.success("💪 **3. Dumbbell Row**\n\n* **Ekipman:** Dumbbell + Bench | **Set/Tekrar:** 3 x 10 | **Teknik:** Kontrollü Negatif Esneme")
        
        # Ön Kol (Biceps - 3 Hareket)
        st.success("🔥 **4. Preacher Curl (Z-Bar veya Sehpa)**\n\n* **Ekipman:** Preacher Bench | **Set/Tekrar:** 3 x 12 | **Teknik:** Biceps Tepe Noktası (Peak) Gelişimi")
        st.success("🔥 **5. Dumbbell Hammer Curls (Çekiç Tutuş)**\n\n* **Ekipman:** Dumbbell | **Set/Tekrar:** 3 x 12 | **Teknik:** Biceps Kalınlığı ve Ön Kol Kuvveti")
        st.success("🔥 **6. Incline Dumbbell Curl (Eğik Sehpa)**\n\n* **Ekipman:** Eğik Bench | **Set/Tekrar:** 3 x 12 | **Teknik:** Maksimum Alt Esneme Odaklı")
        
        # Arka Kol (Triceps - 2 Hareket)
        st.success("⚡ **7. Cable Pushdown (D-Bar veya Halat)**\n\n* **Ekipman:** Kablo İstasyonu | **Set/Tekrar:** 3 x 12 | **Teknik:** Dirsekleri Kilitle, Dipte Arka Kolu Sık")
        st.success("⚡ **8. Triceps Overhead Extension (Kablo veya Dumbbell)**\n\n* **Ekipman:** Baş Arkası İtiş | **Set/Tekrar:** 3 x 12 | **Teknik:** Arka Kolun Uzun Başını Patlatma")
        
        # Bonus Omuz
        st.success("💪 **9. Cable Facepull**\n\n* **Ekipman:** Cable Station | **Set/Tekrar:** 3 x 15 | **Teknik:** Arka Omuz ve Postür Sağlığı")

    elif secilen_gun == "Cuma (3. Gün: Üst Vücut Hipertrofi)":
        st.markdown("### 🔵 3. GÜN: ÜST VÜCUT HİPERTROFİ & DETAY (Cuma)")
        st.info("🔥 **1. Incline Dumbbell Press (Üst Göğüs Odaklı)**\n\n* **Ekipman:** Incline Bench | **Set/Tekrar:** 3 x 8-10 | **Teknik:** Ağır Başla (RPT)")
        st.info("🔥 **2. Lat Pulldown (Geniş Tutuş - Sırt Genişliği)**\n\n* **Ekipman:** Cable Station | **Set/Tekrar:** 3 x 8-10 | **Teknik:** Tepe Noktasında Sıkıştır")
        st.info("🔥 **3. Seated Cable Row (Dar Tutuş / Karına Çekiş)**\n\n* **Ekipman:** Cable Machine | **Set/Tekrar:** 3 x 10-12 | **Teknik:** Kontrollü Bırakış")
        st.info("🔥 **4. Dumbbell Shoulder Press (Oturarak)**\n\n* **Ekipman:** Dumbbell + Sehpa | **Set/Tekrar:** 3 x 10 | **Teknik:** Omuzları Patlat")
        st.info("🔥 **5. Incline Dumbbell Biceps Curl**\n\n* **Ekipman:** Eğik Bench | **Set/Tekrar:** 3 x 12 | **Teknik:** Maksimum Esneme (Uzun Baş)")
        st.info("🔥 **6. Lying Triceps Extension (Alna Triceps / Skullcrusher)**\n\n* **Ekipman:** Z-Bar veya Dumbbell | **Set/Tekrar:** 3 x 12 | **Teknik:** Arka Kolu Parçala")

    elif secilen_gun == "Dinlenme Günü":
        st.markdown("### 🟡 Dinlenme Günü")
        st.warning("🥳 Bugün büyüme günü şampiyon! Kaslarını dinlendir, proteinini eksik etme.")

# --- TAB 2: HAFTALIK KİLO TAKİBİ ---
with tab_kilo:
    st.subheader("📈 Kilo Değişim Trendi")
    try:
        conn = sqlite3.connect('fitness_kocum.db')
        kilo_df = pd.read_sql_query("SELECT tarih, kilo FROM kilo_gecmisi ORDER BY tarih ASC", conn)
        conn.close()
        if not kilo_df.empty:
            st.line_chart(data=kilo_df, x='tarih', y='kilo', use_container_width=True)
            st.table(kilo_df.tail(7))
        else:
            st.info("Kilo grafiği için sol panelden kilonuzu girip kaydetmelisiniz.")
    except Exception as e:
        st.error(f"Grafik yükleme hatası: {e}")

# --- TAB 3: 🏆 PR REKOR DEHTERİM ---
with tab_rekorlar:
    st.subheader("🏆 Kişisel Ağır Yük (PR) Rekor Kayıt Defteri")
    st.write("Salon programındaki hareketlerde bastığın en yüksek ağırlığı kaydet, gelişimini takip et!")
    
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        hareket_secimi = st.selectbox("Rekor Kırdığın Hareketi Seç:", [
            "Olympic Flat Bench Press", "Incline Dumbbell Press", "Plate-Loaded Shoulder Press",
            "Hammer Pull-Down", "Plate-Loaded Row", "Dumbbell Row", "Seated Pec Deck Fly", "Lat Pulldown"
        ])
        rekor_kilo = st.number_input("Bastığın En Ağır Kilo (kg):", min_value=0.0, step=2.5, value=60.0)
        
        if st.button("👑 Yeni Rekoru Veritabanına Kazı"):
            try:
                conn = sqlite3.connect('fitness_kocum.db')
                c = conn.cursor()
                bugun_str = datetime.date.today().strftime("%Y-%m-%d")
                c.execute("INSERT OR REPLACE INTO pr_rekorlar (hareket_adi, rekor_kilo, tarih) VALUES (?, ?, ?)", 
                          (hareket_secimi, rekor_kilo, bugun_str))
                conn.commit()
                conn.close()
                st.success(f"Tebrikler! {hareket_secimi} için {rekor_kilo} kg rekoru kilitlendi!")
                st.rerun()
            except:
                pass
                
    with col_r2:
        st.write("🏅 **Güncel Rekorlar Listesi:**")
        try:
            conn = sqlite3.connect('fitness_kocum.db')
            pr_df = pd.read_sql_query("SELECT hareket_adi as 'Egzersiz', rekor_kilo as 'Maksimum Kilo (kg)', tarih as 'Kırıldığı Tarih' FROM pr_rekorlar", conn)
            conn.close()
            if not pr_df.empty:
                st.table(pr_df)
            else:
                st.info("Henüz kırılmış bir rekor kaydı yok. Bugün salonda ağırlıkları parçala!")
        except:
            pass
