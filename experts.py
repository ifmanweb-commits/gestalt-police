"""
Модуль управления экспертами для VK бота.
Использует TinyDB для хранения данных.
"""

import os
import re
import logging
from tinydb import TinyDB, Query
from vkbottle import API

# Пути к файлам баз данных
EXPERTS_FILE = "./experts.json"
QUESTIONS_FILE = "./questions.json"

# Инициализация баз данных
def init_databases():
    """Инициализирует базы данных, создаёт файлы если они не существуют."""
    # Создаём файлы если не существуют
    # TinyDB ожидает пустой массив [], а не объект {}
    if not os.path.exists(EXPERTS_FILE):
        with open(EXPERTS_FILE, "w", encoding="utf-8") as f:
            f.write("[]")
    
    if not os.path.exists(QUESTIONS_FILE):
        with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
            f.write("[]")
    
    return get_experts_db(), get_questions_db()


def get_experts_db():
    """Возвращает экземпляр TinyDB для экспертов."""
    return TinyDB(EXPERTS_FILE)


def get_questions_db():
    """Возвращает экземпляр TinyDB для вопросов."""
    return TinyDB(QUESTIONS_FILE)


async def resolve_user_id(api: API, identifier: str) -> int:
    """
    Определяет user_id по числу или ссылке.
    
    Args:
        api: VK API
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


def extract_user_id_from_url(url: str) -> int:
    """
    Извлекает user_id из ссылки vk.com.
    
    Args:
        url: Ссылка на профиль пользователя VK
        
    Returns:
        int: ID пользователя или None если не удалось извлечь
    """
    match = re.search(r'vk\.com/(?:id)?(\d+)', url)
    if match:
        return int(match.group(1))
    return None


def is_expert(user_id: int) -> bool:
    """
    Проверяет, является ли пользователь экспертом.
    
    Args:
        user_id: ID пользователя для проверки
        
    Returns:
        bool: True если пользователь является экспертом
    """
    db = get_experts_db()
    Expert = Query()
    expert = db.get(Expert.user_id == user_id)
    return expert is not None


def add_expert(user_id: int, url: str) -> dict:
    """
    Добавляет эксперта в базу данных.
    
    Args:
        user_id: ID пользователя
        url: Ссылка на профиль VK
        
    Returns:
        dict: Результат операции {'success': bool, 'message': str, 'expert': dict}
    """
    db = get_experts_db()
    Expert = Query()
    
    # Проверяем, существует ли уже эксперт
    existing = db.get(Expert.user_id == user_id)
    if existing:
        return {
            'success': False,
            'message': f'Пользователь {user_id} уже в списке экспертов',
            'expert': existing
        }
    
    # Добавляем нового эксперта
    expert_data = {
        'user_id': user_id,
        'url': url
    }
    db.insert(expert_data)
    
    return {
        'success': True,
        'message': f'Эксперт {user_id} добавлен',
        'expert': expert_data
    }


def remove_expert(user_id: int) -> dict:
    """
    Удаляет эксперта из базы данных.
    
    Args:
        user_id: ID пользователя для удаления
        
    Returns:
        dict: Результат операции {'success': bool, 'message': str}
    """
    db = get_experts_db()
    Expert = Query()
    
    # Проверяем, существует ли эксперт
    existing = db.get(Expert.user_id == user_id)
    if not existing:
        return {
            'success': False,
            'message': f'Пользователь {user_id} не найден в списке экспертов'
        }
    
    # Удаляем эксперта
    db.remove(Expert.user_id == user_id)
    
    return {
        'success': True,
        'message': f'Эксперт {user_id} удалён'
    }


def get_expert_list() -> list:
    """
    Получает список всех экспертов.
    
    Returns:
        list: Список экспертов с их данными
    """
    db = get_experts_db()
    return db.all()


def get_expert_count() -> int:
    """
    Получает количество экспертов.
    
    Returns:
        int: Количество экспертов в базе
    """
    db = get_experts_db()
    return len(db.all())