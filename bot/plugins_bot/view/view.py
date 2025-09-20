# Плагин для команды /view с возможностью просмотра записей по дате

from datetime import datetime, date, timedelta
try:
    from bot.menu_system import register_menu
    register_menu({
        'key': 'view', 'tr_key': 'menu_view', 'plugin': 'view', 'handler': 'view_command_handler', 'order': 30
    })
except Exception:
    pass
import calendar
import re
from telethon import events, Button
from bot.require_diary_user import require_diary_user

# tlgbot глобально доступен в плагинах через динамическую загрузку
tlgbot = globals().get('tlgbot')
# Логгер доступен через глобальные переменные
logger = globals().get('logger')

async def parse_date(date_str):
    """
    Парсит дату из строки в формате DD.MM.YYYY или DD.MM или DD.MM.*
    Возвращает tuple:
    - Если обычная дата, то (date_obj, False)
    - Если дата с годом *, то (None, (day, month))
    - Если ошибка, то (None, False)
    """
    try:
        # Регулярное выражение для формата DD.MM.YYYY
        full_date_pattern = r'^(\d{1,2})\.(\d{1,2})\.(\d{4})$'
        # Регулярное выражение для формата DD.MM
        short_date_pattern = r'^(\d{1,2})\.(\d{1,2})$'
        # Регулярное выражение для формата DD.MM.*
        all_years_pattern = r'^(\d{1,2})\.(\d{1,2})\.\*$'
        
        full_match = re.match(full_date_pattern, date_str)
        short_match = re.match(short_date_pattern, date_str)
        all_years_match = re.match(all_years_pattern, date_str)
        
        if full_match:
            day, month, year = map(int, full_match.groups())
            return date(year, month, day), False
        elif short_match:
            day, month = map(int, short_match.groups())
            current_year = datetime.now().year
            return date(current_year, month, day), False
        elif all_years_match:
            day, month = map(int, all_years_match.groups())
            # Возвращаем tuple (day, month) как флаг для поиска по всем годам
            return None, (day, month)
        else:
            return None, False
    except ValueError as e:
        logger.warning(f"Ошибка парсинга даты '{date_str}': {e}")
        return None, False

async def get_entry_by_date(user_id, entry_date):
    """
    Получает запись из базы данных по дате
    """
    try:
        # Получаем экземпляр менеджера БД
        from core.database.manager import DatabaseManager
        from cfg.config_tlg import DAYLOG_DB_PATH
        
        # Создаем экземпляр DB с явным указанием пути к БД (как в других плагинах)
        db_manager = DatabaseManager(db_path=DAYLOG_DB_PATH)
        
        # Дополнительное логирование для отладки
        logger.debug(f"Getting entry with user_id={user_id}, entry_date={entry_date}, type={type(entry_date)}")
        
        # Используем напрямую объект date для запроса к БД
        entry = db_manager.get_diary_entry(user_id, entry_date)
        
        # Для отладки выведем информацию о полученной записи
        date_str = entry_date.strftime("%Y-%m-%d")
        logger.debug(f"Поиск записи для пользователя {user_id} за дату {date_str}: {entry}")
        
        return entry
    except Exception as e:
        logger.error(f"Ошибка при получении записи из БД: {e}")
        return None

async def get_entries_by_day_month(user_id, day, month):
    """
    Получает записи из базы данных по дню и месяцу за все годы
    """
    try:
        # Получаем экземпляр менеджера БД
        from core.database.manager import DatabaseManager
        from cfg.config_tlg import DAYLOG_DB_PATH
        
        # Создаем экземпляр DB с явным указанием пути к БД
        db_manager = DatabaseManager(db_path=DAYLOG_DB_PATH)
        
        # Логирование
        logger.debug(f"Searching entries for user_id={user_id}, day={day}, month={month}")
        
        # Получаем записи за все годы
        entries = db_manager.get_diary_entries_by_day_month(user_id, day, month)
        
        logger.debug(f"Найдено {len(entries)} записей")
        
        return entries
    except Exception as e:
        logger.error(f"Ошибка при получении записей из БД: {e}")
        return []

