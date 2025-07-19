import asyncio
import logging
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.utils.markdown import hbold, hcode

from config import BOT_TOKEN, ADMIN_IDS
from database import Database
from wallet_service import WalletService
from staking_service import StakingService
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
wallet_service = WalletService(db)
staking_service = StakingService(db, wallet_service)

# FSM States
class WalletGenerationStates(StatesGroup):
    waiting_for_count = State()

class WithdrawalStates(StatesGroup):
    waiting_for_wallet = State()
    waiting_for_amount = State()
    waiting_for_address = State()

class SwapStates(StatesGroup):
    waiting_for_wallet = State()
    waiting_for_amount = State()

class StakingStates(StatesGroup):
    waiting_for_wallet = State()
    waiting_for_amount = State()

# User states storage
user_states = {}

def escape_markdown(text: str) -> str:
    """Escape text for Markdown V2"""
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Start command handler"""
    telegram_id = message.from_user.id
    user = message.from_user
    
    # Check if user exists
    existing_user = db.get_user(telegram_id)
    if not existing_user:
        # Create new user
        new_user = db.create_user(telegram_id)
        if not new_user:
            await message.answer("❌ Ошибка создания пользователя")
            return
        
        welcome_text = f"""
🌸 Добро пожаловать, самурай\\! 🌸

Ваш аккаунт: {hcode(new_user['account_id'])}
Создан: {new_user['creation_date'][:19]}

Выберите действие ниже\\! 🗡️
        """
    else:
        welcome_text = f"""
🌸 С возвращением, самурай\\! 🌸

Ваш аккаунт: {hcode(existing_user['account_id'])}
Создан: {existing_user['creation_date'][:19]}

Выберите действие ниже\\! 🗡️
        """
    
    await message.answer(welcome_text, reply_markup=get_main_keyboard(), parse_mode="MarkdownV2")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Help command handler"""
    help_text = """
📚 Справка по использованию бота:

🎌 Генерировать кошельки:
• Создание кошельков для 8 блокчейн\\-сетей
• Поддержка ETH, TRX, SOL, BNB, DOGE, AVAX, POL, XRP
• Безопасное хранение приватных ключей

💰 Баланс:
• Проверка балансов по всем кошелькам
• Поддержка нативных токенов и USDT

📥 Пополнить:
• Получение адресов для пополнения
• Копирование адресов для переводов

📤 Вывести:
• Вывод средств с кошельков
• Поддержка ETH и TRX автоматически
• Ручная обработка для других сетей

🔄 Свапнуть:
• Обмен между нативными токенами и USDT
• Поддержка ETH/ERC20 и TRX/TRC20

💹 Стейкинг:
• Фиксированные периоды: 1, 3, 6, 9 месяцев
• Ставки: 16\\%, 18\\%, 20\\%, 22\\% годовых
• Досрочный вывод с штрафом 50\\%

🔒 Безопасность:
• Приватные ключи хранятся в БД
• Средства остаются в кошельках пользователей
• Все операции логируются

Для связи с поддержкой: @support
    """
    
    await message.answer(help_text, reply_markup=get_back_keyboard("back_to_main"), parse_mode="MarkdownV2")

@dp.message(F.text == "🎌 Генерировать кошелёк")
async def start_wallet_generation(message: types.Message):
    """Start wallet generation process"""
    await message.answer(
        "🎌 Выберите сеть для генерации кошелька:",
        reply_markup=get_network_keyboard()
    )

