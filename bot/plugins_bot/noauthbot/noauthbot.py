"""
Сообщает пользователю у которого нет доступа к боту.
"""

from telethon import events


async def get_name_user(client, user_id):
    """
        получаем информацию о пользователе телеграмма по его user_id (user_id тип int)
    """
    try:
        new_name_user = await client.get_entity(user_id)
        new_name_user = new_name_user.first_name
    except ValueError as err:
        # use tlgbot logger if available, otherwise fallback to print
        try:
            tlgbot.logger.warning(tlgbot.i18n.t('user_info_error', lang=tlgbot.i18n.default_lang, err=str(err), user_id=user_id))
        except Exception:
            print('Ошибка получения информации о пользователе по id: ', err)
        new_name_user = ''
    return new_name_user


@tlgbot.on(events.NewMessage())
async def noauthbot_plugin(event):
    # with open('README.md') as f:
    #     s = f.read()
    sender = await event.get_sender()
    sender_id = sender.id
    if sender_id in tlgbot.settings.get_all_user_id():
        return
    await event.reply(tlgbot.i18n.t('no_access', lang=tlgbot.i18n.default_lang, user_id=sender_id))

    # отправляет сообщение всем администраторам
    all_admin = tlgbot.admins
    # print(all_admin)
    for id_admin in all_admin:
        # new_name_user = await get_name_user(event.client, int(id_admin))
        entry_user_admin = await event.client.get_entity(int(id_admin))
        # print(new_name_user)
    await event.client.send_message(entry_user_admin, tlgbot.i18n.t('noauth_attempt_notify', lang=tlgbot.i18n.default_lang, user_id=sender_id))
