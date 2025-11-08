from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import random
import asyncio

# Стоимость прокрута
SPIN_COST = 100

# Словарь для хранения баланса пользователей: {user_id: balance}
user_balances = {}
# Словарь для хранения состояния ожидания ввода начального баланса
awaiting_balance = set()

# Эмодзи для цифр 0-9
EMOJI_NUM = ["0️⃣","1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣"]

# --- Приветствие ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Это БУРМАЛДА СГЕУ 🎰\nЧтобы начать крутить, используйте команду /dep"
    )

# --- Депозит / старт игры ---
async def dep(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    awaiting_balance.add(user_id)
    await update.message.reply_text("💰 Депните свой баланс:")

# --- Обработка ввода депозита ---
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in awaiting_balance:
        try:
            balance = int(update.message.text)
            if balance <= 0:
                raise ValueError
            user_balances[user_id] = balance
            awaiting_balance.remove(user_id)
            await update.message.reply_text(
                f"✅ Баланс установлен: {balance} рублей\nТеперь можно начать лудку!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Крутить 🎰", callback_data="spin")]])
            )
        except ValueError:
            await update.message.reply_text("❌ Пожалуйста, введите корректное число больше 0.")
    else:
        await update.message.reply_text("Используйте команду /dep чтобы начать лудку.")

# --- Проверка выигрыша ---
def check_win(digits):
    a, b, c = digits
    if a == b == c:
        return 500, "🔥 ДЖЕКПОТ! +500 рублей!"
    elif a == b or b == c or a == c:
        return 200, "🎉 ДВА ОДИНАКОВЫХ! +200 рублей!"
    return 0, "💀 Не повезло... Попробуй ещё!"

# --- Анимация и вращение ---
async def spin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    balance = user_balances.get(user_id, 0)

    if balance < SPIN_COST:
        await query.edit_message_text(
            "❌ Вы проиграли все деньги) Интересный факт: 99% лудоманов останавливаются перед крупным выигрышем. Попробуйте сделать додеп /dep"
        )
        return

    balance -= SPIN_COST

    # --- Анимация "вращения" ---
    max_frames = 5  # количество смен цифр для эффекта прокрутки
    for _ in range(max_frames):
        digits = [random.randint(0, 9) for _ in range(3)]
        display = "".join([EMOJI_NUM[d] for d in digits])
        await query.edit_message_text(f"🎰 КРУТИМ...\n{display}\n💰 Баланс: {balance} рублей")
        await asyncio.sleep(0.3)  # задержка между кадрами

    # --- Финальный результат ---
    final_digits = [random.randint(0, 9) for _ in range(3)]
    display = "".join([EMOJI_NUM[d] for d in final_digits])
    win_amount, message = check_win(final_digits)
    balance += win_amount
    user_balances[user_id] = balance

    text = f"🎰 Результат: {display}\n{message}\n💰 Баланс: {balance} рублей"

    if balance >= SPIN_COST:
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Крутить 🎰", callback_data="spin")]])
        await query.edit_message_text(text, reply_markup=keyboard)
    else:
        await query.edit_message_text(
            text + "\n❌ Вы проиграли все деньги) Интересный факт: 99% лудоманов останавливаются перед крупным выигрышем. Попробуйте сделать додеп /dep"
        )

# --- Запуск бота ---
if __name__ == "__main__":
    app = ApplicationBuilder().token("8106140058:AAGIgK8T3s0vRv1fk4mITuS-ZenPhkMPCDg").build()

    app.add_handler(CommandHandler("start", start))  # приветствие
    app.add_handler(CommandHandler("dep", dep))      # депозит / старт игры
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.add_handler(CallbackQueryHandler(spin, pattern="spin"))

    print("Бот запущен...")
    app.run_polling()
