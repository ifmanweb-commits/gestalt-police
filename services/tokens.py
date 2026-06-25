"""
Модуль для управления токенами VK API.

wall_token - групповой токен для публикации постов на стене группы "Зона роста".
Групповой токен для работы с сообщениями хранится в .env (VK_TOKEN) и загружается через get_group_token().

Структура tokens.json:
{
  "wall_token": "vk1.a...."
}
"""
import json
import os
from dotenv import load_dotenv
from services.logger import log

TOKENS_FILE = "./tokens.json"

# Глобальная переменная для хранения wall_token
_wall_token = None


def load_tokens() -> dict:
    """
    Загружает токены из tokens.json.
    Если файл не существует или пуст, создаёт его с пустой структурой.
    
    Returns:
        dict: Словарь с токенами
    """
    global _wall_token
    
    load_dotenv()
    
    DEFAULT_TOKENS = {
        'wall_token': ''
    }
    
    try:
        need_create = False
        
        if not os.path.exists(TOKENS_FILE):
            need_create = True
            log("tokens.json не существует, будет создан")
        else:
            # Проверяем, не пустой ли файл
            try:
                with open(TOKENS_FILE, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if not content or content == '{}':
                        need_create = True
                        log("tokens.json пуст, будет перезаписан")
                    else:
                        tokens = json.loads(content)
                        # Проверяем наличие wall_token
                        if 'wall_token' not in tokens:
                            # Миграция со старой структуры
                            tokens = DEFAULT_TOKENS.copy()
                            need_create = True
                            log("tokens.json не содержит wall_token, будет создана новая структура")
            except json.JSONDecodeError:
                need_create = True
                log("tokens.json повреждён, будет перезаписан")
        
        if need_create:
            tokens = DEFAULT_TOKENS.copy()
            save_tokens_data(tokens)
            log("tokens.json создан")
            return tokens
        
        with open(TOKENS_FILE, "r", encoding="utf-8") as f:
            tokens = json.load(f)
            _load_globals(tokens)
            log("Токены загружены из tokens.json")
            return tokens
            
    except json.JSONDecodeError as e:
        log(f"Ошибка парсинга JSON в tokens.json: {e}")
        tokens = DEFAULT_TOKENS.copy()
        save_tokens_data(tokens)
        _load_globals(tokens)
        return tokens
    except IOError as e:
        log(f"Ошибка чтения tokens.json: {e}")
        return {}


def _load_globals(tokens: dict) -> None:
    """Загружает глобальные переменные из словаря токенов."""
    global _wall_token
    
    _wall_token = tokens.get('wall_token', '')


def save_tokens_data(tokens: dict) -> None:
    """Сохраняет токены в tokens.json."""
    global _wall_token
    
    try:
        with open(TOKENS_FILE, "w", encoding="utf-8") as f:
            json.dump(tokens, f, indent=2, ensure_ascii=False)
        _load_globals(tokens)
        log("Токены сохранены в tokens.json")
    except IOError as e:
        log(f"Ошибка записи tokens.json: {e}")
        raise


def get_wall_token() -> str | None:
    """Возвращает текущий wall_token для публикации постов на стене."""
    return _wall_token


def get_group_token() -> str | None:
    """Возвращает групповой токен из .env для работы с сообщениями."""
    load_dotenv()
    return os.getenv('VK_TOKEN')


def update_wall_token(token: str) -> bool:
    """
    Обновляет wall_token.
    
    Args:
        token: Новый wall_token
        
    Returns:
        bool: True если успешно
    """
    global _wall_token
    
    try:
        tokens = {
            'wall_token': token
        }
        save_tokens_data(tokens)
        log("wall_token обновлён")
        return True
    except Exception as e:
        log(f"Ошибка обновления wall_token: {e}")
        return False