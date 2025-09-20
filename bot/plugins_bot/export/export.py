# Плагин для команды /export - экспорт записей в различные форматы

from telethon import events, Button
try:
    from bot.menu_system import register_menu
    register_menu({
        'key': 'export', 'tr_key': 'menu_export', 'plugin': 'export', 'handler': 'export_command_handler', 'order': 40
    })
except Exception:
    pass
from datetime import datetime, date, timedelta
import calendar
import os
import re
from bot.require_diary_user import require_diary_user

# tlgbot глобально доступен в плагинах через динамическую загрузку
tlgbot = globals().get('tlgbot')
# Логгер доступен через глобальные переменные
logger = globals().get('logger')

# Словарь для хранения пользовательских выборов диапазона дат
# {user_id: {"start_date": date, "waiting_for": "end_date" или None}}
custom_date_states = {}

async def init_export_manager():
    """
    Инициализация менеджера экспорта
    """
    try:
        from core.database.manager import DatabaseManager
        from core.export.manager import DiaryExportManager
        from cfg.config_tlg import DAYLOG_DB_PATH
        
        # Создаем экземпляр DB с явным указанием пути к БД
        db_manager = DatabaseManager(db_path=DAYLOG_DB_PATH)
        
        # Создаем экземпляр менеджера экспорта
        export_manager = DiaryExportManager(db_manager)
        
        return export_manager
    except Exception as e:
        logger.error(f"Ошибка инициализации менеджера экспорта: {e}")
        return None

async def show_export_options(event):
    """
    Показывает кнопки выбора периода для экспорта записей
    """
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    message = tlgbot.i18n.t('export_select_period', lang=lang) or "Выберите период для экспорта записей в Markdown:"
    
    # Создаем кнопки выбора периода
    buttons = [
        [
            Button.inline(tlgbot.i18n.t('export_today', lang=lang) or "Сегодня", data="export_period_today"),
            Button.inline(tlgbot.i18n.t('export_week', lang=lang) or "Текущая неделя", data="export_period_week")
        ],
        [
            Button.inline(tlgbot.i18n.t('export_month', lang=lang) or "Текущий месяц", data="export_period_month"),
            Button.inline(tlgbot.i18n.t('export_all', lang=lang) or "Весь дневник", data="export_period_all")
        ],
        [
            Button.inline(tlgbot.i18n.t('export_custom', lang=lang) or "Выбрать даты", data="export_period_custom")
        ],
        [
            Button.inline(tlgbot.i18n.t('btn_cancel', lang=lang) or "Отмена", data="export_cancel")
        ]
    ]
    
    await event.respond(message, buttons=buttons)

async def process_custom_date_input(event, user_id, date_input):
    """
    Обрабатывает ввод пользовательской даты
    """
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    # Проверяем, не хочет ли пользователь отменить операцию
    if date_input.lower() in ["отмена", "cancel", "отменить"]:
        # Очищаем состояние
        if user_id in custom_date_states:
            del custom_date_states[user_id]
        
        message = tlgbot.i18n.t('export_canceled', lang=lang) or "Экспорт отменен."
        await event.respond(message)
        return
    
    # Пытаемся распарсить дату
    try:
        # Регулярное выражение для формата DD.MM.YYYY
        date_pattern = r'^(\d{1,2})\.(\d{1,2})\.(\d{4})$'
        match = re.match(date_pattern, date_input)
        
        if match:
            day, month, year = map(int, match.groups())
            parsed_date = date(year, month, day)
            
            state = custom_date_states.get(user_id, {})
            waiting_for = state.get("waiting_for")
            
            if waiting_for == "start_date" or not waiting_for:
                # Это начальная дата диапазона
                custom_date_states[user_id] = {
                    "start_date": parsed_date,
                    "waiting_for": "end_date"
                }
                
                message = tlgbot.i18n.t('export_enter_end_date', lang=lang) or "Введите конечную дату диапазона (ДД.ММ.ГГГГ):"
                message += "\n" + (tlgbot.i18n.t('export_type_cancel', lang=lang) or "Введите 'отмена' для прерывания процесса экспорта.")
                await event.respond(message)
                
            elif waiting_for == "end_date":
                # Это конечная дата диапазона
                start_date = state.get("start_date")
                
                # Проверяем, что конечная дата не раньше начальной
                if parsed_date < start_date:
                    message = tlgbot.i18n.t('export_date_error', lang=lang) or "Ошибка: конечная дата не может быть раньше начальной. Попробуйте еще раз:"
                    await event.respond(message)
                    return
                
                # Запускаем экспорт по выбранному диапазону
                await export_entries_by_period(event, "custom", start_date=start_date, end_date=parsed_date)
                
                # Очищаем состояние
                if user_id in custom_date_states:
                    del custom_date_states[user_id]
            
        else:
            message = tlgbot.i18n.t('export_date_format_error', lang=lang) or "Неверный формат даты. Используйте формат ДД.ММ.ГГГГ:"
            await event.respond(message)
            
    except ValueError:
        message = tlgbot.i18n.t('export_date_error', lang=lang) or "Ошибка в дате. Проверьте корректность введенной даты:"
        await event.respond(message)

