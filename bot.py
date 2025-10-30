import os
import logging
import tempfile
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import yt_dlp
import ffmpeg

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN not found. Set it in Render Environment Variables.")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === /start ===
@dp.message(lambda message: message.text == "/start")
async def start(message: Message):
    await message.answer("🎧 Привет! Отправь ссылку на видео (YouTube, Instagram, TikTok и т.д.), я конвертирую его в MP3!")

# === Главная логика ===
@dp.message()
async def process(message: Message):
    url = message.text.strip()

    if not url.startswith("http"):
        await message.answer("❗ Пожалуйста, отправь ссылку на видео.")
        return

    await message.answer("⏳ Загружаю и конвертирую аудио...")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            mp3_path = os.path.join(tmpdir, "audio.mp3")

            # Выбор cookie-файла
            if "instagram" in url:
                cookie_file = "instagram_cookies.txt"
            elif "youtube" in url or "youtu.be" in url:
                cookie_file = "youtube_cookies.txt"
            else:
                cookie_file = None

            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": os.path.join(tmpdir, "temp.%(ext)s"),
                "quiet": True,
                "noplaylist": True,
            }

            if cookie_file and os.path.exists(cookie_file):
                ydl_opts["cookiefile"] = cookie_file
                logging.info(f"✅ Использую cookie-файл: {cookie_file}")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                input_path = ydl.prepare_filename(info)

            ffmpeg.input(input_path).output(mp3_path, codec="libmp3lame", qscale=2).run(quiet=True)
            await message.answer_audio(types.FSInputFile(mp3_path), caption="✅ Готово! Вот твой MP3 🎵")

    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await message.answer("⚠️ Ошибка при загрузке. Попробуй другую ссылку.")

# === Webhook ===
async def on_startup(app):
    webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_URL', 'videotomp3bot.onrender.com')}/webhook"
    await bot.set_webhook(webhook_url)
    logging.info(f"🔗 Установлен webhook: {webhook_url}")

async def on_shutdown(app):
    await bot.delete_webhook()

def main():
    app = web.Application()
    SimpleRequestHandler(dp, bot).register(app, path="/webhook")
    setup_application(app, dp)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    logging.info("✅ Webhook сервер запущен")
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

if __name__ == "__main__":
    main()
