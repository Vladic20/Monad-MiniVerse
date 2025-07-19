import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.types import FSInputFile

from config import BOT_TOKEN, ADMIN_IDS
from database import Database
from exchange_service import ExchangeService
from keyboards import *

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Initialize services
db = Database()
exchange_service = ExchangeService(db)

# FSM States
class ExchangeStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_confirmation = State()

class AdminStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_amount = State()
    waiting_for_currency = State()

# User states storage
user_states = {}

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Start command handler"""
    user_id = message.from_user.id
    user = message.from_user
    
    # Create user if not exists
    if not db.get_user(user_id):
        db.create_user(user_id, user.username, user.first_name, user.last_name)
    
    welcome_text = f"""
🎉 Добро пожаловать в Crypto Exchange Bot!

💎 Ваш надежный партнер для обмена валют и криптовалют.

🔹 Поддерживаемые валюты: USD, EUR, RUB, BTC, ETH
🔹 Минимальная сумма: ${config.MIN_TRADE_AMOUNT}
🔹 Максимальная сумма: ${config.MAX_TRADE_AMOUNT}
🔹 Комиссия: {config.EXCHANGE_FEE * 100}%

Выберите действие в меню ниже:
    """
    
    await message.answer(welcome_text, reply_markup=get_main_keyboard())

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Help command handler"""
    help_text = """
📚 Справка по использованию бота:

💱 Обмен валют:
1. Нажмите "💱 Обмен валют"
2. Выберите валюту для обмена
3. Выберите валюту для получения
4. Введите сумму
5. Подтвердите операцию

💰 Баланс:
- Просмотр баланса по всем валютам
- История операций

📊 Курсы валют:
- Актуальные курсы обмена
- Графики изменения

⚙️ Настройки:
- Уведомления
- Язык интерфейса
- Безопасность

🔒 Безопасность:
- Все операции защищены
- Комиссия: 2%
- Лимиты на операции

Для связи с поддержкой: @support
    """
    
    await message.answer(help_text, reply_markup=get_back_keyboard("back_to_main"))

@dp.message(F.text == "💰 Баланс")
async def show_balance(message: types.Message):
    """Show user balance"""
    user_id = message.from_user.id
    balance = exchange_service.get_user_balance(user_id)
    
    if not balance:
        await message.answer("❌ Ошибка получения баланса")
        return
    
    balance_text = "💰 Ваш баланс:\n\n"
    for currency, amount in balance.items():
        if amount > 0:
            balance_text += f"{currency}: {amount:.4f}\n"
    
    if all(amount == 0 for amount in balance.values()):
        balance_text += "У вас пока нет средств на балансе.\n"
        balance_text += "Начните с обмена валют! 💱"
    
    await message.answer(balance_text, reply_markup=get_back_keyboard("back_to_main"))

@dp.message(F.text == "💱 Обмен валют")
async def start_exchange(message: types.Message):
    """Start exchange process"""
    await message.answer(
        "💱 Выберите валюту для обмена:",
        reply_markup=get_currency_keyboard()
    )

@dp.message(F.text == "📊 Курсы валют")
async def show_rates(message: types.Message):
    """Show current exchange rates"""
    rates_text = "📊 Текущие курсы валют:\n\n"
    
    base_currencies = ['USD', 'EUR']
    target_currencies = ['USD', 'EUR', 'RUB', 'BTC', 'ETH']
    
    for base in base_currencies:
        rates_text += f"💱 {base}:\n"
        for target in target_currencies:
            if base != target:
                rate = exchange_service.get_exchange_rate(base, target)
                rates_text += f"  {target}: {rate:.6f}\n"
        rates_text += "\n"
    
    await message.answer(rates_text, reply_markup=get_back_keyboard("back_to_main"))

@dp.message(F.text == "📈 История операций")
async def show_history(message: types.Message):
    """Show transaction history"""
    user_id = message.from_user.id
    transactions = db.get_user_transactions(user_id, 5)
    
    if not transactions:
        await message.answer("📈 У вас пока нет операций.", reply_markup=get_back_keyboard("back_to_main"))
        return
    
    history_text = "📈 Последние операции:\n\n"
    for tx in transactions:
        date = tx['created_at'][:19]  # Format datetime
        history_text += f"🕐 {date}\n"
        history_text += f"💱 {tx['amount']:.4f} {tx['from_currency']} → {tx['total_amount']:.4f} {tx['to_currency']}\n"
        history_text += f"📊 Курс: {tx['rate']:.6f}\n"
        history_text += f"💸 Комиссия: {tx['fee']:.4f} {tx['from_currency']}\n"
        history_text += f"✅ Статус: {tx['status']}\n\n"
    
    await message.answer(history_text, reply_markup=get_back_keyboard("back_to_main"))

