import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils.executor import start_webhook
import requests
import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
PLATRUM_API_KEY = os.getenv("PLATRUM_API_KEY")

# Webhook settings
WEBHOOK_HOST = 'https://telegram-task-bot-4fly.onrender.com'
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Webserver settings
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.environ.get("PORT", 3000))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

logging.basicConfig(level=logging.INFO)

# 📧 Сопоставление имён с email'ами
USER_MAP = {
    "Иван": "belyak.vasiliy@gmail.com"
    # Добавляй сюда других: "Яна": "yana@company.com", ...
}

@dp.message_handler(commands=["start"])
async def start_handler(message: Message):
    await message.reply("Бот активен. Пиши /task Иван сделать отчёт до 16:00")

@dp.message_handler(commands=["task"])
async def task_handler(message: Message):
    args = message.get_args()
    if not args:
        await message.reply("Пожалуйста, укажи задачу: /task Иван сделать отчёт до 16:00")
        return

    try:
        parts = args.split(" до ")
        task_info = parts[0].split(" ", 1)
        assignee = task_info[0]
        task_text = task_info[1] if len(task_info) > 1 else "Без описания"
        due_time = parts[1] if len(parts) > 1 else None

        # Подстановка email, если имя найдено
        assigned_email = USER_MAP.get(assignee, assignee)

        # Дата дедлайна
        due_date_iso = None
        if due_time:
            now = datetime.datetime.now()
            hour, minute = map(int, due_time.split(":"))
            due_date = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            due_date_iso = due_date.isoformat()

        headers = {
            "Authorization": f"Bearer {PLATRUM_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "title": task_text,
            "assigned_to": assigned_email,
            "due_date": due_date_iso,
            "status": "Новая"  # ✅ Статус по-русски
        }

        response = requests.post("https://api.platrum.ru/v1/tasks", json=data, headers=headers)

        if response.status_code == 201:
            await message.reply(f"✅ Задача создана для {assignee}: {task_text}")
        else:
            await message.reply(f"❌ Ошибка Platrum: {response.text}")

    except Exception as e:
        await message.reply(f"⚠️ Ошибка: {e}")

async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)
    print("📡 Webhook установлен")

async def on_shutdown(dp):
    logging.warning('Shutting down..')
    await bot.delete_webhook()
    logging.warning('Webhook удалён')

if __name__ == '__main__':
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
