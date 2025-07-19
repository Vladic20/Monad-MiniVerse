#!/usr/bin/env python3
"""
Crypto Exchange Telegram Bot Runner
Простой скрипт для запуска бота с обработкой ошибок
"""

import asyncio
import sys
import os
from pathlib import Path

def check_requirements():
    """Проверка наличия необходимых файлов"""
    required_files = [
        'bot.py',
        'config.py', 
        'database.py',
        'exchange_service.py',
        'keyboards.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Отсутствуют необходимые файлы: {', '.join(missing_files)}")
        return False
    
    return True

def check_env():
    """Проверка конфигурации"""
    if not Path('.env').exists():
        print("⚠️  Файл .env не найден!")
        print("📝 Создайте файл .env на основе .env.example")
        print("🔧 Укажите BOT_TOKEN и другие настройки")
        return False
    
    return True

async def main():
    """Основная функция запуска"""
    print("🚀 Запуск Crypto Exchange Bot...")
    
    # Проверки
    if not check_requirements():
        sys.exit(1)
    
    if not check_env():
        print("💡 Пример настройки .env файла:")
        print("BOT_TOKEN=your_bot_token_here")
        print("ADMIN_IDS=123456789")
        print("SECRET_KEY=your-secret-key")
        sys.exit(1)
    
    try:
        # Импорт и запуск бота
        from bot import main as bot_main
        print("✅ Все проверки пройдены")
        print("🤖 Запуск бота...")
        await bot_main()
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("💡 Установите зависимости: pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        print("🔧 Проверьте настройки в .env файле")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)