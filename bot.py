@dp.message_handler(commands=["debug"])
async def debug_task(message: types.Message):
    try:
        task_id = int(message.get_args().strip())
        url = "https://steves.platrum.ru/tasks/api/task/get"
        headers = {
            "Api-key": os.getenv("PLATRUM_API_KEY"),
            "Content-Type": "application/json"
        }
        data = {"id": task_id}
        response = requests.post(url, headers=headers, json=data)
        result = response.json()

        # Показываем только ключевые поля
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
            await message.reply(f"✅ Информация по задаче:\n{pretty}")
        else:
            await message.reply(f"❌ Ошибка: {result}")

    except Exception as e:
        await message.reply(f"⚠️ Ошибка: {e}")
