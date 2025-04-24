# boards.py — управление досками и панелями задач Platrum

from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from main import dp
from api import platrum_post

@dp.message_handler(commands=["boards"])
async def list_boards(message: types.Message):
    result = platrum_post("/tasks/api/board/list")
    boards = result.get("data", [])
    if not boards:
        await message.reply("Доски не найдены.")
        return

    text = "📋 *Список досок:*
"
    for board in boards:
        text += f"\n📌 *{board['name']}* (ID: {board['id']})\nПанелей: {len(board['panels'])}"
    await message.reply(text, parse_mode="Markdown")

@dp.message_handler(commands=["panels"])
async def list_panels(message: types.Message):
    try:
        board_id = int(message.get_args())
    except:
        await message.reply("Укажи ID доски: /panels <board_id>")
        return

    result = platrum_post("/api/board/panel/list", {"board_id": board_id})
    panels = result.get("data", [])
    if not panels:
        await message.reply("Панели не найдены.")
        return

    text = f"📊 *Панели доски {board_id}:*\n"
    for panel in panels:
        text += f"\n➡️ *{panel['name']}* (ID: {panel['id']})"
    await message.reply(text, parse_mode="Markdown")

@dp.message_handler(commands=["create_panel"])
async def create_panel(message: types.Message):
    try:
        board_id, name = message.get_args().split(" ", 1)
        data = {
            "board_id": int(board_id),
            "name": name,
            "color": "blue",
            "task_fields": [],
            "order": 1,
            "is_archived": False
        }
        result = platrum_post("/api/board/panel/store", data)
        if result.get("status") == "success":
            await message.reply("✅ Панель создана успешно.")
        else:
            await message.reply("❌ Ошибка создания панели.")
    except Exception as e:
        await message.reply(f"⚠️ Ошибка: {e}")

@dp.message_handler(commands=["delete_panel"])
async def delete_panel(message: types.Message):
    try:
        panel_id = int(message.get_args())
        result = platrum_post("/api/board/panel/delete", {"panel_id": panel_id})
        if result.get("status") == "success":
            await message.reply("🗑 Панель удалена.")
        else:
            await message.reply("❌ Ошибка удаления панели.")
    except Exception as e:
        await message.reply(f"⚠️ Ошибка: {e}")
