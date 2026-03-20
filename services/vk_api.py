"""
Сервис для работы с VK API.
"""
import re
import logging
from vkbottle import API


async def get_user_name(api: API, user_id: int) -> str:
    """
    Получает имя пользователя по ID.
    
    Args:
        api: VK API экземпляр
        user_id: ID пользователя
        
    Returns:
        str: Имя пользователя или user{user_id} если не удалось получить
    """
    try:
        user_info = await api.users.get(user_ids=[user_id])
        if user_info:
            return f"{user_info[0].first_name} {user_info[0].last_name}"
    except Exception as e:
        logging.error(f"Не удалось получить имя пользователя {user_id}: {e}")
    return f"user{user_id}"


async def resolve_user_id(api: API, identifier: str) -> int:
    """
    Определяет user_id по числу или ссылке.
    
    Args:
        api: VK API экземпляр
        identifier: Числовой ID или ссылка на профиль
        
    Returns:
        int: user_id или None, если не удалось определить
    """
    # Пробуем распарсить как число
    if identifier.isdigit():
        user_id = int(identifier)
        try:
            user_info = await api.users.get(user_ids=[user_id])
            if user_info:
                return user_id
            else:
                logging.warning(f"Пользователь с ID {user_id} не найден")
                return None
        except Exception as e:
            logging.error(f"Ошибка проверки ID {user_id}: {e}")
            return None
    
    # Пробуем извлечь из ссылки
    # Формат: https://vk.com/id123456789 или https://vk.com/username
    match = re.search(r'vk\.com/(?:id)?([a-zA-Z0-9_]+)', identifier)
    if not match:
        return None
    
    screen_name = match.group(1)
    
    # Если это числовой ID в ссылке
    if screen_name.isdigit():
        user_id = int(screen_name)
        try:
            user_info = await api.users.get(user_ids=[user_id])
            if user_info:
                return user_id
        except Exception as e:
            logging.error(f"Ошибка проверки ID {user_id}: {e}")
            return None
    
    # Это короткое имя (screen_name)
    try:
        user_info = await api.users.get(user_ids=[screen_name])
        if user_info:
            return user_info[0].id
        else:
            logging.warning(f"Пользователь с именем {screen_name} не найден")
            return None
    except Exception as e:
        logging.error(f"Ошибка получения ID по screen_name {screen_name}: {e}")
        return None