@dp.message(F.text == "💰 Баланс")
async def show_balance(message: types.Message):
    """Show user balance"""
    telegram_id = message.from_user.id
    user = db.get_user(telegram_id)
    
    if not user:
        await message.answer("❌ Пользователь не найден")
        return
    
    wallets = db.get_user_wallets(user['user_id'])
    
    if not wallets:
        await message.answer(
            "У вас ещё нет кошельков\\. Сгенерируйте их\\!",
            reply_markup=get_back_keyboard("back_to_main"),
            parse_mode="MarkdownV2"
        )
        return
    
    # Get balances
    balances = await wallet_service.get_all_balances(user['user_id'])
    
    if not balances:
        await message.answer("❌ Ошибка получения балансов")
        return
    
    balance_text = "💰 Ваши балансы:\n\n"
    
    for network, network_wallets in balances.items():
        network_name = config.SUPPORTED_NETWORKS[network]['name']
        balance_text += f"🌐 {network_name}:\n"
        
        for address, balance_data in network_wallets.items():
            balance_text += f"📍 {hcode(address[:10] + '...')}\n"
            
            # Native token balance
            native_balance = balance_data['native']
            if native_balance > 0:
                symbol = balance_data['symbol']
                balance_text += f"  • {symbol}: {native_balance:.6f}\n"
            
            # USDT balance
            if 'USDT' in balance_data and balance_data['USDT'] > 0:
                balance_text += f"  • USDT: {balance_data['USDT']:.6f}\n"
            
            balance_text += "\n"
    
    await message.answer(
        balance_text,
        reply_markup=get_back_keyboard("back_to_main"),
        parse_mode="MarkdownV2"
    )

@dp.message(F.text == "📥 Пополнить")
async def show_deposit_addresses(message: types.Message):
    """Show deposit addresses"""
    telegram_id = message.from_user.id
    user = db.get_user(telegram_id)
    
    if not user:
        await message.answer("❌ Пользователь не найден")
        return
    
    wallets = db.get_user_wallets(user['user_id'])
    
    if not wallets:
        await message.answer(
            "У вас нет кошельков для пополнения\\. Сгенерируйте их\\!",
            reply_markup=get_back_keyboard("back_to_main"),
            parse_mode="MarkdownV2"
        )
        return
    
    deposit_text = "📥 Адреса для пополнения:\n\n"
    
    for wallet in wallets:
        network_name = config.SUPPORTED_NETWORKS[wallet['network']]['name']
        deposit_text += f"🌐 {network_name}:\n"
        deposit_text += f"📍 {hcode(wallet['address'])}\n\n"
    
    await message.answer(
        deposit_text,
        reply_markup=get_back_keyboard("back_to_main"),
        parse_mode="MarkdownV2"
    )

@dp.message(F.text == "📤 Вывести")
async def start_withdrawal(message: types.Message):
    """Start withdrawal process"""
    telegram_id = message.from_user.id
    user = db.get_user(telegram_id)
    
    if not user:
        await message.answer("❌ Пользователь не найден")
        return
    
    wallets = db.get_user_wallets(user['user_id'])
    
    if not wallets:
        await message.answer(
            "У вас нет кошельков для вывода\\. Сгенерируйте их\\!",
            reply_markup=get_back_keyboard("back_to_main"),
            parse_mode="MarkdownV2"
        )
        return
    
    withdrawal_text = "📤 Выберите кошелек для вывода:\n\n"
    
    for wallet in wallets:
        network_name = config.SUPPORTED_NETWORKS[wallet['network']]['name']
        withdrawal_text += f"🌐 {network_name}:\n"
        withdrawal_text += f"📍 {hcode(wallet['address'])}\n\n"
    
    await message.answer(
        withdrawal_text + "Введите адрес кошелька:",
        reply_markup=get_back_keyboard("back_to_main"),
        parse_mode="MarkdownV2"
    )
    
    # Set state
    user_states[telegram_id] = {'action': 'withdrawal'}
    await WithdrawalStates.waiting_for_wallet.set()

@dp.message(F.text == "🔄 Свапнуть")
async def start_swap(message: types.Message):
    """Start swap process"""
    telegram_id = message.from_user.id
    user = db.get_user(telegram_id)
    
    if not user:
        await message.answer("❌ Пользователь не найден")
        return
    
    wallets = db.get_user_wallets(user['user_id'])
    
    # Filter wallets that support swaps (ETH and TRX)
    swap_wallets = [w for w in wallets if w['network'] in ['ETH', 'TRX']]
    
    if not swap_wallets:
        await message.answer(
            "У вас нет кошельков для свапа\\. Создайте кошельки ETH или TRX\\!",
            reply_markup=get_back_keyboard("back_to_main"),
            parse_mode="MarkdownV2"
        )
        return
    
    swap_text = "🔄 Выберите кошелек для свапа:\n\n"
    
    for wallet in swap_wallets:
        network_name = config.SUPPORTED_NETWORKS[wallet['network']]['name']
        swap_text += f"🌐 {network_name}:\n"
        swap_text += f"📍 {hcode(wallet['address'])}\n\n"
    
    await message.answer(
        swap_text + "Введите адрес кошелька:",
        reply_markup=get_back_keyboard("back_to_main"),
        parse_mode="MarkdownV2"
    )
    
    # Set state
    user_states[telegram_id] = {'action': 'swap'}
    await SwapStates.waiting_for_wallet.set()

