import streamlit as st
import pandas as pd
import sqlite3
import datetime
from groq import Groq
import re

# Sayfa Ayarları
st.set_page_config(page_title="Mehmet Ali - Fitness Hub V3", layout="wide")

# Groq API Şifresi
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

st.title("🏋️ Mehmet Ali - Yapay Zeka Destekli Fitness Paneli")
st.markdown("Hacim Odaklı 3 Günlük Üst Vücut Programı & Canlı Makro/Kilo Otomasyonu")

# --- GELİŞMİŞ YEREL VERİTABANI FONKSİYONLARI ---
def veritabanini_hazirla():
    conn = sqlite3.connect('fitness_kocum.db')
    c = conn.cursor()
    # Ana kayıt tablosu (Öğünlerin kalorilerini tutmak için)
    c.execute('''CREATE TABLE IF NOT EXISTS gunluk_kayitlar
                 (tarih TEXT, mesaj_tipi TEXT, kullanici_mesaji TEXT, ai_hesabi TEXT, 
                  kalori INTEGER, protein INTEGER, karb INTEGER, yag INTEGER)''')
    # Profil ayarları tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS profil_ayarlari
                 (id INTEGER PRIMARY KEY, boy INTEGER, kilo REAL, yas INTEGER)''')
    # Kilo geçmişi tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS kilo_gecmisi
                 (tarih TEXT UNIQUE, kilo REAL)''')
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

# Yağ Yakım Formülü (Mifflin-St Jeor) - Günlük Alman Gereken Kaloriyi Söyler
bmh = (10 * kilo) + (6.25 * boy) - (5 * yas) + 5
hedef_kalori = int(bmh * 1.375 - 500)
hedef_protein = int(kilo * 2.2)

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Günlük Hedeflerin")
st.sidebar.metric(label="Alman Gereken Kalori", value=f"{hedef_kalori} kcal")
st.sidebar.metric(label="Gerekli Protein", value=f"{hedef_protein} g")

# --- ANLIK ÖĞÜN EKLEME ALANI ---
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

# --- GÜNLÜK VERİLERİ ÇEKME FONKSİYONU ---
def gunluk_ozet_yukle():
    try:
        conn = sqlite3.connect('fitness_kocum.db')
        bugun_str = datetime.datetime.now().strftime("%Y-%m-%d")
        df = pd.read_sql_query("SELECT * FROM gunluk_kayitlar WHERE tarih LIKE ?", conn, params=(f"{bugun_str}%",))
        conn.close()
        
        beslenme_df = df[df['mesaj_tipi'] == 'Beslenme']
        al_kalori = beslenme_df['kalori'].sum() if not beslenme_df.empty else 0
        al_protein = beslenme_df['protein'].sum() if not beslenme_df.empty else 0
        
        return al_kalori, al_protein
    except:
        return 0, 0

alınan_kalori, alınan_protein = gunluk_ozet_yukle()

# --- MERKEZİ SEKME SİSTEMİ ---
tab_program, tab_kilo = st.tabs(["📊 Günlük Durum & Program", "📈 Haftalık Kilo Takibi"])

