import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Простой урок для теста (потом заменим на динамику через Anthropic API)
FIRST_LESSON = """
📚 Урок 1: Приветствие

Salam! (Привет!) — universal, любое время дня
Sabahınız xeyir! (Доброе утро!)
Axşamınız xeyir! (Добрый вечер!)

Задание: напиши мне "Salam" в ответ 👇
"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salam! 👋 Я — Danış, помогу тебе учить азербайджанский.\n\n"
        "Напиши /lesson чтобы начать первый урок."
    )


async def lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(FIRST_LESSON)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if text == "salam":
        await update.message.reply_text("Əla! ✅ Düzgündür (Отлично! Правильно). Molodets!")
    else:
        await update.message.reply_text(
            "Пока я умею совсем немного 🙂 Напиши /lesson чтобы пройти урок."
        )


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("lesson", lesson))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()


if __name__ == "__main__":
    main()
