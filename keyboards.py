from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import config

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Main menu keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎌 Генерировать кошелёк"), KeyboardButton(text="💰 Баланс")],
            [KeyboardButton(text="📥 Пополнить"), KeyboardButton(text="📤 Вывести")],
            [KeyboardButton(text="🔄 Свапнуть"), KeyboardButton(text="💹 Стейкинг")],
            [KeyboardButton(text="ℹ️ Инфо")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )
    return keyboard

def get_network_keyboard() -> InlineKeyboardMarkup:
    """Network selection keyboard for wallet generation"""
    builder = InlineKeyboardBuilder()
    
    networks = list(config.SUPPORTED_NETWORKS.keys())
    for i in range(0, len(networks), 2):
        row = []
        row.append(InlineKeyboardButton(
            text=f"{networks[i]}", 
            callback_data=f"generate_{networks[i]}"
        ))
        if i + 1 < len(networks):
            row.append(InlineKeyboardButton(
                text=f"{networks[i+1]}", 
                callback_data=f"generate_{networks[i+1]}"
            ))
        builder.row(*row)
    
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main"))
    return builder.as_markup()

def get_wallet_count_keyboard(network: str) -> InlineKeyboardMarkup:
    """Wallet count selection keyboard"""
    builder = InlineKeyboardBuilder()
    
    counts = [1, 3, 5, 10]
    for i in range(0, len(counts), 2):
        row = []
        row.append(InlineKeyboardButton(
            text=str(counts[i]), 
            callback_data=f"count_{network}_{counts[i]}"
        ))
        if i + 1 < len(counts):
            row.append(InlineKeyboardButton(
                text=str(counts[i+1]), 
                callback_data=f"count_{network}_{counts[i+1]}"
            ))
        builder.row(*row)
    
    builder.row(InlineKeyboardButton(text="✏️ Ввести вручную", callback_data=f"manual_count_{network}"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_networks"))
    return builder.as_markup()

def get_asset_keyboard(network: str, operation: str = "withdraw") -> InlineKeyboardMarkup:
    """Asset selection keyboard"""
    builder = InlineKeyboardBuilder()
    
    network_config = config.SUPPORTED_NETWORKS[network]
    symbol = network_config['symbol']
    
    # Add native token
    builder.row(InlineKeyboardButton(
        text=symbol, 
        callback_data=f"{operation}_{network}_{symbol}"
    ))
    
    # Add USDT if supported
    if network_config['supports_usdt']:
        builder.row(InlineKeyboardButton(
            text="USDT", 
            callback_data=f"{operation}_{network}_USDT"
        ))
    
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main"))
    return builder.as_markup()

def get_swap_keyboard(network: str) -> InlineKeyboardMarkup:
    """Swap direction keyboard"""
    builder = InlineKeyboardBuilder()
    
    network_config = config.SUPPORTED_NETWORKS[network]
    symbol = network_config['symbol']
    
    if network_config['supports_usdt']:
        builder.row(InlineKeyboardButton(
            text=f"{symbol} → USDT", 
            callback_data=f"swap_{network}_{symbol}_USDT"
        ))
        builder.row(InlineKeyboardButton(
            text=f"USDT → {symbol}", 
            callback_data=f"swap_{network}_USDT_{symbol}"
        ))
    
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main"))
    return builder.as_markup()

def get_staking_period_keyboard() -> InlineKeyboardMarkup:
    """Staking period selection keyboard"""
    builder = InlineKeyboardBuilder()
    
    periods = config.STAKING_PERIODS
    for period_key, period_data in periods.items():
        builder.row(InlineKeyboardButton(
            text=f"{period_data['months']} мес. ({period_data['rate']}%)", 
            callback_data=f"stake_period_{period_key}"
        ))
    
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main"))
    return builder.as_markup()

def get_staking_actions_keyboard() -> InlineKeyboardMarkup:
    """Staking actions keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(text="📊 Мои стейки", callback_data="my_stakes"))
    builder.row(InlineKeyboardButton(text="💹 Создать стейк", callback_data="create_stake"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main"))
    
    return builder.as_markup()

def get_stake_action_keyboard(stake_id: int) -> InlineKeyboardMarkup:
    """Individual stake action keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(
        text="⚠️ Досрочный вывод", 
        callback_data=f"early_withdraw_{stake_id}"
    ))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="my_stakes"))
    
    return builder.as_markup()

def get_confirm_keyboard(action: str, data: str) -> InlineKeyboardMarkup:
    """Confirmation keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_{action}_{data}"),
        InlineKeyboardButton(text="❌ Нет", callback_data="cancel_action")
    )
    
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

def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Admin keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"))
    builder.row(InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main"))
    
    return builder.as_markup()