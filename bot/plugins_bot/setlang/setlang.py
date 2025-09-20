"""
Плагин для смены языка пользователя командой /setlang с inline-кнопками
"""


from telethon import events, Button
from bot.menu_system import invalidate_menu, build_menu
from cfg import config_tlg

# tlgbot глобально доступен в плагинах через динамическую загрузку
tlgbot = globals().get('tlgbot')

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
    # Инвалидация кэша меню для нового языка
    try:
        invalidate_menu(user.lang)
    except Exception:  # noqa: BLE001
        pass

    # Обновляем текст
    await event.edit(
        tlgbot.i18n.t("lang_changed", lang=user.lang, lang_name=config_tlg.AVAILABLE_LANGS[user.lang])
    )

    # Показ обновлённого меню (inline)
    try:
        buttons = build_menu(user.lang)
        ready_text = tlgbot.i18n.t('start_ready', lang=user.lang)
        await event.respond(ready_text, buttons=buttons)
        # Добавляем/обновляем reply-кнопку меню на новом языке
        try:
            show_btn = tlgbot.i18n.t('menu_show_button', lang=user.lang)
            from telethon import Button as _Btn  # локальный импорт чтобы не тянуть вверх
            await event.respond(show_btn, buttons=[[ _Btn.text(show_btn, resize=True, single_use=False) ]])
        except Exception:  # noqa: BLE001
            pass
    except Exception:
        # Молча игнорируем если что-то не так, чтобы не ломать основной flow
        pass