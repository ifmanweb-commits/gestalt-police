import logging
import os
import json
import re
import emoji
import random
from dotenv import load_dotenv
from vkbottle import API, Bot
from tinydb import TinyDB, Query

# Импорт локальных модулей
from is_spam_message import new_is_spam_message, has_critical_patterns, has_mixed_words
from rules import (
    IsPrivateRule, IsGroupRule, IsSuperuserRule, IsNotSuperuserRule,
    CommandRule, StartsWithRule
)

# Загрузка переменных окружения
load_dotenv()

TOKEN = os.getenv('VK_TOKEN')

# Настройка логирования
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename="bot.log",
    filemode="a"
)

# Загрузка конфигурации
CONFIG_FILE = "./config.json"

def load_config():
    """Загружает конфигурацию из config.json."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                if config.get('superuser_id') is None:
                    logging.error("superuser_id не найден в config.json")
        else:
            logging.error("config.json не найден")
    except json.JSONDecodeError as e:
        logging.error(f"Ошибка парсинга JSON в config.json: {e}")
    except IOError as e:
        logging.error(f"Ошибка чтения config.json: {e}")

# Инициализация TinyDB
db_main_file = "./bot_database.json"
if not os.path.exists(db_main_file):
    with open(db_main_file, "w", encoding="utf-8") as file:
        file.write("{}")
db_main = TinyDB(db_main_file)
User = Query()

def cleanup_database():
    """Удаляет из базы данных записи, принадлежащие не суперпользователю."""
    from rules import get_superuser_id
    superuser_id = get_superuser_id()
    if superuser_id is None:
        logging.error("SUPERUSER_ID не загружен, очистка базы данных отменена")
        return
    
    all_users = db_main.all()
    for user_data in all_users:
        if user_data['user_id'] != superuser_id:
            db_main.remove(User.user_id == user_data['user_id'])
            logging.info(f"Удалена запись пользователя {user_data['user_id']} из базы данных")

# Хранение пользовательских команд
CUSTOM_COMMANDS_FILE = "./custom_commands.json"
custom_commands = {}

def load_custom_commands():
    """Загружает пользовательские команды из JSON файла."""
    global custom_commands
    try:
        if os.path.exists(CUSTOM_COMMANDS_FILE):
            with open(CUSTOM_COMMANDS_FILE, "r", encoding="utf-8") as f:
                custom_commands = json.load(f)
                if not isinstance(custom_commands, dict):
                    logging.error("custom_commands.json имеет неверную структуру. Загружен пустой словарь.")
                    custom_commands = {}
                else:
                    logging.info(f"Загружено {len(custom_commands)} пользовательских команд из {CUSTOM_COMMANDS_FILE}")
        else:
            custom_commands = {}
            save_custom_commands()
            logging.info("custom_commands.json не существовал, создан новый пустой файл")
    except json.JSONDecodeError as e:
        logging.error(f"Ошибка парсинга JSON в custom_commands.json: {e}. Загружен пустой словарь.")
        custom_commands = {}
    except IOError as e:
        logging.error(f"Ошибка чтения custom_commands.json: {e}")
        custom_commands = {}

def save_custom_commands():
    """Сохраняет пользовательские команды в JSON файл."""
    global custom_commands
    try:
        with open(CUSTOM_COMMANDS_FILE, "w", encoding="utf-8") as f:
            json.dump(custom_commands, f, ensure_ascii=False, indent=2)
    except IOError as e:
        logging.error(f"Ошибка записи custom_commands.json: {e}")
        raise

def is_user_admin_in_any_registered_chat(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором хотя бы в одном зарегистрированном чате."""
    from rules import get_superuser_id
    superuser_id = get_superuser_id()
    if user_id != superuser_id:
        return False
    user_data = db_main.get(User.user_id == user_id)
    if not user_data or not user_data.get('chats'):
        return False
    return True

