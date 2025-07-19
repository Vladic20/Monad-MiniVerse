# Инструкции по развертыванию Crypto Wallet Telegram Bot

## 🚀 Быстрый старт

### 1. Подготовка окружения

#### Требования к системе
- Python 3.8 или выше
- PostgreSQL 12 или выше
- Git

#### Установка Python зависимостей
```bash
# Клонирование репозитория
git clone <repository-url>
cd crypto-wallet-bot

# Создание виртуального окружения
python -m venv venv

# Активация виртуального окружения
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt
```

### 2. Настройка базы данных

#### Установка PostgreSQL
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# CentOS/RHEL
sudo yum install postgresql postgresql-server
sudo postgresql-setup initdb
sudo systemctl start postgresql

# macOS (с Homebrew)
brew install postgresql
brew services start postgresql
```

#### Создание базы данных
```bash
# Подключение к PostgreSQL
sudo -u postgres psql

# Создание пользователя и базы данных
CREATE USER crypto_bot WITH PASSWORD 'your_secure_password';
CREATE DATABASE crypto_bot OWNER crypto_bot;
GRANT ALL PRIVILEGES ON DATABASE crypto_bot TO crypto_bot;
\q
```

### 3. Настройка переменных окружения

```bash
# Копирование примера конфигурации
cp .env.example .env

# Редактирование конфигурации
nano .env
```

#### Пример .env файла:
```env
# Telegram Bot Configuration
TELEGRAM_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Database Configuration
DATABASE_URL=postgresql://crypto_bot:your_secure_password@localhost/crypto_bot

# Blockchain APIs Configuration
INFURA_URL=https://mainnet.infura.io/v3/YOUR_INFURA_KEY
TRONGRID_API_KEY=your_tron_grid_api_key_here
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
```

### 4. Получение API ключей

#### Telegram Bot Token
1. Найдите @BotFather в Telegram
2. Отправьте команду `/newbot`
3. Введите имя бота (например: "Crypto Wallet Bot")
4. Введите username бота (например: "crypto_wallet_bot")
5. Скопируйте полученный токен в `.env`

#### Infura API Key (для Ethereum)
1. Зарегистрируйтесь на [Infura](https://infura.io/)
2. Создайте новый проект
3. Скопируйте Project ID
4. Добавьте в `.env` как `YOUR_INFURA_KEY`

#### TronGrid API Key (для Tron)
1. Зарегистрируйтесь на [TronGrid](https://www.trongrid.io/)
2. Получите API ключ
3. Добавьте в `.env`

### 5. Инициализация базы данных

```bash
# Запуск инициализации
python -c "from database import init_db; init_db()"
```

### 6. Тестирование

```bash
# Запуск тестов
python test_bot.py

# Проверка конфигурации
python run.py --check
```

### 7. Запуск бота

#### Разработка
```bash
python run.py
```

#### Продакшн с systemd (Linux)

Создайте файл сервиса `/etc/systemd/system/crypto-wallet-bot.service`:
```ini
[Unit]
Description=Crypto Wallet Telegram Bot
After=network.target postgresql.service

[Service]
Type=simple
User=crypto_bot
WorkingDirectory=/path/to/crypto-wallet-bot
Environment=PATH=/path/to/crypto-wallet-bot/venv/bin
ExecStart=/path/to/crypto-wallet-bot/venv/bin/python run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Запуск сервиса:
```bash
sudo systemctl daemon-reload
sudo systemctl enable crypto-wallet-bot
sudo systemctl start crypto-wallet-bot
sudo systemctl status crypto-wallet-bot
```

#### Продакшн с Docker

Создайте `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "run.py"]
```

Создайте `docker-compose.yml`:
```yaml
version: '3.8'

services:
  bot:
    build: .
    environment:
      - TELEGRAM_TOKEN=${TELEGRAM_TOKEN}
      - DATABASE_URL=${DATABASE_URL}
      - INFURA_URL=${INFURA_URL}
      - TRONGRID_API_KEY=${TRONGRID_API_KEY}
    depends_on:
      - postgres
    restart: unless-stopped

  postgres:
    image: postgres:13
    environment:
      - POSTGRES_DB=crypto_bot
      - POSTGRES_USER=crypto_bot
      - POSTGRES_PASSWORD=your_secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

Запуск с Docker:
```bash
docker-compose up -d
```

## 🔧 Конфигурация

### Основные настройки в `config.py`

```python
# Поддерживаемые сети
SUPPORTED_NETWORKS = ['ETH', 'TRX', 'SOL', 'BNB', 'DOGE', 'AVAX', 'POL', 'XRP']

