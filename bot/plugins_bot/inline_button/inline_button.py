"""
    демонстрация кнопок внутри сообщений
"""

from telethon import events, Button

# кнопки команд
button_main_cmd = [
    # visible label, callback data token
    [Button.inline(tlgbot.i18n.t('inline_button_today', lang=tlgbot.i18n.default_lang) if hasattr(tlgbot, 'i18n') else "сегодня", b"today"),
     Button.inline(tlgbot.i18n.t('inline_button_tomorrow', lang=tlgbot.i18n.default_lang) if hasattr(tlgbot, 'i18n') else "завтра", b"tomorrow")],
    [Button.url('Check this site!', 'https://lonamiwebs.github.io'),
     Button.inline(tlgbot.i18n.t('inline_button_any', lang=tlgbot.i18n.default_lang) if hasattr(tlgbot, 'i18n') else "любой день", b"any")]
]


@tlgbot.on(tlgbot.admin_cmd('inline'))
async def start_cmd_plugin(event):
    await event.respond(tlgbot.i18n.t('inline_choose', lang=tlgbot.i18n.default_lang) if hasattr(tlgbot, 'i18n') else "Выбери ", buttons=button_main_cmd)
    # answer = await event.wait_event(events.CallbackQuery())
    # print(answer.data.decode("utf-8"))


@tlgbot.on(events.CallbackQuery(pattern='today|tomorrow|any'))
# @tlgbot.on(events.NewMessage(chats=tlgbot.settings.get_all_user_id(), pattern='сегодня'))
async def today_cmd(event):
    # data tokens are bytes like b'today' - map to localized label
    res = event.data.decode("utf-8")
    label_map = {
        'today': tlgbot.i18n.t('inline_button_today', lang=tlgbot.i18n.default_lang) if hasattr(tlgbot, 'i18n') else 'сегодня',
        'tomorrow': tlgbot.i18n.t('inline_button_tomorrow', lang=tlgbot.i18n.default_lang) if hasattr(tlgbot, 'i18n') else 'завтра',
        'any': tlgbot.i18n.t('inline_button_any', lang=tlgbot.i18n.default_lang) if hasattr(tlgbot, 'i18n') else 'любой день'
    }
    choice_label = label_map.get(res, res)
    await event.edit(tlgbot.i18n.t('inline_choice_selected', lang=tlgbot.i18n.default_lang, choice=choice_label) if hasattr(tlgbot, 'i18n') else f"Вы выбрали -  {choice_label}")
