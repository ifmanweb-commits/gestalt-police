"""
Сервис для работы с пользовательскими командами.
"""
import json
import logging
import os

CUSTOM_COMMANDS_FILE = "./custom_commands.json"
custom_commands = {}


def load_custom_commands() -> dict:
    """
    Загружает пользовательские команды из JSON файла.
    
    Returns:
        dict: Словарь команд
    """
    global custom_commands
    try:
        if not os.path.exists(CUSTOM_COMMANDS_FILE):
            custom_commands = {}
            save_custom_commands()
            logging.info("custom_commands.json не существовал, создан новый пустой файл")
            return custom_commands
        
        with open(CUSTOM_COMMANDS_FILE, "r", encoding="utf-8") as f:
            custom_commands = json.load(f)
            if not isinstance(custom_commands, dict):
                logging.error("custom_commands.json имеет неверную структуру. Загружен пустой словарь.")
                custom_commands = {}
            else:
                logging.info(f"Загружено {len(custom_commands)} пользовательских команд из {CUSTOM_COMMANDS_FILE}")
    except json.JSONDecodeError as e:
        logging.error(f"Ошибка парсинга JSON в custom_commands.json: {e}. Загружен пустой словарь.")
        custom_commands = {}
    except IOError as e:
        logging.error(f"Ошибка чтения custom_commands.json: {e}")
        custom_commands = {}
    
    return custom_commands


def save_custom_commands() -> None:
    """
    Сохраняет пользовательские команды в JSON файл.
    """
    global custom_commands
    try:
        with open(CUSTOM_COMMANDS_FILE, "w", encoding="utf-8") as f:
            json.dump(custom_commands, f, ensure_ascii=False, indent=2)
    except IOError as e:
        logging.error(f"Ошибка записи custom_commands.json: {e}")
        raise


def get_command_response(text: str) -> str:
    """
    Возвращает ответ на команду, если она существует.
    
    Args:
        text: Текст сообщения
        
    Returns:
        str: Ответ на команду или пустая строка
    """
    global custom_commands
    words = text.split()
    
    # Ищем самую длинную подходящую команду
    possible_commands = []
    for i in range(len(words), 0, -1):
        possible_cmd = ' '.join(words[:i])
        if possible_cmd in custom_commands:
            possible_commands.append(possible_cmd)
    
    if possible_commands:
        return custom_commands[possible_commands[0]]
    
    return ""


def get_all_commands() -> dict:
    """
    Возвращает все команды.
    
    Returns:
        dict: Словарь всех команд
    """
    return custom_commands


def add_command(trigger: str, response: str) -> bool:
    """
    Добавляет или обновляет команду.
    
    Args:
        trigger: Триггер команды (например, !правила)
        response: Текст ответа
        
    Returns:
        bool: True если команда успешно добавлена
    """
    global custom_commands
    custom_commands[trigger] = response
    try:
        save_custom_commands()
        return True
    except IOError:
        return False


def remove_command(trigger: str) -> bool:
    """
    Удаляет команду.
    
    Args:
        trigger: Триггер команды для удаления
        
    Returns:
        bool: True если команда успешно удалена
    """
    global custom_commands
    if trigger in custom_commands:
        del custom_commands[trigger]
        try:
            save_custom_commands()
            return True
        except IOError:
            return False
    return False