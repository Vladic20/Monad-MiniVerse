from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import config

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Main menu keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💰 Баланс"), KeyboardButton(text="💱 Обмен валют")],
            [KeyboardButton(text="📊 Курсы валют"), KeyboardButton(text="📈 История операций")],
            [KeyboardButton(text="ℹ️ Помощь"), KeyboardButton(text="⚙️ Настройки")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )
    return keyboard

def get_currency_keyboard() -> InlineKeyboardMarkup:
    """Currency selection keyboard"""
    builder = InlineKeyboardBuilder()
    
    currencies = config.SUPPORTED_CURRENCIES
    for i in range(0, len(currencies), 2):
        row = []
        row.append(InlineKeyboardButton(text=currencies[i], callback_data=f"currency_{currencies[i]}"))
        if i + 1 < len(currencies):
            row.append(InlineKeyboardButton(text=currencies[i+1], callback_data=f"currency_{currencies[i+1]}"))
        builder.row(*row)
    
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main"))
    return builder.as_markup()

def get_exchange_keyboard(from_currency: str) -> InlineKeyboardMarkup:
    """Exchange target currency keyboard"""
    builder = InlineKeyboardBuilder()
    
    currencies = [curr for curr in config.SUPPORTED_CURRENCIES if curr != from_currency]
    for i in range(0, len(currencies), 2):
        row = []
        row.append(InlineKeyboardButton(text=currencies[i], callback_data=f"exchange_{from_currency}_{currencies[i]}"))
        if i + 1 < len(currencies):
            row.append(InlineKeyboardButton(text=currencies[i+1], callback_data=f"exchange_{from_currency}_{currencies[i+1]}"))
        builder.row(*row)
    
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_currencies"))
    return builder.as_markup()

def get_amount_keyboard(from_currency: str, to_currency: str) -> InlineKeyboardMarkup:
    """Quick amount selection keyboard"""
    builder = InlineKeyboardBuilder()
    
    amounts = [10, 50, 100, 500, 1000]
    for i in range(0, len(amounts), 3):
        row = []
        for j in range(3):
            if i + j < len(amounts):
                amount = amounts[i + j]
                row.append(InlineKeyboardButton(
                    text=str(amount), 
                    callback_data=f"amount_{from_currency}_{to_currency}_{amount}"
                ))
        builder.row(*row)
    
    builder.row(InlineKeyboardButton(text="✏️ Ввести вручную", callback_data=f"manual_amount_{from_currency}_{to_currency}"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=f"back_to_exchange_{from_currency}"))
    return builder.as_markup()

def get_confirm_keyboard(from_currency: str, to_currency: str, amount: float) -> InlineKeyboardMarkup:
    """Confirmation keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_{from_currency}_{to_currency}_{amount}"),
        InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_exchange")
    )
    
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=f"back_to_amount_{from_currency}_{to_currency}"))
    return builder.as_markup()

def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Settings keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(text="🔔 Уведомления", callback_data="settings_notifications"))
    builder.row(InlineKeyboardButton(text="🌍 Язык", callback_data="settings_language"))
    builder.row(InlineKeyboardButton(text="🔒 Безопасность", callback_data="settings_security"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main"))
    
    return builder.as_markup()

def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Admin keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"))
    builder.row(InlineKeyboardButton(text="💰 Управление балансами", callback_data="admin_balances"))
    builder.row(InlineKeyboardButton(text="📈 Управление курсами", callback_data="admin_rates"))
    builder.row(InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main"))
    
    return builder.as_markup()

def get_back_keyboard(callback_data: str) -> InlineKeyboardMarkup:
    """Simple back keyboard"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=callback_data))
    return builder.as_markup()

def get_yes_no_keyboard(callback_prefix: str) -> InlineKeyboardMarkup:
    """Yes/No keyboard"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да", callback_data=f"{callback_prefix}_yes"),
        InlineKeyboardButton(text="❌ Нет", callback_data=f"{callback_prefix}_no")
    )
    return builder.as_markup()