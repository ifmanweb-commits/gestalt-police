"""
Модуль для управления токенами VK API.
Поддержка OAuth 2.1 с refresh_token для автоматического обновления.

Структура tokens.json:
{
  "user_access_token": "...",
  "user_refresh_token": "...",
  "client_id": 54497712,
  "redirect_uri": "https://oauth.vk.com/blank.html"
}

Групповой токен хранится в .env (VK_TOKEN) и не трогается.
"""
import json
import logging
import os
from dotenv import load_dotenv

TOKENS_FILE = "./tokens.json"

# Глобальные переменные для хранения токенов
_user_access_token = None
_user_refresh_token = None
_client_id = None
_redirect_uri = None
_group_token = None


def load_tokens() -> dict:
    """
    Загружает токены из tokens.json.
    Если файл не существует, создаёт его с данными для OAuth 2.1.
    """
    global _user_access_token, _user_refresh_token, _client_id, _redirect_uri, _group_token
    
    load_dotenv()
    
    try:
        if not os.path.exists(TOKENS_FILE):
            user_token = os.getenv('USER_TOKEN', '')
            tokens = {
                'user_access_token': user_token,
                'user_refresh_token': '',
                'client_id': 54497712,
                'redirect_uri': 'https://oauth.vk.com/blank.html'
            }
            save_tokens_data(tokens)
            logging.info("tokens.json создан с OAuth 2.1 структурой")
            _load_globals(tokens)
            return tokens
        
        with open(TOKENS_FILE, "r", encoding="utf-8") as f:
            tokens = json.load(f)
            _load_globals(tokens)
            logging.info("Токены загружены из tokens.json")
            return tokens
            
    except json.JSONDecodeError as e:
        logging.error(f"Ошибка парсинга JSON в tokens.json: {e}")
        return {}
    except IOError as e:
        logging.error(f"Ошибка чтения tokens.json: {e}")
        return {}


def _load_globals(tokens: dict) -> None:
    """Загружает глобальные переменные из словаря токенов."""
    global _user_access_token, _user_refresh_token, _client_id, _redirect_uri
    
    if 'user_access_token' in tokens:
        _user_access_token = tokens.get('user_access_token')
    else:
        _user_access_token = tokens.get('user_token', '')
    
    _user_refresh_token = tokens.get('user_refresh_token', '')
    _client_id = tokens.get('client_id', 54497712)
    _redirect_uri = tokens.get('redirect_uri', 'https://oauth.vk.com/blank.html')


def save_tokens_data(tokens: dict) -> None:
    """Сохраняет токены в tokens.json."""
    global _user_access_token, _user_refresh_token, _client_id, _redirect_uri
    
    try:
        with open(TOKENS_FILE, "w", encoding="utf-8") as f:
            json.dump(tokens, f, indent=2, ensure_ascii=False)
        _load_globals(tokens)
        logging.info("Токены сохранены в tokens.json")
    except IOError as e:
        logging.error(f"Ошибка записи tokens.json: {e}")
        raise


def get_user_access_token() -> str | None:
    """Возвращает текущий пользовательский access_token."""
    return _user_access_token


def get_user_refresh_token() -> str | None:
    """Возвращает текущий пользовательский refresh_token."""
    return _user_refresh_token


def get_client_id() -> int:
    """Возвращает client_id приложения."""
    return _client_id or 54497712


def get_redirect_uri() -> str:
    """Возвращает redirect_uri."""
    return _redirect_uri or 'https://oauth.vk.com/blank.html'


def get_group_token() -> str | None:
    """Возвращает групповой токен из .env."""
    load_dotenv()
    return os.getenv('VK_TOKEN')


async def refresh_access_token() -> bool:
    """
    Обновляет access_token используя refresh_token через VK OAuth API.
    
    Returns:
        bool: True если токен успешно обновлён
    """
    global _user_access_token, _user_refresh_token
    
    refresh_token = get_user_refresh_token()
    if not refresh_token:
        logging.error("refresh_token не найден, невозможно обновить access_token")
        return False
    
    client_id = get_client_id()
    
    url = "https://oauth.vk.com/access_token"
    params = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': client_id
    }
    
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params) as response:
                data = await response.json()
                
                if 'access_token' in data:
                    new_access_token = data['access_token']
                    new_refresh_token = data.get('refresh_token', refresh_token)
                    
                    tokens = {
                        'user_access_token': new_access_token,
                        'user_refresh_token': new_refresh_token,
                        'client_id': client_id,
                        'redirect_uri': get_redirect_uri()
                    }
                    save_tokens_data(tokens)
                    
                    logging.info("access_token успешно обновлён через refresh_token")
                    return True
                else:
                    logging.error(f"Ошибка обновления токена: {data}")
                    return False
                    
    except Exception as e:
        logging.error(f"Ошибка при обновлении access_token: {e}")
        return False


def update_user_tokens(access_token: str, refresh_token: str = None) -> bool:
    """
    Обновляет токены пользователя.
    
    Args:
        access_token: Новый access_token
        refresh_token: Новый refresh_token (опционально)
        
    Returns:
        bool: True если успешно
    """
    global _user_access_token, _user_refresh_token
    
    try:
        tokens = {
            'user_access_token': access_token,
            'user_refresh_token': refresh_token or _user_refresh_token,
            'client_id': get_client_id(),
            'redirect_uri': get_redirect_uri()
        }
        save_tokens_data(tokens)
        logging.info("Токены пользователя обновлены")
        return True
    except Exception as e:
        logging.error(f"Ошибка обновления токенов: {e}")
        return False