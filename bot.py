import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    filters,
    ContextTypes,
    ConversationHandler
)
from telegram.constants import ParseMode

from config import TELEGRAM_TOKEN
from database import get_db, create_user, get_user_by_telegram_id, get_user_wallets, create_wallet, log_withdrawal
from wallet_generator import generate_multiple_wallets
from balance_checker import balance_checker
from staking_manager import staking_manager
from utils import (
    escape_markdown, format_balance_message, format_wallet_list, validate_address,
    validate_amount, get_network_from_address, create_main_keyboard, create_network_keyboard,
    create_asset_keyboard, create_staking_period_keyboard, create_swap_keyboard
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
CHOOSING_NETWORK, CHOOSING_COUNT, CHOOSING_WALLET, CHOOSING_ASSET, ENTERING_AMOUNT, ENTERING_RECIPIENT = range(6)
CHOOSING_STAKE_PERIOD, ENTERING_STAKE_AMOUNT, CONFIRMING_STAKE = range(6, 9)
CHOOSING_SWAP_OPTION, ENTERING_SWAP_AMOUNT, CONFIRMING_SWAP = range(9, 12)

# User states storage
user_states = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    db = next(get_db())
    telegram_id = update.effective_user.id
    
    # Check if user exists
    user = get_user_by_telegram_id(db, telegram_id)
    if not user:
        user = create_user(db, telegram_id)
    
    # Welcome message
    welcome_text = (
        f"🌸 Добро пожаловать, самурай\\! 🌸\n"
        f"Ваш аккаунт: `{user.account_id}`\n"
        f"Создан: {user.creation_date.strftime('%d\\.%m\\.%Y %H:%M')}\n"
        f"Выберите действие ниже\\! 🗡️"
    )
    
    await update.message.reply_text(
        escape_markdown(welcome_text),
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=create_main_keyboard()
    )

async def handle_generate_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle wallet generation request"""
    await update.message.reply_text(
        "🎌 Выберите сеть для генерации кошелька:",
        reply_markup=create_network_keyboard()
    )
    return CHOOSING_NETWORK

async def handle_network_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle network selection for wallet generation"""
    query = update.callback_query
    await query.answer()
    
    network = query.data.split('_')[1]
    context.user_data['selected_network'] = network
    
    await query.edit_message_text(
        f"⚙️ Выбрана сеть: {network}\n"
        f"Введите количество кошельков для генерации \\(1\\-99\\):"
    )
    return CHOOSING_COUNT

async def handle_wallet_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle wallet count input"""
    try:
        count = int(update.message.text)
        if count < 1 or count > 99:
            await update.message.reply_text("Введите корректное число от 1 до 99\\.")
            return CHOOSING_COUNT
        
        network = context.user_data['selected_network']
        db = next(get_db())
        user = get_user_by_telegram_id(db, update.effective_user.id)
        
        # Generate wallets
        await update.message.reply_text(f"⏳ Генерирую {count} кошельков в сети {network}\\.\\.\\. Это может занять некоторое время\\.")
        
        generated_wallets = generate_multiple_wallets(network, count)
        
        # Save to database
        for wallet_data in generated_wallets:
            create_wallet(
                db=db,
                user_id=user.id,
                network=network,
                address=wallet_data['address'],
                private_key=wallet_data['private_key'],
                seed_phrase=wallet_data['seed_phrase']
            )
        
        # Format response
        response = f"🗡️ Сгенерированы кошельки:\n\n"
        for i, wallet_data in enumerate(generated_wallets, 1):
            response += f"{i}\\. `{wallet_data['address']}`\n"
        
        await update.message.reply_text(
            escape_markdown(response),
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=create_main_keyboard()
        )
        
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text("Введите корректное число от 1 до 99\\.")
        return CHOOSING_COUNT

async def handle_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle balance check request"""
    db = next(get_db())
    user = get_user_by_telegram_id(db, update.effective_user.id)
    wallets = get_user_wallets(db, user.id)
    
    if not wallets:
        await update.message.reply_text(
            "💰 У вас ещё нет кошельков\\. Сгенерируйте их\\!",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return
    
    await update.message.reply_text("💰 Собираю общий баланс по всем кошелькам\\.\\.\\.")
    
    # Get balances
    balances = {}
    for wallet in wallets:
        balance = balance_checker.get_balance(wallet.address, wallet.network)
        balances[wallet.address] = balance
    
    # Format and send response
    balance_message = format_balance_message(balances)
    await update.message.reply_text(
        balance_message,
        parse_mode=ParseMode.MARKDOWN_V2
    )

async def handle_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle deposit request"""
    db = next(get_db())
    user = get_user_by_telegram_id(db, update.effective_user.id)
    wallets = get_user_wallets(db, user.id)
    
    if not wallets:
        await update.message.reply_text(
            "📥 У вас нет кошельков для пополнения\\. Сгенерируйте их\\!",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return
    
    wallet_list = format_wallet_list(wallets)
    await update.message.reply_text(
        f"📥 Адреса для пополнения:\n\n{wallet_list}",
        parse_mode=ParseMode.MARKDOWN_V2
    )

async def handle_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle withdrawal request"""
    db = next(get_db())
    user = get_user_by_telegram_id(db, update.effective_user.id)
    wallets = get_user_wallets(db, user.id)
    
    if not wallets:
        await update.message.reply_text(
            "📤 У вас нет кошельков для вывода\\. Сгенерируйте их\\!",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return ConversationHandler.END
    
    wallet_list = format_wallet_list(wallets)
    await update.message.reply_text(
        f"📤 Выберите кошелек для вывода:\n\n{wallet_list}\n\nВведите адрес кошелька:",
        parse_mode=ParseMode.MARKDOWN_V2
    )
    return CHOOSING_WALLET

async def handle_withdraw_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle wallet selection for withdrawal"""
    address = update.message.text.strip()
    db = next(get_db())
    user = get_user_by_telegram_id(db, update.effective_user.id)
    wallets = get_user_wallets(db, user.id)
    
    # Find wallet
    selected_wallet = None
    for wallet in wallets:
        if wallet.address.lower() == address.lower():
            selected_wallet = wallet
            break
    
    if not selected_wallet:
        await update.message.reply_text("Адрес не найден в вашем списке\\.")
        return CHOOSING_WALLET
    
    context.user_data['withdraw_wallet'] = selected_wallet
    
    # Get available assets
    assets = get_available_assets(selected_wallet.network)
    if len(assets) == 1:
        context.user_data['withdraw_asset'] = assets[0]
        await update.message.reply_text(
            f"💰 Выбран актив: {assets[0]}\n"
            f"Введите сумму для вывода:"
        )
        return ENTERING_AMOUNT
    else:
        await update.message.reply_text(
            "Выберите актив для вывода:",
            reply_markup=create_asset_keyboard(selected_wallet.network)
        )
        return CHOOSING_ASSET

async def handle_withdraw_asset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle asset selection for withdrawal"""
    query = update.callback_query
    await query.answer()
    
    asset = query.data.split('_')[1]
    context.user_data['withdraw_asset'] = asset
    
    await query.edit_message_text(f"💰 Выбран актив: {asset}\nВведите сумму для вывода:")
    return ENTERING_AMOUNT

async def handle_withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle withdrawal amount input"""
    amount_str = update.message.text.strip()
    amount = validate_amount(amount_str)
    
    if not amount:
        await update.message.reply_text("Введите корректную положительную сумму\\.")
        return ENTERING_AMOUNT
    
    context.user_data['withdraw_amount'] = amount
    
    await update.message.reply_text("Введите адрес получателя:")
    return ENTERING_RECIPIENT

async def handle_withdraw_recipient(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle recipient address input"""
    recipient = update.message.text.strip()
    wallet = context.user_data['withdraw_wallet']
    asset = context.user_data['withdraw_asset']
    amount = context.user_data['withdraw_amount']
    
    # Validate recipient address
    if not validate_address(recipient, wallet.network):
        await update.message.reply_text("Неверный формат адреса\\.")
        return ENTERING_RECIPIENT
    
    # Log withdrawal
    db = next(get_db())
    user = get_user_by_telegram_id(db, update.effective_user.id)
    
    log_withdrawal(
        db=db,
        user_id=user.id,
        from_address=wallet.address,
        to_address=recipient,
        amount=amount,
        token_type=asset,
        network=wallet.network,
        status='pending'
    )
    
    await update.message.reply_text(
        f"✅ Запрос на вывод отправлен на ручную обработку\\!\n"
        f"Токен: {asset}\n"
        f"Сумма: {amount}",
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=create_main_keyboard()
    )
    
    return ConversationHandler.END

async def handle_swap(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle swap request"""
    db = next(get_db())
    user = get_user_by_telegram_id(db, update.effective_user.id)
    wallets = get_user_wallets(db, user.id)
    
    if not wallets:
        await update.message.reply_text(
            "🔄 У вас нет кошельков для свапа\\.",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return ConversationHandler.END
    
    wallet_list = format_wallet_list(wallets)
    await update.message.reply_text(
        f"🔄 Выберите кошелек для свапа:\n\n{wallet_list}\n\nВведите адрес кошелька:",
        parse_mode=ParseMode.MARKDOWN_V2
    )
    return CHOOSING_WALLET

async def handle_staking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle staking request"""
    db = next(get_db())
    user = get_user_by_telegram_id(db, update.effective_user.id)
    wallets = get_user_wallets(db, user.id)
    
    if not wallets:
        await update.message.reply_text(
            "💹 У вас нет кошельков для стейкинга\\.",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return ConversationHandler.END
    
    wallet_list = format_wallet_list(wallets)
    await update.message.reply_text(
        f"💹 Выберите кошелек для стейкинга:\n\n{wallet_list}\n\nВведите адрес кошелька:",
        parse_mode=ParseMode.MARKDOWN_V2
    )
    return CHOOSING_WALLET

async def handle_my_stakes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle my stakes request"""
    db = next(get_db())
    user = get_user_by_telegram_id(db, update.effective_user.id)
    stakes = staking_manager.get_user_stakes(db, user.id)
    
    if not stakes:
        await update.message.reply_text(
            "📋 У вас нет активных стейков\\.",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return
    
    message = "📋 Ваши активные стейки:\n\n"
    for stake in stakes:
        summary = staking_manager.get_stake_summary(stake)
        message += f"*ID:* {summary['id']}\n"
        message += f"*Кошелек:* `{summary['wallet_address']}`\n"
        message += f"*Актив:* {summary['asset']}\n"
        message += f"*Сумма:* {summary['amount']:.8f}\n"
        message += f"*Ставка:* {summary['rate']}%\n"
        message += f"*Текущее вознаграждение:* {summary['current_reward']:.8f}\n"
        message += f"*Дней осталось:* {summary['days_remaining']}\n\n"
    
    await update.message.reply_text(
        escape_markdown(message),
        parse_mode=ParseMode.MARKDOWN_V2
    )

async def handle_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle info request"""
    info_text = (
        "🌸 *Информация о боте*\n"
        "Добро пожаловать в мир крипто\\-самураев\\! 🗡️\n\n"
        "• Генерировать кошельки: 🎌 Генерировать кошелёк\n"
        "• Проверять балансы: 💰 Баланс\n"
        "• Пополнять: 📥 Пополнить\n"
        "• Выводить: 📤 Вывести\n"
        "• Свап: 🔄 Свапнуть\n"
        "• Стейкинг: 💹 Стейкинг\n"
        "Все данные в безопасности\\. Удачи\\! 🌸"
    )
    
    await update.message.reply_text(
        escape_markdown(info_text),
        parse_mode=ParseMode.MARKDOWN_V2
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages"""
    text = update.message.text
    
    if text == "🎌 Генерировать кошелёк":
        await handle_generate_wallet(update, context)
    elif text == "💰 Баланс":
        await handle_balance(update, context)
    elif text == "📥 Пополнить":
        await handle_deposit(update, context)
    elif text == "📤 Вывести":
        await handle_withdraw(update, context)
    elif text == "🔄 Свапнуть":
        await handle_swap(update, context)
    elif text == "💹 Стейкинг":
        await handle_staking(update, context)
    elif text == "📋 Мои стейки":
        await handle_my_stakes(update, context)
    elif text == "ℹ️ Инфо":
        await handle_info(update, context)
    else:
        await update.message.reply_text(
            "Используйте кнопки меню для навигации\\.",
            parse_mode=ParseMode.MARKDOWN_V2
        )

def main() -> None:
    """Start the bot"""
    # Initialize database
    from database import init_db
    init_db()
    
    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add conversation handler for wallet generation
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🎌 Генерировать кошелёк$"), handle_generate_wallet)],
        states={
            CHOOSING_NETWORK: [CallbackQueryHandler(handle_network_choice, pattern="^network_")],
            CHOOSING_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wallet_count)],
        },
        fallbacks=[],
    )
    
    # Add conversation handler for withdrawal
    withdraw_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📤 Вывести$"), handle_withdraw)],
        states={
            CHOOSING_WALLET: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_withdraw_wallet)],
            CHOOSING_ASSET: [CallbackQueryHandler(handle_withdraw_asset, pattern="^asset_")],
            ENTERING_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_withdraw_amount)],
            ENTERING_RECIPIENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_withdraw_recipient)],
        },
        fallbacks=[],
    )
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(withdraw_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()