from telethon import events, Button
from core.database.manager import DatabaseManager
from cfg.config_tlg import DAYLOG_DB_PATH
from bot.reminders.manager import schedule_user_reminder, disable_user_reminder, parse_hhmm
from datetime import date
import re

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

@tlgbot.on(events.NewMessage(pattern=r'/settings'))
async def settings_root(event):
    user_id = event.sender_id
    lang = 'ru'
    await event.respond(
        tlgbot.i18n.t('settings_reminder_title', lang=lang),
        buttons=[
            [Button.inline(tlgbot.i18n.t('settings_reminder_set_time', lang=lang), data=b'rem:set')],
        ]
    )

@tlgbot.on(events.CallbackQuery(pattern=b'rem:set'))
async def show_time_menu(event):
    lang = 'ru'
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
    await event.edit(tlgbot.i18n.t('settings_reminder_saved', lang='ru', time=time_value))

@tlgbot.on(events.CallbackQuery(pattern=b'rem:custom'))
async def ask_custom_time(event):
    user_id = event.sender_id
    WAIT_CUSTOM_TIME[user_id] = True
    await event.edit(tlgbot.i18n.t('settings_reminder_enter_time', lang='ru'))

@tlgbot.on(events.CallbackQuery(pattern=b'rem:disable'))
async def disable_time(event):
    user_id = event.sender_id
    db.update_user_settings(user_id, reminder_enabled=0)
    disable_user_reminder(tlgbot, user_id)
    await event.edit(tlgbot.i18n.t('settings_reminder_disabled', lang='ru'))

@tlgbot.on(events.NewMessage())
async def catch_custom_time(event):
    user_id = event.sender_id
    if not WAIT_CUSTOM_TIME.get(user_id):
        return
    text = event.raw_text.strip()
    if not TIME_REGEX.match(text):
        await event.respond(tlgbot.i18n.t('settings_reminder_invalid_format', lang='ru'))
        return
    WAIT_CUSTOM_TIME.pop(user_id, None)
    db.update_user_settings(user_id, reminder_time=text, reminder_enabled=1)
    schedule_user_reminder(tlgbot, db, user_id, text)
    await event.respond(tlgbot.i18n.t('settings_reminder_saved', lang='ru', time=text))
