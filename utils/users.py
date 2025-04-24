# utils/users.py — Вспомогательные функции для работы с сотрудниками Platrum

from utils.config import PLATRUM_URL, get_headers
import requests

# Получить всех сотрудников

def get_all_users():
    url = f"{PLATRUM_URL}/company/api/staff/list"
    headers = get_headers()
    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "success":
            return data.get("data", [])
        return []
    except requests.RequestException:
        return []

# Найти user_id по имени (без учёта регистра)
def find_user_id_by_name(name):
    name = name.lower()
    for user in get_all_users():
        if not user.get("is_deleted") and user["user_name"].lower() == name:
            return user["user_id"]
    return None

# Обновление пользователей в кэш (если будет использоваться в будущем)
def update_users():
    # Зарезервировано под возможное кеширование сотрудников
    pass
