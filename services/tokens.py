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
    Если файл не существует или пуст, создаёт его с данными для OAuth 2.1.
    
    Токены по умолчанию из ТЗ (для тестирования):
    - user_access_token: vk2.a.TC9tl31q7ig21luLLIgK9U4tUXzyUVQOKcobiO8WnEMB9cGTmm5EMh2TfLAZ24mf_0F_iSEz0Jeb5SQTWpygtQKCg_lWVhNE6IcTvcrEil2g0g_-UZeE5W7MVgySlpGl5BP5BnnPJVhIpQVrUgb80YLUokWWHfseTpExUVKf6JRXvWAbrwVo1oHIZ0WxNGsa6lLZHSKXE64W0B0ohG3fS2QqGAPnHYE9VwdhKAcI0OtI66Xz2s3ZQRoibqd9R4I_
    - user_refresh_token: vk2.a.a3orwIRYeUOr95A6l-LvHTmhHqXYReQ3vtFuJefIyUyzfW58UVAphLEGHhUO4BQvfoEbQMDvoeREBFyEmwX8Nn1sm7I7WHcfBj-eXzBAtrF-tPllU05lZZDH44ESfCyivh062hMIKa-p61nN_pTQfxUjM3dlfNzS0UIUrhZWaWMEtXO3T3aPW25LeSDxYtNgAp_KB5bH9NG6TPKivtdXYQlSNUX-YhT40g5hTJZ_FG0
    """
    global _user_access_token, _user_refresh_token, _client_id, _redirect_uri, _group_token
    
    load_dotenv()
    
    # Токены по умолчанию из ТЗ
    DEFAULT_TOKENS = {
        'user_access_token': 'vk2.a.TC9tl31q7ig21luLLIgK9U4tUXzyUVQOKcobiO8WnEMB9cGTmm5EMh2TfLAZ24mf_0F_iSEz0Jeb5SQTWpygtQKCg_lWVhNE6IcTvcrEil2g0g_-UZeE5W7MVgySlpGl5BP5BnnPJVhIpQVrUgb80YLUokWWHfseTpExUVKf6JRXvWAbrwVo1oHIZ0WxNGsa6lLZHSKXE64W0B0ohG3fS2QqGAPnHYE9VwdhKAcI0OtI66Xz2s3ZQRoibqd9R4I_',
        'user_refresh_token': 'vk2.a.a3orwIRYeUOr95A6l-LvHTmhHqXYReQ3vtFuJefIyUyzfW58UVAphLEGHhUO4BQvfoEbQMDvoeREBFyEmwX8Nn1sm7I7WHcfBj-eXzBAtrF-tPllU05lZZDH44ESfCyivh062hMIKa-p61nN_pTQfxUjM3dlfNzS0UIUrhZWaWMEtXO3T3aPW25LeSDxYtNgAp_KB5bH9NG6TPKivtdXYQlSNUX-YhT40g5hTJZ_FG0',
        'client_id': 54497712,
        'redirect_uri': 'https://oauth.vk.com/blank.html'
    }
    
    try:
        need_create = False
        
        if not os.path.exists(TOKENS_FILE):
            need_create = True
            logging.info("tokens.json не существует, будет создан")
        else:
            # Проверяем, не пустой ли файл
            try:
                with open(TOKENS_FILE, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if not content or content == '{}':
                        need_create = True
                        logging.info("tokens.json пуст, будет перезаписан")
                    else:
                        tokens = json.loads(content)
                        # Проверяем наличие required ключей
                        if 'user_access_token' not in tokens or not tokens.get('user_access_token'):
                            need_create = True
                            logging.info("tokens.json не содержит user_access_token, будет перезаписан")
            except json.JSONDecodeError:
                need_create = True
                logging.info("tokens.json повреждён, будет перезаписан")
        
        if need_create:
            # Пробуем взять старый токен из .env если есть
            user_token = os.getenv('USER_TOKEN', '')
            if user_token:
                tokens = {
                    'user_access_token': user_token,
                    'user_refresh_token': '',
                    'client_id': 54497712,
                    'redirect_uri': 'https://oauth.vk.com/blank.html'
                }
            else:
                # Используем токены по умолчанию из ТЗ
                tokens = DEFAULT_TOKENS.copy()
            
            save_tokens_data(tokens)
            logging.info("tokens.json создан с OAuth 2.1 структурой")
            return tokens
        
        with open(TOKENS_FILE, "r", encoding="utf-8") as f:
            tokens = json.load(f)
            _load_globals(tokens)
            logging.info("Токены загружены из tokens.json")
            return tokens
            
    except json.JSONDecodeError as e:
        logging.error(f"Ошибка парсинга JSON в tokens.json: {e}")
        # Возвращаем дефолтные токены при ошибке
        tokens = DEFAULT_TOKENS.copy()
        save_tokens_data(tokens)
        _load_globals(tokens)
        return tokens
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