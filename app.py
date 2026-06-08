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
    
    # Telefonlar için en pratik gün seçici (Tıklayınca o günün tüm hareketleri jilet gibi alta açılır)
    secilen_gun = st.selectbox(
        "Görmek istediğiniz antrenman gününü seçin:",
        ["Pazartesi (Göğüs & Omuz)", "Çarşamba (Sırt & Kol)", "Cuma (Hipertrofi Odaklı Üst Gelişim)", "Dinlenme Günü"]
    )

    if secilen_gun == "Pazartesi (Göğüs & Omuz)":
        st.markdown("### 🔴 Pazartesi: Göğüs & Omuz Günü")
        
        st.info("⚡ **1. Olympic Flat Bench Press**\n* **Ekipman:** Flat Bench\n* **Set x Tekrar:** 3 x 6-8-10\n* **Teknik:** RPT (İlk set en ağır, sonra ağırlık düşür - RIR 1-2)")
        st.info("⚡ **2. Hammer Incline Press**\n* **Ekipman:** Incline Machine\n* **Set x Tekrar:** 3 x 8-10\n* **Teknik:** Kontrollü Negatif (Ağırlığı 3 saniyede indir)")
        st.info("⚡ **3. Plate-Loaded Shoulder Press**\n* **Ekipman:** Shoulder Machine\n* **Set x Tekrar:** 3 x 8-10\n* **Teknik:** Rest-Pause (Son set tükenişten sonra 15 sn dinlen, 3 tekrar daha çıkar)")
        st.info("⚡ **4. Dumbbell Lateral Raise**\n* **Ekipman:** Dumbbell / Yan Omuz\n* **Set x Tekrar:** 4 x 12-15\n* **Teknik:** Son Set Drop Set (Ağırlığı azaltarak durmadan devam)")

    elif secilen_gun == "Çarşamba (Sırt & Kol)":
        st.markdown("### 🟢 Çarşamba: Sırt & Kol Günü")
        
        st.success("⚡ **1. Hammer Pull-Down**\n* **Ekipman:** Lat Pull Machine\n* **Set x Tekrar:** 3 x 6-8-10\n* **Teknik:** RPT (Sırt kaslarını zirvede tam sıkıştır)")
        st.success("⚡ **2. Plate-Loaded Row**\n* **Ekipman:** Row Machine\n* **Set x Tekrar:** 3 x 8-10\n* **Teknik:** Dirseği gövdeye sıfır çek, gerilmeyi hisset")
        st.success("⚡ **3. Preacher Curl**\n* **Ekipman:** Z-Bar / Sehpa\n* **Set x Tekrar:** 3 x 12\n* **Teknik:** Tepe noktasında bicepsi 1 saniye sık barı yavaş bırak")
        st.success("⚡ **4. Hammer Curls**\n* **Ekipman:** Dumbbell\n* **Set x Tekrar:** 3 x 12\n* **Teknik:** Bilekleri bükmeden, ön kola odaklanarak kontrollü nizam")

    elif secilen_gun == "Cuma (Hipertrofi Odaklı Üst Gelişim)":
        st.markdown("### 🔵 Cuma: Hipertrofi Odaklı Üst Gövde")
        
        st.help("⚡ **1. Olympic Incline Bench Press**\n* **Ekipman:** Incline Bench / Üst Göğüs\n* **Set x Tekrar:** 3 x 6-8-10\n* **Teknik:** Ağır kiloyla göğüs kemiğine kontrollü indir ve patlayıcı güçle it")
        st.help("⚡ **2. Lat Pulldown**\n* **Ekipman:** Geniş Tutuş Bar\n* **Set x Tekrar:** 3 x 8-10\n* **Teknik:** Göğse doğru çekiş, omuz küreklerini birbirine yaklaştır")
        st.help("⚡ **3. Seated Calf Raise**\n* **Ekipman:** Calf Machine / Kalf\n* **Set x Tekrar:** 4 x 15-20\n* **Teknik:** Alt noktada tam esneme, parmak ucunda maksimum yükseliş")
        st.help("⚡ **4. Triceps Extension**\n* **Ekipman:** Kablo / Halat\n* **Set x Tekrar:** 3 x 12\n* **Teknik:** Dirsekleri gövdeye sabitle, sadece ön kolu hareket ettirerek kilitle")

    elif secilen_gun == "Dinlenme Günü":
        st.markdown("### 🟡 Dinlenme & Aktif İyileşme Günü")
        st.warning("🥳 Bugün kasların büyüme günü şampiyon! Ağır kaldırmak yok. Diz sakatlığı için evdeki fizik tedavi hareketlerine ve esnemelere odaklan. Mikroları (Su ve Kreatin) eksik etme!")
