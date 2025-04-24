# config.py — централизованная конфигурация проекта Platrum Bot

import os

# Основные переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
PLATRUM_API_KEY = os.getenv("PLATRUM_API_KEY")
PLATRUM_URL = os.getenv("PLATRUM_URL", "https://yourdomain.platrum.ru")

# Webhook конфигурация
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "https://your-webhook-host.com")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.environ.get("PORT", 3000))

# Получение стандартных заголовков для Platrum API
def get_headers():
    return {
        "Api-key": PLATRUM_API_KEY,
        "Content-Type": "application/json"
    }
