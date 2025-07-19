import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS', '').split(',') if id]

# Database Configuration
DATABASE_PATH = 'crypto_wallet_bot.db'

# Supported Networks and Assets
SUPPORTED_NETWORKS = {
    'ETH': {
        'name': 'Ethereum',
        'symbol': 'ETH',
        'decimals': 18,
        'min_fee': 0.001,
        'supports_usdt': True,
        'rpc_url': 'https://mainnet.infura.io/v3/YOUR_INFURA_KEY',
        'usdt_contract': '0xdAC17F958D2ee523a2206206994597C13D831ec7'
    },
    'TRX': {
        'name': 'Tron',
        'symbol': 'TRX',
        'decimals': 6,
        'min_fee': 0.1,
        'supports_usdt': True,
        'rpc_url': 'https://api.trongrid.io',
        'usdt_contract': 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t'
    },
    'SOL': {
        'name': 'Solana',
        'symbol': 'SOL',
        'decimals': 9,
        'min_fee': 0,
        'supports_usdt': False,
        'rpc_url': 'https://api.mainnet-beta.solana.com'
    },
    'BNB': {
        'name': 'Binance Smart Chain',
        'symbol': 'BNB',
        'decimals': 18,
        'min_fee': 0,
        'supports_usdt': False,
        'rpc_url': 'https://bsc-dataseed.binance.org'
    },
    'DOGE': {
        'name': 'Dogecoin',
        'symbol': 'DOGE',
        'decimals': 8,
        'min_fee': 0,
        'supports_usdt': False,
        'rpc_url': 'https://sochain.com/api/v2'
    },
    'AVAX': {
        'name': 'Avalanche',
        'symbol': 'AVAX',
        'decimals': 18,
        'min_fee': 0,
        'supports_usdt': False,
        'rpc_url': 'https://api.avax.network/ext/bc/C/rpc'
    },
    'POL': {
        'name': 'Polygon',
        'symbol': 'POL',
        'decimals': 18,
        'min_fee': 0,
        'supports_usdt': False,
        'rpc_url': 'https://polygon-rpc.com'
    },
    'XRP': {
        'name': 'Ripple',
        'symbol': 'XRP',
        'decimals': 6,
        'min_fee': 0,
        'supports_usdt': False,
        'rpc_url': 'https://xrpscan.com/api'
    }
}

# Staking Configuration
STAKING_PERIODS = {
    '1_month': {'months': 1, 'rate': 16, 'days': 30},
    '3_months': {'months': 3, 'rate': 18, 'days': 90},
    '6_months': {'months': 6, 'rate': 20, 'days': 180},
    '9_months': {'months': 9, 'rate': 22, 'days': 270}
}

STAKING_LIMITS = {
    'min_amount': 0.01,
    'min_usdt': 1.0,
    'max_active_stakes': 10,
    'early_withdrawal_penalty': 0.5  # 50%
}

# Security Configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')

# API Keys (optional)
INFURA_KEY = os.getenv('INFURA_KEY', '')
TRONGRID_KEY = os.getenv('TRONGRID_KEY', '')