async def export_entries_by_period(event, period_type, start_date=None, end_date=None):
    """
    Экспортирует записи за выбранный период
    """
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    # Инициализация менеджера экспорта
    export_manager = await init_export_manager()
    if not export_manager:
        await event.respond(tlgbot.i18n.t('export_error', lang=lang) or "Ошибка при инициализации экспорта.")
        return
    
    entries = []
    period_name = ""
    
    # Получаем записи в зависимости от выбранного периода
    if period_type == "today":
        entries = export_manager.get_today_entries(user_id)
        period_name = tlgbot.i18n.t('period_today', lang=lang) or "сегодня"
        
    elif period_type == "week":
        entries = export_manager.get_week_entries(user_id)
        period_name = tlgbot.i18n.t('period_week', lang=lang) or "текущую неделю"
        
    elif period_type == "month":
        entries = export_manager.get_month_entries(user_id)
        period_name = tlgbot.i18n.t('period_month', lang=lang) or "текущий месяц"
        
    elif period_type == "all":
        entries = export_manager.get_all_entries(user_id)
        period_name = tlgbot.i18n.t('period_all', lang=lang) or "весь период"
        
    elif period_type == "custom" and start_date and end_date:
        entries = export_manager.get_entries_by_custom_period(user_id, start_date, end_date)
        # Форматируем период для отображения
        start_str = start_date.strftime("%d.%m.%Y")
        end_str = end_date.strftime("%d.%m.%Y")
        period_name = f"{start_str} - {end_str}"
    
    # Проверяем, есть ли записи для экспорта
    if not entries:
        no_entries_msg = tlgbot.i18n.t('export_no_entries', lang=lang, period=period_name) or f"Нет записей для экспорта за период: {period_name}"
        await event.respond(no_entries_msg)
        return
    
    # Формируем заголовок для файла экспорта
    title = tlgbot.i18n.t('export_title', lang=lang, period=period_name) or f"Мой дневник за {period_name}"
    
    # Экспортируем записи в Markdown
    filename, filepath = export_manager.export_markdown(user_id, entries, title)
    
    if not filename or not filepath or not os.path.exists(filepath):
        export_error_msg = tlgbot.i18n.t('export_file_error', lang=lang) or "Ошибка при создании файла экспорта."
        await event.respond(export_error_msg)
        return
    
    # Отправляем файл пользователю
    success_msg = tlgbot.i18n.t('export_success', lang=lang, count=len(entries)) or f"Экспортировано {len(entries)} записей."
    await event.respond(success_msg)
    
    caption = tlgbot.i18n.t('export_file_caption', lang=lang, period=period_name) or f"Экспорт дневника за {period_name}"
    await tlgbot.send_file(event.chat_id, filepath, caption=caption)
    
    # Опционально: удаляем файл после отправки
    # os.remove(filepath)

