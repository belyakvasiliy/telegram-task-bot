# main.py — запуск Telegram-бота Platrum с регистрацией всех хендлеров

import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import start_webhook

from config import BOT_TOKEN, WEBHOOK_HOST, WEBHOOK_PATH, WEBHOOK_URL, WEBAPP_HOST, WEBAPP_PORT
from users import update_users  # для обновления сотрудников

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
    await message.reply("Привет! Я бот для управления задачами Platrum.\n\nКоманды:\n/task <описание> — создать задачу\n/info <ID> — информация\n/find <ключ> — поиск\n/close <ID> — завершить задачу\n/delete <ID> — удалить задачу\n/update <ID> — изменить задачу\n/boards — список досок\n/wiki — база знаний")

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
