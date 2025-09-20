# Плагин для команды /today с мастером заполнения записи

from datetime import date
try:
    from bot.menu_system import register_menu
    # Регистрация пункта меню (если вызов повторится — будет проигнорирован)
    register_menu({
        'key': 'today', 'tr_key': 'menu_today', 'plugin': 'today', 'handler': 'today_handler', 'order': 10
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

# Глобальный обработчик для отслеживания всех callback-данных (отладочный)
@tlgbot.on(events.CallbackQuery())
async def global_callback_monitor(event):
    try:
        data = event.data.decode("utf-8")
        logger.debug(f"[TODAY] GLOBAL CALLBACK MONITOR: {data}")
    except Exception as e:
        logger.debug(f"[TODAY] GLOBAL CALLBACK MONITOR: Error processing callback: {str(e)}")
    # Обязательно возвращаем False, чтобы событие было обработано другими обработчиками
    return False

# Обработчик для команды /today
@tlgbot.on(tlgbot.cmd('today'))
@require_diary_user
async def today_handler(event):
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    logger.debug(f"[TODAY] Command handler started for user {user_id}, lang: {lang}")
    
    today_date = date.today()
    
    # Проверяем, существует ли уже запись за сегодня
    entry_exists = await diary_manager.check_existing_entry(event, user_id, today_date, lang, prefix="today")
    
    if not entry_exists:
        # Начинаем мастер заполнения для новой записи
        await diary_manager.start_form(event, user_id, today_date, lang)


# Обработчики для инлайн-кнопок формы
@tlgbot.on(events.CallbackQuery(pattern="mood_.*"))
async def mood_callback_handler(event):
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    data = event.data.decode("utf-8")
    choice = data.split("_")[1]  # mood_choice
    
    await diary_manager.process_mood_callback(event, user_id, choice, lang)


@tlgbot.on(events.CallbackQuery(pattern="weather_.*"))
async def weather_callback_handler(event):
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    data = event.data.decode("utf-8")
    choice = data.split("_")[1]  # weather_choice
    
    await diary_manager.process_weather_callback(event, user_id, choice, lang)


@tlgbot.on(events.CallbackQuery(pattern="location_.*"))
async def location_callback_handler(event):
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    data = event.data.decode("utf-8")
    choice = data.split("_")[1]  # location_choice
    
    await diary_manager.process_location_callback(event, user_id, choice, lang)


@tlgbot.on(events.CallbackQuery(pattern="events_.*"))
async def events_callback_handler(event):
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    data = event.data.decode("utf-8")
    choice = data.split("_")[1]  # events_choice
    
    await diary_manager.process_events_callback(event, user_id, choice, lang)


# Обработчик для ручного ввода текста (для полей с опцией "Ввести вручную")
@tlgbot.on(events.NewMessage)
async def handle_manual_input(event):
    user_id = event.sender_id
    
    # Проверяем, находится ли пользователь в состоянии ожидания ручного ввода
    if diary_manager.get_user_state(user_id) is None:
        return
    
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    # Используем метод process_manual_input из DiaryManager
    await diary_manager.process_manual_input(event, user_id, event.text, lang)


# Обработчик для отмены создания/редактирования записи на любом этапе
@tlgbot.on(events.CallbackQuery(pattern="cancel_creation"))
async def cancel_creation_handler(event):
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    # Отладочное сообщение
    logger.debug(f"[TODAY] Cancel creation handler called for user {user_id}")
    
    # Очищаем данные пользователя
    diary_manager.clear_user_data(user_id)
    
    # Сообщаем об отмене
    await event.edit(diary_manager._t('creation_canceled', lang=lang))


# Обработчик для кнопок редактирования существующей записи
@tlgbot.on(events.CallbackQuery(pattern="edit_today|edit_today_events|cancel_edit_today"))
@require_diary_user
async def handle_today_editing(event):
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    # Добавляем подробный лог для отладки
    data = event.data.decode("utf-8")
    logger.debug(f"[TODAY] Edit handler called with data: {data}, user_id: {user_id}")
    
    if data == "cancel_edit_today":
        # Пользователь отказался от редактирования
        await event.edit(diary_manager._t('edit_canceled', lang=lang) or "Редактирование отменено.")
        return
    
    # Начинаем редактирование
    today_date = date.today()
    
    if data == "edit_today_events":
        # Редактирование только событий
        await diary_manager.start_edit_form(event, user_id, today_date, lang, events_only=True)
    elif data == "edit_today":
        # Полное редактирование записи
        await diary_manager.start_edit_form(event, user_id, today_date, lang)
    else:
        # Полное редактирование записи
        await diary_manager.start_edit_form(event, user_id, today_date, lang)