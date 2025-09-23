from telethon import events, Button
from core.database.manager import DatabaseManager
from cfg.config_tlg import DAYLOG_DB_PATH
from bot.reminders.manager import schedule_user_reminder, disable_user_reminder, parse_hhmm
from datetime import date
import re

# Регистрация в меню
try:
    from bot.menu_system import register_menu
    register_menu({
        'key': 'settings', 'tr_key': 'menu_settings', 'plugin': 'settings', 'handler': 'settings_root', 'order': 40
    })
except Exception as e:
    pass

# Глобали внедряются при загрузке плагина
tlgbot = globals().get('tlgbot')
logger = globals().get('logger')

db = DatabaseManager(db_path=DAYLOG_DB_PATH)
# гарантируем колонку
try:
    db.ensure_reminder_columns()
except Exception:
    pass

# Состояние ожидания ввода произвольного времени
WAIT_CUSTOM_TIME = {}
TIME_REGEX = re.compile(r'^(?:[01]\d|2[0-3]):[0-5]\d$')

PRESET_TIMES = ["18:00", "19:00", "20:00", "21:00", "22:00"]

def _resolve_lang(user_id: int) -> str:
    """Определение языка пользователя из settings-хранилища с fallback на ru."""
    try:
        user = tlgbot.settings.get_user(user_id)
        if user and getattr(user, 'lang', None):
            return user.lang
    except Exception:  # noqa: BLE001
        pass
    return 'ru'

@tlgbot.on(events.NewMessage(pattern=r'/settings'))
async def settings_root(event):
    user_id = event.sender_id
    lang = _resolve_lang(user_id)
    await event.respond(
        tlgbot.i18n.t('settings_reminder_title', lang=lang),
        buttons=[
            [
                Button.inline(tlgbot.i18n.t('settings_reminder_set_time', lang=lang), data=b'rem:set'),
                Button.inline(tlgbot.i18n.t('settings_change_language', lang=lang), data=b'setlang:open'),
            ],
            [
                Button.inline(tlgbot.i18n.t('cancel', lang=lang), data=b'settings:cancel'),
            ],
        ]
    )

@tlgbot.on(events.CallbackQuery(pattern=b'rem:set'))
async def show_time_menu(event):
    lang = _resolve_lang(event.sender_id)
    rows = []
    row = []
    for t in PRESET_TIMES:
        row.append(Button.inline(t, data=f'rem:t:{t}'.encode()))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([
        Button.inline(tlgbot.i18n.t('settings_reminder_custom', lang=lang), data=b'rem:custom'),
        Button.inline(tlgbot.i18n.t('settings_reminder_disable', lang=lang), data=b'rem:disable'),
    ])
    rows.append([
        Button.inline(tlgbot.i18n.t('cancel', lang=lang), data=b'settings:cancel'),
    ])
    await event.edit(tlgbot.i18n.t('settings_reminder_choose', lang=lang), buttons=rows)

@tlgbot.on(events.CallbackQuery(pattern=b'rem:t:'))
async def set_preset_time(event):
    data = event.data.decode()
    _, _, time_value = data.split(':', 2)
    user_id = event.sender_id
    if not TIME_REGEX.match(time_value):
        await event.answer('Invalid time')
        return
    db.update_user_settings(user_id, reminder_time=time_value, reminder_enabled=1)
    schedule_user_reminder(tlgbot, db, user_id, time_value)
    lang = _resolve_lang(user_id)
    await event.edit(tlgbot.i18n.t('settings_reminder_saved', lang=lang, time=time_value))

@tlgbot.on(events.CallbackQuery(pattern=b'rem:custom'))
async def ask_custom_time(event):
    user_id = event.sender_id
    WAIT_CUSTOM_TIME[user_id] = True
    lang = _resolve_lang(user_id)
    await event.edit(tlgbot.i18n.t('settings_reminder_enter_time', lang=lang))

@tlgbot.on(events.CallbackQuery(pattern=b'rem:disable'))
async def disable_time(event):
    user_id = event.sender_id
    db.update_user_settings(user_id, reminder_enabled=0)
    disable_user_reminder(tlgbot, user_id)
    lang = _resolve_lang(user_id)
    await event.edit(tlgbot.i18n.t('settings_reminder_disabled', lang=lang))

@tlgbot.on(events.CallbackQuery(pattern=b'setlang:open'))
async def settings_open_setlang(event):
    """Показать выбор языка прямо из меню настроек."""
    user = tlgbot.settings.get_user(event.sender_id)
    from cfg import config_tlg as _cfg  # локальный импорт
    buttons = [
        [Button.inline(name, data=f"setlang_{code}".encode())]
        for code, name in _cfg.AVAILABLE_LANGS.items()
    ]
    # Добавляем кнопку Отмена
    buttons.append([Button.inline(tlgbot.i18n.t('cancel', lang=getattr(user, 'lang', 'ru')), data=b'settings:cancel')])
    
    await event.edit(
        tlgbot.i18n.t('choose_lang', lang=getattr(user, 'lang', 'ru')),
        buttons=buttons
    )

@tlgbot.on(events.NewMessage())
async def catch_custom_time(event):
    user_id = event.sender_id
    if not WAIT_CUSTOM_TIME.get(user_id):
        return
    text = event.raw_text.strip()
    lang = _resolve_lang(user_id)
    if not TIME_REGEX.match(text):
        await event.respond(tlgbot.i18n.t('settings_reminder_invalid_format', lang=lang))
        return
    WAIT_CUSTOM_TIME.pop(user_id, None)
    db.update_user_settings(user_id, reminder_time=text, reminder_enabled=1)
    schedule_user_reminder(tlgbot, db, user_id, text)
    await event.respond(tlgbot.i18n.t('settings_reminder_saved', lang=lang, time=text))

@tlgbot.on(events.CallbackQuery(pattern=b'settings:cancel'))
async def settings_cancel(event):
    """Обработчик кнопки Отмена в меню настроек."""
    user_id = event.sender_id
    lang = _resolve_lang(user_id)
    
    # Сначала ответим на callback, чтобы убрать индикатор загрузки
    await event.answer()
    
    # Удаляем сообщение с меню настроек
    try:
        await event.delete()
        if logger:
            logger.debug(f"settings.py: удалено меню настроек при нажатии на кнопку Отмена")
    except Exception as e:
        if logger:
            logger.error(f"settings.py: ошибка при удалении меню настроек: {e}")
