"""Compatibility shim for tests expecting top-level `csvdbutils` package.

Re-exports symbols from internal bot.tlgbotcore.csvdbutils.csvdbutils module.
"""
from bot.tlgbotcore.csvdbutils.csvdbutils import *  # type: ignore  # noqa: F401,F403

# Best-effort explicit export list
try:  # pragma: no cover
    from bot.tlgbotcore.csvdbutils.csvdbutils import __all__ as _inner_all  # type: ignore
    __all__ = list(_inner_all)  # type: ignore
except Exception:  # pragma: no cover
    __all__ = []
