"""Compatibility shim for tests expecting top-level `csvdb` package.

Re-exports CSVDB from internal bot.tlgbotcore.csvdbutils.csvdb package.
"""
# Локальный импорт без протаскивания всего tlgbotcore (избегаем импорта telethon в тестах)
from bot.tlgbotcore.csvdbutils.csvdb.csvdb import CSVDB  # type: ignore  # noqa: F401

__all__ = ["CSVDB"]
