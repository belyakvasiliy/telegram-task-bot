# main.py — запуск Telegram-бота Platrum с регистрацией всех хендлеров

import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import start_webhook

from utils.config import BOT_TOKEN, WEBHOOK_HOST, WEBHOOK_PATH, WEBHOOK_URL, WEBAPP_HOST, WEBAPP_PORT
from utils.users import update_users, get_all_users, find_user_id_by_name  # обновление и поиск сотрудников
from api import platrum_post  # вызов API создания задачи

# Импорт хендлеров — обязательно, чтобы они были зарегистрированы
from handlers import tasks, users, boards, wiki

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

# Команда /start
@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    update_users()
    await message.reply("Привет! Я бот для управления задачами Platrum.\n\nКоманды:\n/task <Имя> <Описание> — создать задачу\n/info <ID> — информация\n/find <ключ> — поиск\n/close <ID> — завершить задачу\n/delete <ID> — удалить задачу\n/update <ID> — изменить задачу\n/boards — список досок\n/wiki — база знаний\n/users — сотрудники")

# Команда /users — показать список сотрудников
@dp.message_handler(commands=["users"])
async def list_users(message: types.Message):
    users = get_all_users()
    if not users:
        await message.reply("Список сотрудников пуст или недоступен.")
        return
    text = "👥 *Сотрудники:*\n"
    for user in users:
        if not user.get("is_deleted"):
            text += f"\n- {user['user_name']} (ID: {user['user_id']})"
    await message.reply(text, parse_mode="Markdown")

# Команда /task <Имя> <Описание задачи>
@dp.message_handler(commands=["task"])
async def create_task(message: types.Message):
    args = message.get_args()
    if not args or len(args.split()) < 2:
        await message.reply("Укажи задачу в формате: /task <Имя> <Описание>\nПример: /task Иван Сделать отчёт до 17:00")
        return

    name, *task_text_parts = args.split()
    task_text = " ".join(task_text_parts)
    user_id = find_user_id_by_name(name)

    if not user_id:
        await message.reply(f"❌ Неизвестный исполнитель: {name}. Проверь имя через /users")
        return

    now = message.date.strftime("%Y-%m-%d %H:%M:%S")
    data = {
        "name": task_text,
        "description": f"Создано через Telegram от {name}",
        "owner_user_id": user_id,
        "responsible_user_ids": [user_id],
        "status_key": "new",
        "tag_keys": ["бот", "Telegram"],
        "start_date": now,
        "block_id": 3,
        "category_key": "task"
    }

    result = platrum_post("/tasks/api/task/create", data)

    if result.get("status") == "success":
        task_id = result["data"].get("id")
        await message.reply(
            f"✅ Задача создана!\n"
            f"🔗 https://{WEBHOOK_HOST.replace('https://', '')}/tasks/task/{task_id}"
        )
    else:
        await message.reply(f"❌ Ошибка при создании задачи: {result}")

# Подключение webhook и запуск
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
