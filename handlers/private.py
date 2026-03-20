"""
Обработчики личных сообщений для VK бота.
"""
import logging
import random
from vkbottle import API
from vkbottle.bot import Message

from config import SUPERUSER_ID, EXPERTS_CHAT_ID
from models.questions_db import add_question, format_question_for_experts, get_question_by_id
from services.vk_api import get_user_name


async def handle_question(message: Message, api: API) -> bool:
    """
    Обработка #вопрос в личных сообщениях.
    
    Args:
        message: Сообщение VK
        api: VK API экземпляр
        
    Returns:
        bool: True если сообщение обработано
    """
    text = message.text
    if not text:
        return False
    
    user_id = message.from_id
    
    logging.info(f"Получено сообщение от user {user_id}: {text[:100]}")
    
    # Обработка только #вопрос
    if not text.lower().startswith('#вопрос'):
        return False
    
    logging.info(f"Обнаружен хештег #вопрос от user {user_id}")
    question_text = text.replace('#вопрос', '', 1).strip()
    
    if not question_text:
        await message.answer("❌ Вы неверно задали вопрос. Напишите #вопрос и дальше — развёрнутый текст вопроса одним большим сообщением.")
        return True
    
    # Получаем имя пользователя
    user_name = await get_user_name(api, user_id)
    user_link = f"https://vk.com/id{user_id}"
    
    # Сохраняем в БД
    try:
        question_id = add_question(user_id, user_name, question_text, user_link)
        logging.info(f"Вопрос #{question_id} сохранён в БД от {user_name} ({user_id})")
    except Exception as db_error:
        logging.error(f"Ошибка сохранения в БД: {db_error}")
        await message.answer(f"❌ Ошибка сохранения вопроса: {db_error}")
        return True
    
    # Отправляем экспертам
    logging.info(f"EXPERTS_CHAT_ID = {EXPERTS_CHAT_ID}, тип: {type(EXPERTS_CHAT_ID)}")
    if EXPERTS_CHAT_ID:
        expert_message = format_question_for_experts({
            "user_link": user_link,
            "question_text": question_text,
            "question_id": question_id
        })
        logging.info(f"Отправка экспертам: {expert_message[:100]}")
        try:
            await api.messages.send(
                peer_id=EXPERTS_CHAT_ID,
                message=expert_message,
                random_id=random.randint(1, 2**31)
            )
            logging.info(f"Вопрос #{question_id} отправлен экспертам в чат {EXPERTS_CHAT_ID}")
        except Exception as e:
            logging.error(f"Ошибка отправки экспертам: {e}")
            await message.answer(f"❌ Ошибка при отправке вопроса: {e}")
            return True
    else:
        logging.error("EXPERTS_CHAT_ID не установлен!")
        await message.answer("❌ Ошибка: EXPERTS_CHAT_ID не настроен. Обратитесь к администратору.")
        return True
    
    await message.answer("✅ Ваш вопрос отправлен экспертам. Ответ придет в личные сообщения.")
    return True


async def handle_unauthorized(message: Message) -> bool:
    """
    Отказ обычным пользователям.
    
    Args:
        message: Сообщение VK
        
    Returns:
        bool: True если сообщение обработано
    """
    text = message.text
    if not text:
        return False
    
    # Игнорируем #вопрос - он уже обработан
    if text.lower().startswith('#вопрос'):
        return False
    
    await message.answer(
        "📝 Этот бот принимает только вопросы экспертам.\n"
        "Напишите: #вопрос Ваш текст вопроса"
    )
    return True