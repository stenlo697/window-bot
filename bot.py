import logging
import httpx
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8651110604:AAHJ0RvsibAsBXUnxP_j_1r3ujnMXrPlKsA"
GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
ADMIN_ID = 435999393

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ты — вежливый помощник по аренде робота-мойщика окон. Отвечай коротко (2-4 предложения), по делу, дружелюбно. Пиши на русском языке.

Информация о сервисе:
- Стоимость аренды: 25 BYN в сутки. Для новых клиентов — 15 BYN (акция)
- Робот сам ездит по стеклу, моет и не падает — держится на вакуумных присосках
- Подходит для: обычных квартирных окон, балконных окон, стеклопакетов
- Не подходит: структурированное (рифлёное) стекло, окна где нельзя снять москитную сетку
- Безопасность: робот оснащён датчиками края, сигнализирует если присоска слабеет
- Залог: 50 BYN (возвращается после возврата в целости)
- Как забронировать: написать сюда, договориться о времени встречи, покажем как пользоваться — 10 минут
- Доставка: самовывоз бесплатно, доставка по городу 5 BYN
- Время аренды: от 1 до 7 суток
- Если клиент хочет связаться или перезвонить — скажи что напишите удобное время и перезвоним
- Если клиент торгуется — напомни про акцию 15 BYN для новых клиентов, скажи что это лучшая цена
- Если клиент говорит спасибо — ответь тепло и коротко
- Если клиент хочет заказать — попроси написать удобное время для встречи

Если вопрос совсем не по теме — мягко переведи разговор обратно к аренде."""

WELCOME = (
    "Привет! 👋 Я помогу узнать всё про аренду *робота-мойщика окон*.\n\n"
    "Выберите вопрос или напишите свой:"
)

QUICK_REPLIES = [
    ["💰 Сколько стоит?", "🤖 Как работает?"],
    ["✅ Безопасно ли?", "📅 Как забронировать?"],
    ["🪟 Какие окна?", "🔒 Залог?"],
    ["🚗 Доставка?", "📆 На сколько дней?"],
]

user_histories = {}
stats = {"users": set(), "messages": 0, "last_time": None}


def get_keyboard():
    return ReplyKeyboardMarkup(QUICK_REPLIES, resize_keyboard=True)


async def notify_admin(context, user, text, answer):
    name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Без имени"
    username = f"@{user.username}" if user.username else "нет username"
    time_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    msg = (
        f"👤 *{name}* ({username})\n"
        f"🆔 `{user.id}`\n"
        f"🕐 {time_str}\n\n"
        f"✉️ *Клиент:* {text}\n\n"
        f"🤖 *Бот:* {answer}"
    )
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Admin notify error: {e}")


async def ask_groq(user_id: int, user_message: str) -> str:
    if user_id not in user_histories:
        user_histories[user_id] = []

    user_histories[user_id].append({"role": "user", "content": user_message})

    if len(user_histories[user_id]) > 20:
        user_histories[user_id] = user_histories[user_id][-20:]

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + user_histories[user_id],
        "max_tokens": 300,
        "temperature": 0.7,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json=payload,
            timeout=15.0
        )
        data = response.json()
        reply = data["choices"][0]["message"]["content"].strip()

    user_histories[user_id].append({"role": "assistant", "content": reply})
    return reply


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_histories[user.id] = []
    stats["users"].add(user.id)
    stats["last_time"] = datetime.now()
    await update.message.reply_text(WELCOME, parse_mode="Markdown", reply_markup=get_keyboard())

    name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Без имени"
    username = f"@{user.username}" if user.username else "нет username"
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🆕 Новый пользователь запустил бота\n👤 *{name}* ({username})\n🆔 `{user.id}`",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Admin notify error: {e}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text or ""
    clean = text.replace("💰","").replace("🤖","").replace("✅","").replace("📅","") \
                .replace("🪟","").replace("🔒","").replace("🚗","").replace("📆","").strip()

    stats["users"].add(user.id)
    stats["messages"] += 1
    stats["last_time"] = datetime.now()

    try:
        answer = await ask_groq(user.id, clean)
    except Exception as e:
        logger.error(f"Groq error: {e}")
        answer = "Что-то пошло не так 😔 Попробуйте написать ещё раз или выберите вопрос из меню."

    await update.message.reply_text(answer, reply_markup=get_keyboard())
    await notify_admin(context, user, clean, answer)


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    last = stats["last_time"].strftime("%d.%m.%Y %H:%M") if stats["last_time"] else "нет данных"
    msg = (
        f"📊 *Статистика бота:*\n\n"
        f"👤 Уникальных пользователей: {len(stats['users'])}\n"
        f"💬 Всего сообщений: {stats['messages']}\n"
        f"🕐 Последнее обращение: {last}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Бот запущен с Groq AI и уведомлениями...")
    app.run_polling()


if __name__ == "__main__":
    main()