# --- TAB 2: HAFTALIK CANLI ANALİZ GRAFİĞİ ---
with tab_grafik:
    st.subheader("📈 Son 7 Günlük Makro Analiz Raporu")
    try:
        conn = sqlite3.connect('fitness_kocum.db')
        df_all = pd.read_sql_query("SELECT tarih, kalori, protein, mesaj_tipi FROM gunluk_kayitlar WHERE mesaj_tipi='Beslenme'", conn)
        conn.close()
        
        if not df_all.empty:
            df_all['tarih'] = pd.to_datetime(df_all['tarih']).dt.date
            grafik_df = df_all.groupby('tarih').sum().reset_index()
            grafik_df = grafik_df.sort_values('tarih').tail(7)
            
            st.write("🔥 **Günlük Kalori Dalgalanma Grafiği**")
            st.line_chart(data=grafik_df, x='tarih', y='kalori', use_container_width=True)
            
            st.write("🍗 **Günlük Protein Tüketim Analizi (g)**")
            st.bar_chart(data=grafik_df, x='tarih', y='protein', use_container_width=True)
        else:
            st.info("Grafik oluşturulabilmesi için veritabanında en az 1 beslenme kaydı bulunmalıdır.")
    except Exception as e:
        st.error(f"Grafik yükleme hatası: {e}")

# --- TAB 3: MİKRO BESİNLER VE FİZİK TEDAVİ ---
with tab_saglik:
    st.subheader("🩺 Fizik Tedavi & Hidrasyon İstasyonu")
    col_s1, col_s2 = st.columns(2)
    
    with col_s1:
        st.write(f"💧 **Bugün İçilen Su:** {al_su} ml")
        su_ekle = st.selectbox("Su Miktarı Ekle:", [250, 500, 750, 1000])
        if st.button("🥤 Suyu Kafaya Dik"):
            local_veri_kaydet("Su", f"{su_ekle}ml su içildi", "", kalori=su_ekle)
            st.success(f"{su_ekle} ml Su Başarıyla Eklendi!")
            st.rerun()
            
        st.markdown("---")
        if al_kreatin:
            st.success("💪 Bugün 5g Kreatin Alındı! Hücreler dolu.")
        else:
            st.warning("⚠️ Bugün henüz Kreatin almadın!")
            if st.button("💊 Kreatin Aldım"):
                local_veri_kaydet("Kreatin", "5g Kreatin tüketildi", "", kalori=5)
                st.success("Kreatin kaydı işlendi!")
                st.rerun()
                
    with col_s2:
        st.write("📋 **Günlük Fizik Tedavi Görevleri (Diz Sakatlığı)**")
        t1 = st.checkbox("Düz bacak kaldırma (3 set x 15 tekrar)")
        t2 = st.checkbox("Duvara yaslanarak squat (Isometrik hold - 45 sn)")
        t3 = st.checkbox("Foam Roller ile bacak/quad masajı (10 dk)")
        
        if t1 and t2 and t3:
            st.balloons()
            st.success("🏆 Harika! Bugün diz tedavisini eksiksiz tamamladın şampiyon!")

# --- TAB 4: AKILLI POMODORO VE SET SAYACI ---
with tab_zamanlayici:
    st.subheader("⏱️ Odaklanma Odası (KPSS Ders Çalışma & Set Arası)")
    st.write("Aşağıdaki widget tarayıcı tabanlı çalışır, süre akarken Streamlit donmaz veya kasmaz!")
    
    # Canlı HTML/JS Pomodoro Sayacı Component'i
    pomodoro_html = """
    <div style="background-color:#1e1e24; color:white; padding:20px; border-radius:12px; text-align:center; font-family:Arial, sans-serif; box-shadow: 0px 4px 10px rgba(0,0,0,0.3);">
        <h2 id="timer-title" style="margin-bottom:10px; color:#ff4b4b;">🎯 KPSS Odaklanma Modu (45 Dk)</h2>
        <div id="countdown" style="font-size:48px; font-weight:bold; margin:20px 0; font-family:monospace; color:#00ffcc;">45:00</div>
        <button onclick="startTimer(2700, '🎯 KPSS Odaklanma Modu')" style="background-color:#ff4b4b; color:white; border:none; padding:10px 20px; margin:5px; border-radius:5px; cursor:pointer; font-weight:bold;">45 Dk KPSS Ders</button>
        <button onclick="startTimer(90, '💪 Set Arası Dinlenme')" style="background-color:#007bff; color:white; border:none; padding:10px 20px; margin:5px; border-radius:5px; cursor:pointer; font-weight:bold;">90 Sn Set Arası</button>
        <button onclick="stopTimer()" style="background-color:#6c757d; color:white; border:none; padding:10px 20px; margin:5px; border-radius:5px; cursor:pointer; font-weight:bold;">Durdur / Sıfırla</button>
    </div>

    <script>
        let timer;
        function startTimer(seconds, title) {
            clearInterval(timer);
            document.getElementById("timer-title").innerText = title;
            let timeRun = seconds;
            updateDisplay(timeRun);
            
            timer = setInterval(function() {
                timeRun--;
                updateDisplay(timeRun);
                if (timeRun <= 0) {
                    clearInterval(timer);
                    alert("⏰ Süre Tamamlandı Şampiyon! Görev Başarılı.");
                }
            }, 1000);
        }
        function stopTimer() {
            clearInterval(timer);
            document.getElementById("countdown").innerText = "00:00";
            document.getElementById("timer-title").innerText = "⏱️ Süre Bekliyor...";
        }
        function updateDisplay(sec) {
            let mins = Math.floor(sec / 60);
            let remSecs = sec % 60;
            document.getElementById("countdown").innerText = 
                (mins < 10 ? "0" : "") + mins + ":" + (remSecs < 10 ? "0" : "") + remSecs;
        }
    </script>
    """
    st.components.v1.html(pomodoro_html, height=220)
