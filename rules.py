from vkbottle.bot import Message
from vkbottle.dispatch.rules.base import ABCRule
import json
import os

CONFIG_FILE = "./config.json"

def get_superuser_id() -> int:
    """Загружает SUPERUSER_ID из config.json."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config.get('superuser_id')
    except Exception:
        pass
    return None


class IsPrivateRule(ABCRule[Message]):
    """Проверяет, что сообщение в личном чате"""
    async def check(self, message: Message) -> bool:
        return message.peer_id == message.from_id


class IsGroupRule(ABCRule[Message]):
    """Проверяет, что сообщение в групповом чате (беседе)"""
    async def check(self, message: Message) -> bool:
        return message.peer_id != message.from_id


class IsSuperuserRule(ABCRule[Message]):
    """Проверяет, что отправитель - суперпользователь"""
    async def check(self, message: Message) -> bool:
        superuser_id = get_superuser_id()
        if superuser_id is None:
            return False
        return message.from_id == superuser_id


class IsNotSuperuserRule(ABCRule[Message]):
    """Проверяет, что отправитель НЕ суперпользователь"""
    async def check(self, message: Message) -> bool:
        superuser_id = get_superuser_id()
        if superuser_id is None:
            return True
        return message.from_id != superuser_id


class CommandRule(ABCRule[Message]):
    """Проверяет, что сообщение начинается с указанной команды"""
    def __init__(self, command: str):
        self.command = command
    
    async def check(self, message: Message) -> bool:
        if not message.text:
            return False
        text = message.text.strip()
        # Проверяем /команду или !команду
        first_word = text.split()[0].lower()
        return first_word in [f"/{self.command}", f"!{self.command}"]


class StartsWithRule(ABCRule[Message]):
    """Проверяет, что сообщение начинается с указанного префикса"""
    def __init__(self, prefix: str):
        self.prefix = prefix
    
    async def check(self, message: Message) -> bool:
        if not message.text:
            return False
        return message.text.strip().startswith(self.prefix)