# Минимальные суммы для вывода
MIN_WITHDRAWAL = {
    'ETH': 0.001,
    'TRX': 0.1,
    # ...
}

# Параметры стейкинга
STAKING_PERIODS = {
    '1_month': {'months': 1, 'rate': 16},
    '3_months': {'months': 3, 'rate': 18},
    # ...
}
```

### Логирование

Логи сохраняются в файл `bot.log`:
```bash
# Просмотр логов
tail -f bot.log

# Просмотр ошибок
grep ERROR bot.log
```

## 🔒 Безопасность

### Рекомендации по безопасности

1. **Приватные ключи**: Храните в зашифрованном виде
2. **База данных**: Используйте сильные пароли
3. **API ключи**: Не публикуйте в репозитории
4. **Сеть**: Используйте HTTPS для API запросов
5. **Обновления**: Регулярно обновляйте зависимости

### Мониторинг

```bash
# Проверка статуса бота
systemctl status crypto-wallet-bot

# Просмотр логов
journalctl -u crypto-wallet-bot -f

# Проверка использования ресурсов
htop
```

## 🚨 Устранение неполадок

### Частые проблемы

#### 1. Ошибка подключения к базе данных
```bash
# Проверка статуса PostgreSQL
sudo systemctl status postgresql

# Проверка подключения
psql -h localhost -U crypto_bot -d crypto_bot
```

#### 2. Ошибка Telegram API
```bash
# Проверка токена
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"
```

#### 3. Ошибка Infura API
```bash
# Проверка подключения к Ethereum
curl -X POST -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  https://mainnet.infura.io/v3/YOUR_INFURA_KEY
```

### Логи и отладка

```bash
# Включение подробного логирования
export LOG_LEVEL=DEBUG
python run.py

# Просмотр последних ошибок
tail -n 100 bot.log | grep ERROR
```

## 📊 Мониторинг и метрики

### Основные метрики для отслеживания

1. **Количество активных пользователей**
2. **Количество сгенерированных кошельков**
3. **Объем транзакций**
4. **Активные стейки**
5. **Ошибки API**

### Создание дашборда

```python
# Пример скрипта для сбора метрик
from database import get_db
from sqlalchemy import func
from datetime import datetime, timedelta

def get_metrics():
    db = next(get_db())
    
    # Активные пользователи за последние 30 дней
    active_users = db.query(User).filter(
        User.creation_date >= datetime.utcnow() - timedelta(days=30)
    ).count()
    
    # Общее количество кошельков
    total_wallets = db.query(Wallet).count()
    
    # Активные стейки
    active_stakes = db.query(StakingLog).filter(
        StakingLog.status == 'active'
    ).count()
    
    return {
        'active_users': active_users,
        'total_wallets': total_wallets,
        'active_stakes': active_stakes
    }
```

## 🔄 Обновления

### Процесс обновления

1. **Остановка бота**
```bash
sudo systemctl stop crypto-wallet-bot
```

2. **Обновление кода**
```bash
git pull origin main
pip install -r requirements.txt
```

3. **Миграция базы данных** (если необходимо)
```bash
python -c "from database import init_db; init_db()"
```

4. **Запуск бота**
```bash
sudo systemctl start crypto-wallet-bot
```

5. **Проверка статуса**
```bash
sudo systemctl status crypto-wallet-bot
```

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи: `tail -f bot.log`
2. Убедитесь в корректности настроек в `.env`
3. Проверьте статус зависимых сервисов
4. Создайте Issue в репозитории с подробным описанием проблемы

### Полезные команды

```bash
# Проверка здоровья системы
python run.py --health-check

# Тестирование всех функций
python test_bot.py

# Очистка логов
> bot.log

# Резервное копирование базы данных
pg_dump crypto_bot > backup_$(date +%Y%m%d_%H%M%S).sql
```