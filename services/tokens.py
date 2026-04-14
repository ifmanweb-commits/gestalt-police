"""
Модуль для управления токенами VK API.
Токены хранятся в tokens.json и загружаются при старте.
При первом запуске токены берутся из .env
"""
import json
import logging
import os
from dotenv import load_dotenv

TOKENS_FILE = "./tokens.json"

# Глобальные переменные для хранения токенов
_user_token = None
_group_token = None


def load_tokens() -> dict:
    """
    Загружает токены из tokens.json.
    Если файл не существует, создаёт его из переменных окружения .env
    
    Returns:
        dict: Словарь с токенами {'user_token': str, 'group_token': str}
    """
    global _user_token, _group_token
    
    load_dotenv()
    
    try:
        if not os.path.exists(TOKENS_FILE):
            # Файл не существует - создаём из .env
            user_token = os.getenv('USER_TOKEN')
            group_token = os.getenv('VK_TOKEN')
            
            if not user_token or not group_token:
                logging.error("Токены не найдены в .env и tokens.json не существует")
                return {'user_token': None, 'group_token': None}
            
            tokens = {
                'user_token': user_token,
                'group_token': group_token
            }
            save_tokens(user_token, group_token)
            logging.info("tokens.json создан из переменных окружения")
            _user_token = user_token
            _group_token = group_token
            return tokens
        
        # Файл существует - загружаем из него
        with open(TOKENS_FILE, "r", encoding="utf-8") as f:
            tokens = json.load(f)
            _user_token = tokens.get('user_token')
            _group_token = tokens.get('group_token')
            logging.info("Токены загружены из tokens.json")
            return tokens
            
    except json.JSONDecodeError as e:
        logging.error(f"Ошибка парсинга JSON в tokens.json: {e}")
        return {'user_token': None, 'group_token': None}
    except IOError as e:
        logging.error(f"Ошибка чтения tokens.json: {e}")
        return {'user_token': None, 'group_token': None}


def save_tokens(user_token: str, group_token: str) -> None:
    """
    Сохраняет токены в tokens.json.
    
    Args:
        user_token: Пользовательский токен
        group_token: Групповой токен
    """
    global _user_token, _group_token
    
    tokens = {
        'user_token': user_token,
        'group_token': group_token
    }
    
    try:
        with open(TOKENS_FILE, "w", encoding="utf-8") as f:
            json.dump(tokens, f, indent=2, ensure_ascii=False)
        _user_token = user_token
        _group_token = group_token
        logging.info("Токены сохранены в tokens.json")
    except IOError as e:
        logging.error(f"Ошибка записи tokens.json: {e}")
        raise


def get_user_token() -> str | None:
    """
    Возвращает текущий пользовательский токен.
    
    Returns:
        str | None: Пользовательский токен или None
    """
    return _user_token


def get_group_token() -> str | None:
    """
    Возвращает текущий групповой токен.
    
    Returns:
        str | None: Групповой токен или None
    """
    return _group_token


def update_user_token(new_token: str) -> bool:
    """
    Обновляет пользовательский токен.
    
    Args:
        new_token: Новый пользовательский токен
        
    Returns:
        bool: True если токен успешно обновлён
    """
    global _user_token
    
    try:
        current_group = get_group_token()
        if current_group is None:
            logging.error("Групповой токен не найден при обновлении user_token")
            return False
        
        save_tokens(new_token, current_group)
        _user_token = new_token
        logging.info("Пользовательский токен обновлён")
        return True
    except Exception as e:
        logging.error(f"Ошибка обновления пользовательского токена: {e}")
        return False