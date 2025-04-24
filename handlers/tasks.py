# tasks.py — Хендлеры и логика для управления задачами в Platrum

import datetime
import requests
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from main import dp, PLATRUM_API_KEY, PLATRUM_URL, USER_MAP, resolve_owner_id

headers = {"Api-key": PLATRUM_API_KEY, "Content-Type": "application/json"}

@dp.message_handler(commands=["info"])
async def get_task_info(message: types.Message):
    task_id = message.get_args()
    response = requests.post(f"{PLATRUM_URL}/tasks/api/task/get", headers=headers, json={"id": int(task_id)})
    data = response.json().get("data")
    if not data:
        await message.reply("Задача не найдена.")
        return
    await message.reply(f"📌 *{data['name']}*\n📝 {data['description']}\n📅 {data['start_date']} → {data['finish_date']}\n👤 {data['owner_user_id']}\n👥 {', '.join(data['responsible_user_ids'])}", parse_mode="Markdown")

@dp.message_handler(commands=["find"])
async def find_tasks(message: types.Message):
    query = message.get_args()
    response = requests.post(f"{PLATRUM_URL}/tasks/api/task/list", headers=headers, json={"search": query})
    tasks = response.json().get("data", [])
    if not tasks:
        await message.reply("Задачи не найдены.")
        return
    reply = ""
    for task in tasks[:5]:
        reply += f"🔹 *{task['name']}* (ID: {task['id']})\nСтатус: {task['status_key']}\n[Открыть]({PLATRUM_URL}/tasks/task/{task['id']})\n\n"
    await message.reply(reply, parse_mode="Markdown")

@dp.message_handler(commands=["delete"])
async def delete_task(message: types.Message):
    task_id = int(message.get_args())
    response = requests.post(f"{PLATRUM_URL}/tasks/api/task/remove", headers=headers, json={"id": task_id})
    result = response.json()
    if result.get("status") == "success":
        await message.reply("🗑 Задача удалена.")
    else:
        await message.reply(f"⚠️ Ошибка: {response.text}")

@dp.message_handler(commands=["close"])
async def close_task(message: types.Message):
    task_id = int(message.get_args())
    fields = [{"key": "status_key", "value": "done"}]
    response = requests.post(f"{PLATRUM_URL}/tasks/api/task/update", headers=headers, json={"id": task_id, "fields": fields})
    if response.status_code == 200:
        await message.reply("✅ Задача завершена.")
    else:
        await message.reply(f"❌ Ошибка закрытия: {response.text}")

@dp.message_handler(commands=["update"])
async def update_task(message: types.Message):
    task_id = int(message.get_args())
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("Статус: done", callback_data=f"update:{task_id}:done"),
        InlineKeyboardButton("Статус: in_progress", callback_data=f"update:{task_id}:in_progress")
    )
    await message.reply("Выбери новый статус задачи:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith("update:"))
async def update_task_status(callback_query: CallbackQuery):
    _, task_id, status = callback_query.data.split(":")
    fields = [{"key": "status_key", "value": status}]
    response = requests.post(f"{PLATRUM_URL}/tasks/api/task/update", headers=headers, json={"id": int(task_id), "fields": fields})
    if response.status_code == 200:
        await callback_query.message.answer(f"🔁 Статус задачи обновлён на: {status}")
    else:
        await callback_query.message.answer(f"❌ Ошибка обновления: {response.text}")
    await callback_query.answer()
