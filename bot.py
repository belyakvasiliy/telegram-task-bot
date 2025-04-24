import os
import logging
import datetime
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
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

# Имя → ID пользователя в Platrum
USER_MAP = {
     "Василий": "3443a213affa5a96d35c10190f6708b5",
    "Светлана": "f2206949133b4b4936f163edebe6c8ec",
    "Александр": "a54525a9e1a995c783d816f4dcba3f3e"
}

# Временное хранилище задач по user_id
pending_tasks = {}

@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    await message.reply("Бот активен. Пиши /task <Описание задачи> или /task <Имя> <Описание задачи>")

@dp.message_handler(commands=["task"])
async def task_handler(message: types.Message):
    args = message.get_args()
    if not args:
        await message.reply("⚠️ Укажи описание задачи: /task <Описание задачи>")
        return

    parts = args.split(" ", 1)
    if parts[0] in USER_MAP and len(parts) > 1:
        assignee_name = parts[0]
        task_text = parts[1]
        await create_task(message, assignee_name, task_text)
    else:
        # Сохраняем временно задачу без исполнителя
        pending_tasks[message.from_user.id] = args

        keyboard = InlineKeyboardMarkup(row_width=1)
        for name in USER_MAP.keys():
            keyboard.add(InlineKeyboardButton(text=name, callback_data=f"choose_user:{name}"))

        await message.reply("Кому назначить задачу?", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith("choose_user:"))
async def process_user_choice(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    assignee_name = callback_query.data.split(":")[1]
    task_text = pending_tasks.pop(user_id, None)

    if not task_text:
        await callback_query.message.edit_text("⚠️ Не найдена задача для назначения.")
        return

    await create_task(callback_query.message, assignee_name, task_text)
    await callback_query.answer()

async def create_task(message, assignee, task_text):
    user_id = USER_MAP.get(assignee)
    if not user_id:
        await message.reply(f"❌ Неизвестный исполнитель: {assignee}")
        return

    now = datetime.datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    headers = {
        "Api-key": PLATRUM_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "name": task_text,
        "description": f"Создано через Telegram-группу от {message.from_user.full_name}",
        "owner_user_id": user_id,
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
        task_id = result["data"].get("id")
        link = f"https://steves.platrum.ru/tasks/{task_id}"
        await message.reply(f"✅ Задача создана: {task_text}\n🔗 {link}")
    else:
        await message.reply(
            f"❌ Ошибка Platrum: {response.text}\n"
            f"📤 Данные: {data}"
        )

@dp.message_handler(commands=["debug"])
async def debug_task(message: types.Message):
    try:
        task_id = int(message.get_args().strip())
        url = "https://steves.platrum.ru/tasks/api/task/get"
        headers = {
            "Api-key": PLATRUM_API_KEY,
            "Content-Type": "application/json"
        }
        data = {"id": task_id}
        response = requests.post(url, headers=headers, json=data)
        result = response.json()

        if result.get("status") == "success":
            task = result["data"]
            fields = {
                "name": task.get("name"),
                "status_key": task.get("status_key"),
                "owner_user_id": task.get("owner_user_id"),
                "responsible_user_ids": task.get("responsible_user_ids"),
                "block_id": task.get("block_id"),
                "category_key": task.get("category_key"),
            }
            pretty = "\n".join([f"{k}: {v}" for k, v in fields.items()])
            await message.reply(f"✅ Информация по задаче {task_id}:\n{pretty}")
        else:
            await message.reply(f"❌ Ошибка при получении задачи: {result}")

    except Exception as e:
        await message.reply(f"⚠️ Ошибка debug: {e}")

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