async def get_entries_by_period(user_id, start_date, end_date):
    """
    Получает записи из базы данных за указанный период
    """
    try:
        # Получаем экземпляр менеджера БД
        from core.database.manager import DatabaseManager
        from cfg.config_tlg import DAYLOG_DB_PATH
        
        # Создаем экземпляр DB с явным указанием пути к БД
        db_manager = DatabaseManager(db_path=DAYLOG_DB_PATH)
        
        # Логирование
        logger.debug(f"Searching entries for user_id={user_id}, period={start_date} to {end_date}")
        
        # Получаем записи за период
        entries = db_manager.get_entries_by_period(user_id, start_date, end_date)
        
        logger.debug(f"Найдено {len(entries)} записей за период")
        
        return entries
    except Exception as e:
        logger.error(f"Ошибка при получении записей из БД за период: {e}")
        return []

def get_week_dates():
    """
    Возвращает начальную и конечную даты текущей недели
    Неделя считается с понедельника по воскресенье
    """
    today = date.today()
    # Получаем номер дня недели (0 - понедельник, 6 - воскресенье)
    weekday = today.weekday()
    # Начало недели (понедельник)
    start_of_week = today - timedelta(days=weekday)
    # Конец недели (воскресенье)
    end_of_week = start_of_week + timedelta(days=6)
    
    return start_of_week, end_of_week

def get_month_dates():
    """
    Возвращает начальную и конечную даты текущего месяца
    """
    today = date.today()
    # Первый день месяца
    start_of_month = date(today.year, today.month, 1)
    # Последний день месяца
    _, last_day = calendar.monthrange(today.year, today.month)
    end_of_month = date(today.year, today.month, last_day)
    
    return start_of_month, end_of_month

async def display_period_entries(event, entries, period_name):
    """
    Форматирует и отображает записи за период
    """
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    try:
        if not entries:
            await event.respond(tlgbot.i18n.t('view_entries_not_found_period', lang=lang, period=period_name) or f"Записи за {period_name} не найдены.")
            return
        
        # Сортируем записи по дате (от новых к старым)
        sorted_entries = sorted(entries, key=lambda x: x.get('entry_date'), reverse=True)
        
        # Формируем заголовок с информацией о периоде
        header = tlgbot.i18n.t('entries_for_period', lang=lang, period=period_name) or f"📅 **Записи за {period_name}**\n\n"
        await event.respond(header, parse_mode='markdown')
        
        # Отправляем каждую запись отдельным сообщением
        for entry in sorted_entries:
            # Получаем дату записи (может быть объектом date или строкой)
            entry_date = entry.get('entry_date')
            if isinstance(entry_date, str):
                # Если это строка в формате ISO, преобразуем в date
                entry_date = datetime.fromisoformat(entry_date).date()
            # Если это уже объект date, то используем как есть
            
            await display_entry(event, entry, entry_date)
    
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        logger.error(f"Ошибка при отображении записей за период: {traceback_str}")
        await event.respond(f"Ошибка при отображении записей: {str(e)}")

async def show_period_selection(event):
    """
    Показывает кнопки выбора периода для просмотра записей
    """
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    message = tlgbot.i18n.t('view_select_period', lang=lang) or "Выберите период для просмотра записей:"
    
    # Создаем кнопки выбора периода
    buttons = [
        [
            Button.inline(tlgbot.i18n.t('view_today', lang=lang) or "Сегодня", data="view_period_today"),
            Button.inline(tlgbot.i18n.t('view_week', lang=lang) or "Текущая неделя", data="view_period_week")
        ],
        [
            Button.inline(tlgbot.i18n.t('view_month', lang=lang) or "Текущий месяц", data="view_period_month"),
            Button.inline(tlgbot.i18n.t('view_custom', lang=lang) or "Другая дата", data="view_period_custom")
        ]
    ]
    
    await event.respond(message, buttons=buttons)

