# utils/users.py — Вспомогательные функции для работы с сотрудниками Platrum

from utils.api import platrum_post platrum_post

# Получить всех сотрудников

def get_all_users():
    response = platrum_post("/company/api/staff/list")
    if response.get("status") == "success":
        return response.get("data", [])
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
