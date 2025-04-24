# handlers/users.py — команды Telegram для работы с сотрудниками

from aiogram import types
from utils.globals import dp
from utils.users import get_all_users

@dp.message_handler(commands=["users"])
async def list_users(message: types.Message):
    users = get_all_users()
    if not users:
        await message.reply("Список сотрудников пуст или недоступен.")
        return

    text = "👥 *Сотрудники:*\n"
    for user in users:
        if not user.get("is_deleted"):
            text += f"\n- {user['user_name']} (ID: {user['user_id']})"

    await message.reply(text, parse_mode="Markdown")
