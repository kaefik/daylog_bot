"""
Example plugins for tlgbotcore (send hi)
"""

from telethon import events


@tlgbot.on(events.NewMessage(chats=tlgbot.settings.get_all_user_id(), pattern='hi'))
async def handler(event):
    # with open('README.md') as f:
    #     s = f.read()
    await event.reply('Привет!')
