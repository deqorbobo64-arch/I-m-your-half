import telebot
import requests
import os
from datetime import datetime
import threading
from flask import Flask
import yt_dlp

BOT_TOKEN = "8679558924:AAErITY0HEWdvYWGqGKdufSX6cfKm9bRVE0"
OPENROUTER_API_KEY = "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"
CHANNEL_ID = "@tezkor_habar_robot"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

users = {}
premium_users = set()

def ask_ai(prompt):
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "mistralai/mistral-7b-instruct:free",
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    return response.json()['choices'][0]['message']['content']

@app.route('/')
def home():
    return 'Bot ishlayapti!'

def check_subscription(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

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

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id not in users:
        users[user_id] = {'count': 0, 'date': str(datetime.now().date())}
    if not check_subscription(user_id):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(
            "📢 Kanalga a'zo bo'lish",
            url="https://t.me/tezkor_habar_robot"))
        markup.add(telebot.types.InlineKeyboardButton(
            "✅ Tekshirish",
            callback_data="check_sub"))
        bot.send_message(message.chat.id,
            "⚡ Avval kanalga a'zo bo'ling!",
            reply_markup=markup)
        return
    bot.send_message(message.chat.id,
        "👋 Salom! Men <b>I'm your half</b> botman!\n\n"
        "Men quyidagilarni qila olaman:\n\n"
        "💬 Har qanday savolingizga javob beraman\n"
        "🌐 Tarjima qilaman (o'zbek, rus, ingliz)\n"
        "📝 CV, xat, post, hikoya yozaman\n"
        "🎬 Kino haqida ma'lumot beraman\n"
        "🎵 Musiqa topib beraman\n"
        "📹 YouTube/Instagram video yuklab beraman\n"
        "☀️ Ob-havo aytaman\n"
        "🧩 Topishmoq, viktorina o'ynayman\n\n"
        "🆓 Bepul: Kuniga 10 ta savol\n"
        "💎 Premium: 30,000 so'm/oy — cheksiz\n\n"
        "Shunchaki yozing, javob beraman! 😊",
        parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub_callback(call):
    if check_subscription(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Rahmat!")
        msg = call.message
        msg.from_user = call.from_user
        start(msg)
    else:
        bot.answer_callback_query(call.id, "❌ Hali a'zo bo'lmadingiz!")

def is_youtube_or_instagram(text):
    return any(x in text for x in ['youtube.com', 'youtu.be', 'instagram.com', 'tiktok.com'])

@bot.message_handler(func=lambda message: True)
def handle_all(message):
    user_id = message.from_user.id

    if not check_subscription(user_id):
        start(message)
        return

    if not check_limit(user_id):
        bot.send_message(message.chat.id,
            "⚠️ Kunlik limit tugadi!\n\n"
            "💎 Premium olish uchun:\n"
            "Karta: <code>5614 6812 2745 5718</code>\n"
            "👤 Abaraliyev Ismoiljon\n"
            "Narx: 30,000 so'm/oy\n\n"
            "To'lov qilgach @sening_yarming_robot ga yuboring!",
            parse_mode='HTML')
        return

    text = message.text

    # Video yuklab berish
    if is_youtube_or_instagram(text):
        try:
            ydl_opts = {
                'format': 'best[filesize<50M]',
                'quiet': True,
                'outtmpl': '/tmp/%(title)s.%(ext)s'
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(text, download=True)
                filename = ydl.prepare_filename(info)
            with open(filename, 'rb') as f:
                bot.send_video(message.chat.id, f)
            os.remove(filename)
        except:
            bot.send_message(message.chat.id, "❌ Video yuklab bo'lmadi!")
        return

    # Musiqa qidirish
    if any(x in text.lower() for x in ['qo\'shiq', 'musiqa', 'song', 'music', 'топ ', 'найди песню']):
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'noplaylist': True,
                'quiet': True,
                'default_search': 'ytsearch1'
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(text, download=False)
                if 'entries' in info:
                    info = info['entries'][0]
                bot.send_message(message.chat.id,
                    f"🎵 {info['title']}\n\n🔗 {info['webpage_url']}")
        except:
            bot.send_message(message.chat.id, "❌ Topilmadi!")
        return

    # Ob-havo
    if any(x in text.lower() for x in ['ob-havo', 'havo', 'погода', 'weather']):
        city = text.replace('ob-havo', '').replace('havo', '').replace('погода', '').replace('weather', '').strip()
        if not city:
            city = 'Tashkent'
        try:
            response = requests.get(f"https://wttr.in/{city}?format=3")
            bot.send_message(message.chat.id, f"☀️ {response.text}")
        except:
            bot.send_message(message.chat.id, "❌ Xatolik!")
        return

    # AI javob
    try:
        response = ask_ai(text)
        bot.send_message(message.chat.id, response)
    except:
        bot.send_message(message.chat.id, "❌ Xatolik!")

def run_bot():
    print("✅ Bot ishlamoqda...")
    bot.infinity_polling()

run_bot()