@dp.message(F.text == "💹 Стейкинг")
async def show_staking_menu(message: types.Message):
    """Show staking menu"""
    await message.answer(
        "💹 Стейкинг:",
        reply_markup=get_staking_actions_keyboard()
    )

@dp.message(F.text == "ℹ️ Инфо")
async def show_info(message: types.Message):
    """Show bot information"""
    info_text = """
🌸 Информация о боте

Добро пожаловать в мир крипто\\-самураев\\! 🗡️

• Генерировать кошельки: 🎌 Генерировать кошелёк
• Проверять балансы: 💰 Баланс
• Пополнять: 📥 Пополнить
• Выводить: 📤 Вывести
• Свап: 🔄 Свапнуть
• Стейкинг: 💹 Стейкинг

Все данные в безопасности\\. Удачи\\! 🌸
    """
    
    await message.answer(
        info_text,
        reply_markup=get_back_keyboard("back_to_main"),
        parse_mode="MarkdownV2"
    )

# Callback handlers
@dp.callback_query(F.data.startswith("generate_"))
async def handle_network_selection(callback: types.CallbackQuery):
    """Handle network selection for wallet generation"""
    network = callback.data.split("_")[1]
    
    await callback.message.edit_text(
        f"🎌 Выберите количество кошельков для {network}:",
        reply_markup=get_wallet_count_keyboard(network)
    )

@dp.callback_query(F.data.startswith("count_"))
async def handle_wallet_count(callback: types.CallbackQuery):
    """Handle wallet count selection"""
    _, network, count = callback.data.split("_")
    count = int(count)
    
    await generate_wallets(callback, network, count)

@dp.callback_query(F.data.startswith("manual_count_"))
async def handle_manual_count(callback: types.CallbackQuery, state: FSMContext):
    """Handle manual count input"""
    network = callback.data.split("_")[2]
    
    await state.update_data(network=network)
    await state.set_state(WalletGenerationStates.waiting_for_count)
    
    await callback.message.edit_text(
        f"✏️ Введите количество кошельков для {network} \\(1\\-99\\):",
        reply_markup=get_back_keyboard("back_to_networks"),
        parse_mode="MarkdownV2"
    )

@dp.message(WalletGenerationStates.waiting_for_count)
async def handle_count_input(message: types.Message, state: FSMContext):
    """Handle count input"""
    try:
        count = int(message.text)
        if count < 1 or count > 99:
            await message.answer("❌ Введите корректное число от 1 до 99\\.")
            return
        
        data = await state.get_data()
        network = data["network"]
        
        await state.clear()
        await generate_wallets(message, network, count)
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректное число\\.")

async def generate_wallets(message_or_callback, network: str, count: int):
    """Generate wallets"""
    try:
        telegram_id = message_or_callback.from_user.id
        user = db.get_user(telegram_id)
        
        if not user:
            await message_or_callback.answer("❌ Пользователь не найден")
            return
        
        # Generate wallets
        wallets = wallet_service.generate_wallet(network, count)
        
        # Save to database
        for wallet in wallets:
            db.create_wallet(
                user['user_id'], wallet['network'], wallet['address'],
                wallet['private_key'], wallet['seed_phrase']
            )
        
        # Format response
        network_name = config.SUPPORTED_NETWORKS[network]['name']
        response_text = f"🗡️ Сгенерированы кошельки {network_name}:\n\n"
        
        for i, wallet in enumerate(wallets, 1):
            response_text += f"{i}\\. {hcode(wallet['address'])}\n"
        
        if isinstance(message_or_callback, types.Message):
            await message_or_callback.answer(
                response_text,
                reply_markup=get_back_keyboard("back_to_main"),
                parse_mode="MarkdownV2"
            )
        else:
            await message_or_callback.message.edit_text(
                response_text,
                reply_markup=get_back_keyboard("back_to_main"),
                parse_mode="MarkdownV2"
            )
            
    except Exception as e:
        logger.error(f"Error generating wallets: {e}")
        error_text = "❌ Ошибка генерации кошельков\\. Попробуйте снова\\."
        
        if isinstance(message_or_callback, types.Message):
            await message_or_callback.answer(error_text, parse_mode="MarkdownV2")
        else:
            await message_or_callback.message.edit_text(error_text, parse_mode="MarkdownV2")

