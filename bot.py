import logging
import httpx
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8651110604:AAHJ0RvsibAsBXUnxP_j_1r3ujnMXrPlKsA"
GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

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


def get_keyboard():
    return ReplyKeyboardMarkup(QUICK_REPLIES, resize_keyboard=True)


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
    user_id = update.effective_user.id
    user_histories[user_id] = []
    await update.message.reply_text(WELCOME, parse_mode="Markdown", reply_markup=get_keyboard())


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text or ""
    clean = text.replace("💰","").replace("🤖","").replace("✅","").replace("📅","") \
                .replace("🪟","").replace("🔒","").replace("🚗","").replace("📆","").strip()

    try:
        answer = await ask_groq(user_id, clean)
    except Exception as e:
        logger.error(f"Groq error: {e}")
        answer = "Что-то пошло не так 😔 Попробуйте написать ещё раз или выберите вопрос из меню."

    await update.message.reply_text(answer, reply_markup=get_keyboard())


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Бот запущен с Groq AI...")
    app.run_polling()


if __name__ == "__main__":
    main()
