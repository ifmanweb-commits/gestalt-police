"""
Экземпляры VK API для разных задач.

Разделение токенов:
- group_api: групповой токен для модерации, команд, вопросов
- user_api: пользовательский токен только для публикации постов от имени сообщества

Токены загружаются из tokens.json через модуль services.tokens.
"""
import logging
from vkbottle import API
from services.tokens import get_user_token, get_group_token

# Глобальные переменные для API клиентов
group_api = None
user_api = None


def init_apis():
    """
    Инициализирует API клиенты из tokens.json.
    Должна вызываться при старте бота после загрузки токенов.
    """
    global group_api, user_api
    
    group_token = get_group_token()
    user_token = get_user_token()
    
    if not group_token:
        logging.error("Групповой токен не найден, group_api не инициализирован")
    else:
        group_api = API(group_token)
        logging.info("group_api инициализирован")
    
    if not user_token:
        logging.error("Пользовательский токен не найден, user_api не инициализирован")
    else:
        user_api = API(user_token)
        logging.info("user_api инициализирован")


def refresh_user_api(new_token: str):
    """
    Пересоздаёт user_api с новым токеном.
    
    Args:
        new_token: Новый пользовательский токен
    """
    global user_api
    
    if new_token:
        user_api = API(new_token)
        logging.info("user_api обновлён с новым токеном")
    else:
        logging.error("Попытка обновить user_api с пустым токеном")


async def check_token_validity(token: str) -> bool:
    """
    Проверяет валидность токена через users.get.
    
    Args:
        token: Токен для проверки
        
    Returns:
        bool: True если токен валиден
    """
    try:
        test_api = API(token)
        result = await test_api.users.get(user_ids=[1])
        return bool(result)
    except Exception as e:
        logging.error(f"Токен невалиден: {e}")
        return False
