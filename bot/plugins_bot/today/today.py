
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

    db = DatabaseManager()
    today = date.today()
    entry = db.get_diary_entry(user_id, today)
    if entry:
        await event.reply("Запись за сегодня уже существует.")
    else:
        created = db.create_diary_entry(user_id, today)
        if created:
            await event.reply("Создана новая запись за сегодня.")
        else:
            await event.reply("Ошибка при создании записи.")
