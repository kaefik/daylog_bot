from functools import wraps
from cfg.config_tlg import DAYLOG_DB_PATH, DEFAULT_LANG
from core.database.manager import DatabaseManager
from telethon.events import NewMessage


def get_user_lang(event):
    # Попытка получить язык пользователя из event, иначе дефолт
    tlgbot = globals().get('tlgbot')
    user = getattr(tlgbot, 'settings', None).get_user(event.sender_id) if getattr(tlgbot, 'settings', None) else None
    if user and getattr(user, 'lang', None):
        return user.lang
    if hasattr(event, 'lang') and event.lang:
        return event.lang
    if hasattr(event, 'sender') and hasattr(event.sender, 'lang_code') and event.sender.lang_code:
        return event.sender.lang_code
    return DEFAULT_LANG

def require_diary_user(func):
    @wraps(func)
    async def wrapper(event: NewMessage, *args, **kwargs):
        user_id = event.sender_id
        db = DatabaseManager(db_path=DAYLOG_DB_PATH)
        user_row = db.get_user(user_id)
        if not user_row:
            tlgbot = globals().get('tlgbot')
            user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
            lang = getattr(user, 'lang', None) or get_user_lang(event)
            msg = tlgbot.i18n.t('diary_user_required', lang=lang) if hasattr(tlgbot, 'i18n') else "Вы не зарегистрированы в дневнике. Пожалуйста, сначала выполните команду /start."
            await event.reply(msg)
            return
        return await func(event, *args, **kwargs)
    return wrapper
