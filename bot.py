import os
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from yt_dlp import YoutubeDL
import subprocess
import tempfile

# 🔹 Вставь сюда токен своего Telegram-бота
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Функция скачивания и конвертации видео ---
def download_video_as_mp3(url: str) -> str:
    """Скачивает видео по ссылке и конвертирует в MP3"""
    tmp_dir = tempfile.mkdtemp()
    video_path = os.path.join(tmp_dir, "video.mp4")
    mp3_path = os.path.join(tmp_dir, "audio.mp3")

    ydl_opts = {"outtmpl": video_path}
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    subprocess.run([
        "ffmpeg", "-i", video_path, "-vn", "-ab", "192k", "-ar", "44100", "-y", mp3_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return mp3_path


# --- Обработка сообщений с ссылками ---
@dp.message(F.text)
async def handle_link(message: Message):
    url = message.text.strip()
    if any(domain in url for domain in ["youtube", "instagram", "facebook", "tiktok"]):
        await message.reply("🎧 Загружаю и конвертирую... подожди немного.")
        try:
            mp3_path = download_video_as_mp3(url)
            await message.reply_audio(audio=open(mp3_path, "rb"))
        except Exception as e:
            await message.reply(f"❌ Ошибка: {e}")
    else:
        await message.reply("🔗 Отправь ссылку на видео (YouTube, Instagram, TikTok, Facebook).")


# --- Запуск бота ---
async def main():
    print("✅ Бот запущен. Ожидаю сообщения...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