# Withdrawal handlers
@dp.message(WithdrawalStates.waiting_for_wallet)
async def handle_withdrawal_wallet(message: types.Message, state: FSMContext):
    """Handle withdrawal wallet selection"""
    telegram_id = message.from_user.id
    user = db.get_user(telegram_id)
    
    if not user:
        await message.answer("❌ Пользователь не найден")
        await state.clear()
        return
    
    wallet_address = message.text.strip()
    wallet = db.get_wallet_by_address(user['user_id'], wallet_address)
    
    if not wallet:
        await message.answer("❌ Адрес не найден в вашем списке\\.")
        return
    
    await state.update_data(wallet_address=wallet_address, network=wallet['network'])
    
    # Show asset selection
    await message.answer(
        f"📤 Выберите актив для вывода:",
        reply_markup=get_asset_keyboard(wallet['network'], "withdraw")
    )
    
    await state.clear()

@dp.callback_query(F.data.startswith("withdraw_"))
async def handle_withdrawal_asset(callback: types.CallbackQuery, state: FSMContext):
    """Handle withdrawal asset selection"""
    _, network, asset = callback.data.split("_")
    
    await state.update_data(network=network, asset=asset)
    await state.set_state(WithdrawalStates.waiting_for_amount)
    
    network_name = config.SUPPORTED_NETWORKS[network]['name']
    min_fee = config.SUPPORTED_NETWORKS[network]['min_fee']
    
    await callback.message.edit_text(
        f"📤 Введите сумму {asset} для вывода:\n\n"
        f"Сеть: {network_name}\n"
        f"Минимальная комиссия: {min_fee} {asset}",
        reply_markup=get_back_keyboard("back_to_main"),
        parse_mode="MarkdownV2"
    )

@dp.message(WithdrawalStates.waiting_for_amount)
async def handle_withdrawal_amount(message: types.Message, state: FSMContext):
    """Handle withdrawal amount input"""
    try:
        amount = float(message.text)
        if amount <= 0:
            await message.answer("❌ Введите корректную положительную сумму\\.")
            return
        
        data = await state.get_data()
        network = data["network"]
        asset = data["asset"]
        wallet_address = data["wallet_address"]
        
        # Check balance
        current_balance = await wallet_service.get_balance(wallet_address, network, asset)
        if amount > current_balance:
            await message.answer(f"❌ Недостаточно {asset}\\. Баланс: {current_balance:.6f}")
            await state.clear()
            return
        
        await state.update_data(amount=amount)
        await state.set_state(WithdrawalStates.waiting_for_address)
        
        await message.answer(
            f"📤 Введите адрес получателя:",
            reply_markup=get_back_keyboard("back_to_main")
        )
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректное число\\.")

