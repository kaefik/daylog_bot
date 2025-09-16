
# Плагин для команды /today
from datetime import date
from telethon import events

# tlgbot глобально доступен в плагинах через динамическую загрузку
tlgbot = globals().get('tlgbot')

@tlgbot.on(tlgbot.cmd('today'))
async def today_handler(event):
    user_id = event.sender_id
    try:
        from core.database.manager import DatabaseManager
    except ImportError:
        await event.reply("Ошибка импорта DatabaseManager.")
        return

    try:
        from cfg.config_tlg import DAYLOG_DB_PATH
    except ImportError:
        await event.reply("Ошибка импорта DAYLOG_DB_PATH из config_tlg.")
        return

    db = DatabaseManager(db_path=DAYLOG_DB_PATH)
    today = date.today()
    entry = db.get_diary_entry(user_id, today)
    if entry:
        await event.reply("Запись за сегодня уже существует.")
        return

    # Проверяем, есть ли пользователь в users
    user_row = db.get_user(user_id)
    if not user_row:
        # Добавляем пользователя (username и имя берём из event, если есть)
        username = getattr(event.sender, 'username', None) if hasattr(event, 'sender') else None
        first_name = getattr(event.sender, 'first_name', None) if hasattr(event, 'sender') else None
        last_name = getattr(event.sender, 'last_name', None) if hasattr(event, 'sender') else None
        db.create_user(user_id, username=username, first_name=first_name, last_name=last_name)

    created = db.create_diary_entry(user_id, today)
    if created:
        await event.reply("Создана новая запись за сегодня.")
    else:
        await event.reply("Ошибка при создании записи.")
