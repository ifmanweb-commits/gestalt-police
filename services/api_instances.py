"""
Экземпляры VK API для разных задач.

Разделение токенов:
- group_api: групповой токен для модерации, команд, вопросов (группа "Гештальт-полиция")
- wall_api: групповой токен для публикации постов на стене (группа "Зона роста")

Токены загружаются:
- group_api из .env (VK_TOKEN)
- wall_api из tokens.json (wall_token)
"""
import logging
from vkbottle import API
from services.tokens import get_wall_token, get_group_token

# Глобальные переменные для API клиентов
group_api = None
wall_api = None


def init_apis():
    """
    Инициализирует API клиенты.
    group_api - из .env (VK_TOKEN) для работы с сообщениями
    wall_api - из tokens.json (wall_token) для публикации на стене
    
    Должна вызываться при старте бота после загрузки токенов.
    """
    global group_api, wall_api
    
    group_token = get_group_token()
    wall_token = get_wall_token()
    
    if not group_token:
        logging.error("Групповой токен не найден в .env, group_api не инициализирован")
    else:
        group_api = API(group_token)
        logging.info("group_api инициализирован (группа Гештальт-полиция)")
    
    if not wall_token:
        logging.error("wall_token не найден в tokens.json, wall_api не инициализирован")
    else:
        wall_api = API(wall_token)
        logging.info("wall_api инициализирован (группа Зона роста)")


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
