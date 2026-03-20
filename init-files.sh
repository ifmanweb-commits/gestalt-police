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
  "superuser_id": 260509440,
  "experts_chat_id": 2000000374,
  "group_id": 236116938
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
{}
EOF
    echo "custom_commands.json создан"
else
    echo "custom_commands.json уже существует"
fi

# Создаём bot_database.json если не существует (TinyDB формат)
if [ ! -f bot_database.json ]; then
    echo "Создание bot_database.json..."
    echo '{"_default": {}}' > bot_database.json
    echo "bot_database.json создан"
else
    echo "bot_database.json уже существует"
fi

# Создаём experts.json если не существует (TinyDB формат)
if [ ! -f experts.json ]; then
    echo "Создание experts.json..."
    echo '{"_default": {}}' > experts.json
    echo "experts.json создан"
else
    echo "experts.json уже существует"
fi

# Создаём questions.json если не существует (TinyDB формат)
if [ ! -f questions.json ]; then
    echo "Создание questions.json..."
    echo '{"_default": {}}' > questions.json
    echo "questions.json создан"
else
    echo "questions.json уже существует"
fi

# Создаём папки для логов и данных
mkdir -p logs data

# Проверяем .env
if [ ! -f .env ]; then
    echo "ВНИМАНИЕ: Файл .env отсутствует!"
    if [ -f .env.example ]; then
        echo "Скопируйте .env.example в .env и заполните токен VK:"
        echo "  cp .env.example .env"
    else
        echo "Создайте .env с содержимым: VK_TOKEN=ваш_токен"
    fi
else
    echo ".env уже существует"
fi

echo ""
echo "Инициализация завершена!"
echo ""
echo "Для запуска бота выполните:"
echo "  docker compose build"
echo "  docker compose up -d"