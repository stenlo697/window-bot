import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# === ВСТАВЬ СВОЙ ТОКЕН СЮДА ===
TOKEN = "8651110604:AAHJ0RvsibAsBXUnxP_j_1r3ujnMXrPlKsA"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# База знаний
KB = [
    {
        "keys": ["цен", "стоит", "стоимост", "сколько", "тариф", "прайс"],
        "answer": "💰 *Стоимость аренды:*\n\n• 25 BYN в сутки\n• Для новых клиентов — *15 BYN* (акция)\n\nОплата при получении."
    },
    {
        "keys": ["работает", "принцип", "как он", "механизм", "устроен", "что делает"],
        "answer": "🤖 *Как работает робот:*\n\nРобот крепится к стеклу на вакуумных присосках и самостоятельно ездит по окну, протирая его.\n\nВы просто запускаете — дальше всё автоматически. Одно окно занимает около 5–10 минут."
    },
    {
        "keys": ["безопасн", "упадёт", "упадет", "надёжн", "присоск", "датчик"],
        "answer": "✅ *Безопасность:*\n\nРобот оснащён датчиками края — он не упадёт с окна. Если присоска начинает слабеть, устройство сигнализирует и останавливается.\n\nТысячи людей используют такие роботы без происшествий."
    },
    {
        "keys": ["забронир", "заказать", "записаться", "оформить", "получить", "взять"],
        "answer": "📅 *Как забронировать:*\n\n1. Напишите нам удобное время\n2. Договариваемся о встрече\n3. При получении показываем как пользоваться (~10 мин)\n\nПишите прямо сюда — ответим быстро!"
    },
    {
        "keys": ["какие окна", "подходит", "подойдёт", "стеклопакет", "балкон", "москит", "сетк"],
        "answer": "🪟 *Подходящие окна:*\n\n✅ Квартирные стеклопакеты\n✅ Балконные окна\n✅ Панорамные окна\n\n❌ Структурированное (рифлёное) стекло\n❌ Окна с москитной сеткой (сетку нужно снять перед запуском)"
    },
    {
        "keys": ["залог", "депозит", "страхов"],
        "answer": "🔒 *Залог:*\n\nЗалог — *50 BYN*\n\nВозвращается сразу после возврата робота в целости. Это стандартная защита оборудования."
    },
    {
        "keys": ["доставк", "привезут", "самовывоз", "адрес"],
        "answer": "🚗 *Доставка:*\n\n• Самовывоз — бесплатно\n• Доставка по городу — 5 BYN\n\nАдрес уточняется при бронировании."
    },
    {
        "keys": ["сколько дней", "дней можно", "срок", "минимум", "максимум", "на неделю", "период"],
        "answer": "📆 *Сроки аренды:*\n\n• Минимум — 1 сутки\n• Максимум — 7 суток\n\nНужно дольше? Напишите — обсудим индивидуально."
    },
    {
        "keys": ["инструкци", "научит", "покажет", "сложно", "просто", "разберусь"],
        "answer": "📱 *Инструкция:*\n\nВсё очень просто! При получении показываем как запустить — занимает около 10 минут.\n\nТакже есть видео-инструкция."
    },
]

FALLBACK = (
    "Хороший вопрос! 😊 Чтобы ответить точнее — уточните, пожалуйста, что именно вас интересует, "
    "или выберите один из вариантов ниже."
)

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


def get_keyboard():
    return ReplyKeyboardMarkup(QUICK_REPLIES, resize_keyboard=True)


def find_answer(text: str) -> str:
    t = text.lower()
    for entry in KB:
        if any(k in t for k in entry["keys"]):
            return entry["answer"]
    return FALLBACK


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        WELCOME,
        parse_mode="Markdown",
        reply_markup=get_keyboard()
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    # Убираем эмодзи из кнопок для поиска
    clean = text.replace("💰", "").replace("🤖", "").replace("✅", "").replace("📅", "") \
                .replace("🪟", "").replace("🔒", "").replace("🚗", "").replace("📆", "").strip()

    answer = find_answer(clean)
    await update.message.reply_text(
        answer,
        parse_mode="Markdown",
        reply_markup=get_keyboard()
    )


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
