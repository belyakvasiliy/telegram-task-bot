import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils.executor import start_webhook
import os
import re
import datetime
import requests

API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
WEBHOOK_HOST = 'https://telegram-task-bot-4fly.onrender.com'
WEBHOOK_PATH = f'/webhook/{API_TOKEN}'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = int(os.getenv('PORT', 5000))

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Карта Telegram username -> Platrum user_id
TELEGRAM_TO_PLATRUM = {
    "@SvetlanaCherednichok": "f2206949133b4b4936f163edebe6c8ec",
    "@Business_Automation_Expert": "3443a213affa5a96d35c10190f6708b5"
}

PLATRUM_API_KEY = os.getenv("PLATRUM_API_KEY")
PLATRUM_HOST = "https://steves.platrum.ru"

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: Message):
    await message.reply("Привет! Используй команду /task @username Описание задачи")

@dp.message_handler(lambda message: message.text.startswith('/task'))
async def create_task(message: Message):
    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            await message.reply("⚠️ Формат: /task @username Описание задачи")
            return

        telegram_username = parts[1]
        task_name = parts[2]
        user_id = TELEGRAM_TO_PLATRUM.get(telegram_username)

        if not user_id:
            await message.reply("❌ Ошибка: пользователь не найден.")
            return

        task_data = {
            "name": task_name,
            "description": f"Создано через Telegram-группу от {message.from_user.full_name}",
            "owner_user_id": user_id,
            "responsible_user_ids": [user_id],
            "status_key": "new",
            "tag_keys": ["бот", "Telegram"],
            "block_id": 3,
            "category_key": "task"
        }

        url = f"{PLATRUM_HOST}/tasks/api/task/create"
        headers = {
            "Content-Type": "application/json",
            "Api-key": PLATRUM_API_KEY
        }

        response = requests.post(url, json=task_data, headers=headers)

        if response.status_code == 200 and response.json().get("status") == "success":
            await message.reply(f"✅ Задача создана: {task_name}")
        else:
            await message.reply(f"❌ Ошибка Platrum: {response.text}\n📩 Данные: {task_data}")

    except Exception as e:
        await message.reply(f"❌ Произошла ошибка: {e}")

async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(dp):
    logging.warning('Shutting down..')
    await bot.delete_webhook()
    logging.warning('Bye!')

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
