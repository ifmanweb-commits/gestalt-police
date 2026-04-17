"""
Обработчики админ-команд для VK бота.
"""
import logging
import re
from vkbottle import API
from vkbottle.bot import Message

from config import SUPERUSER_ID
from database import get_bot_db
from models.experts_db import add_expert, remove_expert, get_expert_list
from services.custom_commands import add_command, remove_command, get_all_commands, save_custom_commands
from services.vk_api import resolve_user_id
from services.spam_check import is_user_admin_in_chat, _update_admin_cache, _is_admin_cache_valid, _get_admin_cache_record
from services.tokens import get_wall_token, update_wall_token
from services import api_instances
from services.api_instances import check_token_validity
from config import GROUP_ID
from tinydb import Query

logger = logging.getLogger(__name__)


async def register_chat(message: Message, api: API):
    """
    /register <chat_id> - Зарегистрировать чат.
    """
    logger.info(f"register_chat вызван от user_id={message.from_id}, текст={message.text}")
    args = message.text.split()
    if len(args) < 2:
        await message.answer('Добавьте идентификатор чата после команды.')
        return
    
    try:
        chat_id = int(args[1])
        logger.info(f"Парсинг chat_id={chat_id} успешен")
    except ValueError as e:
        logger.error(f"Ошибка парсинга chat_id: {e}")
        await message.answer('Неверный формат идентификатора чата. Используйте числовой ID.')
        return
    
    user_id = message.from_id
    logger.info(f"Проверка пользователя в БД: user_id={user_id}")
    db = get_bot_db()
    User = Query()
    user_data = db.get(User.user_id == user_id)
    
    if user_data:
        logger.info(f"Пользователь найден в БД: {user_data}")
        if chat_id not in user_data['chats']:
            user_data['chats'].append(chat_id)
            if 'delete_statuses' not in user_data:
                user_data['delete_statuses'] = {}
            user_data['delete_statuses'][str(chat_id)] = False
            db.update(user_data, User.user_id == user_id)
            logger.info(f"Добавлен чат {chat_id} в список пользователя")
    else:
        logger.info(f"Пользователь не найден, создаем новую запись")
        db.insert({'user_id': user_id, 'chats': [chat_id], 'delete_statuses': {str(chat_id): False}})
        logger.info(f"Создана новая запись для пользователя {user_id}")
    
    await message.answer(f'Зарегистрирован чат {chat_id}')
    logger.info(f"register_chat завершен успешно")


async def unregister_chat(message: Message, api: API):
    """
    /unregister <chat_id> - Отменить регистрацию чата.
    """
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
    db = get_bot_db()
    User = Query()
    user_data = db.get(User.user_id == user_id)
    
    if user_data and chat_id in user_data['chats']:
        user_data['chats'].remove(chat_id)
        if 'delete_statuses' in user_data:
            user_data['delete_statuses'].pop(str(chat_id), None)
        db.update(user_data, User.user_id == user_id)
        await message.answer(f'Отменена регистрация чата {chat_id}.')
    else:
        await message.answer('Чат не зарегистрирован.')


async def list_chats(message: Message, api: API):
    """
    /list - Показать зарегистрированные чаты.
    """
    user_id = message.from_id
    db = get_bot_db()
    User = Query()
    user_data = db.get(User.user_id == user_id)
    
    if user_data and user_data['chats']:
        chat_list = "Ваши зарегистрированные чаты:\n\n"
        for chat_id in user_data['chats']:
            delete_status = user_data.get('delete_statuses', {}).get(str(chat_id), False)
            status = "Включено" if delete_status else "Отключено"
            chat_list += f"Идентификатор: {chat_id}\nУдаление статусов: {status}\n\n"
        await message.answer(chat_list)
    else:
        await message.answer("У вас нет зарегистрированных чатов.")


async def ruleslist(message: Message, api: API):
    """
    /ruleslist - Показать список команд.
    """
    db = get_bot_db()
    User = Query()
    user_data = db.get(User.user_id == message.from_id)
    
    if not user_data or not user_data.get('chats'):
        await message.answer(
            "У вас нет зарегистрированных чатов. "
            "Сначала зарегистрируйте чат с помощью команды /register <chat_id>."
        )
        return
    
    commands = get_all_commands()
    if not commands:
        await message.answer("Список пользовательских команд пуст.")
        return
    
    result = "📋 **Список пользовательских команд:**\n\n"
    for cmd_name, text in commands.items():
        result += f"{cmd_name}:\n{text}\n\n"
        if len(result) > 4000:
            result += "... (продолжение следует)"
            break
    
    await message.answer(result)


async def setrule(message: Message, api: API):
    """
    /setrule $!команда$ $Текст сообщения$ - Создать команду.
    """
    message_text = message.text
    
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
    
    if add_command(trigger, response_text):
        await message.answer(f'Команда "{trigger}" успешно сохранена.')
    else:
        await message.answer("Ошибка при работе с файлом команд.")


async def delrule(message: Message, api: API):
    """
    /delrule $!команда$ - Удалить команду.
    """
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
    
    if remove_command(trigger):
        await message.answer(f'Команда "{trigger}" удалена.')
    else:
        await message.answer(f'Команда "{trigger}" не найдена.')


