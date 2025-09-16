#!/usr/bin/env python3
"""
Скрипт для запуска Telegram-бота daylog_bot
"""

import sys
import os

# Инициализация БД дневника, если не существует
import importlib.util
import pathlib

import logging
# Настроить базовый логгер для вывода в консоль, если не настроен
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler()]
)
config_path = os.path.join(os.path.dirname(__file__), 'cfg', 'config_tlg.py')
spec = importlib.util.spec_from_file_location('config_tlg', config_path)
config_tlg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_tlg)

import logging
from importlib import import_module

db_path = getattr(config_tlg, 'DAYLOG_DB_PATH', './data/database/daylog.db')
logger = logging.getLogger("daylog_bot")
if not os.path.exists(db_path):
    pathlib.Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    from core.database.manager import DatabaseManager
    DatabaseManager(db_path=db_path)

    # Локализованный логгер, если возможно
    try:
        from bot.tlgbotcore.i18n import I18n
        i18n = I18n(locales_path="bot/locales", default_lang=getattr(config_tlg, "DEFAULT_LANG", "ru"))
        msg = i18n.t("db_diary_initialized", lang=getattr(config_tlg, "DEFAULT_LANG", "ru"), path=db_path)
    except Exception:
        msg = f"Инициализирована БД дневника: {db_path}"
    logger.info(msg)
else:
    try:
        from bot.tlgbotcore.i18n import I18n
        i18n = I18n(locales_path="bot/locales", default_lang=getattr(config_tlg, "DEFAULT_LANG", "ru"))
        msg = i18n.t("db_diary_exists", lang=getattr(config_tlg, "DEFAULT_LANG", "ru"), path=db_path)
    except Exception:
        msg = f"БД дневника уже существует: {db_path}"
    logger.info(msg)

# Устанавливаем рабочую директорию в корень проекта
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Запуск основного файла бота
if __name__ == "__main__":
    from bot.start_tlgbotcore import main
    main()
