# 🚀 Быстрый старт Crypto Wallet Telegram Bot

## 📋 Что нужно для запуска

### 1. Системные требования
- Python 3.8+
- PostgreSQL 12+
- Интернет соединение

### 2. API ключи
- Telegram Bot Token (от @BotFather)
- Infura API Key (для Ethereum)
- TronGrid API Key (для Tron)

## ⚡ Быстрая установка (5 минут)

### Шаг 1: Установка зависимостей
```bash
# Клонирование
git clone <repository-url>
cd crypto-wallet-bot

# Виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Установка пакетов
pip install -r requirements.txt
```

### Шаг 2: Настройка базы данных
```bash
# Установка PostgreSQL (Ubuntu)
sudo apt install postgresql postgresql-contrib

# Создание БД
sudo -u postgres psql
CREATE USER crypto_bot WITH PASSWORD 'password123';
CREATE DATABASE crypto_bot OWNER crypto_bot;
GRANT ALL PRIVILEGES ON DATABASE crypto_bot TO crypto_bot;
\q
```

### Шаг 3: Конфигурация
```bash
# Копирование конфигурации
cp .env.example .env

# Редактирование .env
nano .env
```

**Содержимое .env:**
```env
TELEGRAM_TOKEN=your_bot_token_here
DATABASE_URL=postgresql://crypto_bot:password123@localhost/crypto_bot
INFURA_URL=https://mainnet.infura.io/v3/your_infura_key
TRONGRID_API_KEY=your_tron_grid_key
```

### Шаг 4: Инициализация
```bash
# Создание таблиц
python -c "from database import init_db; init_db()"

# Тестирование
python test_bot.py
```

### Шаг 5: Запуск
```bash
python run.py
```

## 🎯 Первые шаги с ботом

### 1. Создание бота в Telegram
1. Найдите @BotFather
2. Отправьте `/newbot`
3. Введите имя: "Crypto Wallet Bot"
4. Введите username: "your_crypto_bot"
5. Скопируйте токен в `.env`

### 2. Тестирование функций
1. Найдите вашего бота в Telegram
2. Отправьте `/start`
3. Нажмите "🎌 Генерировать кошелёк"
4. Выберите сеть (например, ETH)
5. Введите количество: 1
6. Проверьте сгенерированный адрес

## 🔧 Основные команды

| Команда | Описание |
|---------|----------|
| `/start` | Запуск бота |
| `🎌 Генерировать кошелёк` | Создание кошельков |
| `💰 Баланс` | Проверка балансов |
| `📥 Пополнить` | Получение адресов |
| `📤 Вывести` | Вывод средств |
| `🔄 Свапнуть` | Обмен токенов |
| `💹 Стейкинг` | Создание стейкинга |
| `📋 Мои стейки` | Просмотр стейков |
| `ℹ️ Инфо` | Информация о боте |

## 🛠 Устранение проблем

### Ошибка подключения к БД
```bash
sudo systemctl start postgresql
sudo systemctl status postgresql
```

### Ошибка Telegram API
```bash
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"
```

### Ошибка зависимостей
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

## 📊 Мониторинг

### Просмотр логов
```bash
tail -f bot.log
```

### Проверка статуса
```bash
ps aux | grep python
```

### Очистка логов
```bash
> bot.log
```

## 🔒 Безопасность

### Важные моменты
- ✅ Никогда не публикуйте `.env` файл
- ✅ Используйте сильные пароли для БД
- ✅ Регулярно обновляйте зависимости
- ✅ Мониторьте логи на ошибки

### Рекомендации
- Используйте отдельного пользователя для бота
- Настройте firewall
- Регулярно делайте бэкапы БД

## 📞 Поддержка

### Полезные команды
```bash
# Проверка здоровья системы
python run.py

# Запуск тестов
python test_bot.py

# Примеры использования
python example_usage.py
```

### Логи и отладка
```bash
# Подробные логи
export LOG_LEVEL=DEBUG
python run.py

# Просмотр ошибок
grep ERROR bot.log
```

## 🎉 Готово!

Ваш Crypto Wallet Telegram Bot готов к работе! 

**Следующие шаги:**
1. Протестируйте все функции
2. Настройте мониторинг
3. Изучите полную документацию в `README.md`
4. Настройте продакшн развертывание в `DEPLOYMENT.md`

**Удачи в мире крипто-самураев! 🗡️**