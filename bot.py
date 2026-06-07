import telebot
import edge_tts
import asyncio
import os
import tempfile
import yt_dlp
from dotenv import load_dotenv

# ===== Load .env =====
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN រកមិនឃើញ!")

bot = telebot.TeleBot(BOT_TOKEN)

# ===== Voices =====
VOICES = {
    "piseth": "km-KH-PisethNeural",
    "sreymom": "km-KH-SreymomNeural",
}

# ===== User state =====
user_voice = {}
user_mode = {}  # "tts" | "search" | "download"

# ===== Reply Keyboard (Main Menu) =====
def main_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        telebot.types.KeyboardButton("🔊 TTS បំប្លែងសម្លេង"),
        telebot.types.KeyboardButton("🎵 ស្វែងរកចម្រៀង"),
        telebot.types.KeyboardButton("📥 ដោនវីដេអូ/ចម្រៀង"),
        telebot.types.KeyboardButton("🎙️ ប្ដូរ Voice"),
        telebot.types.KeyboardButton("📖 ជំនួយ"),
    )
    return markup

# ===== Inline Keyboard voice select =====
def voice_inline():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("🎙️ Piseth (ប្រុស)", callback_data="voice_piseth"),
        telebot.types.InlineKeyboardButton("🎤 Sreymom (ស្រី)", callback_data="voice_sreymom"),
    )
    return markup

# ===== /start =====
@bot.message_handler(commands=["start"])
def start(message):
    user_voice[message.chat.id] = "piseth"
    user_mode[message.chat.id] = "tts"
    bot.send_message(
        message.chat.id,
        "👋 សូមស្វាគមន៍មក *Kairozen Bot*!\n\n"
        "🔊 TTS — បំប្លែងអក្សរជាសម្លេងខ្មែរ\n"
        "🎵 ស្វែងរក — រកចម្រៀងតាមចំណងជើង\n"
        "📥 ដោន — ដោនវីដេអូ/ចម្រៀងតាម link\n\n"
        "ជ្រើសរើសមុខងារពី Menu ខាងក្រោម 👇",
        parse_mode="Markdown",
        reply_markup=main_keyboard(),
    )

# ===== /help =====
@bot.message_handler(commands=["help"])
def help_cmd(message):
    bot.send_message(
        message.chat.id,
        "📖 *របៀបប្រើ Kairozen Bot*\n\n"
        "🔊 *TTS បំប្លែងសម្លេង*\n"
        "   ចុច TTS → ផ្ញើអក្សរ → Bot reply សម្លេង\n\n"
        "🎵 *ស្វែងរកចម្រៀង*\n"
        "   ចុច ស្វែងរក → វាយចំណងជើង → ជ្រើសចម្រៀង\n\n"
        "📥 *ដោនវីដេអូ/ចម្រៀង*\n"
        "   ចុច ដោន → paste link YouTube/TikTok/Facebook\n"
        "   Bot នឹងផ្ញើ MP3 ឬ MP4\n\n"
        "🎙️ *Voices ខ្មែរ*\n"
        "   • Piseth → km-KH-PisethNeural (ប្រុស)\n"
        "   • Sreymom → km-KH-SreymomNeural (ស្រី)",
        parse_mode="Markdown",
        reply_markup=main_keyboard(),
    )

# ===== TTS Function =====
async def generate_tts(text, voice, output_path):
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(output_path)

# ===== Search YouTube =====
def search_youtube(query, max_results=5):
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "default_search": "ytsearch5",
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
        entries = result.get("entries", [])
        return [
            {
                "title": e.get("title", "Unknown"),
                "url": f"https://youtube.com/watch?v={e.get('id')}",
                "duration": e.get("duration", 0),
                "id": e.get("id"),
            }
            for e in entries if e
        ]

# ===== Format duration =====
def fmt_duration(seconds):
    if not seconds:
        return "?"
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"

# ===== Download audio (MP3) =====
def download_audio(url, output_path):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return info.get("title", "Audio")