# --- TAB 1: GÜNLÜK DURUM VE ANTRENMAN ---
with tab_program:
    st.subheader("📈 Günlük İlerleme Durumu")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.write(f"🍗 Protein Tüketimi ({alınan_protein}g / {hedef_protein}g)")
        st.progress(min(alınan_protein / max(hedef_protein, 1), 1.0))
    with col_m2:
        st.write(f"🔥 Kalori Alımı ({alınan_kalori} kcal / {hedef_kalori} kcal)")
        st.progress(min(alınan_kalori / max(hedef_kalori, 1), 1.0))

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
        ["Pazartesi (1. Gün: Göğüs & Omuz)", "Çarşamba (2. Gün: Sırt & Kol)", "Cuma (3. Gün: Hipertrofi & Detay)", "Dinlenme Günü"]
    )

    if secilen_gun == "Pazartesi (1. Gün: Göğüs & Omuz)":
        st.markdown("### 🔴 1. GÜN: GÖĞÜS & OMUZ (Pazartesi)")
        st.info("🏋️ **1. Olympic Flat Bench Press**\n\n* **Ekipman:** Flat Bench | **Set/Tekrar:** 3 x 6-8-10 | **Teknik:** RPT (RIR 1-2)")
        st.info("🏋️ **2. Hammer Incline Press**\n\n* **Ekipman:** Incline Machine | **Set/Tekrar:** 3 x 8-10 | **Teknik:** Kontrollü Negatif")
        st.info("🏋️ **3. Plate-Loaded Shoulder Press**\n\n* **Ekipman:** Shoulder Machine | **Set/Tekrar:** 3 x 8-10 | **Teknik:** RP (Son Set)")
        st.info("🏋️ **4. Dumbbell Lateral Raise**\n\n* **Ekipman:** Dumbbell | **Set/Tekrar:** 3 x 12-15 | **Teknik:** RP (Son Set)")
        st.info("🏋️ **5. Functional Trainer Fly**\n\n* **Ekipman:** Cable Cross | **Set/Tekrar:** 3 x 12-15 | **Teknik:** Squeeze (Sıkıştır)")
        st.info("🏋️ **6. Cable Pushdown**\n\n* **Ekipman:** Cable Station | **Set/Tekrar:** 3 x 12 | **Teknik:** RP (Son Set)")

    elif secilen_gun == "Çarşamba (2. Gün: Sırt & Kol)":
        st.markdown("### 🟢 2. GÜN: SIRT & KOL (Çarşamba)")
        st.success("💪 **1. Hammer Pull-Down**\n\n* **Ekipman:** Pull-Down Machine | **Set/Tekrar:** 3 x 6-8-10 | **Teknik:** RPT (RIR 1-2)")
        st.success("💪 **2. Plate-Loaded Row**\n\n* **Ekipman:** Row Machine | **Set/Tekrar:** 3 x 8-10 | **Teknik:** Sırtını İyice Sık")
        st.success("💪 **3. Dumbbell Row**\n\n* **Ekipman:** Dumbbell + Bench | **Set/Tekrar:** 3 x 10 | **Teknik:** Dirseği Geri Çek")
        st.success("💪 **4. Preacher Curl**\n\n* **Ekipman:** Preacher Bench | **Set/Tekrar:** 3 x 12 | **Teknik:** RP (Son Set)")
        st.success("💪 **5. Hammer Curls**\n\n* **Ekipman:** Dumbbell | **Set/Tekrar:** 3 x 12 | **Teknik:** Dirsekleri Sabitle")
        st.success("💪 **6. Cable Facepull**\n\n* **Ekipman:** Cable Station | **Set/Tekrar:** 3 x 15 | **Teknik:** Omuz Sağlığı")

    elif secilen_gun == "Cuma (3. Gün: Hipertrofi & Detay)":
        st.markdown("### 🔵 3. GÜN: HİPERTROFİ & DETAY (Cuma)")
        st.info("🔥 **1. Olympic Incline Bench Press**\n\n* **Ekipman:** Incline Bench | **Set/Tekrar:** 3 x 6-8-10 | **Teknik:** RPT (Üst Göğüs)")
        st.info("🔥 **2. Lat Pulldown (Geniş Tutuş)**\n\n* **Ekipman:** Cable Station | **Set/Tekrar:** 3 x 8-10 | **Teknik:** Göğse Doğru Çek")
        st.info("🔥 **3. Hammer Shoulder Press**\n\n* **Ekipman:** Shoulder Machine | **Set/Tekrar:** 3 x 10 | **Teknik:** Kontrollü")
        st.info("🔥 **4. Seated Calf Raise**\n\n* **Ekipman:** Calf Machine | **Set/Tekrar:** 4 x 15-20 | **Teknik:** Diz Bükülmeden")
        st.info("🔥 **5. Incline DB Curl**\n\n* **Ekipman:** Incline Bench | **Set/Tekrar:** 3 x 12 | **Teknik:** Maksimum Esneme")
        st.info("🔥 **6. Triceps Overhead Extension**\n\n* **Ekipman:** Cable/Dumbbell | **Set/Tekrar:** 3 x 12 | **Teknik:** Dirsekler Yanmasın")

    elif secilen_gun == "Dinlenme Günü":
        st.markdown("### 🟡 Dinlenme Günü")
        st.warning("🥳 Bugün kasların büyüme günü şampiyon! Ağır kaldırmak yok. Diz sakatlığı için evdeki fizik tedavi hareketlerine ve esnemelere odaklan.")

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
