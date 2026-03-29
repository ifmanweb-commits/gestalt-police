"""
VK Bot - Gestalt Police
Основной файл запуска бота.
"""
import logging
import os
from dotenv import load_dotenv
from vkbottle import Bot

# Загрузка переменных окружения
load_dotenv()

# Импортируем экземпляры API (разделение токенов)
from services.api_instances import group_api, user_api

# Токен для инициализации бота (групповой)
BOT_TOKEN = os.getenv('VK_TOKEN')

# Загрузка конфигурации ПЕРЕД импортами, которые используют переменные
from config import load_config
load_config()

# Импорт локальных модулей (после загрузки конфига)
from config import SUPERUSER_ID, EXPERTS_CHAT_ID
from rules import (
    IsPrivateRule, IsGroupRule, IsSuperuserRule,
    CommandRule
)
from models.experts_db import init_databases
from models.questions_db import init_questions_db
from handlers.private import handle_question, handle_unauthorized
from handlers.group import (
    handle_expert_answer, handle_custom_command,
    handle_status_deletion, handle_antispam
)
from handlers.admin import (
    register_chat, unregister_chat, list_chats,
    delete_statuses, allow_statuses, ruleslist,
    setrule, delrule, expert_reg, expert_del, expert_list,
    get_chat_id
)
from services.custom_commands import load_custom_commands

# Настройка логирования
# Используем относительный путь для локальной разработки и абсолютный для Docker
LOG_DIR = "logs" if os.path.exists("logs") else "/app/logs"
try:
    os.makedirs(LOG_DIR, exist_ok=True)
except OSError:
    LOG_DIR = "."

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=os.path.join(LOG_DIR, "bot.log"),
    filemode="a",
    force=True  # Принудительно перезаписываем конфигурацию логирования
)
logging.info("Логирование инициализировано")

# Инициализация API и бота
# group_api используется для модерации, команд, вопросов
# user_api используется только для публикации постов на стене
bot = Bot(BOT_TOKEN)

# ============================================================================
# КОМАНДЫ СУПЕРПОЛЬЗОВАТЕЛЯ В ЛИЧКЕ
# ============================================================================

@bot.on.message(IsPrivateRule() & IsSuperuserRule() & CommandRule("start"))
async def start(message):
    await message.answer(
        'Здравствуйте! Я бот, удаляющий спам.\n\n'
        'Чтобы начать работу, добавьте меня в чат как администратора. '
        'Затем используйте команду /register <chat_id> чтобы зарегистрировать чат и начать получать логи удаленных сообщений. '
        'Используйте /unregister <chat_id> чтобы отменить регистрацию чата.\n\n'
        'Идентификатор чата выглядит примерно так: 2000000001 (для бесед) или ID пользователя. '
        'Чтобы получить идентификатор беседы, можно использовать @VkIdBot или другие аналоги.\n\n'
        'Вы также можете настроить удаление технических сообщений со статусами, см. полный список возможностей с помощью команды /help.'
    )


@bot.on.message(IsPrivateRule() & IsSuperuserRule() & CommandRule("help"))
async def help_command(message):
    help_text = """
Команды:
/start - Начать работу
/register <chat_id> - Зарегистрировать чат
/unregister <chat_id> - Отменить регистрацию чата
/list - Показать ваши зарегистрированные чаты и их идентификаторы
/delete_statuses <chat_id> - Включить автоматическое удаление статусов (по умолчанию выключено)
/allow_statuses <chat_id> - Отключить автоматическое удаление статусов
/ruleslist - Показать список всех сохраненных пользовательских команд
/setrule $!команда$ $Текст сообщения$ - Создать новую или перезаписать существующую команду
/delrule $!команда$ - Удалить существующую команду
/expertreg <id|url> - Добавить эксперта
/expertdel <id> - Удалить эксперта по ID
/expertlist - Показать список всех экспертов
/chatid - Получить ID текущего чата (работает в групповых чатах для администраторов)
/help - Показать справку
"""
    await message.answer(help_text)


@bot.on.message(IsPrivateRule() & IsSuperuserRule() & CommandRule("register"))
async def register(message):
    await register_chat(message, group_api)


