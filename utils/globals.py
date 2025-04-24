# utils/globals.py — централизованные переменные и объекты

import os
from aiogram import Bot, Dispatcher

# Получение токенов и URL из окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
PLATRUM_API_KEY = os.getenv("PLATRUM_API_KEY")
PLATRUM_URL = os.getenv("PLATRUM_URL")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Кэш пользователей и функция поиска владельца задачи
USER_MAP = {}

def resolve_owner_id():
    # Возвращает ID владельца задачи (можно сделать адаптивным)
    return list(USER_MAP.keys())[0] if USER_MAP else None
