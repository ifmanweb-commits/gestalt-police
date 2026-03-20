"""
Модуль для работы с базами данных TinyDB.
"""
from tinydb import TinyDB, Query

# Пути к файлам баз данных
BOT_DATABASE_FILE = "./bot_database.json"
EXPERTS_DATABASE_FILE = "./experts.json"
QUESTIONS_DATABASE_FILE = "./questions.json"


def get_db(file_path: str) -> TinyDB:
    """
    Возвращает экземпляр TinyDB для указанного файла.
    
    Args:
        file_path: Путь к файлу базы данных
        
    Returns:
        TinyDB: Экземпляр базы данных
    """
    return TinyDB(file_path)


# Предопределённые базы данных
def get_bot_db() -> TinyDB:
    """Возвращает базу данных бота."""
    return get_db(BOT_DATABASE_FILE)


def get_experts_db() -> TinyDB:
    """Возвращает базу данных экспертов."""
    return get_db(EXPERTS_DATABASE_FILE)


def get_questions_db() -> TinyDB:
    """Возвращает базу данных вопросов."""
    return get_db(QUESTIONS_DATABASE_FILE)