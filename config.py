import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS', '').split(',') if id]

# Database Configuration
DATABASE_PATH = 'exchange_bot.db'

# Exchange Configuration
SUPPORTED_CURRENCIES = ['USD', 'EUR', 'RUB', 'BTC', 'ETH']
MIN_TRADE_AMOUNT = 1.0
MAX_TRADE_AMOUNT = 10000.0
EXCHANGE_FEE = 0.02  # 2% fee

# Security Configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')