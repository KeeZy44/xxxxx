import streamlit as st
import pandas as pd
import sqlite3
import datetime

# Sayfa Ayarları
st.set_page_config(page_title="Mehmet Ali - Fitness Dashboard V3", layout="wide")

st.title("🏋️ Mehmet Ali - Kişisel Fitness Takip Paneli")
st.markdown("Hacim Odaklı 3 Günlük Üst Vücut Programı & Kilo Takip Otomasyonu")

# --- VERİTABANI İŞLEMLERİ ---
def veritabanini_hazirla():
    conn = sqlite3.connect('fitness_kocum.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS profil_ayarlari
                 (id INTEGER PRIMARY KEY, boy INTEGER, kilo REAL, yas INTEGER)''')
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

veritabanini_hazirla()

# --- SOL PANEL: PROFİL VE HEDEFLER ---
st.sidebar.header("👤 Güncel Durum")
v_boy, v_kilo, v_yas = profil_getir()

boy = st.sidebar.number_input("Boy (cm):", value=v_boy, step=1)
kilo = st.sidebar.number_input("Kilo (kg):", value=v_kilo, step=0.1)
yas = st.sidebar.number_input("Yaş:", value=v_yas, step=1)

if st.sidebar.button("💾 Kiloyu ve Profili Kaydet"):
    profil_kaydet(boy, kilo, yas)
    st.sidebar.success("Kilo geçmişe işlendi!")
    st.rerun()

# Hesaplamalar
hedef_protein = int(kilo * 2.2)
st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Günlük Protein Hedefin")
st.sidebar.metric(label="Gerekli Protein", value=f"{hedef_protein} g")

# --- MERKEZİ SEKME SİSTEMİ ---
tab_program, tab_kilo = st.tabs(["📅 Salon Programım", "📈 Haftalık Kilo Takibi"])

# --- TAB 1: SALON PROGRAMI ---
with tab_program:
    # Kurallar Genişletme Paneli
    with st.expander("🚨 ÖNEMLİ ANTRENMAN KURALLARI & TEKNİKLER"):
        st.markdown("**• Isınma:** 10 dk hafif yürüyüş + eklem hareketleri. [cite: 4]")
        st.markdown("**• Kardiyo:** Sonunda 15 dk (10 eğim, 5 hız). [cite: 5]")
        st.markdown("**• Dinlenme:** Set arası 2-3 dk, hareket arası 1 dk. [cite: 6]")
        st.markdown("**• RPT:** İlk set en ağır. Sonraki setlerde ağırlığı %10 düşür, tekrarı artır. [cite: 8, 9]")
        st.markdown("**• Rest-Pause (RP):** Set bitince 15 sn dinlen, +3-5 tekrar daha yap (3 kez tekrarla). [cite: 10]")

    secilen_gun = st.selectbox(
        "Hangi günün programına bakacaksın?",
        ["Pazartesi (1. Gün: Göğüs & Omuz)", "Çarşamba (2. Gün: Sırt & Kol)", "Cuma (3. Gün: Hipertrofi & Detay)", "Dinlenme Günü"]
    )

    if secilen_gun == "Pazartesi (1. Gün: Göğüs & Omuz)":
        st.markdown("### 🔴 1. GÜN: GÖĞÜS & OMUZ [cite: 11]")
        st.info("🏋️ **1. Olympic Flat Bench Press**\n\n* **Ekipman:** Flat Bench | **Set/Tekrar:** 3 x 6-8-10 | **Teknik:** RPT (RIR 1-2) [cite: 12]")
        st.info("🏋️ **2. Hammer Incline Press**\n\n* **Ekipman:** Incline Machine | **Set/Tekrar:** 3 x 8-10 | **Teknik:** Kontrollü Negatif [cite: 12]")
        st.info("🏋️ **3. Plate-Loaded Shoulder Press**\n\n* **Ekipman:** Shoulder Machine | **Set/Tekrar:** 3 x 8-10 | **Teknik:** RP (Son Set) [cite: 12]")
        st.info("🏋️ **4. Dumbbell Lateral Raise**\n\n* **Ekipman:** Dumbbell | **Set/Tekrar:** 3 x 12-15 | **Teknik:** RP (Son Set) [cite: 12]")
        st.info("🏋️ **5. Functional Trainer Fly**\n\n* **Ekipman:** Cable Cross | **Set/Tekrar:** 3 x 12-15 | **Teknik:** Squeeze (Sıkıştır) [cite: 12]")
        st.info("🏋️ **6. Cable Pushdown**\n\n* **Ekipman:** Cable Station | **Set/Tekrar:** 3 x 12 | **Teknik:** RP (Son Set) [cite: 12]")

    elif secilen_gun == "Çarşamba (2. Gün: Sırt & Kol)":
        st.markdown("### 🟢 2. GÜN: SIRT & KOL [cite: 13]")
        st.success("💪 **1. Hammer Pull-Down**\n\n* **Ekipman:** Pull-Down Machine | **Set/Tekrar:** 3 x 6-8-10 | **Teknik:** RPT (RIR 1-2) [cite: 14]")
        st.success("💪 **2. Plate-Loaded Row**\n\n* **Ekipman:** Row Machine | **Set/Tekrar:** 3 x 8-10 | **Teknik:** Sırtını İyice Sık [cite: 14]")
        st.success("💪 **3. Dumbbell Row**\n\n* **Ekipman:** Dumbbell + Bench | **Set/Tekrar:** 3 x 10 | **Teknik:** Dirseği Geri Çek [cite: 14]")
        st.success("💪 **4. Preacher Curl**\n\n* **Ekipman:** Preacher Bench | **Set/Tekrar:** 3 x 12 | **Teknik:** RP (Son Set) [cite: 15]")
        st.success("💪 **5. Hammer Curls**\n\n* **Ekipman:** Dumbbell | **Set/Tekrar:** 3 x 12 | **Teknik:** Dirsekleri Sabitle [cite: 15]")
        st.success("💪 **6. Cable Facepull**\n\n* **Ekipman:** Cable Station | **Set/Tekrar:** 3 x 15 | **Teknik:** Omuz Sağlığı [cite: 15]")

    elif secilen_gun == "Cuma (3. Gün: Hipertrofi & Detay)":
        st.markdown("### 🔵 3. GÜN: HİPERTROFİ & DETAY [cite: 16]")
        st.info("🔥 **1. Olympic Incline Bench Press**\n\n* **Ekipman:** Incline Bench | **Set/Tekrar:** 3 x 6-8-10 | **Teknik:** RPT (Üst Göğüs) [cite: 17]")
        st.info("🔥 **2. Lat Pulldown (Geniş Tutuş)**\n\n* **Ekipman:** Cable Station | **Set/Tekrar:** 3 x 8-10 | **Teknik:** Göğse Doğru Çek [cite: 17]")
        st.info("🔥 **3. Hammer Shoulder Press**\n\n* **Ekipman:** Shoulder Machine | **Set/Tekrar:** 3 x 10 | **Teknik:** Kontrollü [cite: 17]")
        st.info("🔥 **4. Seated Calf Raise**\n\n* **Ekipman:** Calf Machine | **Set/Tekrar:** 4 x 15-20 | **Teknik:** Diz Bükülmeden [cite: 17]")
        st.info("🔥 **5. Incline DB Curl**\n\n* **Ekipman:** Incline Bench | **Set/Tekrar:** 3 x 12 | **Teknik:** Maksimum Esneme [cite: 17]")
        st.info("🔥 **6. Triceps Overhead Extension**\n\n* **Ekipman:** Cable/Dumbbell | **Set/Tekrar:** 3 x 12 | **Teknik:** Dirsekler Yanmasın [cite: 17]")

    elif secilen_gun == "Dinlenme Günü":
        st.markdown("### 🟡 Dinlenme Günü [cite: 18]")
        st.warning("🥳 Bugün büyüme günü şampiyon! Sakatlık riski olmaması adına bacak antrenmanı eklemedik. Evdeki fizik tedavi ve esnemelerini yapabilirsin. [cite: 18]")

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
        st.error(f"Grafik yüklenirken bir hata oluştu: {e}")
