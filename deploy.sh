#!/bin/bash

# Скрипт развертывания VK бота через Docker
# Использование: ./deploy.sh

set -e

echo "🚀 Начало развертывания VK бота..."

# Останавливаем текущий контейнер (если есть)
echo "⏹️  Остановка текущего контейнера..."
docker-compose down || true

# Собираем новый образ
echo "🔨 Сборка Docker образа..."
docker-compose build --no-cache

# Запускаем контейнер
echo "▶️  Запуск контейнера..."
docker-compose up -d

# Показываем логи
echo "📋 Логи контейнера (последние 50 строк):"
docker-compose logs --tail=50

echo ""
echo "✅ Развертывание завершено!"
echo "📊 Статус контейнера:"
docker-compose ps