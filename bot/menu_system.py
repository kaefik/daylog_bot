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
    admin_only: bool = False


MENU_REGISTRY: List[MenuEntry] = []
MENU_CACHE: Dict[str, List[List[Button]]] = {}


def _is_admin_user(user_id) -> bool:
    """Безопасная проверка: user_id может быть str/int, tlgbot.admins может содержать int.

    Приводим всё к int и проверяем принадлежность. Ошибки глушим.
    """
    try:
        admins = getattr(tlgbot, 'admins', None)
        if admins is None:
            if logger:
                logger.debug("menu_system: no tlgbot.admins attribute yet")
            return False
        uid = int(user_id)
        admin_set = {int(a) for a in admins}
        result = uid in admin_set
        if logger:
            logger.debug(f"menu_system: _is_admin_user uid={uid} admins={list(admin_set)} -> {result}")
        return result
    except Exception as e:  # noqa: BLE001
        if logger:
            logger.debug(f"menu_system: _is_admin_user error for user_id={user_id}: {e}")
        return False

# При обновлении версии с поддержкой admin_only логично сбросить кэш (одноразово при импорте)
MENU_CACHE.clear()


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


def build_menu(lang: str, is_admin: bool = False) -> List[List[Button]]:
    """Строит (и кэширует) inline-меню по языку и роли."""
    cache_key = f"{lang}|admin" if is_admin else lang
    if cache_key in MENU_CACHE:
        if logger:
            logger.debug(f"menu_system: cache hit key={cache_key}")
        return MENU_CACHE[cache_key]
    
    # Убедимся, что tlgbot и i18n существуют и правильно инициализированы
    global tlgbot
    tlgbot = globals().get('tlgbot') or tlgbot
    
    if hasattr(tlgbot, 'i18n') and tlgbot.i18n:
        # Проверим, загружены ли локали правильно
        if not hasattr(tlgbot.i18n, 'locales') or not tlgbot.i18n.locales:
            if logger:
                logger.warning(f"menu_system: i18n locales not loaded, reloading for lang={lang}")
            # Перезагрузим локали
            tlgbot.i18n.load_locales("bot/locales")
            
        t = tlgbot.i18n.t  # type: ignore[attr-defined]
        if logger:
            logger.debug(f"menu_system: using i18n from tlgbot for {lang}")
    else:
        # Фолбэк - просто возвращаем ключ (но логгируем ошибку)
        if logger:
            logger.error(f"menu_system: i18n not available for lang={lang}")
        t = lambda key, lang=None, **kw: key  # noqa: E731

    rows: List[List[Button]] = []
    current: List[Button] = []
    if logger:
        logger.debug(f"menu_system: building menu for lang={lang} is_admin={is_admin}")
    for entry in sorted(MENU_REGISTRY, key=lambda e: e.order):
        if not getattr(entry, 'enabled', True):
            continue
        if getattr(entry, 'admin_only', False) and not is_admin:
            continue
        label = t(entry.tr_key, lang=lang) or entry.tr_key
        current.append(Button.inline(label, data=f"menu:{entry.key}"))
        if len(current) == 2:
            rows.append(current)
            current = []
    if current:
        rows.append(current)
    MENU_CACHE[cache_key] = rows
    return rows


async def dispatch_command(key: str, event) -> None:
    """Находит MenuEntry и вызывает связанный handler."""
    # Убедимся что i18n доступен перед вызовом handler
    global tlgbot
    tlgbot = globals().get('tlgbot') or tlgbot
    
    # Если у event нет атрибута lang, добавим его
    if not hasattr(event, 'lang') and hasattr(event, 'sender_id'):
        try:
            from cfg.config_tlg import DAYLOG_DB_PATH
            from core.database.manager import DatabaseManager
            db = DatabaseManager(db_path=DAYLOG_DB_PATH)
            user_row = db.get_user(event.sender_id)
            if user_row and 'language_code' in user_row:
                event.lang = user_row['language_code']
                if logger:
                    logger.debug(f"menu_system: dispatch_command set event.lang={event.lang}")
        except Exception as e:
            if logger:
                logger.error(f"menu_system: dispatch_command error getting language: {e}")
    
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
        if logger:
            logger.error("menu_system: ensure_menu_router failed - tlgbot is None")
        return  # повторим позже

    @tlg.on(events.CallbackQuery(pattern=r'^menu:'))  # type: ignore[misc]
    async def menu_callback_router(event):  # noqa: D401
        try:
            data = event.data.decode('utf-8')
            key = data.split(':', 1)[1]
        except Exception:
            return
        await event.answer()
        # Удаляем сообщение с меню, чтобы не замусоривать диалог
        try:
            await event.delete()
            if logger:
                logger.debug(f"menu_system: deleted menu message after button click for key={key}")
        except Exception as e:
            if logger:
                logger.error(f"menu_system: error deleting menu message: {e}")
        await dispatch_command(key, event)

    # Обновляем глобальные ссылки
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

    # Удостоверимся, что у tlgbot есть i18n
    if tlgbot and not hasattr(tlgbot, 'i18n'):
        if logger:
            logger.debug("menu_system: tlgbot.i18n not initialized, trying to find from globals")
        # Попробуем найти i18n в глобальных переменных
        i18n = globals().get('i18n')
        if i18n:
            tlgbot.i18n = i18n
            if logger:
                logger.debug("menu_system: attached i18n from globals")

    ensure_menu_router()
    
    # Очищаем кэш при инициализации чтобы избежать проблем с локализацией
    MENU_CACHE.clear()
    if logger:
        logger.debug("menu_system: initialized and cache cleared")
    
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


def _ensure_admin_entries():
    """Регистрирует admin-only пункты если их ещё нет. Идempotent."""
    before = len(MENU_REGISTRY)
    admin_entries: list[dict] = []  # перенесены в _core.py
    for e in admin_entries:
        if not any(x.key == e['key'] for x in MENU_REGISTRY):
            register_menu(e)
    if len(MENU_REGISTRY) != before:
        MENU_CACHE.clear()
        if logger:
            logger.debug("menu_system: admin entries ensured & cache cleared")


def bootstrap_default_entries():  # noqa: D401
    """(Deprecated) Ранее инициализировал пункты. Теперь регистрация в плагинах."""
    ensure_menu_router()
    _ensure_admin_entries()


# Функция-помощник для старта меню после выбора часового пояса
def send_main_menu(event, lang: str, start_ready_text: str):
    user_id = getattr(event, 'sender_id', 0)
    is_admin = _is_admin_user(user_id)
    if logger:
        logger.debug(f"menu_system: send_main_menu user_id={user_id} is_admin={is_admin}")
    buttons = build_menu(lang, is_admin=is_admin)
    return event.respond(start_ready_text, buttons=buttons)