@dp.message(WithdrawalStates.waiting_for_address)
async def handle_withdrawal_address(message: types.Message, state: FSMContext):
    """Handle withdrawal address input"""
    data = await state.get_data()
    network = data["network"]
    asset = data["asset"]
    amount = data["amount"]
    wallet_address = data["wallet_address"]
    
    recipient_address = message.text.strip()
    
    # Validate address
    if not wallet_service.validate_address(recipient_address, network):
        await message.answer("❌ Неверный формат адреса\\.")
        await state.clear()
        return
    
    telegram_id = message.from_user.id
    user = db.get_user(telegram_id)
    
    # Create withdrawal log
    token_type = f"{asset} Withdrawal"
    success = db.create_withdrawal_log(
        user['user_id'], wallet_address, recipient_address,
        amount, token_type, network
    )
    
    if not success:
        await message.answer("❌ Ошибка создания запроса на вывод\\.")
        await state.clear()
        return
    
    # Handle different networks
    if network in ['ETH', 'TRX']:
        # Automatic withdrawal for ETH and TRX
        await message.answer("⏳ Отправляю транзакцию\\.\\.\\.")
        # Here you would implement actual withdrawal logic
        await message.answer(
            f"✅ Вывод инициирован\\! Токен: {asset}\\. Сумма: {amount}\\. TxID: pending\\.",
            parse_mode="MarkdownV2"
        )
    else:
        # Manual processing for other networks
        await message.answer(
            f"✅ Запрос на вывод отправлен на ручную обработку\\! Токен: {asset}\\. Сумма: {amount}\\.",
            parse_mode="MarkdownV2"
        )
    
    await state.clear()

# Swap handlers
@dp.message(SwapStates.waiting_for_wallet)
async def handle_swap_wallet(message: types.Message, state: FSMContext):
    """Handle swap wallet selection"""
    telegram_id = message.from_user.id
    user = db.get_user(telegram_id)
    
    if not user:
        await message.answer("❌ Пользователь не найден")
        await state.clear()
        return
    
    wallet_address = message.text.strip()
    wallet = db.get_wallet_by_address(user['user_id'], wallet_address)
    
    if not wallet or wallet['network'] not in ['ETH', 'TRX']:
        await message.answer("❌ Кошелек не найден или не поддерживает свапы\\.")
        return
    
    await state.update_data(wallet_address=wallet_address, network=wallet['network'])
    
    # Show swap options
    await message.answer(
        f"🔄 Выберите направление свапа:",
        reply_markup=get_swap_keyboard(wallet['network'])
    )
    
    await state.clear()

@dp.callback_query(F.data.startswith("swap_"))
async def handle_swap_direction(callback: types.CallbackQuery, state: FSMContext):
    """Handle swap direction selection"""
    _, network, from_asset, to_asset = callback.data.split("_")
    
    await state.update_data(network=network, from_asset=from_asset, to_asset=to_asset)
    await state.set_state(SwapStates.waiting_for_amount)
    
    await callback.message.edit_text(
        f"🔄 Введите сумму {from_asset} для свапа на {to_asset}:",
        reply_markup=get_back_keyboard("back_to_main"),
        parse_mode="MarkdownV2"
    )

@dp.message(SwapStates.waiting_for_amount)
async def handle_swap_amount(message: types.Message, state: FSMContext):
    """Handle swap amount input"""
    try:
        amount = float(message.text)
        if amount <= 0:
            await message.answer("❌ Введите корректную положительную сумму\\.")
            return
        
        data = await state.get_data()
        network = data["network"]
        from_asset = data["from_asset"]
        to_asset = data["to_asset"]
        wallet_address = data["wallet_address"]
        
        # Check balance
        current_balance = await wallet_service.get_balance(wallet_address, network, from_asset)
        if amount > current_balance:
            await message.answer(f"❌ Недостаточно {from_asset}\\. Баланс: {current_balance:.6f}")
            await state.clear()
            return
        
        # Confirm swap
        confirm_text = f"""
Подтверждение свапа:
Кошелек: {hcode(wallet_address[:10] + '...')}
Направление: {from_asset} → {to_asset}
Сумма: {amount}
Баланс: {current_balance:.6f}

Подтвердить\\?
        """
        
        await message.answer(
            confirm_text,
            reply_markup=get_confirm_keyboard("swap", f"{network}_{from_asset}_{to_asset}_{amount}"),
            parse_mode="MarkdownV2"
        )
        
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректное число\\.")

