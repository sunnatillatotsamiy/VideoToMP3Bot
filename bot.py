import os
import logging
import tempfile
import asyncio
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

# === Команда /start ===
@dp.message(lambda message: message.text == "/start")
async def cmd_start(message: Message):
    await message.answer(
        "🎧 Привет! Отправь мне ссылку на видео (YouTube, Instagram, Facebook и т.д.), и я конвертирую его в MP3."
    )

# === Основная логика скачивания и конвертации ===
@dp.message()
async def convert_to_mp3(message: Message):
    url = message.text.strip()

    if not url.startswith("http"):
        await message.answer("❗ Отправь, пожалуйста, корректную ссылку на видео.")
        return

    await message.answer("⏳ Загружаю и конвертирую аудио, подожди немного...")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            mp3_path = os.path.join(tmpdir, "audio.mp3")

            # Определяем cookie-файл по типу сайта
            if "instagram.com" in url:
                cookie_file = "instagram_cookies.txt"
            elif "youtube.com" in url or "youtu.be" in url:
                cookie_file = "youtube_cookies.txt"
            else:
                cookie_file = None

            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": os.path.join(tmpdir, "temp.%(ext)s"),
                "quiet": True,
                "noplaylist": True,
            }

            # Добавляем cookies, если есть
            if cookie_file and os.path.exists(cookie_file):
                ydl_opts["cookiefile"] = cookie_file
                logging.info(f"✅ Использую cookie-файл: {cookie_file}")
            else:
                logging.warning(f"⚠️ Cookie-файл не найден для {url}")

            # Скачиваем аудио
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                input_path = ydl.prepare_filename(info)

            # Конвертируем в MP3
            ffmpeg.input(input_path).output(mp3_path, codec="libmp3lame", qscale=2).run(quiet=True)

            # Отправляем MP3 пользователю
            await message.answer_audio(types.FSInputFile(mp3_path), caption="✅ Готово! Вот твой MP3 🎵")

    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await message.answer("⚠️ Произошла ошибка при загрузке или конвертации. Попробуй другую ссылку.")

# === Запуск Webhook ===
async def start_webhook():
    app = web.Application()
    webhook_path = "/webhook"
    SimpleRequestHandler(dp, bot).register(app, path=webhook_path)
    setup_application(app, dp)
    logging.info("✅ Webhook сервер запущен на Render")
    return app

if __name__ == "__main__":
    web.run_app(start_webhook(), host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
