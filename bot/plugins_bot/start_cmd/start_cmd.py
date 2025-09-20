"""
обработка команды /start
"""

from telethon import events, Button


# tlgbot глобально доступен в плагинах через динамическую загрузку
tlgbot = globals().get('tlgbot')

# кнопки команд
button_main_cmd = [
    [Button.text("/today"),
     Button.text("/yesterday")],
    [Button.text("/view"),
     Button.text("/export")]
]



@tlgbot.on(tlgbot.cmd('start'))
async def start_cmd_plugin(event):
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or getattr(tlgbot.i18n, 'default_lang', 'ru')
    try:
        from core.database.manager import DatabaseManager
        from cfg.config_tlg import DAYLOG_DB_PATH
    except ImportError:
        await event.respond("Ошибка импорта DatabaseManager или DAYLOG_DB_PATH.")
        return

    db = DatabaseManager(db_path=DAYLOG_DB_PATH)
    db_user = db.get_user(user_id)
    
    # Приветственное сообщение для всех пользователей
    welcome_message = tlgbot.i18n.t('start_welcome', lang=lang) if hasattr(tlgbot, 'i18n') else "Привет! жми на команды и получай информацию!"
    
    if db_user:
        # Если пользователь уже зарегистрирован, добавляем информацию об этом
        already_registered = tlgbot.i18n.t('diary_user_already_exists', lang=lang) if hasattr(tlgbot, 'i18n') else "Вы уже зарегистрированы в дневнике!"
        combined_message = f"{welcome_message}\n\n{already_registered}"
        await event.respond(combined_message, buttons=button_main_cmd)
        return

    username = getattr(event.sender, 'username', None) if hasattr(event, 'sender') else None
    first_name = getattr(event.sender, 'first_name', None) if hasattr(event, 'sender') else None
    last_name = getattr(event.sender, 'last_name', None) if hasattr(event, 'sender') else None
    db.create_user(user_id, username=username, first_name=first_name, last_name=last_name)

    await event.respond(welcome_message, buttons=button_main_cmd)
