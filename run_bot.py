#!/usr/bin/env python3
"""
Скрипт для запуска Telegram-бота daylog_bot
"""

import sys
import os

# Устанавливаем рабочую директорию в корень проекта
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Запуск основного файла бота
if __name__ == "__main__":
    from bot.start_tlgbotcore import main
    main()
