import telebot
import sqlite3
import os

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CHANNEL = os.getenv("CHANNEL", "@kanalingiz")

bot = telebot.TeleBot(TOKEN)

db = sqlite3.connect("movies.db", check_same_thread=False)
db.execute("""
CREATE TABLE IF NOT EXISTS movies (
    code TEXT PRIMARY KEY,
    file_id TEXT
)
""")
db.commit()

waiting = {}

def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

@bot.message_handler(commands=["start"])
def start(message):
    if not is_subscribed(message.from_user.id):
        bot.reply_to(
            message,
            f"Botdan foydalanish uchun kanalga obuna bo'ling:\n{CHANNEL}"
        )
        return

    bot.reply_to(message, "🎬 Kino kodini yuboring.")

@bot.message_handler(commands=["add"])
def add_movie(message):
    if message.from_user.id != ADMIN_ID:
        return

    waiting[message.from_user.id] = "video"
    bot.reply_to(message, "Kino videosini yuboring.")

@bot.message_handler(content_types=["video"])
def receive_video(message):
    if message.from_user.id != ADMIN_ID:
        return

    if waiting.get(ADMIN_ID) != "video":
        return

    waiting[ADMIN_ID] = {
        "step": "code",
        "file_id": message.video.file_id
    }

    bot.reply_to(message, "Endi kino kodini yuboring.")

@bot.message_handler(func=lambda m: True)
def receive_code(message):
    if message.from_user.id == ADMIN_ID:
        data = waiting.get(ADMIN_ID)

        if isinstance(data, dict) and data.get("step") == "code":
            code = message.text.strip()
            db.execute(
                "INSERT OR REPLACE INTO movies VALUES (?, ?)",
                (code, data["file_id"])
            )
            db.commit()
            waiting.pop(ADMIN_ID, None)
            bot.reply_to(message, "✅ Kino saqlandi!")
            return

    if not is_subscribed(message.from_user.id):
        bot.reply_to(message, "Avval kanalga obuna bo'ling!")
        return

    result = db.execute(
        "SELECT file_id FROM movies WHERE code=?",
        (message.text.strip(),)
    ).fetchone()

    if result:
        bot.send_video(message.chat.id, result[0])
    else:
        bot.reply_to(message, "❌ Bunday kino kodi topilmadi.")

print("Kino bot ishga tushdi!")
bot.infinity_polling(skip_pending=True)
