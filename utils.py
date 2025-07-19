import re
from typing import Dict, List, Optional
from config import SUPPORTED_NETWORKS, SUPPORTED_ASSETS, SWAP_SUPPORTED_NETWORKS

def escape_markdown(text: str) -> str:
    """Escape text for Markdown V2"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

def format_balance_message(balances: Dict[str, Dict[str, float]]) -> str:
    """Format balance message for Telegram"""
    if not balances:
        return "💰 У вас ещё нет кошельков\\. Сгенерируйте их\\!"
    
    message = "💰 Ваши балансы:\n\n"
    
    for address, balance_data in balances.items():
        message += f"*Адрес:* `{address}`\n"
        for asset, amount in balance_data.items():
            if amount > 0:
                message += f" \\- {asset}: {amount:.8f}\n"
        message += "\n"
    
    return escape_markdown(message)

def format_wallet_list(wallets: List) -> str:
    """Format wallet list for display"""
    if not wallets:
        return "У вас нет кошельков\\."
    
    message = "📋 Ваши кошельки:\n\n"
    for wallet in wallets:
        message += f"*{wallet\\.network}*\n"
        message += f"`{wallet\\.address}`\n\n"
    
    return escape_markdown(message)

def format_staking_summary(stake_summary: Dict) -> str:
    """Format staking summary for display"""
    message = f"*Кошелек:* `{stake_summary['wallet_address']}`\n"
    message += f"*Актив:* {stake_summary['asset']}\n"
    message += f"*Сумма:* {stake_summary['amount']:.8f}\n"
    message += f"*Срок:* {stake_summary['months']} месяцев\n"
    message += f"*Ставка:* {stake_summary['rate']}%\n"
    message += f"*Текущее вознаграждение:* {stake_summary['current_reward']:.8f}\n"
    message += f"*При досрочном выводе:* {stake_summary['penalty_amount']:.8f}\n"
    message += f"*Дней осталось:* {stake_summary['days_remaining']}"
    
    return escape_markdown(message)

def validate_address(address: str, network: str) -> bool:
    """Validate cryptocurrency address format"""
    patterns = {
        'ETH': r'^0x[a-fA-F0-9]{40}$',
        'TRX': r'^T[a-zA-Z0-9]{33}$',
        'SOL': r'^[1-9A-HJ-NP-Za-km-z]{32,44}$',
        'BNB': r'^0x[a-fA-F0-9]{40}$',
        'DOGE': r'^D[a-zA-Z0-9]{33}$',
        'AVAX': r'^0x[a-fA-F0-9]{40}$',
        'POL': r'^0x[a-fA-F0-9]{40}$',
        'XRP': r'^r[a-zA-Z0-9]{25,34}$',
    }
    
    if network not in patterns:
        return False
    
    return bool(re.match(patterns[network], address))

def validate_amount(amount_str: str) -> Optional[float]:
    """Validate and convert amount string to float"""
    try:
        amount = float(amount_str)
        if amount <= 0:
            return None
        return amount
    except ValueError:
        return None

def get_network_from_address(address: str) -> Optional[str]:
    """Determine network from address format"""
    for network, pattern in {
        'ETH': r'^0x[a-fA-F0-9]{40}$',
        'TRX': r'^T[a-zA-Z0-9]{33}$',
        'SOL': r'^[1-9A-HJ-NP-Za-km-z]{32,44}$',
        'BNB': r'^0x[a-fA-F0-9]{40}$',
        'DOGE': r'^D[a-zA-Z0-9]{33}$',
        'AVAX': r'^0x[a-fA-F0-9]{40}$',
        'POL': r'^0x[a-fA-F0-9]{40}$',
        'XRP': r'^r[a-zA-Z0-9]{25,34}$',
    }.items():
        if re.match(pattern, address):
            return network
    return None

def get_available_assets(network: str) -> List[str]:
    """Get available assets for network"""
    return SUPPORTED_ASSETS.get(network, [])

def is_swap_supported(network: str) -> bool:
    """Check if swap is supported for network"""
    return network in SWAP_SUPPORTED_NETWORKS

def format_swap_options(network: str) -> List[str]:
    """Get swap options for network"""
    if not is_swap_supported(network):
        return []
    
    assets = get_available_assets(network)
    if len(assets) < 2:
        return []
    
    options = []
    for i, asset1 in enumerate(assets):
        for asset2 in assets[i+1:]:
            options.append(f"{asset1}→{asset2}")
            options.append(f"{asset2}→{asset1}")
    
    return options

def create_main_keyboard():
    """Create main menu keyboard"""
    from telegram import ReplyKeyboardMarkup, KeyboardButton
    
    keyboard = [
        [
            KeyboardButton("🎌 Генерировать кошелёк"),
            KeyboardButton("💰 Баланс")
        ],
        [
            KeyboardButton("📥 Пополнить"),
            KeyboardButton("📤 Вывести")
        ],
        [
            KeyboardButton("🔄 Свапнуть"),
            KeyboardButton("💹 Стейкинг")
        ],
        [
            KeyboardButton("📋 Мои стейки"),
            KeyboardButton("ℹ️ Инфо")
        ]
    ]
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def create_network_keyboard():
    """Create network selection keyboard"""
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = []
    for network in SUPPORTED_NETWORKS:
        keyboard.append([InlineKeyboardButton(network, callback_data=f"network_{network}")])
    
    return InlineKeyboardMarkup(keyboard)

def create_asset_keyboard(network: str):
    """Create asset selection keyboard"""
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    
    assets = get_available_assets(network)
    keyboard = []
    for asset in assets:
        keyboard.append([InlineKeyboardButton(asset, callback_data=f"asset_{asset}")])
    
    return InlineKeyboardMarkup(keyboard)

def create_staking_period_keyboard():
    """Create staking period selection keyboard"""
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    from config import STAKING_PERIODS
    
    keyboard = []
    for period_key, period_info in STAKING_PERIODS.items():
        text = f"{period_info['months']} месяцев ({period_info['rate']}%)"
        keyboard.append([InlineKeyboardButton(text, callback_data=f"period_{period_key}")])
    
    return InlineKeyboardMarkup(keyboard)

def create_swap_keyboard(network: str):
    """Create swap options keyboard"""
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    
    options = format_swap_options(network)
    keyboard = []
    for option in options:
        keyboard.append([InlineKeyboardButton(option, callback_data=f"swap_{option}")])
    
    return InlineKeyboardMarkup(keyboard)