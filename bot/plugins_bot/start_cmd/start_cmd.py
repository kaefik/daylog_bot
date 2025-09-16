"""
обработка команды /start
"""

from telethon import events, Button


# кнопки команд
button_main_cmd = [
    [Button.text(tlgbot.i18n.t('start_cmd_1', lang=tlgbot.i18n.default_lang) if hasattr(tlgbot, 'i18n') else "команда1"),
     Button.text(tlgbot.i18n.t('start_cmd_2', lang=tlgbot.i18n.default_lang) if hasattr(tlgbot, 'i18n') else "команда2")],
    [Button.text(tlgbot.i18n.t('start_cmd_3', lang=tlgbot.i18n.default_lang) if hasattr(tlgbot, 'i18n') else "команда3"),
     Button.text(tlgbot.i18n.t('start_cmd_4', lang=tlgbot.i18n.default_lang) if hasattr(tlgbot, 'i18n') else "команда4")]
]


@tlgbot.on(tlgbot.cmd('start'))
async def start_cmd_plugin(event):
    await event.respond(tlgbot.i18n.t('start_welcome', lang=tlgbot.i18n.default_lang) if hasattr(tlgbot, 'i18n') else "Привет! жми на команды и получай получай информацию!", buttons=button_main_cmd)
