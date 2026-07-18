import os
import logging
import asyncio
import psycopg2
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from anthropic import Anthropic

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
DATABASE_URL = os.environ.get("DATABASE_URL")

client = Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = (
    "Ты — Danış, дружелюбный бот-репетитор азербайджанского языка для русскоязычных. "
    "Ты объясняешь грамматику, даёшь короткие уроки и разговорные фразы. "
    "Отвечай кратко (3-6 предложений), используй эмодзи умеренно, "
    "всегда добавляй перевод азербайджанских слов на русский в скобках."
)


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            lessons_completed INTEGER DEFAULT 0,
            last_active TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


def ensure_user(user_id: int, username: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (user_id, username, last_active)
        VALUES (%s, %s, NOW())
        ON CONFLICT (user_id) DO UPDATE SET last_active = NOW()
    """, (user_id, username))
    conn.commit()
    cur.close()
    conn.close()


def increment_lessons(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE users SET lessons_completed = lessons_completed + 1, last_active = NOW()
        WHERE user_id = %s
    """, (user_id,))
    conn.commit()
    cur.close()
    conn.close()


def get_progress(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT lessons_completed FROM users WHERE user_id = %s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else 0


def ask_claude(user_message: str) -> str:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id, user.username or user.first_name)
    await update.message.reply_text(
        "Salam! 👋 Я — Danış, помогу тебе учить азербайджанский.\n\n"
        "Напиши /lesson чтобы начать урок, /progress чтобы посмотреть свой прогресс, "
        "или просто задай вопрос об азербайджанском языке."
    )


async def lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id, user.username or user.first_name)
    await update.message.chat.send_action("typing")
    prompt = "Дай короткий урок азербайджанского для начинающего: одна тема (например, приветствие, числа, еда — выбери сама), 3-4 фразы с переводом и одно небольшое задание в конце."
    loop = asyncio.get_event_loop()
    lesson_text = await loop.run_in_executor(None, ask_claude, prompt)
    increment_lessons(user.id)
    await update.message.reply_text(lesson_text)


async def progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    count = get_progress(user.id)
    await update.message.reply_text(f"📊 Ты прошёл(-а) уроков: {count}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id, user.username or user.first_name)
    user_text = update.message.text.strip()
    await update.message.chat.send_action("typing")
    loop = asyncio.get_event_loop()
    reply = await loop.run_in_executor(None, ask_claude, user_text)
    await update.message.reply_text(reply)


def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("lesson", lesson))
    app.add_handler(CommandHandler("progress", progress))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()


if __name__ == "__main__":
    main()