# Staking handlers
@dp.callback_query(F.data == "my_stakes")
async def show_my_stakes(callback: types.CallbackQuery):
    """Show user stakes"""
    telegram_id = callback.from_user.id
    user = db.get_user(telegram_id)
    
    if not user:
        await callback.answer("❌ Пользователь не найден")
        return
    
    stakes_info = await staking_service.get_user_stakes_info(user['user_id'])
    
    if not stakes_info:
        await callback.message.edit_text(
            "📊 У вас пока нет стейков\\.",
            reply_markup=get_back_keyboard("back_to_staking"),
            parse_mode="MarkdownV2"
        )
        return
    
    stakes_text = "📊 Мои стейки:\n\n"
    
    for stake in stakes_info:
        network_name = config.SUPPORTED_NETWORKS[stake['wallet_address'][:3]]['name']
        stakes_text += f"🌐 {network_name}:\n"
        stakes_text += f"📍 {hcode(stake['wallet_address'][:10] + '...')}\n"
        stakes_text += f"💰 {stake['amount']} {stake['asset']}\n"
        stakes_text += f"📈 Ставка: {stake['rate']}%\n"
        stakes_text += f"📅 Статус: {stake['status']}\n"
        stakes_text += f"🎯 Текущее вознаграждение: {stake['current_reward']:.6f} {stake['asset']}\n"
        
        if stake['status'] == 'active':
            stakes_text += f"⚠️ Штраф при досрочном выводе: {stake['penalty_amount']:.6f} {stake['asset']}\n"
        
        stakes_text += "\n"
    
    await callback.message.edit_text(
        stakes_text,
        reply_markup=get_back_keyboard("back_to_staking"),
        parse_mode="MarkdownV2"
    )

@dp.callback_query(F.data == "create_stake")
async def start_create_stake(callback: types.CallbackQuery):
    """Start create stake process"""
    await callback.message.edit_text(
        "💹 Выберите период стейкинга:",
        reply_markup=get_staking_period_keyboard()
    )

@dp.callback_query(F.data.startswith("stake_period_"))
async def handle_stake_period(callback: types.CallbackQuery, state: FSMContext):
    """Handle staking period selection"""
    period_key = callback.data.split("_")[2]
    
    await state.update_data(period_key=period_key)
    await state.set_state(StakingStates.waiting_for_wallet)
    
    period_data = config.STAKING_PERIODS[period_key]
    await callback.message.edit_text(
        f"💹 Введите адрес кошелька для стейкинга:\n\n"
        f"Период: {period_data['months']} месяцев\n"
        f"Ставка: {period_data['rate']}% годовых",
        reply_markup=get_back_keyboard("back_to_staking"),
        parse_mode="MarkdownV2"
    )

@dp.message(StakingStates.waiting_for_wallet)
async def handle_stake_wallet(message: types.Message, state: FSMContext):
    """Handle staking wallet selection"""
    telegram_id = message.from_user.id
    user = db.get_user(telegram_id)
    
    if not user:
        await message.answer("❌ Пользователь не найден")
        await state.clear()
        return
    
    wallet_address = message.text.strip()
    wallet = db.get_wallet_by_address(user['user_id'], wallet_address)
    
    if not wallet:
        await message.answer("❌ Кошелек не найден\\.")
        return
    
    await state.update_data(wallet_address=wallet_address, network=wallet['network'])
    
    # Show asset selection
    await message.answer(
        f"💹 Выберите актив для стейкинга:",
        reply_markup=get_asset_keyboard(wallet['network'], "stake")
    )
    
    await state.clear()

@dp.callback_query(F.data.startswith("stake_"))
async def handle_stake_asset(callback: types.CallbackQuery, state: FSMContext):
    """Handle staking asset selection"""
    _, network, asset = callback.data.split("_")
    
    await state.update_data(network=network, asset=asset)
    await state.set_state(StakingStates.waiting_for_amount)
    
    min_amount = config.STAKING_LIMITS['min_usdt'] if asset == 'USDT' else config.STAKING_LIMITS['min_amount']
    
    await callback.message.edit_text(
        f"💹 Введите сумму {asset} для стейкинга:\n\n"
        f"Минимальная сумма: {min_amount} {asset}",
        reply_markup=get_back_keyboard("back_to_staking"),
        parse_mode="MarkdownV2"
    )

