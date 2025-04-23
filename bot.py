from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import os
import requests
import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
PLATRUM_API_KEY = os.getenv("PLATRUM_API_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    await message.reply("Бот активен. Пиши /task <исполнитель> <текст задачи> до <время>.")

@dp.message_handler(commands=["task"])
async def task_handler(message: types.Message):
    args = message.get_args()
    if not args:
        await message.reply("Пожалуйста, укажи задачу: /task Иван проверить отчёт до 16:00")
        return

    try:
        parts = args.split(" до ")
        task_info = parts[0].split(" ", 1)
        assignee = task_info[0]
        task_text = task_info[1] if len(task_info) > 1 else "Без описания"
        due_time = parts[1] if len(parts) > 1 else None

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
            "assigned_to": assignee,
            "due_date": due_date_iso
        }

        response = requests.post("https://api.platrum.ru/v1/tasks", json=data, headers=headers)

        if response.status_code == 201:
            await message.reply(f"✅ Задача создана для {assignee}: {task_text}")
        else:
            await message.reply(f"❌ Ошибка Platrum: {response.text}")

    except Exception as e:
        await message.reply(f"⚠️ Ошибка: {e}")

if __name__ == "__main__":
    executor.start_polling(dp)
