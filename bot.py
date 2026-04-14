import telebot
import google.generativeai as genai
import requests
import os
import yt_dlp
from datetime import datetime
import threading
from flask import Flask

# === SOZLAMALAR ===
BOT_TOKEN = "8679558924:AAGrf-E2jlSzzt3lRILoc3C5FOcw-ShVX_o"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
CHANNEL_ID = "@tezkor_habar_robot"

# === SETUP ===
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# === DATABASE ===
users = {}
premium_users = set()

@app.route('/')
def home():
    return 'Bot ishlayapti! ✅'

# === KANAL TEKSHIRISH ===
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
    if user_id not in users:
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
            "⚡ Botdan foydalanish uchun avval kanalga a'zo bo'ling!",
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
        "💎 Premium: Cheksiz (30,000 so'm/oy)\n\n"
        "Quyidagi bo'limlardan birini tanlang:",
        parse_mode='HTML',
        reply_markup=markup)

# === CALLBACK ===
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub_callback(call):
    if check_subscription(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Rahmat!")
        show_menu(call.message.chat.id)
    else:
        bot.answer_callback_query(call.id, "❌ Hali a'zo bo'lmadingiz!")

# === LIMIT ===
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
    bot.send_message(message.chat.id, "🤖 Savolingizni yozing!")
    bot.register_next_step_handler(message, handle_ai)

def handle_ai(message):
    if not check_subscription(message.from_user.id):
        start(message)
        return
    if not check_limit(message.from_user.id):
        bot.send_message(message.chat.id, "⚠️ Limit tugadi!\n💎 /premium")
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
    bot.register_next_step_handler(message, handle_translate_lang)

def handle_translate_lang(message):
    lang = message.text
    if lang == "🔙 Orqaga":
        show_menu(message.chat.id)
        return
    bot.send_message(message.chat.id, "Tarjima qilinadigan matnni yozing:")
    bot.register_next_step_handler(message, lambda m: handle_translate(m, lang))

def handle_translate(message, lang):
    if not check_limit(message.from_user.id):
        bot.send_message(message.chat.id, "⚠️ Limit tugadi! /premium")
        return
    lang_map = {
        "🇺🇿 O'zbekcha": "o'zbek",
        "🇷🇺 Ruscha": "rus",
        "🇬🇧 Inglizcha": "ingliz"
    }
    target = lang_map.get(lang, "o'zbek")
    bot.send_message(message.chat.id, "⏳ Tarjima qilinmoqda...")
    try:
        prompt = f"Quyidagi matnni {target} tiliga tarjima qil, faqat tarjimani yoz:\n{message.text}"
        response = model.generate_content(prompt)
        bot.send_message(message.chat.id, response.text)
    except:
        bot.send_message(message.chat.id, "❌ Xatolik!")

# === MATN YOZISH ===
@bot.message_handler(func=lambda m: m.text == "📝 Matn Yozish")
def text_menu(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📄 CV Yozish", "📧 Xat Yozish")
    markup.row("📱 Post Yozish", "📊 Biznes Reja")
    markup.row("✍️ Hikoya", "🔙 Orqaga")
    bot.send_message(message.chat.id, "Qaysi turdagi matn kerak?",
        reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["📄 CV Yozish", "📧 Xat Yozish", "📱 Post Yozish", "📊 Biznes Reja", "✍️ Hikoya"])
def handle_text_type(message):
    prompts = {
        "📄 CV Yozish": "Kasb va tajribangizni yozing:",
        "📧 Xat Yozish": "Xat mavzusini yozing:",
        "📱 Post Yozish": "Post mavzusini yozing:",
        "📊 Biznes Reja": "Biznes g'oyangizni yozing:",
        "✍️ Hikoya": "Hikoya mavzusini yozing:"
    }
    text_type = message.text
    bot.send_message(message.chat.id, prompts[text_type])
    bot.register_next_step_handler(message, lambda m: generate_text(m, text_type))

def generate_text(message, text_type):
    if not check_limit(message.from_user.id):
        bot.send_message(message.chat.id, "⚠️ Limit tugadi! /premium")
        return
    type_prompts = {
        "📄 CV Yozish": f"Professional CV yoz: {message.text}",
        "📧 Xat Yozish": f"Rasmiy xat yoz: {message.text}",
        "📱 Post Yozish": f"Ijtimoiy tarmoq uchun post yoz: {message.text}",
        "📊 Biznes Reja": f"Biznes reja yoz: {message.text}",
        "✍️ Hikoya": f"Qiziqarli hikoya yoz: {message.text}"
    }
    bot.send_message(message.chat.id, "⏳ Yozilmoqda...")
    try:
        response = model.generate_content(type_prompts[text_type])
        bot.send_message(message.chat.id, response.text)
    except:
        bot.send_message(message.chat.id, "❌ Xatolik!")

# === KINO ===
@bot.message_handler(func=lambda m: m.text == "🎬 Kino")
def movie_menu(message):
    bot.send_message(message.chat.id, "🎬 Kino nomini yozing!")
    bot.register_next_step_handler(message, handle_movie)

def handle_movie(message):
    if not check_limit(message.from_user.id):
        bot.send_message(message.chat.id, "⚠️ Limit tugadi! /premium")
        return
    bot.send_message(message.chat.id, "🔍 Qidirilmoqda...")
    try:
        prompt = f"'{message.text}' kinosi haqida batafsil ma'lumot ber: yil, janr, rejissyor, aktyorlar, IMDB reyting, qisqacha syujet. O'zbek tilida yoz."
        response = model.generate_content(prompt)
        bot.send_message(message.chat.id, response.text)
    except:
        bot.send_message(message.chat.id, "❌ Xatolik!")

# === MUSIQA ===
@bot.message_handler(func=lambda m: m.text == "🎵 Musiqa")
def music_menu(message):
    bot.send_message(message.chat.id, "🎵 Qo'shiq nomini yozing!")
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
            bot.send_message(message.chat.id,
                f"🎵 {info['title']}\n\n🔗 {info['webpage_url']}")
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

@bot.message_handler(func=lambda m: m.text in ["🧩 Topishmoq", "❓ Viktorina", "🔢 Matematika"])
def handle_game(message):
    if not check_limit(message.from_user.id):
        bot.send_message(message.chat.id, "⚠️ Limit tugadi! /premium")
        return
    prompts = {
        "🧩 Topishmoq": "Qiziqarli o'zbek topishmoqi ber va javobini ham yoz.",
        "❓ Viktorina": "Qiziqarli viktorina savoli ber, 4 ta variant ko'rsat (A,B,C,D) va javobini ayt.",
        "🔢 Matematika": "Qiziqarli matematika masalasi ber va yechimini ko'rsat."
    }
    bot.send_message(message.chat.id, "⏳ Tayyorlanmoqda...")
    try:
        response = model.generate_content(prompts[message.text])
        bot.send_message(message.chat.id, response.text)
    except:
        bot.send_message(message.chat.id, "❌ Xatolik!")

# === OB-HAVO ===
@bot.message_handler(func=lambda m: m.text == "☀️ Ob-havo")
def weather_menu(message):
    bot.send_message(message.chat.id, "🌍 Shahar nomini yozing!")
    bot.register_next_step_handler(message, handle_weather)

def handle_weather(message):
    try:
        url = f"https://wttr.in/{message.text}?format=3"
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
        "✅ Video yuklab berish\n"
        "✅ Musiqa yuklab berish\n\n"
        "💰 Narx: <b>30,000 so'm/oy</b>\n\n"
        "💳 To'lov uchun karta:\n"
        "<code>5614 6812 2745 5718</code>\n"
        "👤 Abaraliyev Ismoiljon\n\n"
        "✅ To'lov qilgach screenshotni yuboring:\n"
        "@sening_yarming_robot",
        parse_mode='HTML')

# === HAQIDA ===
@bot.message_handler(func=lambda m: m.text == "ℹ️ Haqida")
def about(message):
    bot.send_message(message.chat.id,
        "🤖 <b>I'm your half Bot</b>\n\n"
        "⚡ Kanal: @tezkor_habar_robot\n\n"
        "🌟 Funksiyalar:\n"
        "• 🤖 AI savol-javob\n"
        "• 🌐 Tarjima\n"
        "• 📝 Matn yozish\n"
        "• 🎬 Kino ma'lumoti\n"
        "• 🎵 Musiqa topish\n"
        "• 📹 Video yuklab berish\n"
        "• 🎮 O'yinlar\n"
        "• ☀️ Ob-havo\n\n"
        "💎 Premium: 30,000 so'm/oy",
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
def run_bot():
    print("✅ Bot ishlamoqda...")
    bot.polling(none_stop=True)

threading.Thread(target=run_bot, daemon=True).start()
app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