@bot.on.message(IsPrivateRule() & IsSuperuserRule() & CommandRule("unregister"))
async def unregister(message):
    await unregister_chat(message, group_api)


@bot.on.message(IsPrivateRule() & IsSuperuserRule() & CommandRule("list"))
async def list_chats_cmd(message):
    await list_chats(message, group_api)


@bot.on.message(IsPrivateRule() & IsSuperuserRule() & CommandRule("delete_statuses"))
async def delete_statuses_cmd(message):
    await delete_statuses(message, group_api)


@bot.on.message(IsPrivateRule() & IsSuperuserRule() & CommandRule("allow_statuses"))
async def allow_statuses_cmd(message):
    await allow_statuses(message, group_api)


@bot.on.message(IsPrivateRule() & IsSuperuserRule() & CommandRule("ruleslist"))
async def ruleslist_cmd(message):
    await ruleslist(message, group_api)


@bot.on.message(IsPrivateRule() & IsSuperuserRule() & CommandRule("setrule"))
async def setrule_cmd(message):
    await setrule(message, group_api)


@bot.on.message(IsPrivateRule() & IsSuperuserRule() & CommandRule("delrule"))
async def delrule_cmd(message):
    await delrule(message, group_api)


@bot.on.message(IsPrivateRule() & IsSuperuserRule() & CommandRule("expertreg"))
async def expertreg_cmd(message):
    await expert_reg(message, group_api)


@bot.on.message(IsPrivateRule() & IsSuperuserRule() & CommandRule("expertdel"))
async def expertdel_cmd(message):
    await expert_del(message, group_api)


@bot.on.message(IsPrivateRule() & IsSuperuserRule() & CommandRule("expertlist"))
async def expertlist_cmd(message):
    await expert_list(message, group_api)


@bot.on.message(IsPrivateRule() & IsSuperuserRule() & CommandRule("chatid"))
async def chatid_cmd(message):
    await get_chat_id(message, group_api)


# ============================================================================
# ЛИЧНЫЕ СООБЩЕНИЯ (ВСЕ ПОЛЬЗОВАТЕЛИ)
# ============================================================================

@bot.on.message(IsPrivateRule())
async def private_handler(message):
    """
    Обработчик личных сообщений.
    Порядок: #вопрос → отказ обычным пользователям
    """
    # Сначала пробуем обработать #вопрос
    if await handle_question(message, group_api):
        return
    
    # Если не #вопрос и не суперпользователь - отказ
    if message.from_id != SUPERUSER_ID:
        await handle_unauthorized(message)


# ============================================================================
# ГРУППОВЫЕ СООБЩЕНИЯ
# ============================================================================

@bot.on.message(IsGroupRule() & CommandRule("chatid"))
async def chatid_group_cmd(message):
    """Обработчик /chatid в групповых чатах"""
    await get_chat_id(message, group_api)


@bot.on.message(IsGroupRule())
async def group_handler(message):
    """
    Единый обработчик групповых сообщений.
    Порядок обработки:
    1. Ответ эксперта в беседе экспертов
    2. !команда от админа
    3. Удаление статусов
    4. Антиспам
    """
    # 1. Ответ эксперта
    if await handle_expert_answer(message, group_api, user_api):
        return
    
    # 2. !команда
    if await handle_custom_command(message, group_api):
        return
    
    # 3. Удаление статусов
    if await handle_status_deletion(message, group_api):
        return
    
    # 4. Антиспам
    # await handle_antispam(message, group_api)  # ЗАКОММЕНТИРОВАНО - проверка на спам отключена


# ============================================================================
# ЗАПУСК
# ============================================================================

def main():
    print("VK Bot is working")
    
    # Загрузка пользовательских команд из файла
    load_custom_commands()
    logging.info("Пользовательские команды загружены")
    
    # Инициализация баз данных
    init_databases()
    logging.info("Базы данных экспертов инициализированы")
    
    init_questions_db()
    logging.info("База данных вопросов инициализирована")
    
    bot.run_forever()


if __name__ == '__main__':
    main()