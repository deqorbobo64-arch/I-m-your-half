import telebot
import google.generativeai as genai
import requests
import json
import os
import yt_dlp
from datetime import datetime
import threading
import time

# === SOZLAMALAR ===
BOT_TOKEN = "8679558924:AAGrf-E2jlSzzt3lRILoc3C5FOcw-ShVX_o"
GEMINI_API_KEY = "AIzaSyDCYf2QVD_VY4Ipo2MP0By23yY2xBRtivU"
CHANNEL_ID = "@tezkor_habar_robot"
ADMIN_ID = 0  # O'z Telegram ID ingizni yozing

# === SETUP ===
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')
bot = telebot.TeleBot(BOT_TOKEN)

# === DATABASE (oddiy) ===
users = {}
premium_users = set()

# === KANALGA AZOLARNI TEKSHIRISH ===
def check_subscription(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# === START ===
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    users[user_id] = {'count': 0, 'date': str(datetime.now().date())}
    
    if not check_subscription(user_id):
        markup = telebot.types.InlineKeyboardMarkup()
        btn = telebot.types.InlineKeyboardButton(
            "📢 Kanalga a'zo bo'lish", 
            url="https://t.me/tezkor_habar_robot"
        )
        check_btn = telebot.types.InlineKeyboardButton(
            "✅ Tekshirish",
            callback_data="check_sub"
        )
        markup.add(btn)
        markup.add(check_btn)
        bot.send_message(message.chat.id, 
            "⚡ Botdan foydalanish uchun kanalga a'zo bo'ling!",
            reply_markup=markup)
        return
    
    show_menu(message.chat.id)

def show_menu(chat_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🤖 AI Savol", "🌐 Tarjima")
    markup.row("📝 Matn Yozish", "🎬 Kino")
    markup.row("🎵 Musiqa", "📹 Video")
    markup.row("🎮 O'yin", "☀️ Ob-havo")
    markup.row("💰 Premium", "ℹ️ Haqida")
    
    bot.send_message(chat_id,
        "👋 Salom! Men <b>I'm your half</b> botman!\n\n"
        "🆓 Bepul: Kuniga 10 ta savol\n"
        "💎 Premium: Cheksiz (15,000 so'm/oy)\n\n"
        "Quyidagi bo'limlardan birini tanlang:",
        parse_mode='HTML',
        reply_markup=markup)

# === CALLBACK ===
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub_callback(call):
    if check_subscription(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Rahmat! Botga xush kelibsiz!")
        show_menu(call.message.chat.id)
    else:
        bot.answer_callback_query(call.id, "❌ Hali a'zo bo'lmadingiz!")

# === LIMIT TEKSHIRISH ===
def check_limit(user_id):
    if user_id in premium_users:
        return True
    if user_id not in users:
        users[user_id] = {'count': 0, 'date': str(datetime.now().date())}
    today = str(datetime.now().date())
    if users[user_id]['date'] != today:
        users[user_id] = {'count': 0, 'date': today}
    if users[user_id]['count'] >= 10:
        return False
    users[user_id]['count'] += 1
    return True

# === AI SAVOL ===
@bot.message_handler(func=lambda m: m.text == "🤖 AI Savol")
def ai_menu(message):
    bot.send_message(message.chat.id, 
        "🤖 Savolingizni yozing, javob beraman!")
    bot.register_next_step_handler(message, handle_ai)

def handle_ai(message):
    user_id = message.from_user.id
    if not check_subscription(user_id):
        bot.send_message(message.chat.id, "❌ Avval kanalga a'zo bo'ling!")
        return
    if not check_limit(user_id):
        bot.send_message(message.chat.id, 
            "⚠️ Kunlik limit tugadi!\n💎 Premium oling: /premium")
        return
    bot.send_message(message.chat.id, "⏳ Javob tayyorlanmoqda...")
    try:
        response = model.generate_content(message.text)
        bot.send_message(message.chat.id, response.text)
    except:
        bot.send_message(message.chat.id, "❌ Xatolik! Qayta urinib ko'ring.")

# === TARJIMA ===
@bot.message_handler(func=lambda m: m.text == "🌐 Tarjima")
def translate_menu(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🇺🇿 O'zbekcha", "🇷🇺 Ruscha", "🇬🇧 Inglizcha")
    markup.row("🔙 Orqaga")
    bot.send_message(message.chat.id, "Qaysi tilga tarjima qilaylik?", 
        reply_markup=markup)

# === MATN YOZISH ===
@bot.message_handler(func=lambda m: m.text == "📝 Matn Yozish")
def text_menu(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📄 CV Yozish", "📧 Xat Yozish")
    markup.row("📱 Post Yozish", "📊 Biznes Reja")
    markup.row("🔙 Orqaga")
    bot.send_message(message.chat.id, "Qaysi turdagi matn kerak?",
        reply_markup=markup)

# === KINO ===
@bot.message_handler(func=lambda m: m.text == "🎬 Kino")
def movie_menu(message):
    bot.send_message(message.chat.id, 
        "🎬 Kino nomini yozing, ma'lumot beraman!")
    bot.register_next_step_handler(message, handle_movie)

def handle_movie(message):
    if not check_limit(message.from_user.id):
        bot.send_message(message.chat.id, "⚠️ Limit tugadi! /premium")
        return
    bot.send_message(message.chat.id, "🔍 Qidirilmoqda...")
    try:
        prompt = f"'{message.text}' kinosi haqida ma'lumot ber: yil, janr, rejissyor, qisqacha syujet. O'zbek tilida yoz."
        response = model.generate_content(prompt)
        bot.send_message(message.chat.id, response.text)
    except:
        bot.send_message(message.chat.id, "❌ Xatolik!")

# === MUSIQA ===
@bot.message_handler(func=lambda m: m.text == "🎵 Musiqa")
def music_menu(message):
    bot.send_message(message.chat.id,
        "🎵 Qo'shiq nomini yozing, YouTube dan topib beraman!")
    bot.register_next_step_handler(message, handle_music)

def handle_music(message):
    if not check_limit(message.from_user.id):
        bot.send_message(message.chat.id, "⚠️ Limit tugadi! /premium")
        return
    bot.send_message(message.chat.id, "🔍 Qidirilmoqda...")
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'default_search': 'ytsearch1',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(message.text, download=False)
            if 'entries' in info:
                info = info['entries'][0]
            url = info['url']
            title = info['title']
            bot.send_message(message.chat.id, 
                f"🎵 {title}\n\n🔗 Link: {info['webpage_url']}")
    except:
        bot.send_message(message.chat.id, "❌ Topilmadi!")

# === VIDEO ===
@bot.message_handler(func=lambda m: m.text == "📹 Video")
def video_menu(message):
    bot.send_message(message.chat.id,
        "📹 YouTube yoki Instagram linkini yuboring!")
    bot.register_next_step_handler(message, handle_video)

def handle_video(message):
    if not check_limit(message.from_user.id):
        bot.send_message(message.chat.id, "⚠️ Limit tugadi! /premium")
        return
    bot.send_message(message.chat.id, "⏳ Yuklanmoqda...")
    try:
        ydl_opts = {
            'format': 'best[filesize<50M]',
            'quiet': True,
            'outtmpl': '/tmp/%(title)s.%(ext)s',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(message.text, download=True)
            filename = ydl.prepare_filename(info)
        with open(filename, 'rb') as f:
            bot.send_video(message.chat.id, f)
        os.remove(filename)
    except:
        bot.send_message(message.chat.id, "❌ Yuklab bo'lmadi!")

# === O'YIN ===
@bot.message_handler(func=lambda m: m.text == "🎮 O'yin")
def game_menu(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🧩 Topishmoq", "❓ Viktorina")
    markup.row("🔢 Matematika", "🔙 Orqaga")
    bot.send_message(message.chat.id, "O'yin tanlang!", reply_markup=markup)

# === OB-HAVO ===
@bot.message_handler(func=lambda m: m.text == "☀️ Ob-havo")
def weather_menu(message):
    bot.send_message(message.chat.id, "🌍 Shahar nomini yozing!")
    bot.register_next_step_handler(message, handle_weather)

def handle_weather(message):
    try:
        url = f"https://wttr.in/{message.text}?format=3&lang=uz"
        response = requests.get(url)
        bot.send_message(message.chat.id, f"☀️ {response.text}")
    except:
        bot.send_message(message.chat.id, "❌ Xatolik!")

# === PREMIUM ===
@bot.message_handler(func=lambda m: m.text == "💰 Premium")
def premium_menu(message):
    bot.send_message(message.chat.id,
        "💎 <b>PREMIUM</b>\n\n"
        "✅ Cheksiz savol\n"
        "✅ Tezroq javob\n"
        "✅ Video yuklab berish\n\n"
        "💰 Narx: <b>15,000 so'm/oy</b>\n\n"
        "To'lov uchun admin bilan bog'laning:\n"
        "@admin",
        parse_mode='HTML')

# === HAQIDA ===
@bot.message_handler(func=lambda m: m.text == "ℹ️ Haqida")
def about(message):
    bot.send_message(message.chat.id,
        "🤖 <b>I'm your half Bot</b>\n\n"
        "⚡ Kanal: @tezkor_habar_robot\n"
        "🌟 Funksiyalar:\n"
        "• AI savol-javob\n"
        "• Tarjima\n"
        "• Kino ma'lumoti\n"
        "• Musiqa va video\n"
        "• O'yinlar\n"
        "• Ob-havo\n\n"
        "💎 Premium: 15,000 so'm/oy",
        parse_mode='HTML')

# === ORQAGA ===
@bot.message_handler(func=lambda m: m.text == "🔙 Orqaga")
def back(message):
    show_menu(message.chat.id)

# === UMUMIY AI ===
@bot.message_handler(func=lambda message: True)
def handle_all(message):
    user_id = message.from_user.id
    if not check_subscription(user_id):
        start(message)
        return
    if not check_limit(user_id):
        bot.send_message(message.chat.id, 
            "⚠️ Kunlik limit tugadi!\n💎 Premium: /premium")
        return
    bot.send_message(message.chat.id, "⏳ Javob tayyorlanmoqda...")
    try:
        response = model.generate_content(message.text)
        bot.send_message(message.chat.id, response.text)
    except:
        bot.send_message(message.chat.id, "❌ Xatolik!")

# === ISHGA TUSHIRISH ===
print("Bot ishlamoqda...")
bot.polling(none_stop=True)
