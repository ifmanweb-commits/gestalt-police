"""
Обработчики групповых сообщений для VK бота.
"""
import logging
import random
import re
from vkbottle import API
from vkbottle.bot import Message

from config import EXPERTS_CHAT_ID, GROUP_ID
from services.custom_commands import get_command_response
from services.spam_check import perform_spam_check
from services.vk_api import get_user_name
from services.wall_post import create_wall_post, update_wall_post
from database import get_bot_db
from models.questions_db import add_expert_answer, get_question_by_id, get_question_full_data, update_question_post_id, get_question_post_id
from tinydb import Query


async def handle_expert_answer(message: Message, group_api: API, wall_api: API) -> bool:
    """
    Обработка ответов экспертов в беседе экспертов.
    Эксперт отвечает на сообщение бота → бот отправляет ответ пользователю.
    
    Args:
        message: Сообщение VK
        group_api: VK API экземпляр (групповой токен) для отправки сообщений
        wall_api: VK API экземпляр (wall_token) для публикации постов на стене
        
    Returns:
        bool: True если сообщение обработано
    """
    if message.peer_id != EXPERTS_CHAT_ID:
        return False
    
    if not message.reply_message:
        return False
    
    reply_to = message.reply_message
    
    # Проверяем, что исходное сообщение отправлено ботом
    if reply_to.from_id >= 0:
        return False
    
    # Извлекаем user_id из текста исходного сообщения
    user_match = re.search(r'https://vk\.com/id(\d+)', reply_to.text)
    if not user_match:
        logging.warning(f"Не удалось извлечь user_id из сообщения: {reply_to.text}")
        return False
    
    target_user_id = int(user_match.group(1))
    
    # Извлекаем question_id из текста сообщения (формат QID:123)
    qid_match = re.search(r'QID:(\d+)', reply_to.text)
    question_id = int(qid_match.group(1)) if qid_match else None
    
    # Получаем имя эксперта (используем group_api)
    expert_name = await get_user_name(group_api, message.from_id)
    expert_link = f"https://vk.com/id{message.from_id}"
    
    # Сохраняем ответ эксперта в БД и публикуем на стене
    post_id = None
    if question_id:
        try:
            # Сохраняем ответ в БД
            add_expert_answer(
                question_id=question_id,
                expert_id=message.from_id,
                expert_name=expert_name,
                expert_link=expert_link,
                answer_text=message.text
            )
            logging.info(f"Ответ эксперта #{question_id} сохранён в БД от {expert_name}")
            
            # Получаем полные данные вопроса
            question_data = get_question_full_data(question_id)
            if question_data:
                question_text = question_data.get('question_text', '')
                expert_answers = question_data.get('expert_answers', [])
                
                # Проверяем, есть ли уже пост для этого вопроса
                post_id = get_question_post_id(question_id)
                
                if post_id is None:
                    # Поста нет - создаём новый (используем wall_api)
                    logging.info(f"Создание нового поста для вопроса #{question_id}")
                    new_post_id = await create_wall_post(
                        api=wall_api,
                        question_text=question_text,
                        expert_answer={
                            'expert_id': message.from_id,
                            'expert_name': expert_name,
                            'text': message.text
                        }
                    )
                    if new_post_id > 0:
                        update_question_post_id(question_id, new_post_id)
                        post_id = new_post_id
                        logging.info(f"ID поста {new_post_id} сохранён для вопроса #{question_id}")
                    else:
                        logging.warning(f"Не удалось создать пост для вопроса #{question_id}")
                else:
                    # Пост есть - редактируем его, добавляя новый ответ (используем wall_api)
                    logging.info(f"Редактирование поста {post_id} для вопроса #{question_id}")
                    updated = await update_wall_post(
                        api=wall_api,
                        post_id=post_id,
                        question_text=question_text,
                        expert_answers=expert_answers
                    )
                    if updated:
                        logging.info(f"Пост {post_id} успешно обновлён")
                    else:
                        logging.warning(f"Не удалось обновить пост {post_id} (возможно, превышен лимит символов)")
            
        except Exception as db_error:
            logging.error(f"Ошибка сохранения ответа в БД: {db_error}")
    
    # Отправляем уведомление пользователю со ссылкой на пост
    if post_id:
        post_url = f"https://vk.com/wall-{GROUP_ID}_{post_id}"
        notify_message = (
            f"🔔 Кто-то из экспертов ответил на ваш вопрос. Вы можете прочитать его тут:\n"
            f"{post_url}\n\n"
            f"Если у вас есть какие-то дополнения - не задавайте новый вопрос здесь. "
            f"Пишите в комментариях под своим вопросом в посте."
        )
        
        try:
            await group_api.messages.send(
                peer_id=target_user_id,
                message=notify_message,
                random_id=random.randint(1, 2**31)
            )
            logging.info(f"Уведомление отправлено пользователю {target_user_id}")
            
            # Уведомляем эксперта об отправке
            await group_api.messages.send(
                peer_id=message.peer_id,
                message=f"✅ Ответ отправлен пользователю https://vk.com/id{target_user_id}",
                reply_to=message.conversation_message_id,
                random_id=random.randint(1, 2**31)
            )
        except Exception as e:
            logging.error(f"Ошибка при отправке уведомления пользователю: {e}")
    
    return True


async def handle_custom_command(message: Message, api: API) -> bool:
    """
    Обработка !команд в групповых чатах.
    Команда выполняется если пользователь - администратор чата ИЛИ эксперт.
    
    Args:
        message: Сообщение VK
        api: VK API экземпляр
        
    Returns:
        bool: True если сообщение обработано
    """
    text = message.text
    if not text or not text.startswith('!'):
        return False
    
    if message.from_id < 0:
        return False
    
    # Проверяем администратора ИЛИ эксперта
    from services.spam_check import is_user_admin_in_chat
    from models.experts_db import is_expert
    
    is_admin = await is_user_admin_in_chat(api, message.peer_id, message.from_id)
    is_expert_user = is_expert(message.from_id)
    
    if not (is_admin or is_expert_user):
        logging.info(f"Пользователь {message.from_id} не является администратором или экспертом в чате {message.peer_id}")
        return False
    
    response = get_command_response(text)
    if not response:
        return False
    
    # Удаляем команду
    try:
        await api.messages.delete(
            peer_id=message.peer_id,
            conversation_message_ids=[message.conversation_message_id]
        )
    except Exception as e:
        logging.error(f"Ошибка при удалении команды: {e}")
    
    
    # Отправляем ответ
    try:
        if message.reply_message:
            await api.messages.send(
                peer_id=message.peer_id,
                message=response,
                reply_to=message.conversation_message_id,
                random_id=random.randint(1, 2**31)
            )
        else:
            logging.info(f"Sending !msg {message.peer_id}")
            await api.messages.send(
                peer_id=message.peer_id,
                message=response,
                random_id=random.randint(1, 2**31)
            )
        logging.info(f"Команда успешно выполнена")
    except Exception as e:
        logging.error(f"Ошибка при отправке ответа на команду: {e}")
    
    return True


async def handle_antispam(message: Message, api: API) -> bool:
    """
    Антиспам проверка.
    
    Args:
        message: Сообщение VK
        api: VK API экземпляр
        
    Returns:
        bool: True если проверка выполнена
    """
    await perform_spam_check(message, api)
    return True
