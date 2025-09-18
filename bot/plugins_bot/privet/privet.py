"""
Example plugin for tlgbotcore (send hi) with i18n support and default language fallback
"""

from telethon import events

# tlgbot глобально доступен в плагинах через динамическую загрузку
tlgbot = globals().get('tlgbot')

@tlgbot.on(tlgbot.cmd('hi'))
async def handler(event):
    user = tlgbot.settings.get_user(event.sender_id)
    # Получаем язык пользователя, если не задан — используем язык по умолчанию из i18n
    lang = getattr(user, "lang", tlgbot.i18n.default_lang)
    await event.reply(tlgbot.i18n.t("greeting", lang=lang))
