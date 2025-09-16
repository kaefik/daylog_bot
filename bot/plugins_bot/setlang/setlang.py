"""
Плагин для смены языка пользователя командой /setlang с inline-кнопками
"""


from telethon import events, Button
from cfg import config_tlg

@tlgbot.on(tlgbot.cmd('setlang'))
async def setlang_handler(event):
    user = tlgbot.settings.get_user(event.sender_id)
    # Формируем inline-кнопки для выбора языка на основе config_tlg.AVAILABLE_LANGS
    buttons = [
        [Button.inline(name, data=f"setlang_{code}")]
        for code, name in config_tlg.AVAILABLE_LANGS.items()
    ]
    await event.reply(
        tlgbot.i18n.t("choose_lang", lang=getattr(user, "lang", "ru")),
        buttons=buttons
    )

@tlgbot.on(events.CallbackQuery(pattern=b"setlang_.*"))
async def setlang_callback_handler(event):
    user = tlgbot.settings.get_user(event.sender_id)
    data = event.data.decode("utf-8")
    lang_code = data.replace("setlang_", "")
    if lang_code not in config_tlg.AVAILABLE_LANGS:
        await event.answer(
            tlgbot.i18n.t("lang_not_supported", lang=getattr(user, "lang", "ru"), code=lang_code),
            alert=True
        )
        return

    # Если по какой-то причине lang_code не задан, используем язык по умолчанию из конфига
    user.lang = lang_code or getattr(config_tlg, "DEFAULT_LANG", "ru")
    tlgbot.settings.update_user(user)  # используйте update_user для обновления существующего пользователя
    await event.edit(
        tlgbot.i18n.t("lang_changed", lang=user.lang, lang_name=config_tlg.AVAILABLE_LANGS[user.lang])
    )