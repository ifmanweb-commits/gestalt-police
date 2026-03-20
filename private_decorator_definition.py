from functools import wraps
import os
import json

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
SUPERUSER_ID = None

def load_superuser_id():
    """Загружает SUPERUSER_ID из config.json."""
    global SUPERUSER_ID
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                SUPERUSER_ID = config.get('superuser_id')
    except Exception:
        pass

# Загружаем при импорте модуля
load_superuser_id()

def is_superuser(user_id: int) -> bool:
    """Проверяет, является ли пользователь суперпользователем."""
    return SUPERUSER_ID is not None and user_id == SUPERUSER_ID

def is_private_chat(peer_id: int, from_id: int) -> bool:
    """В VK: если peer_id == from_id, то это личный чат."""
    return peer_id == from_id

def private_chat_only(func):
    """Декоратор для обработки команд только в личных чатах и только от суперпользователя.
    
    Для использования в vkbottle-ботах.
    """
    @wraps(func)
    async def wrapped(message, *args, **kwargs):
        # Проверяем, что это личный чат
        if message.peer_id != message.from_id:
            # В групповых чатах просто игнорируем команду
            return
        
        # Проверяем, является ли пользователь суперпользователем
        if not is_superuser(message.from_id):
            await message.answer("Это приватный бот, он недоступен для вас.")
            return
        
        return await func(message, *args, **kwargs)
    return wrapped