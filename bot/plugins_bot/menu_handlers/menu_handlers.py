"""
Обработчики кнопок главного меню
"""

from telethon import events
from bot.require_diary_user import require_diary_user

# tlgbot глобально доступен в плагинах через динамическую загрузку
tlgbot = globals().get('tlgbot')
logger = globals().get('logger')

def safe_call_command(shortname: str, handler_name: str, event):
    """Вызов обработчика команды из уже загруженного плагина.

    Исключаем повторный import (ломает декораторы, tlgbot может быть None).
    Возвращает True если вызов сделан.
    """
    try:
        plugins = getattr(tlgbot, '_plugins', {})
        mod = plugins.get(shortname)
        if not mod:
            logger.error(f"menu_handler: plugin '{shortname}' not found in loaded plugins")
            return False
        handler = getattr(mod, handler_name, None)
        if not handler:
            logger.error(f"menu_handler: handler '{handler_name}' not found in plugin '{shortname}'")
            return False
        # Вызов асинхронного обработчика
        return handler(event)
    except Exception as e:
        logger.error(f"menu_handler: error in safe_call_command {shortname}.{handler_name}: {e}")
        return False

def get_menu_text(key, lang='ru'):
    """Получает переведенный текст кнопки меню"""
    if hasattr(tlgbot, 'i18n'):
        return tlgbot.i18n.t(key, lang=lang)
    
    # Фоллбек на русский
    fallbacks = {
        'menu_today': "📝 Сегодня",
        'menu_yesterday': "📅 Вчера", 
        'menu_view': "👁️ Просмотр",
        'menu_export': "📤 Экспорт"
    }
    return fallbacks.get(key, "")

@tlgbot.on(events.NewMessage)
@require_diary_user
async def menu_handler(event):
    """Обработчик кнопок главного меню"""
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or getattr(tlgbot.i18n, 'default_lang', 'ru')
    
    message_text = event.message.text.strip()
    
    # Получаем переведенные тексты кнопок для текущего языка
    today_text = get_menu_text('menu_today', lang)
    yesterday_text = get_menu_text('menu_yesterday', lang)
    view_text = get_menu_text('menu_view', lang)
    export_text = get_menu_text('menu_export', lang)
    
    # Проверяем, соответствует ли сообщение одной из кнопок меню
    if message_text == today_text:
        # Подменяем текст на команду для единообразия
        try:
            event.message.text = '/today'
            event.text = '/today'
        except Exception:
            pass
        coro = safe_call_command('today', 'today_handler', event)
        if coro:
            await coro
        raise events.StopPropagation
    elif message_text == yesterday_text:
        try:
            event.message.text = '/yesterday'
            event.text = '/yesterday'
        except Exception:
            pass
        coro = safe_call_command('yesterday', 'yesterday_handler', event)
        if coro:
            await coro
        raise events.StopPropagation
    elif message_text == view_text:
        # Подменяем текст на команду без аргументов, чтобы handler не пытался парсить "👁️ Просмотр"
        try:
            event.message.text = '/view'
            event.text = '/view'
        except Exception:
            pass
        coro = safe_call_command('view', 'view_command_handler', event)
        if coro:
            await coro
        else:
            # fallback: если команда без параметров не реализована, можно эмулировать /view help
            logger.error("menu_handler: view_handler not found; пользователь нажал кнопку меню")
        raise events.StopPropagation
    elif message_text == export_text:
        coro = safe_call_command('export', 'export_command_handler', event)
        if coro:
            await coro
        raise events.StopPropagation
    
    # Не кнопка меню — не мешаем другим обработчикам (позволяем /setlang и др. работать)
    return