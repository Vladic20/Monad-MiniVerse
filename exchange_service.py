import random
import asyncio
from typing import Dict, Optional, Tuple
from database import Database
import config

class ExchangeService:
    def __init__(self, database: Database):
        self.db = database
        self.exchange_rates = self._initialize_rates()
    
    def _initialize_rates(self) -> Dict[str, float]:
        """Initialize default exchange rates"""
        rates = {
            'USD_EUR': 0.85,
            'USD_RUB': 95.0,
            'USD_BTC': 0.000025,
            'USD_ETH': 0.0004,
            'EUR_USD': 1.18,
            'EUR_RUB': 112.0,
            'EUR_BTC': 0.00003,
            'EUR_ETH': 0.00047,
            'RUB_USD': 0.0105,
            'RUB_EUR': 0.0089,
            'RUB_BTC': 0.00000026,
            'RUB_ETH': 0.0000042,
            'BTC_USD': 40000.0,
            'BTC_EUR': 34000.0,
            'BTC_RUB': 3800000.0,
            'BTC_ETH': 16.0,
            'ETH_USD': 2500.0,
            'ETH_EUR': 2125.0,
            'ETH_RUB': 237500.0,
            'ETH_BTC': 0.0625
        }
        
        # Initialize rates in database
        for pair, rate in rates.items():
            from_curr, to_curr = pair.split('_')
            self.db.update_exchange_rate(from_curr, to_curr, rate)
        
        return rates
    
    def get_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """Get current exchange rate"""
        if from_currency == to_currency:
            return 1.0
        
        # Try to get from database first
        rate = self.db.get_exchange_rate(from_currency, to_currency)
        if rate:
            return rate
        
        # Calculate inverse rate if available
        inverse_rate = self.db.get_exchange_rate(to_currency, from_currency)
        if inverse_rate:
            return 1 / inverse_rate
        
        # Return default rate from memory
        pair = f"{from_currency}_{to_currency}"
        if pair in self.exchange_rates:
            return self.exchange_rates[pair]
        
        # Calculate through USD if both currencies are supported
        if from_currency in config.SUPPORTED_CURRENCIES and to_currency in config.SUPPORTED_CURRENCIES:
            usd_from = self.get_exchange_rate(from_currency, 'USD')
            usd_to = self.get_exchange_rate('USD', to_currency)
            return usd_from * usd_to
        
        return 1.0
    
    def calculate_exchange(self, from_currency: str, to_currency: str, amount: float) -> Tuple[float, float, float]:
        """Calculate exchange with fee"""
        rate = self.get_exchange_rate(from_currency, to_currency)
        fee = amount * config.EXCHANGE_FEE
        total_amount = (amount - fee) * rate
        
        return total_amount, fee, rate
    
    def validate_exchange(self, user_id: int, from_currency: str, amount: float) -> Tuple[bool, str]:
        """Validate exchange request"""
        user = self.db.get_user(user_id)
        if not user:
            return False, "Пользователь не найден"
        
        # Check amount limits
        if amount < config.MIN_TRADE_AMOUNT:
            return False, f"Минимальная сумма обмена: {config.MIN_TRADE_AMOUNT}"
        
        if amount > config.MAX_TRADE_AMOUNT:
            return False, f"Максимальная сумма обмена: {config.MAX_TRADE_AMOUNT}"
        
        # Check user balance
        balance_key = f"balance_{from_currency.lower()}"
        current_balance = user.get(balance_key, 0.0)
        
        if current_balance < amount:
            return False, f"Недостаточно средств. Баланс {from_currency}: {current_balance}"
        
        return True, "OK"
    
    async def execute_exchange(self, user_id: int, from_currency: str, 
                             to_currency: str, amount: float) -> Tuple[bool, str, Dict]:
        """Execute exchange transaction"""
        # Validate request
        is_valid, message = self.validate_exchange(user_id, from_currency, amount)
        if not is_valid:
            return False, message, {}
        
        # Calculate exchange
        total_amount, fee, rate = self.calculate_exchange(from_currency, to_currency, amount)
        
        # Update balances
        success1 = self.db.update_balance(user_id, from_currency, -amount)
        success2 = self.db.update_balance(user_id, to_currency, total_amount)
        
        if not (success1 and success2):
            return False, "Ошибка обновления баланса", {}
        
        # Create transaction record
        self.db.create_transaction(user_id, from_currency, to_currency, 
                                 amount, rate, fee, total_amount)
        
        transaction_info = {
            'from_currency': from_currency,
            'to_currency': to_currency,
            'amount': amount,
            'total_amount': total_amount,
            'rate': rate,
            'fee': fee
        }
        
        return True, "Обмен выполнен успешно", transaction_info
    
    def get_user_balance(self, user_id: int) -> Dict[str, float]:
        """Get user balance for all currencies"""
        user = self.db.get_user(user_id)
        if not user:
            return {}
        
        return {
            'USD': user['balance_usd'],
            'EUR': user['balance_eur'],
            'RUB': user['balance_rub'],
            'BTC': user['balance_btc'],
            'ETH': user['balance_eth']
        }
    
    async def update_rates_periodically(self):
        """Update exchange rates periodically with small variations"""
        while True:
            try:
                # Simulate market fluctuations
                for pair in self.exchange_rates:
                    current_rate = self.exchange_rates[pair]
                    # Add small random variation (±2%)
                    variation = random.uniform(-0.02, 0.02)
                    new_rate = current_rate * (1 + variation)
                    
                    from_curr, to_curr = pair.split('_')
                    self.db.update_exchange_rate(from_curr, to_curr, new_rate)
                    self.exchange_rates[pair] = new_rate
                
                await asyncio.sleep(300)  # Update every 5 minutes
            except Exception as e:
                print(f"Error updating rates: {e}")
                await asyncio.sleep(60)