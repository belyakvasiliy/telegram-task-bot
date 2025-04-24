import os
import logging
import datetime
import requests
from aiogram import Bot, Dispatcher, types
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
    "@SvetlanaCherednichok": "f2206949133b4b4936f163edebe6c8ec",
    "@Business_Automation_Expert": "3443a213affa5a96d35c10190f6708b5"
    
}

@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    await message.reply("Бот активен. Пиши /task <Имя> <Задача> до <время>\nПример: /task Иван Сделать отчёт до 17:00")

@dp.message_handler(commands=["task"])
async def task_handler(message: types.Message):
    args = message.get_args()
    if not args:
        await message.reply("Укажи задачу: /task Иван Сделать отчёт до 17:00")
        return

    try:
        parts = args.split(" до ")
        task_info = parts[0].split(" ", 1)
        assignee = task_info[0]
        task_text = task_info[1] if len(task_info) > 1 else "Без описания"
        due_time = parts[1] if len(parts) > 1 else None

        user_id = USER_MAP.get(assignee)
        if not user_id:
            await message.reply(f"Неизвестный исполнитель: {assignee}")
            return

        now = datetime.datetime.now()
        if due_time:
            hour, minute = map(int, due_time.split(":"))
            planned_end = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        else:
            planned_end = now

        planned_end_str = planned_end.strftime("%Y-%m-%d %H:%M:%S")
        planned_end_url = planned_end_str.replace(" ", "%20")
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")

        headers = {
            "Api-key": PLATRUM_API_KEY,
            "Content-Type": "application/json"
        }

        data = {
            "name": task_text,
            "description": "Создано через Telegram-бота",
            "owner_user_id": user_id,
            "responsible_user_ids": [user_id],
            "status_key": "new",  # ✔️ lowercase
            "tag_keys": ["бот", "Telegram"],
            "start_date": now_str,
            "block_id": 3,
            "category_key": "task"
        }

        url = f"https://steves.platrum.ru/tasks/api/task/create?planned_end_date={planned_end_url}"
        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200 and response.json().get("status") == "success":
            await message.reply(f"✅ Задача создана: {task_text}")
        else:
            await message.reply(
                f"❌ Ошибка Platrum: {response.text}\n"
                f"📤 Отправлено: {data}\n"
                f"🔗 URL: {url}"
            )

    except Exception as e:
        await message.reply(f"⚠️ Ошибка: {e}")

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
