#!/usr/bin/env python3
"""
Примеры использования Crypto Wallet Telegram Bot
"""

import asyncio
from database import init_db, get_db, create_user, create_wallet, get_user_wallets
from wallet_generator import generate_wallet, generate_multiple_wallets
from balance_checker import balance_checker
from staking_manager import staking_manager
from withdrawal_manager import withdrawal_manager
from utils import validate_address, validate_amount, format_balance_message
from config import SUPPORTED_NETWORKS, STAKING_PERIODS

def example_wallet_generation():
    """Пример генерации кошельков"""
    print("=== Пример генерации кошельков ===")
    
    # Генерация одного кошелька
    print("1. Генерация Ethereum кошелька:")
    address, private_key, seed_phrase = generate_wallet('ETH')
    print(f"   Адрес: {address}")
    print(f"   Приватный ключ: {private_key[:10]}...")
    print(f"   Seed фраза: {seed_phrase[:20]}...")
    
    # Генерация нескольких кошельков
    print("\n2. Генерация 3 Solana кошельков:")
    wallets = generate_multiple_wallets('SOL', 3)
    for i, wallet in enumerate(wallets, 1):
        print(f"   Кошелек {i}: {wallet['address']}")
    
    print()

def example_database_operations():
    """Пример работы с базой данных"""
    print("=== Пример работы с базой данных ===")
    
    # Инициализация базы данных
    init_db()
    
    # Создание пользователя
    db = next(get_db())
    user = create_user(db, 12345)
    print(f"1. Создан пользователь: ID={user.id}, Account={user.account_id}")
    
    # Создание кошелька
    address, private_key, seed_phrase = generate_wallet('ETH')
    wallet = create_wallet(
        db=db,
        user_id=user.id,
        network='ETH',
        address=address,
        private_key=private_key,
        seed_phrase=seed_phrase
    )
    print(f"2. Создан кошелек: {wallet.address}")
    
    # Получение кошельков пользователя
    wallets = get_user_wallets(db, user.id)
    print(f"3. У пользователя {len(wallets)} кошельков")
    
    db.close()
    print()

def example_balance_checking():
    """Пример проверки балансов"""
    print("=== Пример проверки балансов ===")
    
    # Тестовые адреса (замените на реальные)
    test_addresses = {
        'ETH': '0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6',
        'TRX': 'TJRabPrwbZy45sbavfcjinPJC18kjpRTv8',
        'SOL': '9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM'
    }
    
    for network, address in test_addresses.items():
        print(f"Проверка баланса {network}:")
        balance = balance_checker.get_balance(address, network)
        print(f"   Адрес: {address}")
        for asset, amount in balance.items():
            print(f"   {asset}: {amount}")
        print()

def example_staking_operations():
    """Пример операций стейкинга"""
    print("=== Пример операций стейкинга ===")
    
    # Получение информации о периодах стейкинга
    for period_key, period_info in STAKING_PERIODS.items():
        print(f"Период: {period_key}")
        print(f"   Месяцев: {period_info['months']}")
        print(f"   Ставка: {period_info['rate']}%")
        
        # Расчет вознаграждения
        reward = staking_manager.calculate_reward(100, period_info['rate'], period_info['months'] * 30)
        print(f"   Вознаграждение за 100 токенов: {reward:.4f}")
        print()

def example_validation():
    """Пример валидации данных"""
    print("=== Пример валидации данных ===")
    
    # Валидация адресов
    test_addresses = [
        ('0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6', 'ETH'),
        ('TJRabPrwbZy45sbavfcjinPJC18kjpRTv8', 'TRX'),
        ('invalid_address', 'ETH'),
        ('0x123', 'ETH')
    ]
    
    print("Валидация адресов:")
    for address, network in test_addresses:
        is_valid = validate_address(address, network)
        print(f"   {address} ({network}): {'✓' if is_valid else '✗'}")
    
    # Валидация сумм
    test_amounts = ['1.5', '0.001', '100', '0', '-1', 'invalid']
    
    print("\nВалидация сумм:")
    for amount in test_amounts:
        result = validate_amount(amount)
        print(f"   '{amount}': {result if result is not None else 'неверно'}")
    
    print()

def example_withdrawal_validation():
    """Пример валидации вывода"""
    print("=== Пример валидации вывода ===")
    
    # Тестовые данные
    test_withdrawals = [
        {
            'address': '0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6',
            'amount': 0.1,
            'asset': 'ETH',
            'network': 'ETH',
            'private_key': '0x1234567890abcdef' * 4  # Тестовый ключ
        },
        {
            'address': 'TJRabPrwbZy45sbavfcjinPJC18kjpRTv8',
            'amount': 1.0,
            'asset': 'TRX',
            'network': 'TRX',
            'private_key': '0x1234567890abcdef' * 4  # Тестовый ключ
        }
    ]
    
    for withdrawal in test_withdrawals:
        print(f"Валидация вывода {withdrawal['asset']}:")
        is_valid, message = withdrawal_manager.validate_withdrawal(
            withdrawal['address'],
            withdrawal['amount'],
            withdrawal['asset'],
            withdrawal['network'],
            withdrawal['private_key']
        )
        print(f"   Результат: {'✓' if is_valid else '✗'}")
        print(f"   Сообщение: {message}")
        print()

def example_network_support():
    """Пример поддержки сетей"""
    print("=== Поддержка сетей ===")
    
    print("Поддерживаемые сети:")
    for network in SUPPORTED_NETWORKS:
        print(f"   - {network}")
    
    print("\nСтатус поддержки:")
    print("   ETH/TRX: Полная поддержка (баланс, вывод, свап)")
    print("   SOL/BNB/DOGE/AVAX/POL/XRP: Баланс + вывод (ручная обработка)")
    
    print("\nМинимальные суммы для вывода:")
    from config import MIN_WITHDRAWAL
    for asset, amount in MIN_WITHDRAWAL.items():
        print(f"   {asset}: {amount}")

def main():
    """Основная функция с примерами"""
    print("🚀 Примеры использования Crypto Wallet Telegram Bot\n")
    
    try:
        example_wallet_generation()
        example_database_operations()
        example_balance_checking()
        example_staking_operations()
        example_validation()
        example_withdrawal_validation()
        example_network_support()
        
        print("✅ Все примеры выполнены успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка при выполнении примеров: {e}")
        print("Убедитесь, что все зависимости установлены и база данных настроена.")

if __name__ == "__main__":
    main()