# ===== Download video (MP4) =====
def download_video(url, output_path):
    ydl_opts = {
        "format": "best[filesize<50M]/best[height<=720]",
        "outtmpl": output_path,
        "quiet": True,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return info.get("title", "Video")

# ===== Handle Reply Keyboard buttons =====
@bot.message_handler(func=lambda m: m.text in [
    "🔊 TTS បំប្លែងសម្លេង",
    "🎵 ស្វែងរកចម្រៀង",
    "📥 ដោនវីដេអូ/ចម្រៀង",
    "🎙️ ប្ដូរ Voice",
    "📖 ជំនួយ",
])
def handle_menu(message):
    chat_id = message.chat.id
    text = message.text

    if text == "🔊 TTS បំប្លែងសម្លេង":
        user_mode[chat_id] = "tts"
        v = user_voice.get(chat_id, "piseth").capitalize()
        bot.send_message(chat_id,
            f"🔊 *Mode: TTS*\nVoice: *{v}*\n\nផ្ញើអក្សរដែលចង់បំប្លែងជាសម្លេង 👇",
            parse_mode="Markdown", reply_markup=main_keyboard())

    elif text == "🎵 ស្វែងរកចម្រៀង":
        user_mode[chat_id] = "search"
        bot.send_message(chat_id,
            "🎵 *ស្វែងរកចម្រៀង*\n\nវាយចំណងជើងចម្រៀង ឬឈ្មោះសិល្បករ 👇",
            parse_mode="Markdown", reply_markup=main_keyboard())

    elif text == "📥 ដោនវីដេអូ/ចម្រៀង":
        user_mode[chat_id] = "download"
        bot.send_message(chat_id,
            "📥 *ដោនវីដេអូ/ចម្រៀង*\n\n"
            "Paste link YouTube, TikTok, Facebook...\n\n"
            "Bot នឹងផ្ញើ:\n"
            "• 🎵 MP3 (ចម្រៀង)\n"
            "• 🎬 MP4 (វីដេអូ)",
            parse_mode="Markdown", reply_markup=main_keyboard())

    elif text == "🎙️ ប្ដូរ Voice":
        current = user_voice.get(chat_id, "piseth").capitalize()
        bot.send_message(chat_id,
            f"🎙️ Voice បច្ចុប្បន្ន: *{current}*\nជ្រើស Voice ថ្មី:",
            parse_mode="Markdown",
            reply_markup=voice_inline())

    elif text == "📖 ជំនួយ":
        help_cmd(message)

# ===== Callback: voice select =====
@bot.callback_query_handler(func=lambda c: c.data.startswith("voice_"))
def cb_voice(call):
    selected = call.data.replace("voice_", "")
    user_voice[call.message.chat.id] = selected
    name = "Piseth (ប្រុស)" if selected == "piseth" else "Sreymom (ស្រី)"
    bot.answer_callback_query(call.id, f"✅ ប្រើ {name}")
    bot.edit_message_text(
        f"✅ បានប្ដូរ Voice ជា *{name}*",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
    )

# ===== Callback: download from search result =====
@bot.callback_query_handler(func=lambda c: c.data.startswith("dl_audio_") or c.data.startswith("dl_video_"))
def cb_download(call):
    chat_id = call.message.chat.id
    parts = call.data.split("_", 3)
    fmt = parts[1]  # "audio" or "video"
    url = parts[3] if len(parts) > 3 else None

    if not url:
        bot.answer_callback_query(call.id, "❌ Link មិនត្រឹមត្រូវ")
        return

    bot.answer_callback_query(call.id, "⏳ កំពុងដោន...")
    loading = bot.send_message(chat_id, "⏳ កំពុងដោន សូមរង់ចាំ...")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "output")

            if fmt == "audio":
                title = download_audio(url, out)
                mp3 = out + ".mp3"
                if os.path.exists(mp3):
                    with open(mp3, "rb") as f:
                        bot.send_audio(chat_id, f, title=title, caption=f"🎵 *{title}*", parse_mode="Markdown")
                else:
                    bot.send_message(chat_id, "❌ ដោន MP3 បរាជ័យ")
            else:
                # video
                title = download_video(url, out + ".mp4")
                mp4 = out + ".mp4"
                if os.path.exists(mp4):
                    size = os.path.getsize(mp4)
                    if size > 50 * 1024 * 1024:
                        bot.send_message(chat_id, "❌ វីដេអូធំពេក (>50MB) សូមដោន MP3 ជំនួស")
                    else:
                        with open(mp4, "rb") as f:
                            bot.send_video(chat_id, f, caption=f"🎬 *{title}*", parse_mode="Markdown")
                else:
                    bot.send_message(chat_id, "❌ ដោន MP4 បរាជ័យ")

        bot.delete_message(chat_id, loading.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ មានបញ្ហា: {str(e)[:200]}", chat_id, loading.message_id)

# ===== Handle all text messages =====
@bot.message_handler(func=lambda m: m.content_type == "text")
def handle_text(message):
    chat_id = message.chat.id
    text = message.text.strip()
    mode = user_mode.get(chat_id, "tts")

    # ===== MODE: TTS =====
    if mode == "tts":
        voice_key = user_voice.get(chat_id, "piseth")
        voice_name = VOICES[voice_key]
        loading = bot.send_message(chat_id, "⏳ កំពុងបំប្លែងសម្លេង...")
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = tmp.name
            asyncio.run(generate_tts(text, voice_name, tmp_path))
            with open(tmp_path, "rb") as audio:
                bot.send_voice(
                    chat_id, audio,
                    caption=f"🎙️ *{voice_key.capitalize()}* | {len(text)} អក្សរ",
                    parse_mode="Markdown",
                    reply_to_message_id=message.message_id,
                )
            bot.delete_message(chat_id, loading.message_id)
        except Exception as e:
            bot.edit_message_text(f"❌ មានបញ្ហា: {str(e)[:200]}", chat_id, loading.message_id)
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

    # ===== MODE: SEARCH =====
    elif mode == "search":
        loading = bot.send_message(chat_id, f"🔍 កំពុងស្វែងរក: *{text}*...", parse_mode="Markdown")
        try:
            results = search_youtube(text, max_results=5)
            if not results:
                bot.edit_message_text("❌ រកមិនឃើញ សូមសាកល្បងឡើងវិញ", chat_id, loading.message_id)
                return

            bot.delete_message(chat_id, loading.message_id)
            bot.send_message(chat_id, f"🎵 *លទ្ធផលស្វែងរក: {text}*\nជ្រើសចម្រៀង:", parse_mode="Markdown")

            for i, r in enumerate(results, 1):
                dur = fmt_duration(r["duration"])
                markup = telebot.types.InlineKeyboardMarkup()
                markup.row(
                    telebot.types.InlineKeyboardButton(
                        "🎵 ដោន MP3", callback_data=f"dl_audio_x_{r['url']}"),
                    telebot.types.InlineKeyboardButton(
                        "🎬 ដោន MP4", callback_data=f"dl_video_x_{r['url']}"),
                )
                markup.row(
                    telebot.types.InlineKeyboardButton(
                        "🔗 បើក YouTube", url=r["url"]),
                )
                bot.send_message(
                    chat_id,
                    f"{i}. *{r['title']}*\n⏱️ {dur}",
                    parse_mode="Markdown",
                    reply_markup=markup,
                )

        except Exception as e:
            bot.edit_message_text(f"❌ មានបញ្ហា: {str(e)[:200]}", chat_id, loading.message_id)

    # ===== MODE: DOWNLOAD =====
    elif mode == "download":
        url = text.strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            bot.send_message(chat_id, "❌ សូម paste link ត្រឹមត្រូវ (http://... ឬ https://...)")
            return

        markup = telebot.types.InlineKeyboardMarkup()
        markup.row(
            telebot.types.InlineKeyboardButton("🎵 ដោន MP3", callback_data=f"dl_audio_x_{url}"),
            telebot.types.InlineKeyboardButton("🎬 ដោន MP4", callback_data=f"dl_video_x_{url}"),
        )
        bot.send_message(
            chat_id,
            "📥 ជ្រើសទម្រង់ដែលចង់ដោន:",
            reply_markup=markup,
        )

# ===== Run =====
if __name__ == "__main__":
    print("🤖 Kairozen Bot កំពុងដំណើរការ...")
    bot.infinity_polling(skip_pending=True)