@dp.message(StakingStates.waiting_for_amount)
async def handle_stake_amount(message: types.Message, state: FSMContext):
    """Handle staking amount input"""
    try:
        amount = float(message.text)
        if amount <= 0:
            await message.answer("❌ Введите корректную положительную сумму\\.")
            return
        
        data = await state.get_data()
        period_key = data["period_key"]
        wallet_address = data["wallet_address"]
        asset = data["asset"]
        
        telegram_id = message.from_user.id
        user = db.get_user(telegram_id)
        
        # Create stake
        success, message_text, stake_data = await staking_service.create_stake(
            user['user_id'], wallet_address, amount, asset, period_key
        )
        
        if success:
            period_data = config.STAKING_PERIODS[period_key]
            confirm_text = f"""
✅ Стейкинг успешно создан\\!

💰 Сумма: {amount} {asset}
📅 Период: {period_data['months']} месяцев
📈 Ставка: {period_data['rate']}% годовых
🎯 Ожидаемое вознаграждение: {stake_data['expected_reward']:.6f} {asset}
📅 Окончание: {stake_data['end_date'][:19]}

Спасибо за использование стейкинга\\! 🌸
            """
        else:
            confirm_text = f"❌ {message_text}"
        
        await message.answer(
            confirm_text,
            reply_markup=get_back_keyboard("back_to_main"),
            parse_mode="MarkdownV2"
        )
        
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректное число\\.")

# Confirmation handlers
@dp.callback_query(F.data.startswith("confirm_"))
async def handle_confirmation(callback: types.CallbackQuery):
    """Handle confirmations"""
    action_data = callback.data.split("_", 2)[2]
    
    if action_data.startswith("swap_"):
        await handle_swap_confirmation(callback, action_data)
    else:
        await callback.answer("❌ Неизвестное действие")

async def handle_swap_confirmation(callback: types.CallbackQuery, action_data: str):
    """Handle swap confirmation"""
    _, network, from_asset, to_asset, amount = action_data.split("_")
    amount = float(amount)
    
    telegram_id = callback.from_user.id
    user = db.get_user(telegram_id)
    
    # Create swap log
    token_type = f"SWAP: {from_asset} to {to_asset}"
    success = db.create_withdrawal_log(
        user['user_id'], "swap", "swap",
        amount, token_type, network, "pending"
    )
    
    if success:
        await callback.message.edit_text(
            "⏳ Ждите, ваш обмен в процессе обработки\\.",
            parse_mode="MarkdownV2"
        )
    else:
        await callback.message.edit_text(
            "❌ Ошибка создания свапа\\.",
            parse_mode="MarkdownV2"
        )

# Back navigation handlers
@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    """Back to main menu"""
    await callback.message.edit_text(
        "🏠 Главное меню\nВыберите действие:",
        reply_markup=get_main_keyboard()
    )

@dp.callback_query(F.data == "back_to_networks")
async def back_to_networks(callback: types.CallbackQuery):
    """Back to network selection"""
    await callback.message.edit_text(
        "🎌 Выберите сеть для генерации кошелька:",
        reply_markup=get_network_keyboard()
    )

@dp.callback_query(F.data == "back_to_staking")
async def back_to_staking(callback: types.CallbackQuery):
    """Back to staking menu"""
    await callback.message.edit_text(
        "💹 Стейкинг:",
        reply_markup=get_staking_actions_keyboard()
    )

# Cancel handlers
@dp.callback_query(F.data == "cancel_action")
async def cancel_action(callback: types.CallbackQuery):
    """Cancel action"""
    await callback.message.edit_text(
        "❌ Действие отменено",
        reply_markup=get_back_keyboard("back_to_main")
    )

# Error handler
@dp.errors()
async def errors_handler(update: types.Update, exception: Exception):
    """Handle errors"""
    logger.error(f"Exception while handling {update}: {exception}")
    try:
        if update.message:
            await update.message.answer("❌ Произошла ошибка\\. Попробуйте позже\\.", parse_mode="MarkdownV2")
        elif update.callback_query:
            await update.callback_query.answer("❌ Произошла ошибка")
    except:
        pass

async def main():
    """Main function"""
    logger.info("Starting Crypto Wallet Bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())