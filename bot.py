import os
import logging
import datetime
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.executor import start_webhook

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

# 👤 Имя → ID пользователя в Platrum
USER_MAP = {
    "Василий": "3443a213affa5a96d35c10190f6708b5",
    "Светлана": "f2206949133b4b4936f163edebe6c8ec",
    "Александр": "a54525a9e1a995c783d816f4dcba3f3e"
}

user_pending_tasks = {}  # message_id: {"text": str, "from_user_id": int}

@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    await message.reply("Бот активен. Пиши /task <Описание задачи>")

@dp.message_handler(commands=["task"])
async def task_handler(message: types.Message):
    args = message.get_args()
    if not args:
        await message.reply("Укажи задачу: /task Сделать отчёт")
        return

    keyboard = InlineKeyboardMarkup(row_width=1)
    for name in USER_MAP:
        keyboard.add(InlineKeyboardButton(name, callback_data=f"assign:{name}|{args}"))

    sent = await message.reply("Кому назначить задачу?", reply_markup=keyboard)
    user_pending_tasks[sent.message_id] = {"text": args, "from_user_id": message.from_user.id}

@dp.callback_query_handler(lambda c: c.data.startswith("assign:"))
async def assign_callback(callback_query: types.CallbackQuery):
    await callback_query.answer()
    data = callback_query.data[len("assign:"):]
    name, task_text = data.split("|", 1)
    user_id = USER_MAP.get(name)
    now = datetime.datetime.now()

    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    planned_end_str = now.strftime("%Y-%m-%d %H:%M:%S")  # временно до добавления времени вручную

    headers = {
        "Api-key": PLATRUM_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "name": task_text,
        "description": f"Создано через Telegram-группу от {callback_query.from_user.full_name}",
        "owner_user_id": user_id,
        "responsible_user_ids": [user_id],
        "status_key": "new",
        "tag_keys": ["бот", "Telegram"],
        "start_date": now_str,
        "block_id": 3,
        "category_key": "task"
    }

    url = f"https://steves.platrum.ru/tasks/api/task/create?planned_end_date={planned_end_str.replace(' ', '%20')}"
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200 and response.json().get("status") == "success":
        task_id = response.json().get("data", {}).get("id")
        task_link = f"https://steves.platrum.ru/tasks/task/{task_id}"
        await bot.send_message(callback_query.from_user.id, f"✅ Задача создана: {task_text}\n🔗 {task_link}")
    else:
        await bot.send_message(callback_query.from_user.id,
            f"❌ Ошибка Platrum: {response.text}\n📤 Отправлено: {data}\n🔗 URL: {url}")

async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)
    print("📡 Webhook установлен")

async def on_shutdown(dp):
    logging.warning('Shutting down..')
    await bot.delete_webhook()
    logging.warning('Webhook удалён')

if __name__ == '__main__':
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
