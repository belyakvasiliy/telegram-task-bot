# main.py — Telegram-бот для Platrum с автоопределением URL и владельца

import os
import logging
import datetime
import requests

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.executor import start_webhook

# Конфигурация
BOT_TOKEN = os.getenv("BOT_TOKEN")
PLATRUM_API_KEY = os.getenv("PLATRUM_API_KEY")
PLATRUM_URL = os.getenv("PLATRUM_URL", "https://yourdomain.platrum.ru")

WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", 'https://your-webhook-host.com')
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.environ.get("PORT", 3000))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

USER_MAP = {}

# Автообновление пользователей
def update_users():
    global USER_MAP
    headers = {"Api-key": PLATRUM_API_KEY, "Content-Type": "application/json"}
    response = requests.post(f"{PLATRUM_URL}/company/api/staff/list", headers=headers)
    if response.status_code == 200:
        data = response.json().get("data", [])
        USER_MAP.clear()
        for user in data:
            if not user.get("is_deleted"):
                USER_MAP[user['user_name']] = user['user_id']

# Определение владельца задачи (по Telegram ID или fallback)
def resolve_owner_id(telegram_user_id):
    update_users()
    # В будущем — связка telegram_user_id ↔ user_id
    # Пока просто первый ID из списка
    return next(iter(USER_MAP.values()), None)

@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    update_users()
    await message.reply("Привет! Я бот для управления задачами Platrum.\n\nКоманды:\n/task <описание> — создать задачу\n/info <ID> — информация\n/find <ключ> — поиск\n/close <ID> — завершить задачу\n/delete <ID> — удалить задачу\n/update <ID> — изменить задачу")

@dp.message_handler(commands=["task"])
async def task_handler(message: types.Message):
    args = message.get_args()
    if not args:
        await message.reply("Укажи описание задачи: /task Сделать отчёт")
        return
    update_users()
    keyboard = InlineKeyboardMarkup(row_width=1)
    for name in USER_MAP:
        keyboard.add(InlineKeyboardButton(name, callback_data=f"assign:{name}:{args}"))
    await message.reply("Кому назначить задачу?", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith("assign:"))
async def assign_task(callback_query: CallbackQuery):
    _, name, task_text = callback_query.data.split(":", 2)
    user_id = USER_MAP.get(name)
    owner_id = resolve_owner_id(callback_query.from_user.id)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    headers = {"Api-key": PLATRUM_API_KEY, "Content-Type": "application/json"}
    data = {
        "name": task_text,
        "description": f"Создано через Telegram от {name}",
        "owner_user_id": owner_id,
        "responsible_user_ids": [user_id],
        "status_key": "new",
        "tag_keys": ["бот", "Telegram"],
        "start_date": now,
        "block_id": 3,
        "category_key": "task"
    }
    response = requests.post(f"{PLATRUM_URL}/tasks/api/task/create", headers=headers, json=data)
    result = response.json()
    if response.status_code == 200 and result.get("status") == "success":
        task_id = result["data"].get("id")
        await callback_query.message.answer(f"✅ Задача создана: {task_text}\n🔗 {PLATRUM_URL}/tasks/task/{task_id}")
    else:
        await callback_query.message.answer(f"❌ Ошибка Platrum: {response.text}")
    await callback_query.answer()

# Остальные команды (info, find, delete, close, update) остаются как есть, просто используем переменные PLATRUM_URL и API_KEY

async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)
    update_users()

async def on_shutdown(dp):
    await bot.delete_webhook()

if __name__ == '__main__':
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
