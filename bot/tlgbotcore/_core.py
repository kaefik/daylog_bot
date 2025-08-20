# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Core commands for admin users
"""
import asyncio
import traceback

from cfg.config_tlg import TYPE_DB

if TYPE_DB == 'CSV':
    from bot.tlgbotcore.sqliteutils import User
elif TYPE_DB == 'SQLITE':
    from bot.tlgbotcore.sqliteutils import User

DELETE_TIMEOUT = 2


# вспомогательные функции
async def get_name_user(client, user_id):
    """
        получаем информацию о пользователе телеграмма по его user_id (user_id тип int)
    """
    try:
        new_name_user = await client.get_entity(user_id)
        new_name_user = new_name_user.first_name
    except ValueError as err:
        print('Ошибка получения информации о пользователе по id: ', err)
        new_name_user = ''
    return new_name_user


# END вспомогательные функции


@tlgbot.on(tlgbot.admin_cmd(r"(?:re)?load", r"(?P<shortname>\w+)"))
async def load_reload(event):
    if not tlgbot.me.bot:
        await event.delete()
    shortname = event.pattern_match["shortname"]

    if shortname == "_core":
        await event.respond("Плагин _core нельзя перезагружать.")
        return
    else:
        try:

            if shortname in tlgbot._plugins:
                await tlgbot.remove_plugin(shortname)

            # так как плагин хранится в папке с именем плагина
            tlgbot.load_plugin(f"{shortname}/{shortname}")

            msg = await event.respond(
                f"Successfully (re)loaded plugin {shortname}")
            if not tlgbot.me.bot:
                await asyncio.sleep(DELETE_TIMEOUT)
                await tlgbot.delete_messages(msg.to_id, msg)

        except Exception as e:
            tb = traceback.format_exc()
            logger.warn(f"Failed to (re)load plugin {shortname}: {tb}")
            await event.respond(f"Failed to (re)load plugin {shortname}: {e}")


@tlgbot.on(tlgbot.admin_cmd(r"(?:unload|disable|remove)", r"(?P<shortname>\w+)"))
async def remove(event):
    if not tlgbot.me.bot:
        await event.delete()
    shortname = event.pattern_match["shortname"]

    if shortname == "_core":
        msg = await event.respond(f"Not removing {shortname}")
    elif shortname in tlgbot._plugins:
        await tlgbot.remove_plugin(shortname)
        msg = await event.respond(f"Removed plugin {shortname}")
    else:
        msg = await event.respond(f"Plugin {shortname} is not loaded")

    if not tlgbot.me.bot:
        await asyncio.sleep(DELETE_TIMEOUT)
        await tlgbot.delete_messages(msg.to_id, msg)


@tlgbot.on(tlgbot.admin_cmd(r"plugins"))
async def list_plugins(event):
    result = f'{len(tlgbot._plugins)} plugins loaded:'
    for name, mod in sorted(tlgbot._plugins.items(), key=lambda t: t[0]):
        desc = (mod.__doc__ or '__no description__').replace('\n', ' ').strip()
        result += f'\n**{name}**: {desc}'

    if not tlgbot.me.bot:
        await event.edit(result)
    else:
        await event.respond(result)


@tlgbot.on(tlgbot.admin_cmd(r"(?:help)", r"(?P<shortname>\w+)"))
async def remove(event):
    if not tlgbot.me.bot:
        await event.delete()
    shortname = event.pattern_match["shortname"]

    if shortname == "_core":
        path_help_file = 'tlgbotcore/_core.md'
    else:
        path_help_file = f"{tlgbot._plugin_path}/{shortname}/{shortname}.md"

    if shortname in tlgbot._plugins:
        try:
            with open(path_help_file) as f:
                content_help = f.read()
        except FileNotFoundError:
            content_help = tlgbot._plugins[shortname].__doc__
            if not content_help:
                content_help = "Справочной информации по данному плагину нет."
        await event.reply(content_help)
    else:
        await event.reply(f"Plugin {shortname} is not loaded")


# команды работы с БД пользователей
@tlgbot.on(tlgbot.admin_cmd("adduser"))
# @bot.on(events.NewMessage(chats=allow_user_id(settings.get_all_user()), pattern='/AddUser'))
async def add_user_admin(event):
    """
    добавление активного пользователя с ролью обычного пользователя , по возможности получаем имя пользователя
    :return:
    """
    # sender = await event.get_sender()
    await event.respond("Выполняется команда /adduser")
    # диалог с запросом информации нужной для работы команды /AddUser
    chat_id = event.chat_id
    async with tlgbot.conversation(chat_id) as conv:
        # response = conv.wait_event(events.NewMessage(incoming=True))
        await conv.send_message("Привет! Введите номер id пользователя"
                                "который нужно добавить для доступа к боту:")
        id_new_user = await conv.get_response()
        id_new_user = id_new_user.message
        # print("id_new_user ", id_new_user)
        while not all(x.isdigit() for x in id_new_user):
            await conv.send_message("ID нового пользователя - это число. Попробуйте еще раз.")
            id_new_user = await conv.get_response()
            id_new_user = id_new_user.message
        # print("id_new_user ", id_new_user)

        new_name_user = await get_name_user(event.client, int(id_new_user))

        print('Имя нового пользователя', new_name_user)
        new_user = User(id=id_new_user, active=True, name=new_name_user)
        tlgbot.settings.add_user(new_user)
        # add_new_user(id_new_user, settings)
        await conv.send_message(f"Добавили нового пользователя с ID: {id_new_user} с именем {new_name_user}")
        tlgbot.load_all_plugins()


@tlgbot.on(tlgbot.admin_cmd("infouser"))
async def info_user_admin(event):
    """
    вывод информации о пользователях которые имеют доступ к боту
    :return:
    """
    ids = []
    clients = tlgbot.settings.get_all_user()
    for cl in clients:
        ids.append(cl.__str__())

    ids = [str(x) for x in ids]
    strs = '\n'.join(ids)
    await event.respond(f"Пользователи которые имеют доступ:\n{strs}")


@tlgbot.on(tlgbot.admin_cmd("deluser"))
async def del_user_admin(event):
    """
    удаление пользователя из БД пользователей, тем самым запрещая доступ указанному пользователю
    :return:
    """
    # диалог с запросом информации нужной для работы команды /deluser
    chat_id = event.chat_id
    async with tlgbot.conversation(chat_id) as conv:
        # response = conv.wait_event(events.NewMessage(incoming=True))
        await conv.send_message("Привет! Введите номер id пользователя "
                                "который нужно запретить доступ к боту")
        id_del_user = await conv.get_response()
        id_del_user = id_del_user.message
        while not any(x.isdigit() for x in id_del_user):
            await conv.send_message("ID пользователя - это число. "
                                    "Попробуйте еще раз.")
            id_del_user = await conv.get_response()
            id_del_user = id_del_user.message

        if not (int(id_del_user) in tlgbot.admins):
            tlgbot.settings.del_user(int(id_del_user))
            await conv.send_message(f"Пользователю с ID: {id_del_user} доступ к боту запрещен.")
            tlgbot.load_all_plugins()
        else:
            await conv.send_message("Удаление пользователя с правами администратора запрещено.")
# END команды работы с БД пользователей
