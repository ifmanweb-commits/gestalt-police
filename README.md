# Gestalt Police: VK-бот для модерации

Версия: `v1.0.0`

## Введение

Бот для автоматического определения и удаления спама в сообществах ВКонтакте. Бот использует многоуровневую систему анализа сообщений для выявления и блокировки спама.

## Быстрый старт с Docker

### Требования
- Docker и Docker Compose на сервере (Ubuntu)
- Токен сообщества VK

### Развёртывание на сервере

1. **Клонируйте репозиторий:**
   ```bash
   git clone https://github.com/ifmanweb-commits/gestalt-police.git
   cd gestalt-police
   ```

2. **Инициализируйте файлы:**
   ```bash
   chmod +x init-files.sh
   ./init-files.sh
   ```

3. **Настройте токен VK:**
   ```bash
   cp .env.example .env
   # Отредактируйте .env и укажите ваш VK_TOKEN
   ```

4. **Запустите бота:**
   ```bash
   docker compose build
   docker compose up -d
   ```

### Обновление (деплой)

При внесении изменений в код:

```bash
# Локально:
git add .
git commit -m "Описание изменений"
git push

# На сервере:
chmod +x deploy.sh
./deploy.sh
```

Скрипт `deploy.sh` автоматически:
- Обновит код из репозитория (`git pull`)
- Проверит и создаст необходимые файлы
- Пересоберёт Docker-образ
- Перезапустит контейнер

## Структура проекта

```
gestalt-police/
├── docker-compose.yml      # Конфигурация Docker Compose
├── Dockerfile              # Образ Docker
├── requirements.txt        # Python-зависимости
├── vk_bot.py              # Основной код бота
├── rules.py               # Правила модерации
├── is_spam_message.py     # Логика определения спама
├── .env                   # Переменные окружения (не в git)
├── .env.example           # Шаблон переменных окружения
├── config.json            # Конфигурация бота
├── bot_database.json      # База данных бота
├── custom_commands.json   # Пользовательские команды
├── bot.log                # Лог-файл
├── init-files.sh          # Скрипт инициализации
└── deploy.sh              # Скрипт деплоя
```

## Файлы данных

Следующие файлы хранятся вне контейнера (volumes) и сохраняются при пересборке:

| Файл | Описание |
|------|----------|
| `config.json` | Настройки бота (admin_ids, allowed_chats, spam_keywords) |
| `bot_database.json` | База данных пользователей и статистики |
| `custom_commands.json` | Пользовательские команды |
| `bot.log` | Лог-файл бота |
| `.env` | Токен VK (не коммитить в репозиторий!) |

## Полезные команды

```bash
# Просмотр логов
docker compose logs -f

# Статус контейнера
docker compose ps

# Остановка бота
docker compose down

# Перезапуск бота
docker compose restart

# Полная пересборка
docker compose build --no-cache
docker compose up -d
```

## Получение токена VK

1. Создайте сообщество ВКонтакте
2. Перейдите в Управление → Настройки → API
3. Создайте ключ доступа с правами:
   - Управление сообществом
   - Добавление публикаций на стену
   - Доступ к сообщениям сообщества
4. Скопируйте токен в файл `.env`

## Troubleshooting

### Бот не запускается
```bash
# Проверьте логи
docker compose logs

# Проверьте токен
cat .env
```

### Ошибки с файлами
```bash
# Запустите инициализацию
./init-files.sh
```

### Проблемы с правами доступа
```bash
# Исправьте права на файлы
chmod 644 config.json bot_database.json custom_commands.json bot.log
```

## Лицензия

MIT License