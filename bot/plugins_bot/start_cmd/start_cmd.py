"""
обработка команды /start
"""

from telethon import events, Button
from bot.menu_system import build_menu, bootstrap_default_entries, send_main_menu, init_menu_system
import pytz


# tlgbot глобально доступен в плагинах через динамическую загрузку
tlgbot = globals().get('tlgbot')
logger = globals().get('logger')

# Старый механизм reply-клавиатуры заменён на inline-меню через menu_system.

# Популярные часовые пояса для России и соседних стран
POPULAR_TIMEZONES = [
    "Europe/Moscow",
    "Europe/Kaliningrad",
    "Europe/Samara",
    "Asia/Yekaterinburg",
    "Asia/Omsk",
    "Asia/Krasnoyarsk",
    "Asia/Irkutsk",
    "Asia/Yakutsk",
    "Asia/Vladivostok",
    "Asia/Magadan",
    "Asia/Kamchatka"
]

def create_timezone_buttons():
    """Создает кнопки с часовыми поясами"""
    buttons = []
    current_row = []
    
    for i, tz in enumerate(POPULAR_TIMEZONES):
        # По 2 кнопки в строке
        if i % 2 == 0 and i > 0:
            buttons.append(current_row)
            current_row = []
        
        # Получаем более читаемое представление зоны (только город)
        tz_display = tz.split('/')[-1].replace('_', ' ')
        current_row.append(Button.inline(tz_display, data=f"tz:{tz}"))
    
    # Добавляем последнюю строку, если она не пустая
    if current_row:
        buttons.append(current_row)
    
    # Добавляем кнопку Отмена в отдельную строку внизу
    cancel_text = tlgbot.i18n.t('cancel') if hasattr(tlgbot, 'i18n') else "Отмена"
    buttons.append([Button.inline(cancel_text, data="tz:cancel")])
    
    return buttons


@tlgbot.on(tlgbot.cmd('start'))
async def start_cmd_plugin(event):
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or getattr(tlgbot.i18n, 'default_lang', 'ru')
    try:
        from core.database.manager import DatabaseManager
        from cfg.config_tlg import DAYLOG_DB_PATH
    except ImportError:
        await event.respond("Ошибка импорта DatabaseManager или DAYLOG_DB_PATH.")
        return

    db = DatabaseManager(db_path=DAYLOG_DB_PATH)
    db_user = db.get_user(user_id)
    
    # Инициализация системы меню (гарантирует прикрепление callback роутера)
    init_menu_system(tlgbot, logger)
    bootstrap_default_entries()

    # Приветственное сообщение для всех пользователей
    welcome_message = tlgbot.i18n.t('start_welcome', lang=lang) if hasattr(tlgbot, 'i18n') else "Привет! жми на команды и получай информацию!"
    
    # Если пользователь не зарегистрирован, создаем его
    if not db_user:
        username = getattr(event.sender, 'username', None) if hasattr(event, 'sender') else None
        first_name = getattr(event.sender, 'first_name', None) if hasattr(event, 'sender') else None
        last_name = getattr(event.sender, 'last_name', None) if hasattr(event, 'sender') else None
        
        # Создаем пользователя с дефолтным часовым поясом
        db.create_user(user_id, username=username, first_name=first_name, last_name=last_name)
        
        # Отправляем приветственное сообщение
        await event.respond(welcome_message)
    else:
        # Если пользователь уже зарегистрирован, добавляем информацию об этом
        already_registered = tlgbot.i18n.t('diary_user_already_exists', lang=lang) if hasattr(tlgbot, 'i18n') else "Вы уже зарегистрированы в дневнике!"
        combined_message = f"{welcome_message}\n\n{already_registered}"
        await event.respond(combined_message)
    
    # Запрос на выбор часового пояса для всех пользователей
    timezone_message = tlgbot.i18n.t('timezone_select', lang=lang) if hasattr(tlgbot, 'i18n') else "Выберите ваш часовой пояс:"
    timezone_buttons = create_timezone_buttons()
    
    await event.respond(timezone_message, buttons=timezone_buttons)
    # Сразу показываем кнопку меню (по запросу UX) ещё до выбора часового пояса
    if hasattr(tlgbot, 'i18n'):
        show_btn = tlgbot.i18n.t('menu_show_button', lang=lang)
    else:
        show_btn = '📎 Menu'
    try:
        await event.respond(show_btn, buttons=[[Button.text(show_btn, resize=True, single_use=False)]])
    except Exception as e:  # noqa: BLE001
        if logger:
            logger.error(f"start_cmd: early reply menu button send failed: {e}")


# Обработчик выбора часового пояса
@tlgbot.on(events.CallbackQuery(pattern=r'^tz:'))
async def timezone_callback(event):
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or getattr(tlgbot.i18n, 'default_lang', 'ru')
    
    # Получаем выбранный часовой пояс из callback data
    callback_data = event.data.decode('utf-8').split(':')[1]
    
    try:
        from core.database.manager import DatabaseManager
        from cfg.config_tlg import DAYLOG_DB_PATH
        
        db = DatabaseManager(db_path=DAYLOG_DB_PATH)
        db_user = db.get_user(user_id)
        
        # Проверяем, был ли отменен выбор часового пояса
        if callback_data == "cancel":
            if db_user:
                # Пользователь уже зарегистрирован - не меняем часовой пояс
                cancel_message = tlgbot.i18n.t('timezone_unchanged', lang=lang) if hasattr(tlgbot, 'i18n') else "Текущий часовой пояс оставлен без изменений."
                await event.edit(cancel_message)
            else:
                # Новый пользователь - устанавливаем часовой пояс Москвы по умолчанию
                default_timezone = "Europe/Moscow"
                db.update_user_settings(user_id, timezone=default_timezone)
                default_message = tlgbot.i18n.t('timezone_default', lang=lang) if hasattr(tlgbot, 'i18n') else "Установлен часовой пояс по умолчанию (Europe/Moscow)."
                await event.edit(default_message)
            
            # Показываем кнопки основных команд
            start_ready = tlgbot.i18n.t('start_ready', lang=lang) if hasattr(tlgbot, 'i18n') else "Теперь вы можете начать вести дневник!"
            await send_main_menu(event, lang, start_ready)
            return
        
        # Проверяем валидность часового пояса
        selected_timezone = callback_data
        pytz.timezone(selected_timezone)
        
        # Обновляем часовой пояс пользователя
        db.update_user_settings(user_id, timezone=selected_timezone)
        
        timezone_message = tlgbot.i18n.t('timezone_selected', lang=lang, timezone=selected_timezone) if hasattr(tlgbot, 'i18n') else f"Часовой пояс установлен: {selected_timezone}"
        await event.edit(timezone_message)
        
        # Показываем кнопки основных команд
        start_ready = tlgbot.i18n.t('start_ready', lang=lang) if hasattr(tlgbot, 'i18n') else "Теперь вы можете начать вести дневник!"
        await send_main_menu(event, lang, start_ready)
    except Exception as e:
        logger.error(f"Ошибка обработки часового пояса: {e}")
        error_message = tlgbot.i18n.t('timezone_error', lang=lang) if hasattr(tlgbot, 'i18n') else "Ошибка при установке часового пояса."
        await event.edit(error_message)
        # Показываем кнопки основных команд только при ошибке
        start_ready = tlgbot.i18n.t('start_ready', lang=lang) if hasattr(tlgbot, 'i18n') else "Теперь вы можете начать вести дневник!"
        await send_main_menu(event, lang, start_ready)