async def display_entry(event, entry, display_date):
    """
    Форматирует и отображает запись пользователю
    """
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    try:
        # Форматируем дату для отображения
        date_formatted = display_date.strftime("%d.%m.%Y")
        
        # Получаем данные из записи
        mood = entry.get("mood") or tlgbot.i18n.t('not_specified', lang=lang) or "Не указано"
        weather = entry.get("weather") or tlgbot.i18n.t('not_specified', lang=lang) or "Не указано"
        location = entry.get("location") or tlgbot.i18n.t('not_specified', lang=lang) or "Не указано"
        events = entry.get("events") or tlgbot.i18n.t('not_specified', lang=lang) or "Не указано"
        
        # Форматируем сообщение
        message = (tlgbot.i18n.t('entry_header', lang=lang, date=date_formatted) or f"📝 **Запись от {date_formatted}**") + "\n\n"
        message += (tlgbot.i18n.t('entry_mood', lang=lang, mood=mood) or f"😊 Настроение: {mood}") + "\n"
        message += (tlgbot.i18n.t('entry_weather', lang=lang, weather=weather) or f"🌤 Погода: {weather}") + "\n"
        message += (tlgbot.i18n.t('entry_location', lang=lang, location=location) or f"📍 Местоположение: {location}") + "\n"
        message += (tlgbot.i18n.t('entry_events', lang=lang, events=events) or f"📌 События: {events}") + "\n"
        
        await event.respond(message, parse_mode='markdown')
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        logger.error(f"Ошибка при отображении записи: {traceback_str}")
        await event.respond(f"Ошибка при отображении записи: {str(e)}")

async def display_multiple_entries(event, entries):
    """
    Форматирует и отображает несколько записей пользователю
    """
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    try:
        if not entries:
            await event.respond(tlgbot.i18n.t('view_entries_not_found', lang=lang) or "Записи не найдены.")
            return
        
        # Сортируем записи по дате (от новых к старым)
        sorted_entries = sorted(entries, key=lambda x: x.get('entry_date'), reverse=True)
        
        # Получаем образец даты для заголовка
        sample_date_value = sorted_entries[0].get('entry_date')
        if isinstance(sample_date_value, str):
            sample_date = datetime.fromisoformat(sample_date_value).date()
        else:
            sample_date = sample_date_value
            
        date_formatted = sample_date.strftime("%d.%m")
        
        header = tlgbot.i18n.t('entries_for_date', lang=lang, date=date_formatted) or f"📅 **Записи за {date_formatted} (все годы)**\n\n"
        await event.respond(header, parse_mode='markdown')
        
        # Отправляем каждую запись отдельным сообщением
        for entry in sorted_entries:
            # Получаем дату записи (может быть объектом date или строкой)
            entry_date = entry.get('entry_date')
            if isinstance(entry_date, str):
                # Если это строка в формате ISO, преобразуем в date
                entry_date = datetime.fromisoformat(entry_date).date()
            # Если это уже объект date, то используем как есть
            
            await display_entry(event, entry, entry_date)
    
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        logger.error(f"Ошибка при отображении записей: {traceback_str}")
        await event.respond(f"Ошибка при отображении записей: {str(e)}")

@tlgbot.on(events.NewMessage(pattern=r'^/view(?:\s+(\S+))?'))
@require_diary_user
async def view_command_handler(event):
    """
    Обработчик команды /view
    Принимает опциональный аргумент - дату в формате:
    - DD.MM.YYYY - конкретная дата
    - DD.MM - дата в текущем году
    - DD.MM.* - дата во всех годах
    Если дата не указана, выводится меню выбора периода
    """
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    try:
        # Если пришли не из текстового сообщения (например из menu:view callback через dispatch)
        # у event может не быть .message (CallbackQuery). В этом случае просто показать меню выбора периода.
        if not hasattr(event, 'message') or event.message is None:
            await show_period_selection(event)
            return

        # Получаем аргумент команды (дату) из текстового сообщения
        command_text = (event.message.text or '').strip()
        parts = command_text.split(maxsplit=1)
        
        logger.debug(f"Command /view received: {command_text}")
        
        # Определяем дату для поиска
        target_date = None
        day_month_all_years = None
        
        if len(parts) > 1 and parts[1]:
            # Пользователь указал дату
            date_str = parts[1].strip()
            logger.debug(f"Parsing date string: {date_str}")
            
            # Новая функция parse_date возвращает tuple (date_obj, day_month_tuple)
            target_date, day_month_all_years = await parse_date(date_str)
            
            if not target_date and not day_month_all_years:
                # Не удалось распарсить дату
                logger.warning(f"Invalid date format: {date_str}")
                error_msg = tlgbot.i18n.t('invalid_date_format', lang=lang) or f"Неверный формат даты. Используйте ДД.ММ.ГГГГ, ДД.ММ или ДД.ММ.*"
                await event.respond(error_msg)
                return
        else:
            # Дата не указана, показываем меню выбора периода
            await show_period_selection(event)
            return
        
        # В зависимости от типа запроса, выполняем соответствующий поиск
        if day_month_all_years:
            # Запрос для всех годов
            day, month = day_month_all_years
            logger.debug(f"Searching entries for day={day}, month={month} across all years")
            
            # Получаем записи
            entries = await get_entries_by_day_month(user_id, day, month)
            
            # Отображаем результаты
            await display_multiple_entries(event, entries)
        else:
            # Обычный запрос по конкретной дате
            logger.debug(f"Target date for search: {target_date}, type: {type(target_date)}")
            
            # Получаем запись из БД
            entry = await get_entry_by_date(user_id, target_date)
            
            if entry:
                # Запись найдена, отображаем пользователю
                await display_entry(event, entry, target_date)
            else:
                # Запись не найдена
                date_formatted = target_date.strftime("%d.%m.%Y")
                not_found_msg = tlgbot.i18n.t('view_entry_not_found', lang=lang, date=date_formatted) or f"Запись за {date_formatted} не найдена."
                await event.respond(not_found_msg)
    
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        logger.error(f"Ошибка при выполнении команды /view: {traceback_str}")
        await event.respond(f"Произошла ошибка: {str(e)}")

