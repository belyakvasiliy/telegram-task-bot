import logging
import os
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import aiohttp
from datetime import datetime

API_KEY = os.getenv("PLATRUM_API_KEY")
PROJECT_URL = os.getenv("PLATRUM_PROJECT_URL") or "https://steves.platrum.ru"
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Предопределённые пользователи
user_map = {
    "@SvetlanaCherednichok": "f2206949133b4b4936f163edebe6c8ec",
    "@Business_Automation_Expert": "3443a213affa5a96d35c10190f6708b5"
}

def create_task_payload(text, user_id):
    return {
        "name": text,
        "description": "Создано через Telegram-группу от Vasyl Beliak",
        "owner_user_id": user_id,
        "responsible_user_ids": [user_id],
        "status_key": "new",
        "tag_keys": ["бот", "Telegram"],
        "block_id": 3,
        "category_key": "task"
    }

@dp.message_handler(commands=["task"])
async def handle_task_command(message: types.Message):
    args = message.get_args()
    logging.info(f"Command args: {args}")

    if not args:
        await message.reply("⚠️ Формат: /task @username Описание задачи")
        return

    try:
        parts = args.split(" ", 1)
        mention = parts[0]
        task_text = parts[1] if len(parts) > 1 else ""

        if mention not in user_map:
            await message.reply("⚠️ Пользователь не найден. Используйте @SvetlanaCherednichok или @Business_Automation_Expert")
            return

        user_id = user_map[mention]
        payload = create_task_payload(task_text, user_id)

        url = f"{PROJECT_URL}/tasks/api/task/create"

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers={
                    "Content-Type": "application/json",
                    "Api-key": API_KEY
                },
                json=payload
            ) as resp:
                resp_data = await resp.json()

                if resp_data.get("status") == "success":
                    await message.reply(f"✅ Задача создана: {task_text}")
                else:
                    await message.reply(f"❌ Ошибка Platrum: {resp_data}\n📩 Данные: {payload}")
    except Exception as e:
        await message.reply(f"❌ Произошла ошибка: {str(e)}")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)
