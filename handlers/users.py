# users.py — логика работы с пользователями и сотрудниками в системе Platrum

import requests
from main import PLATRUM_API_KEY, PLATRUM_URL

headers = {"Api-key": PLATRUM_API_KEY, "Content-Type": "application/json"}

# Получение списка всех сотрудников

def get_all_users():
    response = requests.post(f"{PLATRUM_URL}/company/api/staff/list", headers=headers)
    if response.status_code == 200:
        return response.json().get("data", [])
    return []

# Получение user_id по имени пользователя (или Telegram ID в будущем)
def find_user_id_by_name(name):
    users = get_all_users()
    for user in users:
        if user['user_name'] == name and not user.get("is_deleted"):
            return user['user_id']
    return None

# Получение user_name по user_id
def find_user_name_by_id(user_id):
    users = get_all_users()
    for user in users:
        if user['user_id'] == user_id:
            return user['user_name']
    return None

# Получение информации о пользователе по Telegram ID (если связка реализована)
def get_user_by_telegram_id(telegram_id):
    # Здесь можно реализовать привязку telegram_id ↔ user_id через БД или словарь
    return None