@tlgbot.on(events.CallbackQuery(pattern=r"view_period_.*"))
@require_diary_user
async def view_period_handler(event):
    """
    Обработчик кнопок выбора периода
    """
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    # Получаем выбранный период из данных кнопки
    period = event.data.decode('utf-8').replace('view_period_', '')
    
    try:
        # Отвечаем на коллбэк, чтобы убрать индикатор загрузки с кнопки
        await event.answer()
        
        if period == 'today':
            # Показываем запись за сегодня
            today = date.today()
            entry = await get_entry_by_date(user_id, today)
            
            if entry:
                await display_entry(event, entry, today)
            else:
                date_formatted = today.strftime("%d.%m.%Y")
                not_found_msg = tlgbot.i18n.t('view_entry_not_found', lang=lang, date=date_formatted) or f"Запись за {date_formatted} не найдена."
                await event.respond(not_found_msg)
                
        elif period == 'week':
            # Показываем записи за текущую неделю
            start_of_week, end_of_week = get_week_dates()
            
            # Получаем записи за неделю
            entries = await get_entries_by_period(user_id, start_of_week, end_of_week)
            
            # Формируем название периода для отображения
            period_name = tlgbot.i18n.t('current_week', lang=lang) or "текущую неделю"
            
            # Отображаем результаты
            await display_period_entries(event, entries, period_name)
            
        elif period == 'month':
            # Показываем записи за текущий месяц
            start_of_month, end_of_month = get_month_dates()
            
            # Получаем записи за месяц
            entries = await get_entries_by_period(user_id, start_of_month, end_of_month)
            
            # Формируем название периода для отображения
            month_names = ["январь", "февраль", "март", "апрель", "май", "июнь", 
                         "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"]
            current_month = month_names[date.today().month - 1]
            period_name = tlgbot.i18n.t('current_month', lang=lang, month=current_month) or f"текущий месяц ({current_month})"
            
            # Отображаем результаты
            await display_period_entries(event, entries, period_name)
            
        elif period == 'custom':
            # Показываем сообщение о том, как указать произвольную дату
            message = tlgbot.i18n.t('view_custom_help', lang=lang) or """
Для просмотра записей за произвольную дату используйте следующие форматы:

/view ДД.ММ.ГГГГ - просмотр записи за конкретную дату
/view ДД.ММ - просмотр записи за указанную дату текущего года
/view ДД.ММ.* - просмотр записей за указанную дату всех лет
            """
            await event.respond(message.strip())
    
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        logger.error(f"Ошибка при обработке выбора периода: {traceback_str}")
        await event.respond(f"Произошла ошибка: {str(e)}")

# Добавляем обработчик для команды /help, чтобы включить информацию о команде /view
@tlgbot.on(events.NewMessage(pattern=r'^/view_help$'))
async def view_help_handler(event):
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    help_text = tlgbot.i18n.t('view_command_help', lang=lang) or """
Команда /view позволяет просмотреть записи дневника.

Использование:
/view - выбор периода для просмотра (сегодня, неделя, месяц)
/view ДД.ММ.ГГГГ - просмотр записи за указанную дату
/view ДД.ММ - просмотр записи за указанную дату текущего года
/view ДД.ММ.* - просмотр записей за указанную дату всех лет
    """
    
    await event.respond(help_text.strip())