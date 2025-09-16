import logging
import sys
from typing import Optional
from pathlib import Path


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    enable_debug: bool = False
) -> None:
    """
    Настройка логирования с улучшенным форматированием и опциональным файлом.
    
    Args:
        level: Уровень логирования (по умолчанию INFO)
        log_file: Путь к файлу логов (опционально)
        enable_debug: Включить отладочную информацию
    """
    # Очищаем существующие хэндлеры
    root = logging.getLogger()
    root.handlers.clear()
    
    # Устанавливаем уровень
    if enable_debug:
        level = logging.DEBUG
    root.setLevel(level)
    
    # Создаём форматтер с цветами для консоли
    console_formatter = ColoredFormatter(
        fmt="%(asctime)s [%(levelname)8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Консольный хэндлер
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(level)
    root.addHandler(console_handler)
    
    # Файловый хэндлер (если указан)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)8s] %(name)s:%(lineno)d: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)  # В файл пишем всё
        root.addHandler(file_handler)
    
    # Настройка уровней для внешних библиотек
    logging.getLogger('telethon').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    # Отключаем icecream в продакшене
    if not enable_debug:
        disable_icecream()


class ColoredFormatter(logging.Formatter):
    """Форматтер с цветами для консоли."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green  
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # Добавляем цвет к уровню логирования
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        
        return super().format(record)


def disable_icecream() -> None:
    """Отключает icecream в продакшн среде."""
    try:
        import icecream
        icecream.ic.disable()
    except ImportError:
        pass  # icecream не установлен


def setup_dev_logging() -> None:
    """Настройка логирования для разработки с отладкой."""
    setup_logging(
        level=logging.DEBUG,
        log_file="logs/tlgbotcore.log",
        enable_debug=True
    )


def setup_prod_logging() -> None:
    """Настройка логирования для продакшена."""
    setup_logging(
        level=logging.INFO,
        log_file="logs/tlgbotcore.log",
        enable_debug=False
    )


