#!/bin/bash
# Скрипт инициализации файлов для gestalt-police бота
# Создаёт необходимые файлы, если они отсутствуют

set -e

echo "Инициализация файлов для gestalt-police..."

# Создаём config.json если не существует
if [ ! -f config.json ]; then
    echo "Создание config.json..."
    cat > config.json << 'EOF'
{
    "admin_ids": [],
    "allowed_chats": [],
    "spam_keywords": [],
    "settings": {
        "delete_spam": true,
        "ban_user": false,
        "log_spam": true
    }
}
EOF
    echo "config.json создан"
else
    echo "config.json уже существует"
fi

# Создаём custom_commands.json если не существует
if [ ! -f custom_commands.json ]; then
    echo "Создание custom_commands.json..."
    cat > custom_commands.json << 'EOF'
{
    "commands": []
}
EOF
    echo "custom_commands.json создан"
else
    echo "custom_commands.json уже существует"
fi

# Создаём bot_database.json если не существует
if [ ! -f bot_database.json ]; then
    echo "Создание bot_database.json..."
    cat > bot_database.json << 'EOF'
{
    "users": {},
    "banned_users": [],
    "spam_stats": {}
}
EOF
    echo "bot_database.json создан"
else
    echo "bot_database.json уже существует"
fi

# Создаём bot.log если не существует
if [ ! -f bot.log ]; then
    echo "Создание bot.log..."
    touch bot.log
    echo "bot.log создан"
else
    echo "bot.log уже существует"
fi

# Проверяем .env
if [ ! -f .env ]; then
    echo "ВНИМАНИЕ: Файл .env отсутствует!"
    echo "Скопируйте .env.example в .env и заполните токен VK:"
    echo "  cp .env.example .env"
    echo "  Отредактируйте .env и укажите VK_TOKEN"
else
    echo ".env уже существует"
fi

echo ""
echo "Инициализация завершена!"
echo ""
echo "Для запуска бота выполните:"
echo "  docker compose build"
echo "  docker compose up -d"