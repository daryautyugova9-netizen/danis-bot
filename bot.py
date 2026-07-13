import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from anthropic import Anthropic

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

client = Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = (
    "Ты — Danış, дружелюбный бот-репетитор азербайджанского языка для русскоязычных. "
    "Ты объясняешь грамматику, даёшь короткие уроки и разговорные фразы. "
    "Отвечай кратко (3-6 предложений), используй эмодзи умеренно, "
    "всегда добавляй перевод азербайджанских слов на русский в скобках."
)

def ask_claude(user_message: str) -> str:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salam! 👋 Я — Danış, помогу тебе учить азербайджанский.\n\n"
        "Напиши /lesson чтобы начать урок, или просто задай вопрос об азербайджанском языке."
    )


async def lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action("typing")
    prompt = "Дай короткий урок азербайджанского для начинающего: одна тема (например, приветствие, числа, еда — выбери сама), 3-4 фразы с переводом и одно небольшое задание в конце."
    loop = asyncio.get_event_loop()
    lesson_text = await loop.run_in_executor(None, ask_claude, prompt)
    await update.message.reply_text(lesson_text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip()
    await update.message.chat.send_action("typing")
    loop = asyncio.get_event_loop()
    reply = await loop.run_in_executor(None, ask_claude, user_text)
    await update.message.reply_text(reply)


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("lesson", lesson))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()


if __name__ == "__main__":
    main()
