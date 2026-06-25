"""
Единый модуль логирования.
Ротация по дням, хранение 7 дней, формат: [HH:MM:SS] Сообщение
Логи пишутся в /app/logs/ (Docker) или logs/ (локально).
"""
import logging
import logging.handlers
import os
import time


_logger = None

# Определяем директорию для логов
LOG_DIR = "/app/logs" if os.path.exists("/app/logs") else "logs"

# Суффикс для ротированных файлов: bot.log.2025-06-25
# TimedRotatingFileHandler по умолчанию добавляет .YYYY-MM-DD


class _MoscowFormatter(logging.Formatter):
    """Форматтер с московским временем (UTC+3)."""

    MOSCOW_OFFSET = 3 * 3600  # 3 часа в секундах

    def formatTime(self, record, datefmt=None):
        # Конвертируем created в московское время
        moscow_time = time.gmtime(record.created + self.MOSCOW_OFFSET)
        return time.strftime("%H:%M:%S", moscow_time)

    def format(self, record):
        # Формат: [HH:MM:SS] Сообщение
        time_str = self.formatTime(record)
        return f"[{time_str}] {record.getMessage()}"


def setup_logging():
    """
    Инициализирует единый логгер.
    Вызывается один раз при старте бота.
    """
    global _logger

    os.makedirs(LOG_DIR, exist_ok=True)

    log_path = os.path.join(LOG_DIR, "bot.log")

    handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_path,
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )
    # Убираем стандартный суффикс .%Y-%m-%d (он и так добавляется)
    handler.suffix = "%Y-%m-%d"

    handler.setFormatter(_MoscowFormatter())

    _logger = logging.getLogger("gestalt")
    _logger.setLevel(logging.INFO)
    _logger.handlers.clear()
    _logger.addHandler(handler)
    _logger.propagate = False  # Не дублируем в корневой логгер

    return _logger


def log(message: str):
    """
    Записывает сообщение в лог.
    Единая точка входа для всех модулей.
    """
    global _logger
    if _logger is None:
        setup_logging()
    _logger.info(message)


def log_error(message: str):
    """Записывает сообщение об ошибке (на том же уровне INFO, без разделения уровней)."""
    log(message)