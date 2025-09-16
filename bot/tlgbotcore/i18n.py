"""
утилита для загрузки и получения сообщений по ключу и языку
"""

import json
from pathlib import Path

class I18n:
    def __init__(self, locales_path="locales", default_lang="ru"):
        self.locales = {}
        self.default_lang = default_lang
        self.load_locales(locales_path)

    def load_locales(self, locales_path):
        for file in Path(locales_path).glob("*.json"):
            lang = file.stem
            with open(file, encoding="utf-8") as f:
                self.locales[lang] = json.load(f)

    def t(self, key, lang=None, **kwargs):
        lang = lang or self.default_lang
        msg = self.locales.get(lang, {}).get(key) or self.locales[self.default_lang].get(key, key)
        return msg.format(**kwargs)