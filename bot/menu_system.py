"""Централизованная система меню (автогенерация, кэш, диспатч команд).

Модель данных MENU_REGISTRY элемент:
{
  'key': 'today',          # внутренний ключ
  'tr_key': 'menu_today',  # ключ локализации (текст кнопки)
  'plugin': 'today',       # имя плагина в tlgbot._plugins
  'handler': 'today_handler', # имя async функции-обработчика
  'order': 10              # порядок сортировки
}
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Awaitable, Dict, List, Optional
from telethon import Button, events

# tlgbot и logger будут внедрены при загрузке (как в плагинах)
tlgbot = globals().get('tlgbot')
logger = globals().get('logger')

@dataclass(slots=True)
class MenuEntry:
    key: str
    tr_key: str
    plugin: str
    handler: str
    order: int = 100
    enabled: bool = True


MENU_REGISTRY: List[MenuEntry] = []
MENU_CACHE: Dict[str, List[List[Button]]] = {}


def register_menu(entry: dict | MenuEntry) -> None:
    """Регистрирует пункт меню. Игнорирует дубликат key."""
    if isinstance(entry, dict):
        entry = MenuEntry(**entry)  # type: ignore[arg-type]
    # Проверка уникальности
    if any(e.key == entry.key for e in MENU_REGISTRY):
        return
    MENU_REGISTRY.append(entry)
    # Инвалидация всех кэшей (пока грубо)
    MENU_CACHE.clear()
    if logger:
        logger.debug(f"menu_system: registered menu entry {entry.key}")


def invalidate_menu(lang: Optional[str] = None) -> None:
    if lang is None:
        MENU_CACHE.clear()
    else:
        MENU_CACHE.pop(lang, None)
    if logger:
        logger.debug(f"menu_system: invalidate {'all' if lang is None else lang}")


def build_menu(lang: str) -> List[List[Button]]:
    """Строит (и кэширует) inline-меню по языку."""
    if lang in MENU_CACHE:
        return MENU_CACHE[lang]
    if hasattr(tlgbot, 'i18n'):
        t = tlgbot.i18n.t  # type: ignore[attr-defined]
    else:
        t = lambda key, lang=None, **kw: key  # noqa: E731

    rows: List[List[Button]] = []
    current: List[Button] = []
    for entry in sorted(MENU_REGISTRY, key=lambda e: e.order):
        if not getattr(entry, 'enabled', True):
            continue
        label = t(entry.tr_key, lang=lang) or entry.tr_key
        current.append(Button.inline(label, data=f"menu:{entry.key}"))
        if len(current) == 2:
            rows.append(current)
            current = []
    if current:
        rows.append(current)
    MENU_CACHE[lang] = rows
    return rows


async def dispatch_command(key: str, event) -> None:
    """Находит MenuEntry и вызывает связанный handler."""
    entry = next((e for e in MENU_REGISTRY if e.key == key), None)
    if not entry:
        if logger:
            logger.error(f"menu_system: unknown key {key}")
        return
    plugins = getattr(tlgbot, '_plugins', {})
    mod = plugins.get(entry.plugin)
    if not mod:
        if logger:
            logger.error(f"menu_system: plugin {entry.plugin} not loaded")
        return
    handler = getattr(mod, entry.handler, None)
    if not handler:
        if logger:
            logger.error(f"menu_system: handler {entry.handler} missing in {entry.plugin}")
        return
    await handler(event)


_MENU_ROUTER_ATTACHED = False

def ensure_menu_router():
    """Ленивая регистрация callback-роутера (tlgbot может быть ещё None при import)."""
    global _MENU_ROUTER_ATTACHED, tlgbot, logger
    if _MENU_ROUTER_ATTACHED:
        return
    tlg = globals().get('tlgbot') or tlgbot
    if tlg is None:
        return  # повторим позже

    @tlg.on(events.CallbackQuery(pattern=r'^menu:'))  # type: ignore[misc]
    async def menu_callback_router(event):  # noqa: D401
        try:
            data = event.data.decode('utf-8')
            key = data.split(':', 1)[1]
        except Exception:
            return
        await event.answer()
        await dispatch_command(key, event)

    tlgbot = tlg
    _MENU_ROUTER_ATTACHED = True
    if logger:
        logger.debug("menu_system: callback router attached")


def init_menu_system(tlg, log=None):
    """Явная инициализация (использовать в /start до bootstrap_default_entries).

    Обновляет глобальные ссылки и цепляет роутер, если ещё не.
    """
    global tlgbot, logger
    if tlg is not None:
        tlgbot = tlg
    if log is not None:
        logger = log
    ensure_menu_router()
    return tlgbot


def disable_menu(key: str):
    for e in MENU_REGISTRY:
        if e.key == key:
            e.enabled = False
    MENU_CACHE.clear()
    if logger:
        logger.debug(f"menu_system: disabled {key}")


def enable_menu(key: str):
    for e in MENU_REGISTRY:
        if e.key == key:
            e.enabled = True
    MENU_CACHE.clear()
    if logger:
        logger.debug(f"menu_system: enabled {key}")


def bootstrap_default_entries():
    """Подключается из start_cmd при первом /start (одноразово если пусто)."""
    # Убедимся что роутер зарегистрирован
    ensure_menu_router()
    if MENU_REGISTRY:
        return
    # Базовые пункты — можно позже перенести в сами плагины
    register_menu({
        'key': 'today', 'tr_key': 'menu_today', 'plugin': 'today', 'handler': 'today_handler', 'order': 10
    })
    register_menu({
        'key': 'yesterday', 'tr_key': 'menu_yesterday', 'plugin': 'yesterday', 'handler': 'yesterday_handler', 'order': 20
    })
    register_menu({
        'key': 'view', 'tr_key': 'menu_view', 'plugin': 'view', 'handler': 'view_command_handler', 'order': 30
    })
    register_menu({
        'key': 'export', 'tr_key': 'menu_export', 'plugin': 'export', 'handler': 'export_command_handler', 'order': 40
    })

    if logger:
        logger.debug("menu_system: default entries bootstrapped")


# Функция-помощник для старта меню после выбора часового пояса
def send_main_menu(event, lang: str, start_ready_text: str):
    buttons = build_menu(lang)
    return event.respond(start_ready_text, buttons=buttons)
