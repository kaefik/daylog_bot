
# Плагин для команды /today



from datetime import date
from telethon import events
from bot.require_diary_user import require_diary_user

# tlgbot глобально доступен в плагинах через динамическую загрузку
tlgbot = globals().get('tlgbot')

@tlgbot.on(tlgbot.cmd('today'))
@require_diary_user
async def today_handler(event):
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    try:
        from core.database.manager import DatabaseManager
    except ImportError:
        await event.reply(tlgbot.i18n.t('db_manager_import_error', lang=lang))
        return

    try:
        from cfg.config_tlg import DAYLOG_DB_PATH
    except ImportError:
        await event.reply(tlgbot.i18n.t('db_path_import_error', lang=lang))
        return

    db = DatabaseManager(db_path=DAYLOG_DB_PATH)
    today = date.today()
    entry = db.get_diary_entry(user_id, today)
    if entry:
        await event.reply(tlgbot.i18n.t('today_entry_exists', lang=lang))
        return

    created = db.create_diary_entry(user_id, today)
    if created:
        await event.reply(tlgbot.i18n.t('today_entry_created', lang=lang))
    else:
        await event.reply(tlgbot.i18n.t('today_entry_error', lang=lang))
