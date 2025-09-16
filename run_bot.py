#!/usr/bin/env python3
"""
Скрипт для запуска Telegram-бота daylog_bot
"""

import sys
import os

# Инициализация БД дневника, если не существует
import importlib.util
import pathlib

config_path = os.path.join(os.path.dirname(__file__), 'cfg', 'config_tlg.py')
spec = importlib.util.spec_from_file_location('config_tlg', config_path)
config_tlg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_tlg)

db_path = getattr(config_tlg, 'DAYLOG_DB_PATH', './data/database/daylog.db')
if not os.path.exists(db_path):
    # Создать директорию, если нужно
    pathlib.Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    from core.database.manager import DatabaseManager
    DatabaseManager(db_path=db_path)
    print(f"Инициализирована БД дневника: {db_path}")

# Устанавливаем рабочую директорию в корень проекта
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Запуск основного файла бота
if __name__ == "__main__":
    from bot.start_tlgbotcore import main
    main()
