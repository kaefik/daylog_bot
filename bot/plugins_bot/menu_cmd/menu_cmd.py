"""Плагин команды /menu и текстовой кнопки '📎 Меню' для показа главного inline-меню повторно.

Логика:
- /menu всегда пересобирает и показывает текущее inline меню (с учётом enable/disable).
- Нажатие на reply-кнопку (текст совпадает с локализованным menu_show_button) обрабатывается как /menu.

Примечание: reply-кнопка создаётся в /start (start_cmd) и должна быть persistent, чтобы пользователь мог вызвать меню когда угодно.
"""
from telethon import events, Button
from bot.menu_system import build_menu, _is_admin_user
from bot.require_diary_user import require_diary_user

# tlgbot и logger внедряются динамически загрузчиком
tlgbot = globals().get('tlgbot')
logger = globals().get('logger')


def _get_lang(event):
    if hasattr(tlgbot, 'settings'):
        user = tlgbot.settings.get_user(event.sender_id)
        if user and getattr(user, 'lang', None):
            return user.lang
    return getattr(getattr(tlgbot, 'i18n', None), 'default_lang', 'ru')


async def _show_menu(event):
    lang = _get_lang(event)
    if hasattr(tlgbot, 'i18n'):
        t = tlgbot.i18n.t
        ready_text = t('start_ready', lang=lang)
    else:
        ready_text = 'Меню'
    buttons = build_menu(lang, is_admin=_is_admin_user(getattr(event, 'sender_id', 0)))
    await event.respond(ready_text, buttons=buttons)
    # Дублируем reply-кнопку меню (если пользователь очистил клавиатуру)
    try:
        if hasattr(tlgbot, 'i18n'):
            show_btn = tlgbot.i18n.t('menu_show_button', lang=lang)
        else:
            show_btn = '📎 Menu'
        await event.respond(show_btn, buttons=[[Button.text(show_btn, resize=True, single_use=False)]])
    except Exception as e:  # noqa: BLE001
        if logger:
            logger.error(f"menu_cmd: failed to send reply menu button: {e}")


@tlgbot.on(tlgbot.cmd('menu'))  # type: ignore[misc]
@require_diary_user
async def menu_command_handler(event):
    await _show_menu(event)


@tlgbot.on(events.NewMessage)  # type: ignore[misc]
@require_diary_user
async def menu_text_button_handler(event):
    """Перехватывает нажатие reply-кнопки (как обычное сообщение с её текстом)."""
    if not hasattr(tlgbot, 'i18n'):
        return
    lang = _get_lang(event)
    expected = tlgbot.i18n.t('menu_show_button', lang=lang)
    # Точное совпадение текста
    if (event.raw_text or '').strip() == expected:
        if logger:
            logger.debug('menu_cmd: reply menu button pressed')
        await _show_menu(event)
        # Не останавливаем дальнейшие обработчики — здесь нет риска конфликтов
        # Можно вернуть чтобы не плодить ответы
        return
