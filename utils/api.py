# api.py — обёртка для работы с API Platrum

import requests
from utils.config import PLATRUM_URL, get_headers

# Общий метод для POST-запросов к Platrum API
def platrum_post(endpoint: str, payload: dict = None):
    url = f"{PLATRUM_URL}{endpoint}"
    headers = get_headers()
    try:
        response = requests.post(url, headers=headers, json=payload or {})
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"status": "error", "error": str(e)}

# Метод GET можно добавить при необходимости:
# def platrum_get(endpoint: str, params: dict = None):
#     url = f"{PLATRUM_URL}{endpoint}"
#     headers = get_headers()
#     try:
#         response = requests.get(url, headers=headers, params=params or {})
#         response.raise_for_status()
#         return response.json()
#     except requests.RequestException as e:
#         return {"status": "error", "error": str(e)}
