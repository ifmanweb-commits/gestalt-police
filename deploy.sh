#!/bin/bash
# Скрипт деплоя для gestalt-police бота
# Использование: ./deploy.sh

set -e

echo "================================"
echo "  gestalt-police: Деплой"
echo "================================"
echo ""

# Обновляем код из репозитория
echo "📥 Обновление кода из репозитория..."
git pull origin main || git pull origin master
echo ""

# Инициализируем файлы если нужно
if [ -f init-files.sh ]; then
    echo "📋 Проверка и инициализация файлов..."
    chmod +x init-files.sh
    ./init-files.sh
    echo ""
fi

# Собираем и запускаем контейнер
echo "🐳 Сборка Docker образа..."
docker compose build --no-cache

echo ""
echo "🚀 Запуск контейнера..."
docker compose up -d

echo ""
echo "================================"
echo "  Деплой завершён!"
echo "================================"
echo ""
echo "Статус контейнера:"
docker compose ps

echo ""
echo "Логи (последние 20 строк):"
docker compose logs --tail=20