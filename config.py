"""
Модуль конфигурации.
Загружает настройки из config.json.
"""
import json
import logging
import os

CONFIG_FILE = "./config.json"

# Глобальные переменные для конфигурации
SUPERUSER_ID = None
EXPERTS_CHAT_ID = None
GROUP_ID = None


def load_config():
    """
    Загружает конфигурацию из config.json.
    """
    global SUPERUSER_ID, EXPERTS_CHAT_ID, GROUP_ID
    try:
        if not os.path.exists(CONFIG_FILE):
            logging.error("config.json не найден")
            return
        
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            SUPERUSER_ID = config.get('superuser_id')
            EXPERTS_CHAT_ID = config.get('experts_chat_id')
            GROUP_ID = config.get('group_id')
            
            if SUPERUSER_ID is None:
                logging.error("superuser_id не найден в config.json")
            if EXPERTS_CHAT_ID is None:
                logging.warning("experts_chat_id не найден в config.json")
            if GROUP_ID is None:
                logging.warning("group_id не найден в config.json")
    except json.JSONDecodeError as e:
        logging.error(f"Ошибка парсинга JSON в config.json: {e}")
    except IOError as e:
        logging.error(f"Ошибка чтения config.json: {e}")