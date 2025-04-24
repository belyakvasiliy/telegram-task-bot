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
    "Василий": "3443a213affa5a96d35c10190f6708b5",
    "Светлана": "f2206949133b4b4936f163edebe6c8ec",
    "Александр": "a54525a9e1a995c783d816f4dcba3f3e"
}

OWNER_ID = "3443a213affa5a96d35c10190f6708b5"

@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    await message.reply("Бот активен. Используй:\n"
                        "/task <задача> — создать задачу\n"
                        "/taskinfo <ID> — инфо по задаче\n"
                        "/find <слово> — поиск задач")

@dp.message_handler(commands=["task"])
async def task_handler(message: types.Message):
    args = message.get_args()
    if not args:
        await message.reply("Укажи описание задачи: /task Сделать отчёт")
        return

    keyboard = InlineKeyboardMarkup(row_width=1)
    for name in USER_MAP:
        keyboard.add(InlineKeyboardButton(name, callback_data=f"assign:{name}:{args}"))

    await message.reply("Кому назначить задачу?", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith("assign:"))
async def assign_task(callback_query: CallbackQuery):
    _, name, task_text = callback_query.data.split(":", 2)
    user_id = USER_MAP.get(name)
    now = datetime.datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    headers = {
        "Api-key": PLATRUM_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "name": task_text,
        "description": f"Создано через Telegram-группу от {name}",
        "owner_user_id": OWNER_ID,
        "responsible_user_ids": [user_id],
        "status_key": "new",
        "tag_keys": ["бот", "Telegram"],
        "start_date": now_str,
        "block_id": 3,
        "category_key": "task"
    }

    url = "https://steves.platrum.ru/tasks/api/task/create"
    response = requests.post(url, headers=headers, json=data)
    result = response.json()

    if response.status_code == 200 and result.get("status") == "success":
        task_id = result.get("data", {}).get("id")
        link = f"https://steves.platrum.ru/tasks/task/{task_id}"
        await callback_query.message.answer(f"✅ Задача создана: {task_text}\n🔗 {link}")
    else:
        await callback_query.message.answer(f"❌ Ошибка Platrum: {response.text}\n📤 Данные: {data}")

    await callback_query.answer()

@dp.message_handler(commands=["taskinfo"])
async def task_info_handler(message: types.Message):
    task_id = message.get_args().strip()
    if not task_id.isdigit():
        await message.reply("Укажи корректный ID задачи: /taskinfo <ID>")
        return

    url = "https://steves.platrum.ru/tasks/api/task/get"
    headers = {
        "Api-key": PLATRUM_API_KEY,
        "Content-Type": "application/json"
    }
    data = {"id": int(task_id)}
    response = requests.post(url, headers=headers, json=data)
    result = response.json()

    if result.get("status") != "success":
        await message.reply(f"❌ Ошибка Platrum: {response.text}")
        return

    task = result["data"]
    link = f"https://steves.platrum.ru/tasks/task/{task_id}"

    def yes_no(val): return "✅ Да" if val else "❌ Нет"

    info = (
        f"📝 *Задача #{task_id}*\n"
        f"*Название:* {task.get('name')}\n"
        f"*Описание:* {task.get('description')}\n"
        f"*Статус:* {task.get('status_key')}\n"
        f"*Категория:* {task.get('category_key')}\n"
        f"*Продукт:* {task.get('product') or '—'}\n"
        f"*Теги:* {', '.join(task.get('tag_keys', [])) or '—'}\n\n"
        f"*Постановщик:* `{task.get('owner_user_id')}`\n"
        f"*Исполнители:* {', '.join(task.get('responsible_user_ids', [])) or '—'}\n"
        f"*Аудиторы:* {', '.join(task.get('auditors', [])) or '—'}\n"
        f"*Наблюдатели:* {', '.join(task.get('watchers', [])) or '—'}\n\n"
        f"*Создана:* {task.get('creation_date')}\n"
        f"*Начало:* {task.get('start_date')}\n"
        f"*Завершение:* {task.get('finish_date') or '—'}\n"
        f"*Закрыта:* {task.get('close_date') or '—'}\n"
        f"*Комментариев:* {task.get('comment_count', 0)}\n"
        f"*Избранная:* {yes_no(task.get('is_favorite'))}\n"
        f"*Срочная:* {yes_no(task.get('is_important'))}\n"
        f"*Периодическая:* {yes_no(task.get('is_recurrent'))}\n"
        f"*Выполнена:* {yes_no(task.get('is_finished'))}\n\n"
        f"📎 [Открыть задачу в Platrum]({link})"
    )
    await message.reply(info, parse_mode="Markdown")

@dp.message_handler(commands=["find"])
async def find_task(message: types.Message):
    keyword = message.get_args().strip().lower()
    if not keyword:
        await message.reply("Пожалуйста, укажи ключевое слово: /find <ключевое слово>")
        return

    url = "https://steves.platrum.ru/tasks/api/task/list"
    headers = {
        "Api-key": PLATRUM_API_KEY,
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, json={})
    result = response.json()

    if result.get("status") != "success":
        await message.reply(f"❌ Ошибка Platrum: {response.text}")
        return

    tasks = result.get("data", [])
    matches = [task for task in tasks if keyword in task.get("name", "").lower()]

    if not matches:
        await message.reply("🔍 Ничего не найдено.")
        return

    reply = "🔍 Найденные задачи:\n"
    for task in matches[:5]:
        task_id = task["id"]
        name = task["name"]
        link = f"https://steves.platrum.ru/tasks/task/{task_id}"
        reply += f"• {name} — [Открыть]({link})\n"

    await message.reply(reply, parse_mode="Markdown")

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
