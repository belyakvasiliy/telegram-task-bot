# handlers/tasks.py — Логика Telegram-команд по задачам

from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.globals import dp, PLATRUM_API_KEY, PLATRUM_URL, USER_MAP, resolve_owner_id
from utils.api import platrum_post

@dp.message_handler(commands=["task"])
async def create_task_handler(message: types.Message):
    args = message.get_args()
    if not args or len(args.split()) < 2:
        await message.reply("Укажи задачу в формате: /task <Имя> <Описание>\nПример: /task Иван Сделать отчёт до 17:00")
        return

    name, *task_text_parts = args.split()
    task_text = " ".join(task_text_parts)
    user_id = USER_MAP.get(name.lower())

    if not user_id:
        await message.reply(f"❌ Неизвестный исполнитель: {name}. Проверь имя через /users")
        return

    now = message.date.strftime("%Y-%m-%d %H:%M:%S")
    data = {
        "name": task_text,
        "description": f"Создано через Telegram от {name}",
        "owner_user_id": user_id,
        "responsible_user_ids": [user_id],
        "status_key": "new",
        "tag_keys": ["бот", "Telegram"],
        "start_date": now,
        "block_id": 3,
        "category_key": "task"
    }

    result = platrum_post("/tasks/api/task/create", data)

    if result.get("status") == "success":
        task_id = result["data"].get("id")
        await message.reply(
            f"✅ Задача создана!\n🔗 https://{PLATRUM_URL.replace('https://', '')}/tasks/task/{task_id}"
        )
    else:
        await message.reply(f"❌ Ошибка при создании задачи: {result}")
