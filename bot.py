import os
import logging
import psycopg2
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")

LESSONS = [
    {
        "title": "Урок 1: Приветствие",
        "text": (
            "📚 Урок 1: Приветствие\n\n"
            "Salam! (Привет!) — universal, любое время дня\n"
            "Sabahınız xeyir! (Доброе утро!)\n"
            "Axşamınız xeyir! (Добрый вечер!)\n\n"
            "Задание: напиши мне \"Salam\" в ответ 👇"
        ),
    },
    {
        "title": "Урок 2: Числа 1-10",
        "text": (
            "📚 Урок 2: Числа 1-10\n\n"
            "Bir (один), İki (два), Üç (три), Dörd (четыре), Beş (пять)\n"
            "Altı (шесть), Yeddi (семь), Səkkiz (восемь), Doqquz (девять), On (десять)\n\n"
            "Задание: напиши мне число 5 по-азербайджански 👇"
        ),
    },
    {
        "title": "Урок 3: Еда",
        "text": (
            "📚 Урок 3: Еда\n\n"
            "Çörək (хлеб), Su (вода), Ət (мясо), Balıq (рыба)\n"
            "Çay (чай), Meyvə (фрукты), Dadlıdır! (Вкусно!)\n\n"
            "Задание: напиши мне \"Dadlıdır\" в ответ 👇"
        ),
    },
    {
        "title": "Урок 4: Семья",
        "text": (
            "📚 Урок 4: Семья\n\n"
            "Ana (мама), Ata (папа), Bacı (сестра), Qardaş (брат)\n"
            "Ailə (семья)\n\n"
            "Задание: напиши мне слово \"мама\" по-азербайджански 👇"
        ),
    },
    {
        "title": "Урок 5: Основные вопросы",
        "text": (
            "📚 Урок 5: Основные вопросы\n\n"
            "Necəsiniz? (Как дела?)\n"
            "Bu neçəyədir? (Сколько это стоит?)\n"
            "Hardadır...? (Где находится...?)\n\n"
            "Задание: напиши мне \"Necəsiniz?\" в ответ 👇"
        ),
    },
]


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


def get_progress(user_id: int) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT lessons_completed FROM users WHERE user_id = %s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else 0


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id, user.username or user.first_name)
    await update.message.reply_text(
        "Salam! 👋 Я — Danış, помогу тебе учить азербайджанский.\n\n"
        "Напиши /lesson чтобы начать следующий урок, /progress чтобы посмотреть свой прогресс."
    )


async def lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id, user.username or user.first_name)
    count = get_progress(user.id)
    current = LESSONS[count % len(LESSONS)]
    increment_lessons(user.id)
    await update.message.reply_text(current["text"])


async def progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    count = get_progress(user.id)
    await update.message.reply_text(f"📊 Ты прошёл(-а) уроков: {count}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id, user.username or user.first_name)
    await update.message.reply_text(
        "Əla! ✅ Продолжай в том же духе.\n\nНапиши /lesson для следующего урока или /progress чтобы увидеть прогресс."
    )


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
