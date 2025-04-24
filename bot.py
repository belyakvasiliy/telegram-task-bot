import logging
import re
import requests
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
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

user_task_draft = {}  # temporary storage for messages before user selection

@dp.message_handler(commands=["task"])
async def handle_task_command(message: types.Message):
    task_text = message.text.replace(f"/task@{BOT_USERNAME}", "/task").replace("/task", "").strip()

    if not task_text:
        await message.reply("✏️ Введите описание задачи после /task")
        return

    user_task_draft[message.from_user.id] = task_text

    keyboard = InlineKeyboardMarkup(row_width=1)
    for username in USERNAME_TO_PLATRUM_ID:
        keyboard.add(InlineKeyboardButton(f"@{username}", callback_data=f"assign:{username}"))

    await message.reply("Кому назначить задачу?", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("assign:"))
async def process_assignment(callback_query: types.CallbackQuery):
    username = callback_query.data.split(":")[1]
    platrum_id = USERNAME_TO_PLATRUM_ID.get(username)
    task_name = user_task_draft.pop(callback_query.from_user.id, None)

    if not platrum_id or not task_name:
        await bot.answer_callback_query(callback_query.id, "Ошибка назначения.")
        return

    data = {
        "name": task_name,
        "description": f"Создано через Telegram-группу от {callback_query.from_user.full_name}",
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
        await bot.send_message(callback_query.from_user.id, f"✅ Задача создана: {task_name}\n🔗 {task_url}")
    else:
        await bot.send_message(callback_query.from_user.id, f"❌ Ошибка Platrum: {result}\n📤 Данные: {data}")

    await bot.answer_callback_query(callback_query.id)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
