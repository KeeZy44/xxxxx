import streamlit as st
import pandas as pd
import sqlite3
import datetime
from groq import Groq
import re

# Sayfa Ayarları
st.set_page_config(page_title="Mehmet Ali - AI Fitness Hub V2", layout="wide")

# Groq API Şifresi
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

st.title("⚡ Mehmet Ali - AI Fitness & Yaşam Otomasyon Merkezi (V2)")
st.markdown("Gelişmiş Veritabanı, Canlı Analitik ve Zamanlayıcı Entegrasyonu | 2026")

# --- GELİŞMİŞ YEREL VERİTABANI FONKSİYONLARI ---
def veritabanini_hazirla():
    conn = sqlite3.connect('fitness_kocum.db')
    c = conn.cursor()
    # Ana kayıt tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS gunluk_kayitlar
                 (tarih TEXT, mesaj_tipi TEXT, kullanici_mesaji TEXT, ai_hesabi TEXT, 
                  kalori INTEGER, protein INTEGER, karb INTEGER, yag INTEGER)''')
    # Profil ayarları tablosu (Kalıcılık için)
    c.execute('''CREATE TABLE IF NOT EXISTS profil_ayarlari
                 (id INTEGER PRIMARY KEY, boy INTEGER, kilo REAL, yas INTEGER)''')
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
    return 180, 80.0, 20  # Varsayılan değerler

def profil_kaydet(boy, kilo, yas):
    conn = sqlite3.connect('fitness_kocum.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO profil_ayarlari (id, boy, kilo, yas) VALUES (1, ?, ?, ?)", (boy, kilo, yas))
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

# Veritabanını ilk açılışta tetikle
veritabanini_hazirla()

# --- SOL PANEL: KALICI PROFİL VE ÖLÇÜMLER ---
st.sidebar.header("👤 Kalıcı Profil Ayarları")
v_boy, v_kilo, v_yas = profil_getir()

boy = st.sidebar.number_input("Boyunuz (cm):", value=v_boy, step=1)
kilo = st.sidebar.number_input("Güncel Kilo (kg):", value=v_kilo, step=0.1)
yas = st.sidebar.number_input("Yaşınız:", value=v_yas, step=1)

if st.sidebar.button("💾 Ölçümleri Hafızaya Kazı"):
    profil_kaydet(boy, kilo, yas)
    st.sidebar.success("Profil başarıyla kilitlendi!")

# Yağ Yakım Formülü (Mifflin-St Jeor)
bmh = (10 * kilo) + (6.25 * boy) - (5 * yas) + 5
hedef_kalori = int(bmh * 1.375 - 500)
hedef_protein = int(kilo * 2.2)
hedef_yag = int(kilo * 0.8)
hedef_karb = int((hedef_kalori - ((hedef_protein * 4) + (hedef_yag * 9))) / 4)

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Günlük Makro Hedefleri")
st.sidebar.metric(label="Hedef Kalori", value=f"{hedef_kalori} kcal")
st.sidebar.write(f"🍗 **Protein:** {hedef_protein}g | 🥑 **Yağ:** {hedef_yag}g")

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

# --- VERİLERİ DETAYLI ÇEKME FONKSİYONLARI ---
def gunluk_ozet_yukle():
    try:
        conn = sqlite3.connect('fitness_kocum.db')
        bugun_str = datetime.datetime.now().strftime("%Y-%m-%d")
        df = pd.read_sql_query("SELECT * FROM gunluk_kayitlar WHERE tarih LIKE ?", conn, params=(f"{bugun_str}%",))
        conn.close()
        
        beslenme_df = df[df['mesaj_tipi'] == 'Beslenme']
        al_kalori = beslenme_df['kalori'].sum() if not beslenme_df.empty else 0
        al_protein = beslenme_df['protein'].sum() if not beslenme_df.empty else 0
        
        su_df = df[df['mesaj_tipi'] == 'Su']
        al_su = su_df['kalori'].sum() if not su_df.empty else 0
        
        kreatin_df = df[df['mesaj_tipi'] == 'Kreatin']
        al_kreatin = True if not kreatin_df.empty else False
        
        return al_kalori, al_protein, al_su, al_kreatin
    except:
        return 0, 0, 0, False

alınan_kalori, alınan_protein, al_su, al_kreatin = gunluk_ozet_yukle()

# --- MERKEZİ SEKME SİSTEMİ (TAB) ---
tab_ana, tab_grafik, tab_saglik, tab_zamanlayici = st.tabs([
    "📊 Günlük Durum & Program", "📈 Haftalık Canlı Analiz", "🩺 Fizik Tedavi & Mikrolar", "⏱️ Pomodoro & Set Sayacı"
])

# --- TAB 1: GÜNLÜK DURUM VE ANTRENMAN ---
with tab_ana:
    st.subheader("📈 Günlük İlerleme Durumu")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.write(f"🍗 Protein Tüketimi ({alınan_protein}g / {hedef_protein}g)")
        st.progress(min(alınan_protein / max(hedef_protein, 1), 1.0))
    with col_m2:
        st.write(f"🔥 Kalori Alımı ({alınan_kalori} kcal / {hedef_kalori} kcal)")
        st.progress(min(alınan_kalori / max(hedef_kalori, 1), 1.0))

    st.markdown("---")
    st.subheader("📅 Haftalık Salon Programı")
    
    # Telefonlar için mükemmel akıllı gün seçici
    secilen_gun = st.selectbox(
        "Görmek istediğiniz antrenman gününü seçin:",
        ["Pazartesi (Göğüs & Omuz)", "Çarşamba (Sırt & Kol)", "Cuma (Hipertrofi Odaklı Üst Gelişim)", "Dinlenme Günü"]
    )

    if secilen_gun == "Pazartesi (Göğüs & Omuz)":
        st.markdown("### 🔴 Pazartesi: Göğüs & Omuz Günü")
        
        with st.container():
            st.info("⚡ **1. Olympic Flat Bench Press**\n\n* **Ekipman:** Flat Bench\n* **Set x Tekrar:** 3 x 6-8-10\n* **Teknik:** RPT (İlk set en ağır, sonra ağırlık düşür - RIR 1-2)")
        with st.container():
            st.info("⚡ **2. Hammer Incline Press**\n\n* **Ekipman:** Incline Machine\n* **Set x Tekrar:** 3 x 8-10\n* **Teknik:** Kontrollü Negatif (Ağırlığı 3 saniyede indir)")
        with st.container():
            st.info("⚡ **3. Plate-Loaded Shoulder Press**\n\n* **Ekipman:** Shoulder Machine\n* **Set x Tekrar:** 3 x 8-10\n* **Teknik:** Rest-Pause (Son set tükenişten sonra 15 sn dinlen, 3 tekrar daha çıkar)")
        with st.container():
            st.info("⚡ **4. Dumbbell Lateral Raise**\n\n* **Ekipman:** Dumbbell / Yan Omuz\n* **Set x Tekrar:** 4 x 12-15\n* **Teknik:** Son Set Drop Set (Ağırlığı azaltarak durmadan devam)")

    elif secilen_gun == "Çarşamba (Sırt & Kol)":
        st.markdown("### 🟢 Çarşamba: Sırt & Kol Günü")
        
        with st.container():
            st.success("⚡ **1. Hammer Pull-Down
