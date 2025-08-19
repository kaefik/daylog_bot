#!/usr/bin/bash
# запуск тестов для проверки CSVDB
# ключ -s указывает путь где находятся
python -m unittest discover -s tests/ $1