async def expert_reg(message: Message, api: API):
    """
    /expertreg <id|url> - Добавить эксперта.
    """
    args = message.text.split()
    if len(args) < 2:
        await message.answer('Добавьте ID пользователя или ссылку на профиль.')
        return
    
    identifier = args[1]
    user_id = await resolve_user_id(api, identifier)
    
    if user_id is None:
        await message.answer('Не удалось определить пользователя.')
        return
    
    result = add_expert(user_id, identifier)
    await message.answer(result['message'])


async def expert_del(message: Message, api: API):
    """
    /expertdel <id> - Удалить эксперта.
    """
    args = message.text.split()
    if len(args) < 2:
        await message.answer('Добавьте ID пользователя после команды.')
        return
    
    try:
        user_id = int(args[1])
    except ValueError:
        await message.answer('ID должен быть числом.')
        return
    
    result = remove_expert(user_id)
    await message.answer(result['message'])


async def expert_list(message: Message, api: API):
    """
    /expertlist - Показать список экспертов.
    """
    experts = get_expert_list()
    
    if not experts:
        await message.answer('Список экспертов пуст.')
        return
    
    result = f"📋 **Список экспертов** ({len(experts)}):\n\n"
    for expert in experts:
        user_id = expert.get('user_id', 'Unknown')
        url = expert.get('url', 'Unknown')
        result += f"• {user_id} - {url}\n"
    
    await message.answer(result)


async def get_chat_id(message: Message, api: API):
    """
    /chatid - Получить ID чата.
    Работает только для администраторов.
    """
    # Проверяем администратора
    is_admin = await is_user_admin_in_chat(api, message.peer_id, message.from_id)
    if not is_admin:
        await message.answer("❌ Эта команда доступна только администраторам чата.")
        return
    
    await message.answer(f"ID этого чата: {message.peer_id}")


async def refresh_admin_cache(message: Message, api: API):
    """
    /refresh_admins - Принудительно обновить кэш администраторов.
    Работает только для администраторов.
    """
    # Сначала проверяем по текущему кэшу (чтобы не любой мог обновлять)
    is_admin = await is_user_admin_in_chat(api, message.peer_id, message.from_id)
    if not is_admin:
        await message.answer("❌ Эта команда доступна только администраторам чата.")
        return
    
    chat_id = message.peer_id
    
    # Обновляем кэш через API
    admin_ids = await _update_admin_cache(api, chat_id)
    
    if admin_ids:
        await message.answer(f"✅ Кэш администраторов обновлён. Найдено {len(admin_ids)} администраторов.")
    else:
        await message.answer("⚠️ Не удалось получить список администраторов. Проверьте права бота в чате.")


async def set_wall_token(message: Message, api: API):
    """
    /setwalltoken <новый_токен> - Обновить wall_token для публикации на стене.
    Работает только для суперпользователя.
    """
    if message.from_id != SUPERUSER_ID:
        await message.answer("❌ Эта команда доступна только суперпользователю.")
        return
    
    # Получаем полный текст команды
    full_text = message.text.strip()
    
    # Парсим команду: /setwalltoken <токен>
    parts = full_text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "❌ Не указан новый токен.\n\n"
            "Используйте: /setwalltoken <vk1.a.xxxxx>"
        )
        return
    
    new_token = parts[1].strip()
    
    if not new_token:
        await message.answer("❌ Токен не может быть пустым.")
        return
    
    # Проверяем валидность токена
    is_valid = await check_token_validity(new_token)
    if not is_valid:
        await message.answer("❌ Токен недействителен. Проверьте правильность токена.")
        return
    
    # Обновляем токен в tokens.json
    if update_wall_token(new_token):
        # Пересоздаём API клиент с новым токеном
        api_instances.wall_api = API(new_token)
        await message.answer("✅ wall_token успешно обновлён и применён без перезапуска бота.")
    else:
        await message.answer("❌ Ошибка при сохранении токена.")


async def check_wall_token_cmd(message: Message, api: API):
    """
    /checkwalltoken - Проверить текущий wall_token.
    Работает только для суперпользователя.
    """
    if message.from_id != SUPERUSER_ID:
        await message.answer("❌ Эта команда доступна только суперпользователю.")
        return
    
    current_token = get_wall_token()
    if not current_token:
        await message.answer("❌ wall_token не найден.")
        return
    
    is_valid = await check_token_validity(current_token)
    if is_valid:
        await message.answer("✅ Токен работает корректно.")
    else:
        await message.answer("❌ Токен недействителен. Используйте /setwalltoken для обновления.")


async def test_post_cmd(message: Message, api: API):
    """
    /testpost - Опубликовать тестовый пост на стене группы.
    Работает только для суперпользователя.
    """
    if message.from_id != SUPERUSER_ID:
        await message.answer("❌ Эта команда доступна только суперпользователю.")
        return
    
    if api_instances.wall_api is None:
        await message.answer("❌ wall_api не инициализирован. Проверьте tokens.json.")
        return
    
    try:
        owner_id = -GROUP_ID
        
        response = await api_instances.wall_api.wall.post(
            owner_id=owner_id,
            message="🧪 Тестовый пост\n\nЭто тестовое сообщение для проверки работы бота."
        )
        
        post_id = response.post_id
        await message.answer(f"✅ Тестовый пост успешно опубликован!\n\nID поста: {post_id}")
        
    except Exception as e:
        logging.error(f"Ошибка при публикации тестового поста: {e}")
        await message.answer(f"❌ Ошибка при публикации поста: {e}")