@dp.message(F.text == "⚙️ Настройки")
async def show_settings(message: types.Message):
    """Show settings menu"""
    if message.from_user.id in ADMIN_IDS:
        await message.answer("⚙️ Настройки:", reply_markup=get_admin_keyboard())
    else:
        await message.answer("⚙️ Настройки:", reply_markup=get_settings_keyboard())

@dp.message(F.text == "ℹ️ Помощь")
async def show_help(message: types.Message):
    """Show help information"""
    await cmd_help(message)

# Callback handlers
@dp.callback_query(F.data.startswith("currency_"))
async def handle_currency_selection(callback: types.CallbackQuery):
    """Handle currency selection"""
    currency = callback.data.split("_")[1]
    user_states[callback.from_user.id] = {"from_currency": currency}
    
    await callback.message.edit_text(
        f"💱 Вы выбрали {currency}\nТеперь выберите валюту для получения:",
        reply_markup=get_exchange_keyboard(currency)
    )

@dp.callback_query(F.data.startswith("exchange_"))
async def handle_exchange_selection(callback: types.CallbackQuery):
    """Handle exchange currency pair selection"""
    _, from_currency, to_currency = callback.data.split("_")
    user_states[callback.from_user.id]["to_currency"] = to_currency
    
    rate = exchange_service.get_exchange_rate(from_currency, to_currency)
    rate_text = f"📊 Курс: 1 {from_currency} = {rate:.6f} {to_currency}\n\n"
    
    await callback.message.edit_text(
        f"💱 Обмен {from_currency} → {to_currency}\n{rate_text}Выберите сумму:",
        reply_markup=get_amount_keyboard(from_currency, to_currency)
    )

@dp.callback_query(F.data.startswith("amount_"))
async def handle_amount_selection(callback: types.CallbackQuery):
    """Handle amount selection"""
    _, from_currency, to_currency, amount = callback.data.split("_")
    amount = float(amount)
    
    await show_exchange_preview(callback, from_currency, to_currency, amount)

@dp.callback_query(F.data.startswith("manual_amount_"))
async def handle_manual_amount(callback: types.CallbackQuery, state: FSMContext):
    """Handle manual amount input"""
    _, from_currency, to_currency = callback.data.split("_")
    
    await state.update_data(from_currency=from_currency, to_currency=to_currency)
    await state.set_state(ExchangeStates.waiting_for_amount)
    
    await callback.message.edit_text(
        f"✏️ Введите сумму {from_currency} для обмена:\n\n"
        f"Минимум: {config.MIN_TRADE_AMOUNT}\n"
        f"Максимум: {config.MAX_TRADE_AMOUNT}",
        reply_markup=get_back_keyboard(f"back_to_amount_{from_currency}_{to_currency}")
    )

@dp.message(ExchangeStates.waiting_for_amount)
async def handle_amount_input(message: types.Message, state: FSMContext):
    """Handle amount input"""
    try:
        amount = float(message.text)
        data = await state.get_data()
        from_currency = data["from_currency"]
        to_currency = data["to_currency"]
        
        await state.clear()
        await show_exchange_preview(message, from_currency, to_currency, amount)
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректное число.")

async def show_exchange_preview(message_or_callback, from_currency: str, to_currency: str, amount: float):
    """Show exchange preview"""
    total_amount, fee, rate = exchange_service.calculate_exchange(from_currency, to_currency, amount)
    
    preview_text = f"""
💱 Предварительный расчет обмена:

📤 Отправляете: {amount:.4f} {from_currency}
📥 Получаете: {total_amount:.4f} {to_currency}
💸 Комиссия: {fee:.4f} {from_currency}
📊 Курс: 1 {from_currency} = {rate:.6f} {to_currency}

Подтвердите операцию:
    """
    
    keyboard = get_confirm_keyboard(from_currency, to_currency, amount)
    
    if isinstance(message_or_callback, types.Message):
        await message_or_callback.answer(preview_text, reply_markup=keyboard)
    else:
        await message_or_callback.message.edit_text(preview_text, reply_markup=keyboard)

@dp.callback_query(F.data.startswith("confirm_"))
async def handle_exchange_confirmation(callback: types.CallbackQuery):
    """Handle exchange confirmation"""
    _, from_currency, to_currency, amount = callback.data.split("_")
    amount = float(amount)
    user_id = callback.from_user.id
    
    # Execute exchange
    success, message, transaction_info = await exchange_service.execute_exchange(
        user_id, from_currency, to_currency, amount
    )
    
    if success:
        result_text = f"""
✅ Обмен выполнен успешно!

📤 Отправлено: {transaction_info['amount']:.4f} {transaction_info['from_currency']}
📥 Получено: {transaction_info['total_amount']:.4f} {transaction_info['to_currency']}
💸 Комиссия: {transaction_info['fee']:.4f} {transaction_info['from_currency']}
📊 Курс: {transaction_info['rate']:.6f}
🕐 Время: {transaction_info.get('timestamp', 'Сейчас')}

Спасибо за использование нашего сервиса! 🎉
        """
    else:
        result_text = f"❌ Ошибка: {message}"
    
    await callback.message.edit_text(result_text, reply_markup=get_back_keyboard("back_to_main"))

