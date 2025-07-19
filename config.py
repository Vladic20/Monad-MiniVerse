import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/crypto_bot')

# Blockchain APIs Configuration
INFURA_URL = os.getenv('INFURA_URL', 'https://mainnet.infura.io/v3/YOUR_INFURA_KEY')
TRONGRID_API_KEY = os.getenv('TRONGRID_API_KEY')
SOLANA_RPC_URL = os.getenv('SOLANA_RPC_URL', 'https://api.mainnet-beta.solana.com')

# Network RPC URLs
NETWORK_RPC_URLS = {
    'ETH': INFURA_URL,
    'BSC': 'https://bsc-dataseed.binance.org/',
    'AVAX': 'https://api.avax.network/ext/bc/C/rpc',
    'POL': 'https://polygon-rpc.com/',
}

# Token Contracts
USDT_CONTRACTS = {
    'ETH': '0xdAC17F958D2ee523a2206206994597C13D831ec7',  # USDT ERC20
    'TRX': 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t',  # USDT TRC20
}

# Minimum withdrawal amounts and fees
MIN_WITHDRAWAL = {
    'ETH': 0.001,
    'TRX': 0.1,
    'SOL': 0.001,
    'BNB': 0.001,
    'DOGE': 1,
    'AVAX': 0.001,
    'POL': 0.001,
    'XRP': 0.1,
}

NETWORK_FEES = {
    'ETH': 0.001,
    'TRX': 0.1,
    'SOL': 0,
    'BNB': 0,
    'DOGE': 0,
    'AVAX': 0,
    'POL': 0,
    'XRP': 0,
}

# Staking configuration
STAKING_PERIODS = {
    '1_month': {'months': 1, 'rate': 16},
    '3_months': {'months': 3, 'rate': 18},
    '6_months': {'months': 6, 'rate': 20},
    '9_months': {'months': 9, 'rate': 22},
}

MIN_STAKING_AMOUNTS = {
    'ETH': 0.01,
    'TRX': 1,
    'SOL': 0.01,
    'BNB': 0.01,
    'DOGE': 1,
    'AVAX': 0.01,
    'POL': 0.01,
    'XRP': 1,
    'USDT': 1,
}

MAX_ACTIVE_STAKES = 10
EARLY_WITHDRAWAL_PENALTY = 0.5  # 50%

# Supported networks and assets
SUPPORTED_NETWORKS = ['ETH', 'TRX', 'SOL', 'BNB', 'DOGE', 'AVAX', 'POL', 'XRP']
SUPPORTED_ASSETS = {
    'ETH': ['ETH', 'USDT'],
    'TRX': ['TRX', 'USDT'],
    'SOL': ['SOL'],
    'BNB': ['BNB'],
    'DOGE': ['DOGE'],
    'AVAX': ['AVAX'],
    'POL': ['POL'],
    'XRP': ['XRP'],
}

# Swap supported networks
SWAP_SUPPORTED_NETWORKS = ['ETH', 'TRX']