@tlgbot.on(events.NewMessage(pattern=r'^/export'))
@require_diary_user
async def export_command_handler(event):
    """
    Обработчик команды /export
    Показывает опции для экспорта записей
    """
    await show_export_options(event)
    return

# Обработчики inline кнопок выбора периода экспорта
@tlgbot.on(events.CallbackQuery(pattern=r'^export_period_today$'))
async def export_today_callback(event):
    """Обработчик выбора экспорта за сегодня"""
    await event.answer()
    # Редактируем сообщение, убирая кнопки
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    await event.edit(tlgbot.i18n.t('export_processing_today', lang=lang) or "Подготовка экспорта за сегодня...")
    await export_entries_by_period(event, "today")

@tlgbot.on(events.CallbackQuery(pattern=r'^export_period_week$'))
async def export_week_callback(event):
    """Обработчик выбора экспорта за неделю"""
    await event.answer()
    # Редактируем сообщение, убирая кнопки
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    await event.edit(tlgbot.i18n.t('export_processing_week', lang=lang) or "Подготовка экспорта за текущую неделю...")
    await export_entries_by_period(event, "week")

@tlgbot.on(events.CallbackQuery(pattern=r'^export_period_month$'))
async def export_month_callback(event):
    """Обработчик выбора экспорта за месяц"""
    await event.answer()
    # Редактируем сообщение, убирая кнопки
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    await event.edit(tlgbot.i18n.t('export_processing_month', lang=lang) or "Подготовка экспорта за текущий месяц...")
    await export_entries_by_period(event, "month")

@tlgbot.on(events.CallbackQuery(pattern=r'^export_period_all$'))
async def export_all_callback(event):
    """Обработчик выбора экспорта всех записей"""
    await event.answer()
    # Редактируем сообщение, убирая кнопки
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    await event.edit(tlgbot.i18n.t('export_processing_all', lang=lang) or "Подготовка экспорта всех записей...")
    await export_entries_by_period(event, "all")

@tlgbot.on(events.CallbackQuery(pattern=r'^export_period_custom$'))
async def export_custom_callback(event):
    """Обработчик выбора произвольного периода экспорта"""
    await event.answer()
    
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    # Редактируем сообщение, убирая кнопки
    message = tlgbot.i18n.t('export_enter_start_date', lang=lang) or "Введите начальную дату диапазона (ДД.ММ.ГГГГ):"
    message += "\n" + (tlgbot.i18n.t('export_type_cancel', lang=lang) or "Введите 'отмена' для прерывания процесса экспорта.")
    await event.edit(message)
    
    # Устанавливаем состояние ожидания начальной даты
    custom_date_states[user_id] = {
        "waiting_for": "start_date"
    }

# Обработчик для кнопки отмены
@tlgbot.on(events.CallbackQuery(pattern=r'^export_cancel$'))
async def export_cancel_callback(event):
    """Обработчик кнопки отмены экспорта"""
    await event.answer()
    
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    # Очищаем состояние пользователя, если оно было
    if user_id in custom_date_states:
        del custom_date_states[user_id]
    
    # Отправляем сообщение об отмене
    await event.edit(tlgbot.i18n.t('export_canceled', lang=lang) or "Экспорт отменен.")

# Обработчик текстовых сообщений для ввода дат при выборе произвольного периода
@tlgbot.on(events.NewMessage(func=lambda e: e.text and not e.text.startswith('/')))
async def custom_date_handler(event):
    """
    Обработчик ввода пользовательских дат для экспорта
    """
    user_id = event.sender_id
    
    # Проверяем, ожидается ли ввод даты от этого пользователя
    if user_id in custom_date_states and custom_date_states[user_id].get("waiting_for"):
        # Обрабатываем ввод даты
        await process_custom_date_input(event, user_id, event.text.strip())
        return True  # Чтобы другие обработчики не сработали
    
    return False  # Пропускаем другие текстовые сообщения