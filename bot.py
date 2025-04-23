from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import Message
import os

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def start_handler(message: Message):
    await message.answer("Бот активен. Пиши /task <описание задачи>.")

@dp.message_handler(commands=["task"])
async def task_handler(message: Message):
    task_text = message.get_args()
    if task_text:
        await message.answer(f"📝 Задача получена: {task_text}")
    else:
        await message.answer("Пожалуйста, укажи текст задачи после команды /task.")

if __name__ == "__main__":
    executor.start_polling(dp)