# Back navigation handlers
@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    """Back to main menu"""
    await callback.message.edit_text(
        "🏠 Главное меню\nВыберите действие:",
        reply_markup=get_main_keyboard()
    )

@dp.callback_query(F.data == "back_to_currencies")
async def back_to_currencies(callback: types.CallbackQuery):
    """Back to currency selection"""
    await callback.message.edit_text(
        "💱 Выберите валюту для обмена:",
        reply_markup=get_currency_keyboard()
    )

@dp.callback_query(F.data.startswith("back_to_exchange_"))
async def back_to_exchange(callback: types.CallbackQuery):
    """Back to exchange selection"""
    from_currency = callback.data.split("_")[-1]
    await callback.message.edit_text(
        f"💱 Вы выбрали {from_currency}\nТеперь выберите валюту для получения:",
        reply_markup=get_exchange_keyboard(from_currency)
    )

@dp.callback_query(F.data.startswith("back_to_amount_"))
async def back_to_amount(callback: types.CallbackQuery):
    """Back to amount selection"""
    _, from_currency, to_currency = callback.data.split("_")
    rate = exchange_service.get_exchange_rate(from_currency, to_currency)
    rate_text = f"📊 Курс: 1 {from_currency} = {rate:.6f} {to_currency}\n\n"
    
    await callback.message.edit_text(
        f"💱 Обмен {from_currency} → {to_currency}\n{rate_text}Выберите сумму:",
        reply_markup=get_amount_keyboard(from_currency, to_currency)
    )

# Admin handlers
@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):
    """Show admin statistics"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Доступ запрещен")
        return
    
    # Get basic stats
    stats_text = "📊 Статистика системы:\n\n"
    stats_text += "🔹 Поддерживаемые валюты: 5\n"
    stats_text += "🔹 Комиссия: 2%\n"
    stats_text += "🔹 Минимальная сумма: $1\n"
    stats_text += "🔹 Максимальная сумма: $10,000\n\n"
    stats_text += "📈 Активные курсы обновляются каждые 5 минут"
    
    await callback.message.edit_text(stats_text, reply_markup=get_back_keyboard("back_to_admin"))

@dp.callback_query(F.data == "admin_balances")
async def admin_balances(callback: types.CallbackQuery):
    """Admin balance management"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Доступ запрещен")
        return
    
    await callback.message.edit_text(
        "💰 Управление балансами\n\n"
        "Функция в разработке...",
        reply_markup=get_back_keyboard("back_to_admin")
    )

@dp.callback_query(F.data == "admin_rates")
async def admin_rates(callback: types.CallbackQuery):
    """Admin rate management"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Доступ запрещен")
        return
    
    await callback.message.edit_text(
        "📈 Управление курсами\n\n"
        "Функция в разработке...",
        reply_markup=get_back_keyboard("back_to_admin")
    )

@dp.callback_query(F.data == "admin_users")
async def admin_users(callback: types.CallbackQuery):
    """Admin user management"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Доступ запрещен")
        return
    
    await callback.message.edit_text(
        "👥 Управление пользователями\n\n"
        "Функция в разработке...",
        reply_markup=get_back_keyboard("back_to_admin")
    )

@dp.callback_query(F.data == "back_to_admin")
async def back_to_admin(callback: types.CallbackQuery):
    """Back to admin menu"""
    await callback.message.edit_text(
        "⚙️ Админ панель:",
        reply_markup=get_admin_keyboard()
    )

# Cancel handlers
@dp.callback_query(F.data == "cancel_exchange")
async def cancel_exchange(callback: types.CallbackQuery):
    """Cancel exchange operation"""
    await callback.message.edit_text(
        "❌ Операция отменена",
        reply_markup=get_back_keyboard("back_to_main")
    )

# Error handler
@dp.errors()
async def errors_handler(update: types.Update, exception: Exception):
    """Handle errors"""
    logger.error(f"Exception while handling {update}: {exception}")
    try:
        if update.message:
            await update.message.answer("❌ Произошла ошибка. Попробуйте позже.")
        elif update.callback_query:
            await update.callback_query.answer("❌ Произошла ошибка")
    except:
        pass

async def main():
    """Main function"""
    # Start rate update task
    asyncio.create_task(exchange_service.update_rates_periodically())
    
    # Start bot
    logger.info("Starting bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())