"""
Модуль управления вопросами для VK бота.
Использует TinyDB для хранения данных.
"""

import os
import json
from datetime import datetime
from tinydb import TinyDB

# Пути к файлам баз данных
QUESTIONS_FILE = "./questions.json"


def init_questions_db():
    """
    Инициализирует базу данных вопросов.
    Создаёт questions.json с {"_default": {}} если файл не существует.
    """
    if not os.path.exists(QUESTIONS_FILE):
        with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
            json.dump({"_default": {}}, f, ensure_ascii=False, indent=2)


def get_questions_db():
    """
    Возвращает экземпляр TinyDB для вопросов.
    
    Returns:
        TinyDB: Экземпляр базы данных вопросов
    """
    return TinyDB(QUESTIONS_FILE)


def get_next_question_id():
    """
    Возвращает следующий ID для вопроса (автоинкремент).
    
    Returns:
        int: Следующий доступный ID вопроса
    """
    db = get_questions_db()
    all_questions = db.all()
    
    if not all_questions:
        return 1
    
    # Находим максимальный ID
    max_id = max(q.get('id', 0) for q in all_questions)
    return max_id + 1


def add_question(user_id: int, user_name: str, question_text: str, user_link: str) -> int:
    """
    Добавляет новый вопрос в базу данных.
    
    Args:
        user_id: ID пользователя, задавшего вопрос
        user_name: Имя пользователя
        question_text: Текст вопроса
        user_link: Ссылка на профиль пользователя
        
    Returns:
        int: ID добавленного вопроса
    """
    db = get_questions_db()
    
    question_id = get_next_question_id()
    timestamp = datetime.now().isoformat()
    
    question_data = {
        "id": question_id,
        "user_id": user_id,
        "user_name": user_name,
        "user_link": user_link,
        "question_text": question_text,
        "timestamp": timestamp,
        "post_id": None,
        "expert_answers": []
    }
    
    db.insert(question_data)
    
    return question_id


def format_question_for_experts(question_data: dict) -> str:
    """
    Форматирует вопрос для отправки в чат экспертов.
    
    Args:
        question_data: Данные вопроса из базы данных
        
    Returns:
        str: Отформатированное сообщение для экспертов
    """
    user_link = question_data.get('user_link', '')
    question_text = question_data.get('question_text', '')
    
    return f"Вопрос от {user_link}\n\n{question_text}"


def get_question_by_id(question_id: int) -> dict:
    """
    Получает вопрос по ID.
    
    Args:
        question_id: ID вопроса
        
    Returns:
        dict: Данные вопроса или None если не найден
    """
    db = get_questions_db()
    from tinydb import Query
    Question = Query()
    return db.get(Question.id == question_id)


def add_expert_answer(question_id: int, expert_id: int, expert_name: str, 
                      expert_link: str, answer_text: str) -> bool:
    """
    Добавляет ответ эксперта к вопросу.
    
    Args:
        question_id: ID вопроса
        expert_id: ID эксперта
        expert_name: Имя эксперта
        expert_link: Ссылка на профиль эксперта
        answer_text: Текст ответа
        
    Returns:
        bool: True если ответ успешно добавлен
    """
    db = get_questions_db()
    from tinydb import Query
    Question = Query()
    
    question = db.get(Question.id == question_id)
    if not question:
        return False
    
    if 'expert_answers' not in question:
        question['expert_answers'] = []
    
    answer_data = {
        "expert_id": expert_id,
        "expert_name": expert_name,
        "expert_link": expert_link,
        "text": answer_text,
        "timestamp": datetime.now().isoformat()
    }
    
    question['expert_answers'].append(answer_data)
    db.update(question, Question.id == question_id)
    
    return True


def get_all_questions() -> list:
    """
    Получает все вопросы из базы данных.
    
    Returns:
        list: Список всех вопросов
    """
    db = get_questions_db()
    return db.all()