import os
import logging
import datetime
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import start_webhook
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

BOT_TOKEN = os.getenv("BOT_TOKEN")
PLATRUM_API_KEY = os.getenv("PLATRUM_API_KEY")

WEBHOOK_HOST = 'https://telegram-task-bot-4fly.onrender.com'
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.environ.get("PORT", 3000))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

USER_MAP = {
    "Yuliya Kovalenko": "4a4031d6f951ca3ecd8a7468ac50a57c",
    "Vasyl Beliak": "3443a213affa5a96d35c10190f6708b5",
    "Elena Palianychko": "b30f2128f4722ae26eb1c93abf24d243"
}
OWNER_ID = "3443a213affa5a96d35c10190f6708b5"
PLATRUM_URL = "https://tothenextlevel.platrum.ru"

@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    await message.reply("Привет! Я бот для создания и управления задачами в Platrum.\n\n"
                        "📝 Команды:\n"
                        "/task <описание> — создать задачу\n"
                        "/info <ID> — узнать всё о задаче\n"
                        "/find <текст> — найти задачи")

@dp.message_handler(commands=["task"])
async def task_handler(message: types.Message):
    args = message.get_args()
    if not args:
        await message.reply("Укажи описание задачи: /task Сделать отчёт")
        return
    keyboard = InlineKeyboardMarkup(row_width=1)
    for name in USER_MAP.keys():
        keyboard.add(InlineKeyboardButton(name, callback_data=f"assign:{name}:{args}"))
    await message.reply("Кому назначить задачу?", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith("assign:"))
async def assign_task(callback_query: CallbackQuery):
    _, name, task_text = callback_query.data.split(":", 2)
    user_id = USER_MAP.get(name)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    headers = {
        "Api-key": PLATRUM_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "name": task_text,
        "description": f"Создано через Telegram от {name}",
        "owner_user_id": OWNER_ID,
        "responsible_user_ids": [user_id],
        "status_key": "new",
        "tag_keys": ["бот", "Telegram"],
        "start_date": now,
        "block_id": 3,
        "category_key": "task"
    }

    url = f"{PLATRUM_URL}/tasks/api/task/create"
    response = requests.post(url, headers=headers, json=data)
    result = response.json()

    if response.status_code == 200 and result.get("status") == "success":
        task_id = result["data"].get("id")
        link = f"{PLATRUM_URL}/tasks/task/{task_id}"
        await callback_query.message.answer(f"✅ Задача создана: {task_text}\n🔗 {link}")
    else:
        await callback_query.message.answer(f"❌ Ошибка Platrum: {response.text}")

    await callback_query.answer()

@dp.message_handler(commands=["info"])
async def get_task_info(message: types.Message):
    try:
        task_id = int(message.get_args())
        headers = {
            "Api-key": PLATRUM_API_KEY,
            "Content-Type": "application/json"
        }
        response = requests.post(f"{PLATRUM_URL}/tasks/api/task/get", headers=headers, json={"id": task_id})
        data = response.json().get("data")

        if not data:
            await message.reply("Задача не найдена.")
            return

        info = (
            f"📌 *{data.get('name')}*\n"
            f"📝 {data.get('description')}\n"
            f"📅 Старт: {data.get('start_date')}\n"
            f"📌 Статус: {data.get('status_key')}\n"
            f"👤 Постановщик: {data.get('owner_user_id')}\n"
            f"👥 Исполнители: {', '.join(data.get('responsible_user_ids', []))}\n"
            f"🔗 [Открыть задачу]({PLATRUM_URL}/tasks/task/{task_id})"
        )
        await message.reply(info, parse_mode="Markdown")
    except Exception as e:
        await message.reply(f"⚠️ Ошибка: {e}")

@dp.message_handler(commands=["find"])
async def find_tasks(message: types.Message):
    query = message.get_args()
    if not query:
        await message.reply("Укажи текст для поиска: /find отчёт")
        return

    headers = {
        "Api-key": PLATRUM_API_KEY,
        "Content-Type": "application/json"
    }

    data = {"search": query}
    response = requests.post(f"{PLATRUM_URL}/tasks/api/task/list", headers=headers, json=data)
    tasks = response.json().get("data", [])

    if not tasks:
        await message.reply("Ничего не найдено.")
        return

    reply = ""
    for task in tasks[:5]:  # максимум 5
        task_id = task.get("id")
        name = task.get("name")
        status = task.get("status_key")
        reply += f"🔹 *{name}* (ID: {task_id})\nСтатус: {status}\n[Открыть]({PLATRUM_URL}/tasks/task/{task_id})\n\n"

    await message.reply(reply, parse_mode="Markdown")

async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)
    print("📡 Webhook установлен")

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
