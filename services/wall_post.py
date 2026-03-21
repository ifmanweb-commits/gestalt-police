"""
Сервис для публикации постов на стене группы VK.

Использует user_api (пользовательский токен) для публикации постов от имени сообщества.
"""
import logging
from vkbottle import API
from config import GROUP_ID


# Лимит символов для поста VK
VK_POST_MAX_LENGTH = 4096


def format_expert_link(expert_id: int, expert_name: str) -> str:
    """
    Форматирует ссылку на эксперта в VK-разметке.
    
    Args:
        expert_id: ID эксперта
        expert_name: Имя эксперта
        
    Returns:
        str: Ссылка в формате [id123|Имя]
    """
    return f"[id{expert_id}|{expert_name}]"


def format_post_content(question_text: str, expert_answers: list) -> str:
    """
    Форматирует контент поста для публикации на стене.
    
    Args:
        question_text: Текст вопроса
        expert_answers: Список ответов экспертов
        
    Returns:
        str: Отформатированный контент поста
    """
    content = f"Вопрос экспертам:\n{question_text}\n\n"
    
    for answer in expert_answers:
        expert_link = format_expert_link(answer['expert_id'], answer['expert_name'])
        content += f"Ответ эксперта {expert_link}:\n{answer['text']}\n\n"
    
    return content.strip()


def is_post_within_limit(content: str) -> bool:
    """
    Проверяет, что контент поста не превышает лимит VK.
    
    Args:
        content: Текст поста
        
    Returns:
        bool: True если текст в пределах лимита
    """
    return len(content) <= VK_POST_MAX_LENGTH


async def create_wall_post(api: API, question_text: str, expert_answer: dict) -> int:
    """
    Создаёт новый пост на стене группы.
    
    ВАЖНО: Используйте user_api (пользовательский токен) для публикации от имени сообщества.
    
    Args:
        api: VK API экземпляр (должен быть user_api)
        question_text: Текст вопроса
        expert_answer: Данные ответа эксперта (expert_id, expert_name, text)
        
    Returns:
        int: ID созданного поста или -1 если ошибка/превышен лимит
    """
    # Формируем контент с первым ответом
    content = format_post_content(question_text, [expert_answer])
    
    # Проверяем лимит
    if not is_post_within_limit(content):
        logging.warning(f"Текст поста превышает лимит VK ({len(content)} символов)")
        return -1
    
    try:
        # owner_id со знаком минус для группы
        owner_id = -GROUP_ID
        
        # Публикация от имени сообщества (from_group=1)
        # Требуется user_api с правами на публикацию от имени сообщества
        response = await api.wall.post(
            owner_id=owner_id,
            from_group=1,
            message=content
        )
        
        post_id = response.post_id
        logging.info(f"Создан пост на стене группы: {post_id}")
        return post_id
        
    except Exception as e:
        logging.error(f"Ошибка при создании поста на стене: {e}")
        return -1


async def update_wall_post(api: API, post_id: int, question_text: str, expert_answers: list) -> bool:
    """
    Редактирует существующий пост на стене, добавляя новый ответ эксперта.
    
    ВАЖНО: Используйте user_api (пользовательский токен) для редактирования от имени сообщества.
    
    Args:
        api: VK API экземпляр (должен быть user_api)
        post_id: ID поста для редактирования
        question_text: Текст вопроса
        expert_answers: Список всех ответов экспертов
        
    Returns:
        bool: True если пост успешно обновлён
    """
    # Формируем новый контент со всеми ответами
    content = format_post_content(question_text, expert_answers)
    
    # Проверяем лимит
    if not is_post_within_limit(content):
        logging.warning(f"Текст поста превышает лимит VK после добавления ответа ({len(content)} символов)")
        return False
    
    try:
        # owner_id со знаком минус для группы
        owner_id = -GROUP_ID
        
        # Редактирование от имени сообщества (требуется user_api)
        await api.wall.edit(
            owner_id=owner_id,
            post_id=post_id,
            message=content
        )
        
        logging.info(f"Обновлён пост на стене группы: {post_id}")
        return True
        
    except Exception as e:
        logging.error(f"Ошибка при редактировании поста на стене: {e}")
        return False
