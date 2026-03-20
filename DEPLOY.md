# Инструкция по развертыванию VK бота Gestalt Police

## Требования

- Сервер с Docker и Docker Compose
- Git
- Токен VK бота

## Алгоритм развертывания

### 1. Первоначальная настройка

```bash
# Клонируем репозиторий
git clone <URL_репозитория>
cd gestalt-police

# Копируем .env.example в .env и настраиваем
cp .env.example .env

# Редактируем .env, указываем VK_TOKEN и другие параметры
nano .env
```

### 2. Запуск бота

```bash
# Запускаем через docker-compose
docker-compose up -d

# Или используем скрипт deploy.sh
chmod +x deploy.sh
./deploy.sh
```

### 3. Проверка работы

```bash
# Просмотр логов
docker-compose logs -f

# Проверка статуса контейнера
docker-compose ps
```

## Алгоритм обновления (CI/CD)

После внесения изменений в код на локальном компьютере:

```bash
# 1. Локально делаем коммит и пушим в репозиторий
git add .
git commit -m "Описание изменений"
git push origin main

# 2. На сервере заходим в директорию проекта
cd /path/to/gestalt-police

# 3. Забираем изменения из репозитория
git pull origin main

# 4. Пересобираем и перезапускаем контейнер
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Или используем скрипт deploy.sh
./deploy.sh
```

## Структура проекта

```
gestalt-police/
├── vk_bot.py              # Точка входа бота
├── config.py              # Конфигурация
├── database.py            # База данных пользователей
├── rules.py               # Правила маршрутизации сообщений
├── handlers/
│   ├── __init__.py
│   ├── admin.py           # Админ-команды
│   ├── private.py         # Личные сообщения
│   └── group.py           # Групповые сообщения
├── models/
│   ├── __init__.py
│   ├── experts_db.py      # Модель экспертов
│   └── questions_db.py    # Модель вопросов
├── services/
│   ├── __init__.py
│   ├── spam_check.py      # Проверка на спам
│   ├── vk_api.py          # VK API утилиты
│   └── custom_commands.py # Пользовательские команды
├── Dockerfile             # Docker образ
├── docker-compose.yml     # Docker Compose конфигурация
├── .env                   # Переменные окружения (не в git!)
├── .env.example           # Пример .env файла
├── requirements.txt       # Python зависимости
└── deploy.sh              # Скрипт развертывания
```

## Файлы данных (сохраняются между перезапусками)

- `config.json` - конфигурация бота
- `bot_database.json` - база данных пользователей
- `experts.json` - список экспертов
- `questions.json` - база данных вопросов
- `custom_commands.json` - пользовательские команды
- `logs/bot.log` - логи бота

## Переменные окружения (.env)

```bash
VK_TOKEN=ваш_токен_vk_bot
SUPERUSER_ID=ваш_id_суперпользователя
EXPERTS_CHAT_ID=id_чата_экспертов
```

## Команды управления

```bash
# Запуск
docker-compose up -d

# Остановка
docker-compose down

# Перезапуск
docker-compose restart

# Просмотр логов
docker-compose logs -f

# Пересборка образа
docker-compose build --no-cache

# Обновление из репозитория
git pull && docker-compose down && docker-compose build --no-cache && docker-compose up -d