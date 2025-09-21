"""Упрощённый доступ для старых тестов.

Тесты импортируют модули как `from csvdb import CSVDB` и `from csvdbutils import User`.
Мы размещены по пути `bot.tlgbotcore.csvdbutils`, поэтому добавляем совместимые алиасы,
если пакет устанавливается в PYTHONPATH (корень проекта уже добавлен при запуске тестов через uv/pytest).
"""

from .csvdbutils import *  # noqa: F401,F403
from .csvdb import *  # noqa: F401,F403

__all__ = []  # сформируем явный список
try:  # собираем имена из подмодулей
	from .csvdbutils import __all__ as _a1  # type: ignore
	from .csvdb import __all__ as _a2  # type: ignore
	__all__ = list(set(list(_a1) + list(_a2)))  # type: ignore[arg-type]
except Exception:  # pragma: no cover
	pass