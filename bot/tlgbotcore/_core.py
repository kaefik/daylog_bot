# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Core commands for admin users
"""
import asyncio
import traceback
import logging
from typing import Any
from telethon import events, Button
try:
    from bot.menu_system import register_menu
    # Регистрация admin-only пунктов меню (идемпотентно)
    register_menu({'key': 'listusers', 'tr_key': 'menu_listusers', 'plugin': '_core', 'handler': 'info_user_admin', 'order': 900, 'admin_only': True})
    register_menu({'key': 'adduser', 'tr_key': 'menu_adduser', 'plugin': '_core', 'handler': 'add_user_admin', 'order': 910, 'admin_only': True})
    register_menu({'key': 'deluser', 'tr_key': 'menu_deluser', 'plugin': '_core', 'handler': 'del_user_admin', 'order': 920, 'admin_only': True})
except Exception:
    pass

from cfg import config_tlg  # Добавьте импорт конфига для доступа к DEFAULT_LANG
from cfg.config_tlg import TYPE_DB
from bot.tlgbotcore.models import User

logger = logging.getLogger(__name__)

DELETE_TIMEOUT = 2

# runtime injects `tlgbot` when loading the plugin; declare for static analysis
tlgbot: Any

logger = logging.getLogger(__name__)


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


def _get_event_lang(event):
    """Return language code for the user who triggered the event, fallback to bot default."""
    try:
        user = tlgbot.settings.get_user(event.sender_id)
        return getattr(user, 'lang', tlgbot.i18n.default_lang)
    except Exception:
        return tlgbot.i18n.default_lang


# END вспомогательные функции

# Функции для работы с событиями от кнопок
# Обработчик для кнопок при добавлении пользователя
notify_add_user_id = None
notify_add_user_name = None

@tlgbot.on(events.CallbackQuery(pattern='notify_add_yes|notify_add_no'))
async def on_notify_add_button(event):
    global notify_add_user_id, notify_add_user_name
    choice = event.data.decode("utf-8")
    lang = _get_event_lang(event)
    
    if choice == 'notify_add_yes' and notify_add_user_id:
        try:
            # Отправляем уведомление пользователю
            await event.client.send_message(
                int(notify_add_user_id), 
                tlgbot.i18n.t('adduser_notify_user', lang=tlgbot.i18n.default_lang)
            )
            await event.edit(tlgbot.i18n.t('adduser_notify_sent', lang=lang))
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления пользователю {notify_add_user_id}: {e}")
            await event.edit(f"Ошибка при отправке уведомления: {e}")
    else:
        await event.edit(tlgbot.i18n.t('adduser_success', lang=lang, user_id=notify_add_user_id, name=notify_add_user_name))
    
    # Сбросим ID для следующего использования
    notify_add_user_id = None
    notify_add_user_name = None

# Обработчик для кнопок при удалении пользователя
notify_del_user_id = None

@tlgbot.on(events.CallbackQuery(pattern='notify_del_yes|notify_del_no'))
async def on_notify_del_button(event):
    global notify_del_user_id
    choice = event.data.decode("utf-8")
    lang = _get_event_lang(event)
    
    if choice == 'notify_del_yes' and notify_del_user_id:
        try:
            # Отправляем уведомление пользователю
            await event.client.send_message(
                int(notify_del_user_id), 
                tlgbot.i18n.t('deluser_notify_user', lang=tlgbot.i18n.default_lang)
            )
            await event.edit(tlgbot.i18n.t('deluser_notify_sent', lang=lang))
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления пользователю {notify_del_user_id}: {e}")
            await event.edit(f"Ошибка при отправке уведомления: {e}")
    else:
        await event.edit(tlgbot.i18n.t('deluser_success', lang=lang, user_id=notify_del_user_id))
    
    # Сбросим ID для следующего использования
    notify_del_user_id = None


@tlgbot.on(tlgbot.admin_cmd(r"(?:re)?load", r"(?P<shortname>\w+)"))
async def load_reload(event):
    if not tlgbot.me.bot:
        await event.delete()
    shortname = event.pattern_match["shortname"]

    if shortname == "_core":
        lang = _get_event_lang(event)
        await event.respond(tlgbot.i18n.t('reload_core_forbidden', lang=lang))
        return
    else:
        try:

            if shortname in tlgbot._plugins:
                await tlgbot.remove_plugin(shortname)

            # так как плагин хранится в папке с именем плагина
            tlgbot.load_plugin(f"{shortname}/{shortname}")

            lang = _get_event_lang(event)
            msg = await event.respond(
                tlgbot.i18n.t('reload_success', lang=lang, name=shortname)
            )
            if not tlgbot.me.bot:
                await asyncio.sleep(DELETE_TIMEOUT)
                await tlgbot.delete_messages(msg.to_id, msg)

        except Exception as e:
            tb = traceback.format_exc()
            # log in default language
            logger.warn(tlgbot.i18n.t('reload_failed', lang=tlgbot.i18n.default_lang, name=shortname, error=tb))
            await event.respond(tlgbot.i18n.t('reload_failed', lang=_get_event_lang(event), name=shortname, error=e))


@tlgbot.on(tlgbot.admin_cmd(r"(?:unload|disable|remove)", r"(?P<shortname>\w+)"))
async def remove(event):
    if not tlgbot.me.bot:
        await event.delete()
    shortname = event.pattern_match["shortname"]

    if shortname == "_core":
        lang = _get_event_lang(event)
        msg = await event.respond(tlgbot.i18n.t('remove_not_removing', lang=lang, name=shortname))
    elif shortname in tlgbot._plugins:
        await tlgbot.remove_plugin(shortname)
        lang = _get_event_lang(event)
        msg = await event.respond(tlgbot.i18n.t('remove_removed', lang=lang, name=shortname))
    else:
        lang = _get_event_lang(event)
        msg = await event.respond(tlgbot.i18n.t('remove_not_loaded', lang=lang, name=shortname))

    if not tlgbot.me.bot:
        await asyncio.sleep(DELETE_TIMEOUT)
        await tlgbot.delete_messages(msg.to_id, msg)


@tlgbot.on(tlgbot.admin_cmd(r"plugins"))
async def list_plugins(event):
    result = f'{len(tlgbot._plugins)} plugins loaded:'
    for name, mod in sorted(tlgbot._plugins.items(), key=lambda t: t[0]):
        desc = (mod.__doc__ or '__no description__').replace('\n', ' ').strip()
        result += f'\n**{name}**: {desc}'

    lang = _get_event_lang(event)
    # localized header
    header = tlgbot.i18n.t('list_plugins_header', lang=lang, count=len(tlgbot._plugins))
    full = header + '\n' + '\n'.join([f'**{n}**: {(m.__doc__ or "__no description__").replace("\n", " ").strip()}' for n, m in sorted(tlgbot._plugins.items(), key=lambda t: t[0])])
    if not tlgbot.me.bot:
        await event.edit(full)
    else:
        await event.respond(full)


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
                content_help = tlgbot.i18n.t('help_no_info', lang=_get_event_lang(event))
        await event.reply(content_help)
    else:
        await event.reply(tlgbot.i18n.t('help_plugin_not_loaded', lang=_get_event_lang(event), name=shortname))


# команды работы с БД пользователей
@tlgbot.on(tlgbot.admin_cmd("adduser"))
async def add_user_admin(event):
    """
    добавление активного пользователя с ролью обычного пользователя , по возможности получаем имя пользователя
    :return:
    """
    global notify_add_user_id, notify_add_user_name
    lang = _get_event_lang(event)
    await event.respond(tlgbot.i18n.t('adduser_start', lang=lang))
    chat_id = event.chat_id
    async with tlgbot.conversation(chat_id) as conv:
        await conv.send_message(tlgbot.i18n.t('adduser_ask_id', lang=lang))
        id_new_user = await conv.get_response()
        id_new_user = id_new_user.message
        while not all(x.isdigit() for x in id_new_user):
            await conv.send_message(tlgbot.i18n.t('adduser_id_not_digit', lang=lang))
            id_new_user = await conv.get_response()
            id_new_user = id_new_user.message

        new_name_user = await get_name_user(event.client, int(id_new_user))

        logger.info(tlgbot.i18n.t('log_new_user_name', lang=tlgbot.i18n.default_lang, name=new_name_user))
        # Указываем язык по умолчанию из конфига
        new_user = User(
            id=id_new_user,
            active=True,
            name=new_name_user,
            lang=getattr(config_tlg, "DEFAULT_LANG", "ru")
        )
        tlgbot.settings.add_user(new_user)
        tlgbot.refresh_admins()
        
        # Сохраняем ID и имя для обработчика кнопок
        notify_add_user_id = id_new_user
        notify_add_user_name = new_name_user
        
        # Создаем кнопки для выбора
        notify_buttons = [
            [Button.inline(tlgbot.i18n.t('yes', lang=lang), b"notify_add_yes"),
             Button.inline(tlgbot.i18n.t('no', lang=lang), b"notify_add_no")]
        ]
        
        # Спрашиваем, отправлять ли уведомление пользователю, с помощью inline-кнопок
        await conv.send_message(
            tlgbot.i18n.t('adduser_ask_notify', lang=lang),
            buttons=notify_buttons
        )
        
        await tlgbot.load_all_plugins()


@tlgbot.on(tlgbot.admin_cmd("listusers"))
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
    lang = _get_event_lang(event)
    await event.respond(tlgbot.i18n.t('listusers', lang=lang, users=strs))


@tlgbot.on(tlgbot.admin_cmd("deluser"))
async def del_user_admin(event):
    """
    удаление пользователя из БД пользователей, тем самым запрещая доступ указанному пользователю
    :return:
    """
    global notify_del_user_id
    # диалог с запросом информации нужной для работы команды /deluser
    chat_id = event.chat_id
    lang = _get_event_lang(event)
    async with tlgbot.conversation(chat_id) as conv:
        # response = conv.wait_event(events.NewMessage(incoming=True))
        await conv.send_message(tlgbot.i18n.t('deluser_ask_id', lang=lang))
        id_del_user = await conv.get_response()
        id_del_user = id_del_user.message
        while not any(x.isdigit() for x in id_del_user):
            await conv.send_message(tlgbot.i18n.t('deluser_id_not_digit', lang=lang))
            id_del_user = await conv.get_response()
            id_del_user = id_del_user.message

        if not (int(id_del_user) in tlgbot.admins):
            # Сохраняем ID для обработчика кнопок
            notify_del_user_id = id_del_user
            
            # Создаем кнопки для выбора
            notify_buttons = [
                [Button.inline(tlgbot.i18n.t('yes', lang=lang), b"notify_del_yes"),
                 Button.inline(tlgbot.i18n.t('no', lang=lang), b"notify_del_no")]
            ]
            
            # Спрашиваем, отправлять ли уведомление пользователю, с помощью inline-кнопок
            await conv.send_message(
                tlgbot.i18n.t('deluser_ask_notify', lang=lang),
                buttons=notify_buttons
            )
            
            # Удаляем пользователя
            tlgbot.settings.del_user(int(id_del_user))
            tlgbot.refresh_admins()
            await tlgbot.load_all_plugins()
        else:
            await conv.send_message(tlgbot.i18n.t('deluser_admin_forbidden', lang=lang))
# END команды работы с БД пользователей