async def is_user_admin_in_chat(api: API, chat_id: int, user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором в конкретном чате."""
    try:
        from rules import get_superuser_id
        superuser_id = get_superuser_id()
        # В VK боты не имеют прямого доступа к статусу участника через API
        # Проверяем только суперпользователя
        if user_id == superuser_id:
            return True
        # Для других пользователей проверяем через базу зарегистрированных чатов
        user_data = db_main.get(User.user_id == user_id)
        if user_data and chat_id in user_data.get('chats', []):
            return True
        return False
    except Exception as e:
        logging.warning(f"Не удалось проверить статус пользователя {user_id} в чате {chat_id}: {e}")
        return False

# Инициализация API и бота
api = API(TOKEN)
bot = Bot(TOKEN)

# ============================================================================
# КОМАНДЫ В ЛИЧНОМ ЧАТЕ (только для суперпользователя)
# ============================================================================

@bot.on.message(IsPrivateRule() & IsSuperuserRule() & CommandRule("start"))
async def start(message):
    """Обработчик команды /start."""
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
    """Обработчик команды /help."""
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
/help - Показать справку
"""
    await message.answer(help_text)

@bot.on.message(IsPrivateRule() & IsSuperuserRule() & CommandRule("register"))
async def register(message):
    """Обработчик команды /register."""
    args = message.text.split()
    if len(args) < 2:
        await message.answer('Добавьте идентификатор чата после команды.')
        return
    
    try:
        chat_id = int(args[1])
    except ValueError:
        await message.answer('Неверный формат идентификатора чата. Используйте числовой ID.')
        return
    
    user_id = message.from_id
    user_data = db_main.get(User.user_id == user_id)
    
    if user_data:
        if chat_id not in user_data['chats']:
            user_data['chats'].append(chat_id)
            if 'delete_statuses' not in user_data:
                user_data['delete_statuses'] = {}
            user_data['delete_statuses'][str(chat_id)] = False
            db_main.update(user_data, User.user_id == user_id)
    else:
        db_main.insert({'user_id': user_id, 'chats': [chat_id], 'delete_statuses': {str(chat_id): False}})
    
    await message.answer(f'Зарегистрирован чат {chat_id}')

@bot.on.message(IsPrivateRule() & IsSuperuserRule() & CommandRule("unregister"))
async def unregister(message):
    """Обработчик команды /unregister."""
    args = message.text.split()
    if len(args) < 2:
        await message.answer('Добавьте идентификатор чата после команды.')
        return
    
    try:
        chat_id = int(args[1])
    except ValueError:
        await message.answer('Неверный формат идентификатора чата. Используйте числовой ID.')
        return
    
    user_id = message.from_id
    user_data = db_main.get(User.user_id == user_id)
    
    if user_data and chat_id in user_data['chats']:
        user_data['chats'].remove(chat_id)
        if 'delete_statuses' in user_data:
            user_data['delete_statuses'].pop(str(chat_id), None)
        db_main.update(user_data, User.user_id == user_id)
        await message.answer(f'Отменена регистрация чата {chat_id}.')
    else:
        await message.answer('Чат не зарегистрирован.')

@bot.on.message(IsPrivateRule() & IsSuperuserRule() & CommandRule("list"))
async def list_chats(message):
    """Обработчик команды /list."""
    user_id = message.from_id
    user_data = db_main.get(User.user_id == user_id)
    
    if user_data and user_data['chats']:
        chat_list = "Ваши зарегистрированные чаты:\n\n"
        for chat_id in user_data['chats']:
            delete_status = user_data.get('delete_statuses', {}).get(str(chat_id), False)
            status = "Включено" if delete_status else "Отключено"
            chat_list += f"Идентификатор: {chat_id}\nУдаление статусов: {status}\n\n"
        await message.answer(chat_list)
    else:
        await message.answer("У вас нет зарегистрированных чатов.")

@bot.on.message(IsPrivateRule() & IsSuperuserRule() & CommandRule("delete_statuses"))
async def delete_statuses(message):
    """Обработчик команды /delete_statuses."""
    args = message.text.split()
    if len(args) < 2:
        await message.answer('Добавьте идентификатор чата после команды.')
        return
    
    try:
        chat_id = int(args[1])
    except ValueError:
        await message.answer('Неверный формат идентификатора чата. Используйте числовой ID.')
        return
    
    user_id = message.from_id
    user_data = db_main.get(User.user_id == user_id)
    
    if user_data and chat_id in user_data.get('chats', []):
        if 'delete_statuses' not in user_data:
            user_data['delete_statuses'] = {}
        user_data['delete_statuses'][str(chat_id)] = True
        db_main.update(user_data, User.user_id == user_id)
        await message.answer(f'Автоматическое удаление статусов включено для чата {chat_id}')
    else:
        await message.answer('Чат не зарегистрирован.')

@bot.on.message(IsPrivateRule() & IsSuperuserRule() & CommandRule("allow_statuses"))
async def allow_statuses(message):
    """Обработчик команды /allow_statuses."""
    args = message.text.split()
    if len(args) < 2:
        await message.answer('Добавьте идентификатор чата после команды.')
        return
    
    try:
        chat_id = int(args[1])
    except ValueError:
        await message.answer('Неверный формат идентификатора чата. Используйте числовой ID.')
        return
    
    user_id = message.from_id
    user_data = db_main.get(User.user_id == user_id)
    
    if user_data and chat_id in user_data['chats']:
        if 'delete_statuses' in user_data:
            user_data['delete_statuses'][str(chat_id)] = False
        db_main.update(user_data, User.user_id == user_id)
        await message.answer(f'Автоматическое удаление статусов отключено для чата {chat_id}')
    else:
        await message.answer('Чат не зарегистрирован.')

@bot.on.message(IsPrivateRule() & IsSuperuserRule() & CommandRule("ruleslist"))
async def ruleslist(message):
    """Обработчик команды /ruleslist."""
    if not is_user_admin_in_any_registered_chat(message.from_id):
        await message.answer(
            "У вас нет зарегистрированных чатов. "
            "Сначала зарегистрируйте чат с помощью команды /register <chat_id>."
        )
        return
    
    if not custom_commands:
        await message.answer("Список пользовательских команд пуст.")
        return
    
    result = "📋 **Список пользовательских команд:**\n\n"
    for cmd_name, text in custom_commands.items():
        result += f"{cmd_name}:\n{text}\n\n"
        if len(result) > 4000:
            result += "... (продолжение следует)"
            break
    
    await message.answer(result)

@bot.on.message(IsPrivateRule() & IsSuperuserRule() & CommandRule("setrule"))
async def setrule(message):
    """Обработчик команды /setrule."""
    if not is_user_admin_in_any_registered_chat(message.from_id):
        await message.answer(
            "У вас нет зарегистрированных чатов. "
            "Сначала зарегистрируйте чат с помощью команды /register <chat_id>."
        )
        return
    
    message_text = message.text
    
    # Парсинг аргументов с использованием $ как разделителя
    # Паттерн: /setrule $trigger$ $response_text$
    pattern = r'/setrule\s+\$([^\$]+)\$\s+\$(.+?)\$$'
    match = re.match(pattern, message_text, re.DOTALL)
    
    if not match:
        pattern2 = r'\$([^\$]+)\$\s+\$(.+?)\$$'
        match = re.search(pattern2, message_text, re.DOTALL)
    
    if not match:
        await message.answer(
            "Неверный формат команды. Аргументы должны быть заключены в знаки доллара ($).\n"
            "Используйте: /setrule $!команда$ $Текст сообщения$\n\n"
            "Важно: оба аргумента должны быть обособлены знаками $ без пробелов между $ и текстом.\n"
            "Пример: /setrule $!правила$ $Правила чата: не спамить!$"
        )
        return
    
    trigger = match.group(1).strip()
    response_text = match.group(2).strip()
    
    if not trigger:
        await message.answer("Команда не может быть пустой.")
        return
    
    if not trigger.startswith('!'):
        await message.answer("Команда должна начинаться с символа '!'.")
        return
    
    if not response_text:
        await message.answer("Текст ответа не может быть пустым.")
        return
    
    if len(response_text) > 4096:
        await message.answer("Текст ответа не может превышать 4096 символов.")
        return
    
    global custom_commands
    custom_commands[trigger] = response_text
    
    try:
        save_custom_commands()
        await message.answer(f'Команда "{trigger}" успешно сохранена.')
    except IOError:
        await message.answer("Ошибка при работе с файлом команд.")

@bot.on.message(IsPrivateRule() & IsSuperuserRule() & CommandRule("delrule"))
async def delrule(message):
    """Обработчик команды /delrule."""
    if not is_user_admin_in_any_registered_chat(message.from_id):
        await message.answer(
            "У вас нет зарегистрированных чатов. "
            "Сначала зарегистрируйте чат с помощью команды /register <chat_id>."
        )
        return
    
    message_text = message.text
    
    pattern = r'/delrule\s+\$([^\$]+)\$'
    match = re.search(pattern, message_text)
    
    if not match:
        await message.answer(
            "Неверный формат команды. Аргумент должен быть заключен в знаки доллара ($).\n"
            "Используйте: /delrule $!команда$"
        )
        return
    
    trigger = match.group(1).strip()
    
    global custom_commands
    if trigger in custom_commands:
        del custom_commands[trigger]
        try:
            save_custom_commands()
            await message.answer(f'Команда "{trigger}" удалена.')
        except IOError:
            await message.answer("Ошибка при работе с файлом команд.")
    else:
        await message.answer(f'Команда "{trigger}" не найдена.')

# Эхо-обработчик для личных чатов (только суперпользователь, не команды)
@bot.on.message(IsPrivateRule() & IsSuperuserRule())
async def echo_handler(message):
    """Эхо-обработчик для личных чатов."""
    text = message.text
    if not text:
        return
    
    # Игнорируем команды (начинающиеся с '/' или '!')
    if text.startswith('/') or text.startswith('!'):
        return
    
    # Эхо-сообщение
    await message.answer(text)

# Обработчик для неавторизованных пользователей в личке
@bot.on.message(IsPrivateRule() & IsNotSuperuserRule())
async def unauthorized_handler(message):
    """Обработчик для неавторизованных пользователей."""
    await message.answer("Вы не авторизованный администратор.")

# ============================================================================
# ГРУППОВЫЕ ЧАТЫ
# ============================================================================

# !команды в групповых чатах (обработка команд с пробелами)
@bot.on.message(IsGroupRule() & StartsWithRule("!"))
async def custom_command_handler(message):
    """Обработчик !команд в групповых чатах."""
    text = message.text
    if not text:
        return
    
    # Игнорируем сообщения от других ботов
    if message.from_id < 0:
        return
    
    # Проверяем, является ли отправитель администратором
    is_admin = await is_user_admin_in_chat(api, message.peer_id, message.from_id)
    if not is_admin:
        logging.info(f"Пользователь {message.from_id} не является администратором в чате {message.peer_id}")
        return
    
    # Ищем команду - первое слово или фраза до конца
    # Команда может содержать пробелы, например "!ссылка правила"
    # Проверяем все возможные команды от длинных к коротким
    words = text.split()
    
    # Собираем возможные команды (от полного текста до первого слова)
    possible_commands = []
    for i in range(len(words), 0, -1):
        possible_cmd = ' '.join(words[:i])
        if possible_cmd in custom_commands:
            possible_commands.append(possible_cmd)
    
    if not possible_commands:
        return
    
    # Используем самую длинную совпавшую команду
    cmd_text = possible_commands[0]
    
    logging.info(f"Обработка команды {cmd_text} от пользователя {message.from_id} в чате {message.peer_id}")
    logging.info(f"Попытка удаления: peer_id={message.peer_id}, conversation_message_id={message.conversation_message_id}, from_id={message.from_id}")
    
    # Удаляем сообщение с командой
    try:
        logging.info(f"Удаление сообщения {message.conversation_message_id} в чате {message.peer_id}")
        result = await api.messages.delete(
            peer_id=message.peer_id,
            conversation_message_ids=[message.conversation_message_id]
        )
        logging.info(f"Результат удаления: {result}")
    except Exception as e:
        logging.error(f"Ошибка при удалении: {type(e).__name__}: {e}")
    
    response_text = custom_commands[cmd_text]
    
    # Отправляем ответ
    try:
        if message.reply_message:
            await api.messages.send(
                peer_id=message.peer_id,
                message=response_text,
                reply_to=message.conversation_message_id,
                random_id=random.randint(1,2**31)
            )
        else:
            await api.messages.send(
                peer_id=message.peer_id,
                message=response_text,
                random_id=random.randint(1,2**31)
            )
        logging.info(f"Команда {cmd_text} успешно выполнена")
    except Exception as e:
        logging.error(f"Ошибка при отправке ответа на команду {cmd_text}: {e}")

# Антиспам (только групповые чаты)
@bot.on.message(IsGroupRule())
async def antispam_handler(message):
    """Обработчик новых сообщений для антиспам-проверки."""
    # Если это !команда от админа, пропускаем
    if message.text and message.text.startswith('!'):
        if message.from_id >= 0:  # Не бот
            is_admin = await is_user_admin_in_chat(api, message.peer_id, message.from_id)
            if is_admin:
                return  # Админские команды не проверяем на спам
    
    await perform_spam_check(message)

# Системные сообщения (удаляем все автоматически)
@bot.on.message(IsGroupRule())
async def status_handler(message):
    """Обработчик системных сообщений."""
    # Проверяем, зарегистрирован ли этот чат
    registered_users = db_main.search(User.chats.any([message.peer_id]))
    
    for user_data in registered_users:
        delete_status = user_data.get('delete_statuses', {}).get(str(message.peer_id), False)
        if delete_status:
            try:
                await api.messages.delete(peer_id=message.peer_id, conversation_message_ids=[message.conversation_message_id])
            except Exception as e:
                logging.warning(f"Не удалось удалить статус в чате {message.peer_id}: {str(e)}")
            break

# ============================================================================
# АНТИСПАМ ЛОГИКА
# ============================================================================

# Паттерны для рекламы ботов
BOT_AD_PATTERNS = [
    r'@\w*bot',
    r't\.me/\w*bot',
    r'https://t\.me/\w*bot',
]

def has_bot_advertisement(text: str) -> bool:
    """Проверяет, содержит ли текст рекламу ботов."""
    for pattern in BOT_AD_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False

async def perform_spam_check(message):
    """Выполняет проверку сообщения на спам."""
    if not message.text and not message.attachments:
        return
    
    chat_id = message.peer_id
    from_user = message.from_id
    
    # Игнорируем сообщения от ботов
    if from_user < 0:
        return
    
    # Игнорируем сообщения от администраторов
    is_admin = await is_user_admin_in_chat(api, chat_id, from_user)
    if is_admin:
        return
    
    text = message.text or ""
    if not text:
        return
    
    # Проверка на критический спам
    crit_tokens = has_critical_patterns(text)
    crit_tokens_bool = crit_tokens is not None
    crit_tokens_string = crit_tokens.group() if crit_tokens else None
    
    # Проверка на обычный спам
    spam_tokens = new_is_spam_message(text)
    spam_tokens_bool = spam_tokens is not None
    
    # Проверка на смешанные слова
    mixed_words = has_mixed_words(text)
    num_mixed = len(mixed_words)
    
    # Проверка на эмодзи
    emoji_num = sum(1 for _ in emoji.emoji_list(text))
    emoji_critical_num = emoji_num > 12
    
    # Проверка на рекламу ботов
    is_bot_ad = has_bot_advertisement(text)
    
    is_critical = (
        crit_tokens_bool or
        num_mixed > 1 or
        emoji_critical_num
    )
    
    is_regular_spam = (
        spam_tokens_bool and not crit_tokens_bool
    )
    
    # Бан за критический спам
    if (len(text) < 500) and is_critical:
        verdict = f"""
<b>Критические токены:</b> {crit_tokens_bool} | {crit_tokens_string}
<b>Смешанные слова:</b> {num_mixed}; [ {', '.join(mixed_words)} ]
<b>Более 12 эмодзи:</b> {emoji_critical_num}
        """
        
        user_link = f"vk.com/id{from_user}"
        user_display_name = f"user{from_user}"
        
        message_text = text[:500]
        text_message_content = (
            f"🎯 <b>Автоматический бан:</b>\n\n"
            f"👤 <a href='{user_link}'><b>{user_display_name}</b></a> из чата {chat_id}\n\n"
            f"{message_text}\n{verdict}"
        )
        
        try:
            # Удаляем сообщение
            await api.messages.delete(peer_id=chat_id, conversation_message_ids=[message.conversation_message_id])
            
            # В VK нет прямого бана через бота, но можно удалить пользователя из беседы
            if chat_id > 2000000000:  # Беседа
                try:
                    await api.messages.remove_chat_user(chat_id=chat_id, user_id=from_user)
                except Exception as ban_error:
                    logging.warning(f"Не удалось удалить пользователя из беседы: {ban_error}")
            
            # Уведомляем зарегистрированных пользователей
            for user in db_main.all():
                if chat_id in user['chats']:
                    try:
                        await api.messages.send(
                            peer_id=user['user_id'],
                            message=text_message_content,
                            disable_web_page_preview=True,
                            random_id=random.randint(1,2**31)
                        )
                    except Exception as e:
                        logging.error(f"Ошибка при отправке уведомления: {e}")
            return
            
        except Exception as e:
            error_message = f"Возникла ошибка при автоматическом бане: {str(e)}\n\n{verdict}"
            for user in db_main.all():
                if chat_id in user['chats']:
                    try:
                        await api.messages.send(
                            peer_id=user['user_id'],
                            message=error_message,
                            random_id=random.randint(1,2**31)
                        )
                    except Exception as e:
                        logging.error(f"Ошибка при отправке уведомления об ошибке: {e}")
            return
    
    # Удаление за обычный спам или рекламу ботов
    elif (len(text) < 500) and (is_regular_spam or is_bot_ad):
        verdict = f"""
<b>Обычный спам:</b> {spam_tokens_bool}
<b>Реклама ботов:</b> {is_bot_ad}
        """
        
        try:
            await api.messages.delete(peer_id=chat_id, conversation_message_ids=[message.conversation_message_id])
            
            user_link = f"vk.com/id{from_user}"
            user_display_name = f"user{from_user}"
            
            notify_text = (
                f"🗑️ <b>Сообщение удалено (спам):</b>\n\n"
                f"👤 <a href='{user_link}'><b>{user_display_name}</b></a> из чата {chat_id}\n\n"
                f"{text[:500]}\n{verdict}"
            )
            
            for user in db_main.all():
                if chat_id in user['chats']:
                    try:
                        await api.messages.send(
                            peer_id=user['user_id'],
                            message=notify_text,
                            random_id=random.randint(1,2**31)
                        )
                    except Exception as e:
                        logging.error(f"Ошибка при отправке уведомления об удалении: {e}")
                        
        except Exception as e:
            logging.error(f"Ошибка при удалении спам-сообщения: {e}")

def main():
    print("VK Bot is working")
    
    load_config()
    load_custom_commands()
    cleanup_database()
    
    bot.run_forever()

if __name__ == '__main__':
    main()