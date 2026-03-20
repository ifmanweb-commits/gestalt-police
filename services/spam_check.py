"""
Сервис для проверки сообщений на спам.
"""
import logging
import random
import re
import emoji
from vkbottle import API

from is_spam_message import new_is_spam_message, has_critical_patterns, has_mixed_words
from database import get_bot_db, get_bot_db
from tinydb import Query


BOT_AD_PATTERNS = [
    r'@\w*bot',
    r't\.me/\w*bot',
    r'https://t\.me/\w*bot',
]


def has_bot_advertisement(text: str) -> bool:
    """
    Проверяет текст на рекламу ботов.
    
    Args:
        text: Текст для проверки
        
    Returns:
        bool: True если найдена реклама ботов
    """
    for pattern in BOT_AD_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


async def is_user_admin_in_chat(api: API, chat_id: int, user_id: int) -> bool:
    """
    Проверяет, является ли пользователь администратором в чате.
    
    Args:
        api: VK API экземпляр
        chat_id: ID чата
        user_id: ID пользователя
        
    Returns:
        bool: True если пользователь администратор
    """
    try:
        from config import SUPERUSER_ID
        if user_id == SUPERUSER_ID:
            return True
        
        db = get_bot_db()
        User = Query()
        user_data = db.get(User.user_id == user_id)
        if user_data and chat_id in user_data.get('chats', []):
            return True
        return False
    except Exception as e:
        logging.warning(f"Не удалось проверить статус пользователя {user_id} в чате {chat_id}: {e}")
        return False


async def perform_spam_check(message, api: API):
    """
    Выполняет проверку сообщения на спам.
    
    Args:
        message: Сообщение VK
        api: VK API экземпляр
    """
    if not message.text and not message.attachments:
        return
    
    chat_id = message.peer_id
    from_user = message.from_id
    
    if from_user < 0:
        return
    
    # Проверяем администратора
    if await is_user_admin_in_chat(api, chat_id, from_user):
        return
    
    text = message.text or ""
    if not text:
        return
    
    crit_tokens = has_critical_patterns(text)
    crit_tokens_bool = crit_tokens is not None
    crit_tokens_string = crit_tokens.group() if crit_tokens else None
    
    spam_tokens = new_is_spam_message(text)
    spam_tokens_bool = spam_tokens is not None
    
    mixed_words = has_mixed_words(text)
    num_mixed = len(mixed_words)
    
    emoji_num = sum(1 for _ in emoji.emoji_list(text))
    emoji_critical_num = emoji_num > 12
    
    is_bot_ad = has_bot_advertisement(text)
    
    is_critical = (crit_tokens_bool or num_mixed > 1 or emoji_critical_num)
    is_regular_spam = (spam_tokens_bool and not crit_tokens_bool)
    
    if (len(text) < 500) and is_critical:
        verdict = f"""
<b>Критические токены:</b> {crit_tokens_bool} | {crit_tokens_string}
<b>Смешанные слова:</b> {num_mixed}; [ {', '.join(mixed_words)} ]
<b>Более 12 эмодзи:</b> {emoji_critical_num}
        """
        
        user_link = f"vk.com/id{from_user}"
        user_display_name = f"user{from_user}"
        message_text = text[:500]
        text_message_content = (
            f"🎯 <b>Автоматический бан:</b>\n\n"
            f"👤 <a href='{user_link}'><b>{user_display_name}</b></a> из чата {chat_id}\n\n"
            f"{message_text}\n{verdict}"
        )
        
        try:
            await api.messages.delete(peer_id=chat_id, conversation_message_ids=[message.conversation_message_id])
            if chat_id > 2000000000:
                try:
                    await api.messages.remove_chat_user(chat_id=chat_id, user_id=from_user)
                except Exception as ban_error:
                    logging.warning(f"Не удалось удалить пользователя из беседы: {ban_error}")
            
            db = get_bot_db()
            for user in db.all():
                if chat_id in user.get('chats', []):
                    try:
                        await api.messages.send(
                            peer_id=user['user_id'],
                            message=text_message_content,
                            disable_web_page_preview=True,
                            random_id=random.randint(1, 2**31)
                        )
                    except Exception as e:
                        logging.error(f"Ошибка при отправке уведомления: {e}")
            return
        except Exception as e:
            error_message = f"Возникла ошибка при автоматическом бане: {str(e)}\n\n{verdict}"
            db = get_bot_db()
            for user in db.all():
                if chat_id in user.get('chats', []):
                    try:
                        await api.messages.send(
                            peer_id=user['user_id'],
                            message=error_message,
                            random_id=random.randint(1, 2**31)
                        )
                    except Exception as e:
                        logging.error(f"Ошибка при отправке уведомления об ошибке: {e}")
            return
    
    elif (len(text) < 500) and (is_regular_spam or is_bot_ad):
        verdict = f"""
<b>Обычный спам:</b> {spam_tokens_bool}
<b>Реклама ботов:</b> {is_bot_ad}
        """
        
        try:
            await api.messages.delete(peer_id=chat_id, conversation_message_ids=[message.conversation_message_id])
            
            user_link = f"vk.com/id{from_user}"
            user_display_name = f"user{from_user}"
            
            notify_text = (
                f"🗑️ <b>Сообщение удалено (спам):</b>\n\n"
                f"👤 <a href='{user_link}'><b>{user_display_name}</b></a> из чата {chat_id}\n\n"
                f"{text[:500]}\n{verdict}"
            )
            
            db = get_bot_db()
            for user in db.all():
                if chat_id in user.get('chats', []):
                    try:
                        await api.messages.send(
                            peer_id=user['user_id'],
                            message=notify_text,
                            random_id=random.randint(1, 2**31)
                        )
                    except Exception as e:
                        logging.error(f"Ошибка при отправке уведомления об удалении: {e}")
        except Exception as e:
            logging.error(f"Ошибка при удалении спам-сообщения: {e}")
