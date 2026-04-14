"""
Сервис для публикации постов на стене группы VK.

Использует user_api (пользовательский токен) для публикации постов от имени сообщества.

При получении ошибки 5 (User authorization failed) автоматически обновляет
access_token через refresh_token и повторяет запрос.
"""
import logging
from vkbottle import API
from vkbottle.exception_factory import VKAPIError
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
    
    return await _post_with_retry(api, owner_id=-GROUP_ID, message=content, is_create=True)


async def _post_with_retry(api: API, owner_id: int, message: str, is_create: bool = True, post_id: int = None) -> int:
    """
    Публикует пост с автоматическим обновлением токена при ошибке авторизации.
    
    Args:
        api: VK API экземпляр
        owner_id: ID владельца
        message: Текст поста
        is_create: True для создания поста, False для редактирования
        post_id: ID поста для редактирования
        
    Returns:
        int: ID созданного поста или -1 если ошибка
    """
    try:
        if is_create:
            response = await api.wall.post(
                owner_id=owner_id,
                message=message
            )
            post_id = response.post_id
            logging.info(f"Создан пост на стене группы: {post_id}")
            return post_id
        else:
            await api.wall.edit(
                owner_id=owner_id,
                post_id=post_id,
                message=message
            )
            logging.info(f"Обновлён пост на стене группы: {post_id}")
            return True
            
    except VKAPIError(5) as e:
        # User authorization failed - пробуем обновить токен
        logging.warning(f"Получена ошибка авторизации (код 5), пробуем обновить токен...")
        
        from services.api_instances import handle_token_refresh
        if await handle_token_refresh():
            logging.info("Токен обновлён, повторяем запрос...")
            # Повторяем запрос с обновлённым токеном
            try:
                if is_create:
                    response = await api.wall.post(
                        owner_id=owner_id,
                        message=message
                    )
                    post_id = response.post_id
                    logging.info(f"Создан пост на стене группы (после обновления токена): {post_id}")
                    return post_id
                else:
                    await api.wall.edit(
                        owner_id=owner_id,
                        post_id=post_id,
                        message=message
                    )
                    logging.info(f"Обновлён пост на стене группы (после обновления токена): {post_id}")
                    return True
            except Exception as retry_error:
                logging.error(f"Ошибка при повторном запросе: {retry_error}")
                return -1 if is_create else False
        else:
            logging.error("Не удалось обновить токен")
            return -1 if is_create else False
            
    except Exception as e:
        logging.error(f"Ошибка при {'создании' if is_create else 'редактировании'} поста на стене: {e}")
        return -1 if is_create else False


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
    
    # owner_id со знаком минус для группы
    owner_id = -GROUP_ID
    
    return await _post_with_retry(api, owner_id=owner_id, message=content, is_create=False, post_id=post_id)
