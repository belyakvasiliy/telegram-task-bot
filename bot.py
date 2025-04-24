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

# 👥 Список исполнителей
USER_MAP = {
    "Василий": "3443a213affa5a96d35c10190f6708b5",
    "Светлана": "f2206949133b4b4936f163edebe6c8ec",
    "Александр": "a54525a9e1a995c783d816f4dcba3f3e"
}

# ⏳ Сохраняем временно описание задачи до выбора исполнителя
PENDING_TASKS = {}

@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    await message.reply("Бот активен. Пиши /task <Описание задачи>")

@dp.message_handler(commands=["task"])
async def task_handler(message: types.Message):
    task_text = message.get_args().strip()
    if not task_text:
        await message.reply("⚠️ Формат: /task <Описание задачи>")
        return

    PENDING_TASKS[message.chat.id] = task_text

    keyboard = InlineKeyboardMarkup(row_width=1)
    for name in USER_MAP:
        keyboard.add(InlineKeyboardButton(text=name, callback_data=f"assign:{name}"))

    await message.reply("Кому назначить задачу?", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith("assign:"))
async def assign_callback(callback_query: types.CallbackQuery):
    name = callback_query.data.split(":")[1]
    user_id = USER_MAP.get(name)
    task_text = PENDING_TASKS.get(callback_query.message.chat.id)

    if not task_text:
        await callback_query.answer("⚠️ Не найдена задача.", show_alert=True)
        return

    now = datetime.datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    headers = {
        "Api-key": PLATRUM_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "name": task_text,
        "description": f"Создано через Telegram-группу от Vasyl Beliak",
        "owner_user_id": "3443a213affa5a96d35c10190f6708b5",
        "responsible_user_ids": [user_id],
        "status_key": "new",
        "tag_keys": ["бот", "Telegram"],
        "start_date": now_str,
        "block_id": 3,
        "category_key": "task"
    }

    url = f"https://steves.platrum.ru/tasks/api/task/create"
    response = requests.post(url, headers=headers, json=data)
    result = response.json()

    if response.status_code == 200 and result.get("status") == "success":
        task_id = result.get("data", {}).get("id")
        link = f"https://steves.platrum.ru/tasks/task/{task_id}"
        await bot.send_message(callback_query.message.chat.id, f"✅ Задача создана: {task_text}\n🔗 {link}")
    else:
        await bot.send_message(callback_query.message.chat.id,
            f"❌ Ошибка Platrum: {response.text}\n\n📤 Отправлено: {data}")

    await callback_query.answer()
    PENDING_TASKS.pop(callback_query.message.chat.id, None)

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
