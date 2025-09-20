# Плагин для команды /yesterday с мастером заполнения записи за предыдущий день

from datetime import date, timedelta
try:
    from bot.menu_system import register_menu
    register_menu({
        'key': 'yesterday', 'tr_key': 'menu_yesterday', 'plugin': 'yesterday', 'handler': 'yesterday_handler', 'order': 20
    })
except Exception:
    pass
from telethon import events
from bot.require_diary_user import require_diary_user
from core.diary import DiaryManager

# tlgbot глобально доступен в плагинах через динамическую загрузку
tlgbot = globals().get('tlgbot')
# Логгер доступен через глобальные переменные
logger = globals().get('logger')

# Создаем экземпляр DiaryManager
diary_manager = DiaryManager(tlgbot, logger, getattr(tlgbot, 'i18n', None))

# Добавляем обработчик для логирования всех callback-событий в модуле
@tlgbot.on(events.CallbackQuery())
async def log_all_yesterday_callbacks(event):
    # Логируем только те события, которые могут относиться к команде yesterday
    try:
        data = event.data.decode("utf-8")
        if "yesterday" in data or "cancel_edit_yesterday" in data:
            logger.debug(f"[YESTERDAY] GLOBAL CALLBACK MONITOR: {data}")
    except Exception as e:
        logger.debug(f"[YESTERDAY] GLOBAL CALLBACK MONITOR: Error processing callback: {str(e)}")
    # Обязательно возвращаем False, чтобы событие было обработано другими обработчиками
    return False

# Обработчик для команды /yesterday
@tlgbot.on(tlgbot.cmd('yesterday'))
@require_diary_user
async def yesterday_handler(event):
    # Добавляем отладочную информацию в начале обработчика
    logger.debug(f"[YESTERDAY] Command handler started")
    
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    logger.debug(f"[YESTERDAY] User ID: {user_id}, Lang: {lang}")
    
    yesterday_date = date.today() - timedelta(days=1)
    
    # Проверяем, существует ли уже запись за вчера
    entry_exists = await diary_manager.check_existing_entry(event, user_id, yesterday_date, lang, prefix="yesterday")
    
    if not entry_exists:
        # Начинаем мастер заполнения для новой записи
        await diary_manager.start_form(event, user_id, yesterday_date, lang, prefix="yesterday_")


# Обработчики для инлайн-кнопок формы
@tlgbot.on(events.CallbackQuery(pattern="yesterday_mood_.*"))
async def yesterday_mood_callback_handler(event):
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    data = event.data.decode("utf-8")
    choice = data.split("_")[2]  # yesterday_mood_choice
    
    await diary_manager.process_mood_callback(event, user_id, choice, lang, prefix="yesterday_")


@tlgbot.on(events.CallbackQuery(pattern="yesterday_weather_.*"))
async def yesterday_weather_callback_handler(event):
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    data = event.data.decode("utf-8")
    choice = data.split("_")[2]  # yesterday_weather_choice
    
    await diary_manager.process_weather_callback(event, user_id, choice, lang, prefix="yesterday_")


@tlgbot.on(events.CallbackQuery(pattern="yesterday_location_.*"))
async def yesterday_location_callback_handler(event):
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    data = event.data.decode("utf-8")
    choice = data.split("_")[2]  # yesterday_location_choice
    
    await diary_manager.process_location_callback(event, user_id, choice, lang, prefix="yesterday_")


@tlgbot.on(events.CallbackQuery(pattern="yesterday_events_.*"))
async def yesterday_events_callback_handler(event):
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    data = event.data.decode("utf-8")
    choice = data.split("_")[2]  # yesterday_events_choice
    
    await diary_manager.process_events_callback(event, user_id, choice, lang, prefix="yesterday_")


# Обработчик для ручного ввода текста
@tlgbot.on(events.NewMessage)
async def yesterday_handle_manual_input(event):
    user_id = event.sender_id
    
    # Проверяем, находится ли пользователь в состоянии ожидания ручного ввода
    if diary_manager.get_user_state(user_id) is None:
        return
    
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    # Используем метод process_manual_input из DiaryManager
    await diary_manager.process_manual_input(event, user_id, event.text, lang, prefix="yesterday_")


# Обработчик для редактирования записи и отмены редактирования
@tlgbot.on(events.CallbackQuery(pattern="edit_yesterday|edit_yesterday_events|cancel_edit_yesterday"))
@require_diary_user
async def handle_yesterday_editing(event):
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    # Добавляем подробный лог для отладки
    data = event.data.decode("utf-8")
    logger.debug(f"[YESTERDAY] Edit handler called with data: {data}, user_id: {user_id}")
    
    if data == "cancel_edit_yesterday":
        # Пользователь отказался от редактирования
        await event.edit(diary_manager._t('edit_canceled', lang=lang) or "Редактирование отменено.")
        return
    
    # Начинаем редактирование
    yesterday_date = date.today() - timedelta(days=1)
    
    if data == "edit_yesterday_events":
        # Редактирование только событий
        await diary_manager.start_edit_form(event, user_id, yesterday_date, lang, prefix="yesterday_", events_only=True)
    else:
        # Полное редактирование записи
        await diary_manager.start_edit_form(event, user_id, yesterday_date, lang, prefix="yesterday_")


# Обработчик для отмены создания/редактирования записи на любом этапе
@tlgbot.on(events.CallbackQuery(pattern="cancel_creation"))
async def cancel_creation_handler(event):
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    # Отладочное сообщение
    logger.debug(f"[YESTERDAY] Cancel creation handler called for user {user_id}")
    
    # Очищаем данные пользователя
    diary_manager.clear_user_data(user_id)
    
    # Сообщаем об отмене
    await event.edit(diary_manager._t('creation_canceled', lang=lang))