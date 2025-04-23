import logging
import re
import requests
from aiogram import Bot, Dispatcher, executor, types
from datetime import datetime
import os

API_TOKEN = os.getenv("BOT_TOKEN")
PLATRUM_API_KEY = os.getenv("PLATRUM_API_KEY")
PLATRUM_HOST = "steves.platrum.ru"
BOT_USERNAME = "platrum123_bot"

# Telegram username to Platrum user ID mapping
USERNAME_TO_PLATRUM_ID = {
    "SvetlanaCherednichok": "f2206949133b4b4936f163edebe6c8ec",
    "Business_Automation_Expert": "3443a213affa5a96d35c10190f6708b5"
}

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=["task"])
async def handle_task_command(message: types.Message):
    text = message.text.replace(f"/task@{BOT_USERNAME}", "/task").replace("/task", "").strip()

    # Match format like: "@username Task description"
    match = re.match(r"@?(\w+)\s+(.*)", text)
    if not match:
        await message.reply("⚠️ Формат: /task @username Описание задачи")
        return

    username, task_name = match.groups()
    platrum_id = USERNAME_TO_PLATRUM_ID.get(username)

    if not platrum_id:
        await message.reply(f"❌ Неизвестный пользователь @{username}. Добавьте его в список.")
        return

    data = {
        "name": task_name,
        "description": f"Создано через Telegram-группу от {message.from_user.full_name}",
        "owner_user_id": platrum_id,
        "responsible_user_ids": [platrum_id],
        "status_key": "new",
        "tag_keys": ["бот", "Telegram"],
        "block_id": 3,
        "category_key": "task"
    }

    headers = {
        "Api-key": PLATRUM_API_KEY,
        "Content-Type": "application/json"
    }

    url = f"https://{PLATRUM_HOST}/tasks/api/task/create"
    response = requests.post(url, json=data, headers=headers)
    result = response.json()

    if result.get("status") == "success" and "data" in result:
        task_id = result["data"].get("id")
        task_url = f"https://{PLATRUM_HOST}/tasks/{task_id}"
        await message.reply(f"✅ Задача создана: {task_name}\n🔗 {task_url}")
    else:
        await message.reply(f"❌ Ошибка Platrum: {result}\n📤 Данные: {data}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
