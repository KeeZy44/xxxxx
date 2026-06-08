import asyncio
from groq import Groq
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import sqlite3
from datetime import datetime
import re

# TELEGRAM VE YAPAY ZEKA YAPILANDIRMASI
# NOT: Alttaki tırnakların içine BotFather'dan aldığın o uzun Telegram Token şifreni yapıştır!
TELEGRAM_TOKEN = "8843521692:AAGYW2w8zAH67ox8-NkQpNZoUD3nZcYI9Z4"
GROQ_API_KEY = "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"

client = Groq(api_key=GROQ_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Bot üzerinden gelen verilerin V2 tablo yapısına uygun kaydedilmesi
def bot_veri_kaydet(mesaj_tipi, kullanici_mesaji, ai_hesabi, kalori=0, protein=0, karb=0, yag=0):
    conn = sqlite3.connect('fitness_kocum.db')
    c = conn.cursor()
    tarih = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO gunluk_kayitlar VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
              (tarih, mesaj_tipi, kullanici_mesaji, ai_hesabi, kalori, protein, karb, yag))
    conn.commit()
    conn.close()

sistem_komutu = """
Sen Mehmet Ali'nin profesyonel fitness koçusun. Kullanıcı yediklerini yazdığında besin değerlerini hesapla.
Cevabında mutlaka 'Kalori: 300 kcal' ve 'Protein: 20 gram' gibi net ve belirgin ifadeler kullan.
Cevapların kısa, disiplinli ve emojili olsun.
"""

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("💪 Mehmet Ali, Demir Koç V2 göreve hazır! Yediklerini yazarak makrona ekleyebilir veya /panel komutuyla yeni arayüze zıplayabilirsin!")

# --- GÜNCEL TUNEL LİNKİNİN GÖMÜLDÜĞÜ PANEL KOMUTU ---
@dp.message(Command("panel"))
async def panel_command(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text="🌐 Canlı Fitness Panelini Aç", 
        url="https://be372844e4cb13.lhr.life"  # En son aldığın güncel kararlı tünel linki
    ))
    await message.answer("🎯 Buyur şampiyon, V2 Gelişmiş Analitik Panelinin linki burada:", reply_markup=builder.as_markup())

@dp.message()
async def ai_response(message: types.Message):
    await bot.send_chat_action(chat_id=message.chat.id, action='typing')
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "system", "content": sistem_komutu}, {"role": "user", "content": message.text}],
            temperature=0.3,
        )
        ai_cevabi = completion.choices[0].message.content
        
        kalori, protein = 0, 0
        k_match = re.search(r'Kalori:\s*(\d+)', ai_cevabi, re.IGNORECASE)
        p_match = re.search(r'Protein:\s*(\d+)', ai_cevabi, re.IGNORECASE)
        
        if k_match: kalori = int(k_match.group(1))
        if p_match: protein = int(p_match.group(1))
        
        bot_veri_kaydet("Beslenme", message.text, ai_cevabi, kalori, protein, 0, 0)
        await message.answer(ai_cevabi)
    except Exception as e:
        await message.answer("Bağlantı hatası koç, tekrar dene!")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())