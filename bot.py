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

pending_tasks = {}

@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    await message.reply("Бот активен. Пиши /task <Задача> до <время>. Исполнителя выберешь из списка.")

@dp.message_handler(commands=["task"])
async def task_handler(message: types.Message):
    args = message.get_args()
    if not args:
        await message.reply("Укажи задачу: /task Сделать отчёт до 17:00")
        return

    try:
        parts = args.split(" до ")
        task_text = parts[0]
        due_time = parts[1] if len(parts) > 1 else None

        now = datetime.datetime.now()
        if due_time:
            hour, minute = map(int, due_time.split(":"))
            planned_end = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        else:
            planned_end = now

        planned_end_str = planned_end.strftime("%Y-%m-%d %H:%M:%S")
        planned_end_url = planned_end_str.replace(" ", "%20")
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")

        pending_tasks[message.from_user.id] = {
            "text": task_text,
            "due": planned_end_url,
            "start": now_str
        }

        keyboard = InlineKeyboardMarkup()
        for name in USER_MAP:
            keyboard.add(InlineKeyboardButton(name, callback_data=f"assign:{name}"))

        await message.reply("Кому назначить задачу?", reply_markup=keyboard)

    except Exception as e:
        await message.reply(f"⚠️ Ошибка: {e}")

@dp.callback_query_handler(lambda c: c.data.startswith("assign:"))
async def assign_task(callback_query: types.CallbackQuery):
    name = callback_query.data.split(":")[1]
    user_id = USER_MAP.get(name)
    user_data = pending_tasks.pop(callback_query.from_user.id, None)

    if not user_data:
        await bot.answer_callback_query(callback_query.id, "Нет данных задачи.")
        return

    headers = {
        "Api-key": PLATRUM_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "name": user_data["text"],
        "description": f"Создано через Telegram-бота от {callback_query.from_user.full_name}",
        "owner_user_id": user_id,
        "responsible_user_ids": [user_id],
        "status_key": "new",
        "tag_keys": ["бот", "Telegram"],
        "start_date": user_data["start"],
        "block_id": 3,
        "category_key": "task"
    }

    url = f"https://steves.platrum.ru/tasks/api/task/create?planned_end_date={user_data['due']}"
    response = requests.post(url, headers=headers, json=data)
    result = response.json()

    if response.status_code == 200 and result.get("status") == "success":
        task_id = result["data"]["id"]
        task_url = f"https://steves.platrum.ru/tasks/task/{task_id}"
        await bot.send_message(callback_query.from_user.id, f"✅ Задача создана: {user_data['text']}\n🔗 {task_url}")
    else:
        await bot.send_message(callback_query.from_user.id, f"❌ Ошибка Platrum: {result}\n📤 Данные: {data}")

    await bot.answer_callback_query(callback_query.id)

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
