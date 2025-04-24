# wiki.py — работа с разделами и статьями базы знаний Platrum

from aiogram import types
from main import dp
from api import platrum_post

@dp.message_handler(commands=["wiki"])
async def list_spaces(message: types.Message):
    result = platrum_post("/wiki/api/space/list")
    spaces = result.get("data", [])
    if not spaces:
        await message.reply("📚 Разделы не найдены.")
        return

    text = "📚 *Разделы базы знаний:*\n"
    for space in spaces:
        text += f"\n🔸 *{space['title']}* (ID: {space['id']})"
    await message.reply(text, parse_mode="Markdown")

@dp.message_handler(commands=["articles"])
async def list_articles(message: types.Message):
    try:
        space_id = int(message.get_args())
    except:
        await message.reply("Укажи ID раздела: /articles <space_id>")
        return

    result = platrum_post("/wiki/api/article/list", {"space_id": space_id})
    articles = result.get("data", [])
    if not articles:
        await message.reply("📄 Статьи не найдены.")
        return

    text = f"📄 *Статьи в разделе {space_id}:*\n"
    for article in articles:
        text += f"\n▪️ *{article['title']}* (ID: {article['id']})"
    await message.reply(text, parse_mode="Markdown")

@dp.message_handler(commands=["article"])
async def get_article(message: types.Message):
    try:
        article_id = int(message.get_args())
        result = platrum_post("/wiki/api/article/get", {"id": article_id})
        article = result.get("data")
        if not article:
            await message.reply("❌ Статья не найдена.")
            return

        text = f"📘 *{article['title']}*\n"
        for block in article.get("content_blocks", []):
            if block.get("content"):
                text += f"\n{block['content']}"
        await message.reply(text, parse_mode="Markdown")
    except Exception as e:
        await message.reply(f"⚠️ Ошибка: {e}")

