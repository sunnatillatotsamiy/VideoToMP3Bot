import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

# Логирование (чтобы видеть ошибки в Render)
logging.basicConfig(level=logging.INFO)

# Токен берём из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN not found. Set it in Render Environment Variables.")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === Обработчики сообщений ===
@dp.message()
async def handle_message(message: Message):
    await message.answer("🎧 Привет! Отправь мне ссылку на видео, и я конвертирую его в MP3.")

# === Webhook сервер ===
async def start_webhook():
    app = web.Application()
    webhook_path = "/webhook"

    # Настройка Webhook
    SimpleRequestHandler(dp, bot).register(app, path=webhook_path)
    setup_application(app, dp)

    logging.info("✅ Webhook сервер запущен на Render")

    return app


if __name__ == "__main__":
    # Запуск приложения (Render автоматически подставит PORT)
    web.run_app(start_webhook(), host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
