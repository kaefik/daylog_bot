# Плагин для команды /yesterday с мастером заполнения записи за предыдущий день

from datetime import date, timedelta
from enum import Enum
from telethon import events, Button
from bot.require_diary_user import require_diary_user

# tlgbot глобально доступен в плагинах через динамическую загрузку
tlgbot = globals().get('tlgbot')
# logger глобально доступен в плагинах через динамическую загрузку
logger = globals().get('logger')

# Добавляем обработчик для логирования всех callback-событий в модуле
@tlgbot.on(events.CallbackQuery())
async def log_all_yesterday_callbacks(event):
    # Логируем только те события, которые могут относиться к команде yesterday
    try:
        data = event.data.decode("utf-8")
        if "yesterday" in data or "cancel_edit_yesterday" in data:
            logger.debug(f"[YESTERDAY] GLOBAL CALLBACK MONITOR: Received callback with data: {data}")
            logger.debug(f"[YESTERDAY] GLOBAL CALLBACK MONITOR: Event type: {type(event)}")
            logger.debug(f"[YESTERDAY] GLOBAL CALLBACK MONITOR: Event sender_id: {event.sender_id}")
            
            # Если это наш обработчик, то предотвращаем срабатывание других обработчиков 
            # для событий отмены редактирования записи за вчерашний день
            if data == "cancel_edit_yesterday":
                # Не возвращаем True здесь, чтобы позволить специализированному обработчику handle_yesterday_editing
                # обработать событие, но добавляем проверку, чтобы в других плагинах не начиналось редактирование
                pass
    except Exception as e:
        logger.debug(f"[YESTERDAY] GLOBAL CALLBACK MONITOR: Error processing callback: {str(e)}")
    # Обязательно возвращаем False, чтобы событие было обработано другими обработчиками
    return False

# Определяем состояния FSM
class FormState(str, Enum):
    WAITING_MOOD = "waiting_mood"
    WAITING_WEATHER = "waiting_weather"
    WAITING_LOCATION = "waiting_location"
    WAITING_EVENTS = "waiting_events"

# Словарь для хранения временных данных пользователей (в памяти)
# В реальном приложении лучше использовать Redis или другое хранилище
user_states = {}
user_form_data = {}

# Функция для отображения содержимого записи
async def display_entry_content(event, user_id, entry_date, lang="ru"):
    try:
        from core.database.manager import DatabaseManager
        from cfg.config_tlg import DAYLOG_DB_PATH
        
        db = DatabaseManager(db_path=DAYLOG_DB_PATH)
        entry = db.get_diary_entry(user_id, entry_date)
        
        if not entry:
            await event.respond(tlgbot.i18n.t('entry_not_found', lang=lang) or "Запись не найдена.")
            return
            
        # Формируем сообщение с содержимым записи
        mood = entry.get("mood") or tlgbot.i18n.t('not_specified', lang=lang) or "Не указано"
        weather = entry.get("weather") or tlgbot.i18n.t('not_specified', lang=lang) or "Не указано"
        location = entry.get("location") or tlgbot.i18n.t('not_specified', lang=lang) or "Не указано"
        events = entry.get("events") or tlgbot.i18n.t('not_specified', lang=lang) or "Не указано"
        
        # Используем локализованные строки для каждой части сообщения
        date_str = str(entry_date)
        message = (tlgbot.i18n.t('entry_title', lang=lang, date=date_str) or f"📝 Запись от {date_str}") + "\n\n"
        message += (tlgbot.i18n.t('entry_mood', lang=lang, mood=mood) or f"🙂 Настроение: {mood}") + "\n"
        message += (tlgbot.i18n.t('entry_weather', lang=lang, weather=weather) or f"🌤 Погода: {weather}") + "\n"
        message += (tlgbot.i18n.t('entry_location', lang=lang, location=location) or f"📍 Местоположение: {location}") + "\n"
        message += (tlgbot.i18n.t('entry_events', lang=lang, events=events) or f"📌 События: {events}") + "\n"
        
        await event.respond(message, parse_mode='markdown')
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        logger.error(f"ERROR displaying entry: {traceback_str}")
        await event.respond(f"Ошибка при отображении записи: {str(e)}")

# Inline-клавиатуры для каждого поля
def get_mood_keyboard(lang="ru"):
    return [
        [
            Button.inline(tlgbot.i18n.t('mood_excellent', lang=lang) or "Отлично", data=f"yesterday_mood_excellent"),
            Button.inline(tlgbot.i18n.t('mood_good', lang=lang) or "Хорошо", data=f"yesterday_mood_good"),
        ],
        [
            Button.inline(tlgbot.i18n.t('mood_normal', lang=lang) or "Нормально", data=f"yesterday_mood_normal"),
            Button.inline(tlgbot.i18n.t('mood_bad', lang=lang) or "Плохо", data=f"yesterday_mood_bad"),
        ],
        [
            Button.inline(tlgbot.i18n.t('mood_terrible', lang=lang) or "Ужасно", data=f"yesterday_mood_terrible"),
        ],
        [
            Button.inline(tlgbot.i18n.t('btn_skip', lang=lang) or "Пропустить", data=f"yesterday_mood_skip"),
            Button.inline(tlgbot.i18n.t('btn_cancel', lang=lang) or "Отмена", data=f"cancel_creation"),
        ]
    ]

def get_weather_keyboard(lang="ru"):
    return [
        [
            Button.inline(tlgbot.i18n.t('weather_sunny', lang=lang) or "Солнечно", data=f"yesterday_weather_sunny"),
            Button.inline(tlgbot.i18n.t('weather_cloudy', lang=lang) or "Облачно", data=f"yesterday_weather_cloudy"),
        ],
        [
            Button.inline(tlgbot.i18n.t('weather_rainy', lang=lang) or "Дождь", data=f"yesterday_weather_rainy"),
            Button.inline(tlgbot.i18n.t('weather_snowy', lang=lang) or "Снег", data=f"yesterday_weather_snowy"),
        ],
        [
            Button.inline(tlgbot.i18n.t('weather_foggy', lang=lang) or "Туман", data=f"yesterday_weather_foggy"),
            Button.inline(tlgbot.i18n.t('btn_manual', lang=lang) or "Ввести вручную", data=f"yesterday_weather_manual"),
        ],
        [
            Button.inline(tlgbot.i18n.t('btn_skip', lang=lang) or "Пропустить", data=f"yesterday_weather_skip"),
            Button.inline(tlgbot.i18n.t('btn_back', lang=lang) or "Назад", data=f"yesterday_weather_back"),
            Button.inline(tlgbot.i18n.t('btn_cancel', lang=lang) or "Отмена", data=f"cancel_creation"),
        ]
    ]

def get_location_keyboard(lang="ru"):
    return [
        [
            Button.inline(tlgbot.i18n.t('location_home', lang=lang) or "Дом", data=f"yesterday_location_home"),
            Button.inline(tlgbot.i18n.t('location_work', lang=lang) or "Работа", data=f"yesterday_location_work"),
        ],
        [
            Button.inline(tlgbot.i18n.t('location_street', lang=lang) or "Улица", data=f"yesterday_location_street"),
            Button.inline(tlgbot.i18n.t('btn_manual', lang=lang) or "Ввести вручную", data=f"yesterday_location_manual"),
        ],
        [
            Button.inline(tlgbot.i18n.t('btn_skip', lang=lang) or "Пропустить", data=f"yesterday_location_skip"),
            Button.inline(tlgbot.i18n.t('btn_back', lang=lang) or "Назад", data=f"yesterday_location_back"),
            Button.inline(tlgbot.i18n.t('btn_cancel', lang=lang) or "Отмена", data=f"cancel_creation"),
        ]
    ]

def get_events_keyboard(lang="ru", edit_mode=False):
    buttons = [
        [
            Button.inline(tlgbot.i18n.t('btn_skip', lang=lang) or "Пропустить", data="yesterday_events_skip"),
            Button.inline(tlgbot.i18n.t('btn_back', lang=lang) or "Назад", data="yesterday_events_back"),
            Button.inline(tlgbot.i18n.t('btn_cancel', lang=lang) or "Отмена", data="cancel_creation"),
        ]
    ]
    
    # Если в режиме редактирования, добавляем кнопки "Заменить", "Добавить" и "Правка"
    if edit_mode:
        # Отладочное сообщение при создании кнопок
        logger.debug(f"Creating edit mode buttons with data: yesterday_events_replace, yesterday_events_append and yesterday_events_edit")
        
        replace_btn = Button.inline(tlgbot.i18n.t('btn_replace', lang=lang) or "Заменить текст", data="yesterday_events_replace")
        append_btn = Button.inline(tlgbot.i18n.t('btn_append', lang=lang) or "Добавить к тексту", data="yesterday_events_append")
        edit_btn = Button.inline(tlgbot.i18n.t('btn_edit_text', lang=lang) or "Правка", data="yesterday_events_edit")
        buttons.insert(0, [replace_btn, append_btn, edit_btn])
        
    return buttons

@tlgbot.on(tlgbot.cmd('yesterday'))
@require_diary_user
async def yesterday_handler(event):
    # Добавляем отладочную информацию в начале обработчика
    logger.debug(f"[YESTERDAY] Command handler started")
    logger.debug(f"[YESTERDAY] Event type: {type(event)}")
    
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    logger.debug(f"[YESTERDAY] User ID: {user_id}, Lang: {lang}")
    try:
        from core.database.manager import DatabaseManager
    except ImportError:
        await event.reply(tlgbot.i18n.t('db_manager_import_error', lang=lang))
        return

    try:
        from cfg.config_tlg import DAYLOG_DB_PATH
    except ImportError:
        await event.reply(tlgbot.i18n.t('db_path_import_error', lang=lang))
        return

    db = DatabaseManager(db_path=DAYLOG_DB_PATH)
    yesterday_date = date.today() - timedelta(days=1)
    entry = db.get_diary_entry(user_id, yesterday_date)
    
    # Добавляем отладочную информацию
    logger.debug(f"Entry from DB for yesterday command: {entry}")
    
    if entry:
        # Проверяем, содержит ли запись все необходимые поля
        required_fields = ["mood", "weather", "location", "events"]
        for field in required_fields:
            if field not in entry:
                logger.warning(f"Missing field '{field}' in entry from DB")
                # Инициализируем отсутствующие поля
                entry[field] = None
    
    if entry:
        # Добавляем inline-кнопки для редактирования существующей записи
        buttons = [
            [
                Button.inline(tlgbot.i18n.t('btn_edit', lang=lang) or "Редактировать", data="edit_yesterday"),
                Button.inline(tlgbot.i18n.t('btn_edit_events_only', lang=lang) or "Редактировать событие", data="edit_yesterday_events"),
                Button.inline(tlgbot.i18n.t('btn_cancel', lang=lang) or "Отмена", data="cancel_edit_yesterday")
            ]
        ]
        
        # Добавляем отладочную информацию для кнопок
        logger.debug(f"[YESTERDAY] Creating buttons for edit options. User ID: {user_id}")
        for row_idx, row in enumerate(buttons):
            for btn_idx, btn in enumerate(row):
                logger.debug(f"[YESTERDAY] Button [{row_idx}][{btn_idx}]: text={btn.text}, data={btn.data}")
        
        await event.reply(
            tlgbot.i18n.t('yesterday_entry_exists_edit', lang=lang) or "Запись за вчерашний день уже существует. Хотите отредактировать её?",
            buttons=buttons
        )
        return
    
    # Начинаем мастер заполнения с первого шага - настроение
    user_states[user_id] = FormState.WAITING_MOOD
    user_form_data[user_id] = {"entry_date": yesterday_date}
    
    await event.reply(
        "Какое у вас было настроение вчера?",
        buttons=get_mood_keyboard(lang)
    )

# Обработчики для инлайн-кнопок формы
@tlgbot.on(events.CallbackQuery(pattern="yesterday_mood_.*"))
async def yesterday_mood_callback_handler(event):
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    if user_id not in user_states or user_states[user_id] != FormState.WAITING_MOOD:
        await event.answer(tlgbot.i18n.t('form_invalid_state', lang=lang) or "Неверное состояние формы")
        return
    
    data = event.data.decode("utf-8")
    choice = data.split("_")[2]  # yesterday_mood_choice
    
    # Обработка выбора
    if choice == "back":
        # Для настроения нет предыдущего шага
        await event.answer(tlgbot.i18n.t('form_first_step', lang=lang) or "Это первый шаг")
        return
    
    if choice != "skip":
        # Преобразуем выбор в соответствующее значение для БД
        mood_mapping = {
            "excellent": "Отлично",
            "good": "Хорошо",
            "normal": "Нормально",
            "bad": "Плохо",
            "terrible": "Ужасно"
        }
        user_form_data[user_id]["mood"] = mood_mapping.get(choice)
    
    # Переходим к следующему шагу - погода
    user_states[user_id] = FormState.WAITING_WEATHER
    
    # Для режима редактирования показываем текущее значение
    if user_form_data[user_id].get("edit_mode"):
        # Безопасно получаем текущее значение погоды
        current_weather = "Не указано"
        if "weather" in user_form_data[user_id] and user_form_data[user_id]["weather"]:
            current_weather = user_form_data[user_id]["weather"]
        else:
            current_weather = tlgbot.i18n.t('not_specified', lang=lang) or "Не указано"
            
        # Исправляем вызов метода локализации, передавая параметр weather напрямую
        edit_weather_message = f"Вчерашняя погода:\n\n{current_weather}\n\nВыберите новую погоду:"
            
        await event.edit(
            edit_weather_message,
            buttons=get_weather_keyboard(lang)
        )
    else:
        await event.edit(
            "Какая была погода вчера?",
            buttons=get_weather_keyboard(lang)
        )

@tlgbot.on(events.CallbackQuery(pattern="yesterday_weather_.*"))
async def yesterday_weather_callback_handler(event):
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    if user_id not in user_states or user_states[user_id] != FormState.WAITING_WEATHER:
        await event.answer(tlgbot.i18n.t('form_invalid_state', lang=lang) or "Неверное состояние формы")
        return
    
    data = event.data.decode("utf-8")
    choice = data.split("_")[2]  # yesterday_weather_choice
    
    # Обработка выбора
    if choice == "back":
        # Возвращаемся к предыдущему шагу - настроение
        user_states[user_id] = FormState.WAITING_MOOD
        
        # Для режима редактирования показываем текущее значение
        if user_form_data[user_id].get("edit_mode"):
            current_mood = user_form_data[user_id].get("mood") or tlgbot.i18n.t('not_specified', lang=lang) or "Не указано"
            
            # Исправляем вызов метода локализации, передавая параметр mood напрямую
            edit_mood_message = f"Вчерашнее настроение:\n\n{current_mood}\n\nВыберите новое настроение:"
                
            await event.edit(
                edit_mood_message,
                buttons=get_mood_keyboard(lang)
            )
        else:
            await event.edit(
                "Какое у вас было настроение вчера?",
                buttons=get_mood_keyboard(lang)
            )
        return
    
    if choice == "manual":
        # Обработка ввода погоды вручную
        user_form_data[user_id]["manual_weather"] = True
        logger.debug(f"Manual weather input mode activated. User ID: {user_id}")
        await event.edit(
            "Введите описание погоды вчера:" + 
            "\n\n" + (tlgbot.i18n.t('type_cancel_to_abort', lang=lang) or "Напишите 'отмена' для отмены создания записи.")
        )
        # Остаемся в том же состоянии, но ожидаем текстовый ввод
        return
    
    if choice != "skip":
        # Преобразуем выбор в соответствующее значение для БД
        weather_mapping = {
            "sunny": "Солнечно",
            "cloudy": "Облачно",
            "rainy": "Дождь",
            "snowy": "Снег",
            "foggy": "Туман"
        }
        user_form_data[user_id]["weather"] = weather_mapping.get(choice)
    
    # Переходим к следующему шагу - местоположение
    user_states[user_id] = FormState.WAITING_LOCATION
    
    # Для режима редактирования показываем текущее значение
    if user_form_data[user_id].get("edit_mode"):
        current_location = user_form_data[user_id].get("location") or tlgbot.i18n.t('not_specified', lang=lang) or "Не указано"
        
        # Исправляем вызов метода локализации, передавая параметр location напрямую
        edit_location_message = f"Вчерашнее местоположение:\n\n{current_location}\n\nВыберите новое местоположение:"
        
        await event.edit(
            edit_location_message,
            buttons=get_location_keyboard(lang)
        )
    else:
        await event.edit(
            "Где вы находились вчера?",
            buttons=get_location_keyboard(lang)
        )

@tlgbot.on(events.CallbackQuery(pattern="yesterday_location_.*"))
async def yesterday_location_callback_handler(event):
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    if user_id not in user_states or user_states[user_id] != FormState.WAITING_LOCATION:
        await event.answer(tlgbot.i18n.t('form_invalid_state', lang=lang) or "Неверное состояние формы")
        return
    
    data = event.data.decode("utf-8")
    choice = data.split("_")[2]  # yesterday_location_choice
    
    # Обработка выбора
    if choice == "back":
        # Возвращаемся к предыдущему шагу - погода
        user_states[user_id] = FormState.WAITING_WEATHER
        
        # Для режима редактирования показываем текущее значение
        if user_form_data[user_id].get("edit_mode"):
            current_weather = user_form_data[user_id].get("weather") or tlgbot.i18n.t('not_specified', lang=lang) or "Не указано"
            
            # Исправляем вызов метода локализации, передавая параметр weather напрямую
            edit_weather_message = f"Вчерашняя погода:\n\n{current_weather}\n\nВыберите новую погоду:"
            
            await event.edit(
                edit_weather_message,
                buttons=get_weather_keyboard(lang)
            )
        else:
            await event.edit(
                "Какая была погода вчера?",
                buttons=get_weather_keyboard(lang)
            )
        return
    
    if choice == "manual":
        # Обработка ввода местоположения вручную
        user_form_data[user_id]["manual_location"] = True
        logger.debug(f"Manual location mode activated. User ID: {user_id}")
        await event.edit(
            "Введите ваше местоположение вчера:" + 
            "\n\n" + (tlgbot.i18n.t('type_cancel_to_abort', lang=lang) or "Напишите 'отмена' для отмены создания записи.")
        )
        # Остаемся в том же состоянии, но ожидаем текстовый ввод
        return
    
    if choice != "skip":
        # Преобразуем выбор в соответствующее значение для БД
        location_mapping = {
            "home": "Дом",
            "work": "Работа",
            "street": "Улица"
        }
        user_form_data[user_id]["location"] = location_mapping.get(choice)
    
    # Переходим к следующему шагу - события
    user_states[user_id] = FormState.WAITING_EVENTS
    
    # Для режима редактирования показываем текущее значение
    edit_mode = user_form_data[user_id].get("edit_mode", False)
    current_events = user_form_data[user_id].get("events", "")
    
    # Отладочное сообщение
    logger.debug(f"Showing events form with edit_mode={edit_mode} in location_callback. User ID: {user_id}, Current events: {current_events}")
    
    if edit_mode:
        # Исправляем вызов метода локализации, передавая параметр events напрямую
        edit_events_message = f"Вчерашние события:\n{current_events}.\n\nОпишите события вчерашнего дня (или нажмите 'Пропустить'):"
        
        await event.edit(
            edit_events_message,
            buttons=get_events_keyboard(lang, edit_mode=True)
        )
    else:
        await event.edit(
            "Опишите события вчерашнего дня (или нажмите 'Пропустить'):",
            buttons=get_events_keyboard(lang, edit_mode=False)
        )

@tlgbot.on(events.CallbackQuery(pattern="yesterday_events_.*"))
async def yesterday_events_callback_handler(event):
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    if user_id not in user_states or user_states[user_id] != FormState.WAITING_EVENTS:
        await event.answer(tlgbot.i18n.t('form_invalid_state', lang=lang) or "Неверное состояние формы")
        return
    
    data = event.data.decode("utf-8")
    parts = data.split("_")
    choice = parts[2] if len(parts) > 2 else ""  # yesterday_events_choice
    
    # Обработка кнопок редактирования
    if choice == "replace":
        current_events = user_form_data[user_id].get("events") or ""
        
        # Устанавливаем флаг режима замены
        user_form_data[user_id]["replace_mode"] = True
        
        # Отладочное сообщение
        logger.debug(f"Replace button clicked. User ID: {user_id}, Current events: {current_events}")
        
        replace_message = tlgbot.i18n.t('events_replace_prompt', lang=lang, events=current_events)
        if not replace_message:
            replace_message = f"Вчерашние события:\n\"{current_events}\"\n\nВведите новый текст, который полностью заменит текущий:"
            
        await event.edit(replace_message + "\n\n" + (tlgbot.i18n.t('type_cancel_to_abort', lang=lang) or "Напишите 'отмена' для отмены создания записи."))
        # Ожидаем ввод пользователя, который будет обработан в handle_manual_input
        return
    
    elif choice == "append":
        current_events = user_form_data[user_id].get("events") or ""
        
        # Устанавливаем флаг режима добавления
        user_form_data[user_id]["append_mode"] = True
        
        append_message = tlgbot.i18n.t('events_append_prompt', lang=lang, events=current_events)
        if not append_message:
            append_message = f"Вчерашние события:\n\"{current_events}\"\n\nВведите текст, который будет добавлен к текущему:"
            
        await event.edit(append_message + "\n\n" + (tlgbot.i18n.t('type_cancel_to_abort', lang=lang) or "Напишите 'отмена' для отмены создания записи."))
        # Ожидаем ввод пользователя, который будет обработан в handle_manual_input
        return
        
    elif choice == "edit":
        current_events = user_form_data[user_id].get("events") or ""
        
        # Устанавливаем флаг режима редактирования текста
        user_form_data[user_id]["edit_text_mode"] = True
        
        # Отладочное сообщение
        logger.debug(f"Edit button clicked. User ID: {user_id}, Current events: {current_events}")
        
        edit_message = tlgbot.i18n.t('events_edit_prompt', lang=lang, events=current_events)
        if not edit_message:
            edit_message = f"Вчерашние события:\n\"{current_events}\"\n\nОтредактируйте текст:"
            
        await event.edit(edit_message + "\n\n" + (tlgbot.i18n.t('type_cancel_to_abort', lang=lang) or "Напишите 'отмена' для отмены создания записи."))
        
        # Отправляем второе сообщение только с текстом событий, чтобы пользователю было легче скопировать
        await event.respond(current_events)
        
        # Ожидаем ввод пользователя, который будет обработан в handle_manual_input
        return
    
    # Обработка выбора
    if choice == "back":
        # Возвращаемся к предыдущему шагу - местоположение
        user_states[user_id] = FormState.WAITING_LOCATION
        
        # Для режима редактирования показываем текущее значение
        if user_form_data[user_id].get("edit_mode"):
            current_location = user_form_data[user_id].get("location") or tlgbot.i18n.t('not_specified', lang=lang) or "Не указано"
            
            # Исправляем вызов метода локализации, передавая параметр location напрямую
            edit_location_message = f"Вчерашнее местоположение:\n\n{current_location}\n\nВыберите новое местоположение:"
            
            await event.edit(
                edit_location_message,
                buttons=get_location_keyboard(lang)
            )
        else:
            await event.edit(
                "Где вы находились вчера?",
                buttons=get_location_keyboard(lang)
            )
        return
    
    # Если пользователь не нажал "Пропустить", сохраняем текущие события
    # (события обычно вводятся вручную, поэтому здесь в основном обрабатывается пропуск)
    
    # Завершаем форму и сохраняем данные в БД
    try:
        from core.database.manager import DatabaseManager
        from cfg.config_tlg import DAYLOG_DB_PATH
        
        db = DatabaseManager(db_path=DAYLOG_DB_PATH)
        
        # Собираем данные из формы
        entry_date = user_form_data[user_id]["entry_date"]
        mood = user_form_data[user_id].get("mood")
        weather = user_form_data[user_id].get("weather")
        location = user_form_data[user_id].get("location")
        events = user_form_data[user_id].get("events", "")
        
        # Проверяем, существует ли уже запись за этот день
        existing_entry = db.get_diary_entry(user_id, entry_date)
        
        if existing_entry:
            # Обновляем существующую запись
            success = db.update_diary_entry(
                user_id, 
                entry_date,
                mood=mood, 
                weather=weather, 
                location=location, 
                events=events
            )
            if success:
                await event.edit(tlgbot.i18n.t('yesterday_entry_updated', lang=lang) or "Запись за вчерашний день успешно обновлена!")
                # Отображаем содержимое обновленной записи
                await display_entry_content(event, user_id, entry_date, lang)
            else:
                await event.edit(tlgbot.i18n.t('yesterday_entry_update_error', lang=lang) or "Ошибка обновления записи")
        else:
            # Создаем новую запись
            created = db.create_diary_entry(
                user_id, 
                entry_date,
                mood=mood,
                weather=weather,
                location=location,
                events=events
            )
            if created:
                await event.edit(tlgbot.i18n.t('yesterday_entry_created', lang=lang) or "Новая запись за вчерашний день создана.")
                # Отображаем содержимое новой записи
                await display_entry_content(event, user_id, entry_date, lang)
            else:
                await event.edit(tlgbot.i18n.t('yesterday_entry_error', lang=lang) or "Ошибка создания записи")
                
        # Очищаем данные пользователя
        if user_id in user_states:
            del user_states[user_id]
        if user_id in user_form_data:
            del user_form_data[user_id]
        
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        logger.error(f"ERROR saving entry: {traceback_str}")
        if user_form_data[user_id].get("edit_mode"):
            await event.edit(tlgbot.i18n.t('today_entry_update_error', lang=lang) or f"Ошибка при обновлении записи: {str(e)}")
        else:
            await event.edit(tlgbot.i18n.t('today_entry_error', lang=lang) or f"Ошибка при создании записи: {str(e)}")

# Обработчик для ручного ввода текста
@tlgbot.on(events.NewMessage)
async def yesterday_handle_manual_input(event):
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    # Проверяем, что пользователь находится в процессе заполнения формы
    if user_id not in user_states:
        return
    
    # Получаем текущее состояние пользователя
    state = user_states[user_id]
    
    # Проверяем, есть ли у нас команда (начинается с /)
    if event.text.startswith('/'):
        # Это команда, не обрабатываем ее здесь
        return
    
    # Проверяем, ввёл ли пользователь команду отмены
    if event.text.lower() in ['отмена', 'cancel', '/cancel']:
        # Очищаем данные пользователя
        if user_id in user_states:
            del user_states[user_id]
        if user_id in user_form_data:
            del user_form_data[user_id]
        
        # Сообщаем об отмене
        await event.reply(tlgbot.i18n.t('creation_canceled', lang=lang) or "👌 Создание записи отменено. Данные не сохранены.")
        return
    
    if state == FormState.WAITING_WEATHER and user_form_data[user_id].get("manual_weather"):
        # Пользователь вводит погоду вручную
        logger.debug(f"Manual weather input. User ID: {user_id}, Input: '{event.text}'")
        user_form_data[user_id]["weather"] = event.text
        user_form_data[user_id]["manual_weather"] = False
        
        # Переходим к следующему шагу - местоположение
        user_states[user_id] = FormState.WAITING_LOCATION
        
        # Для режима редактирования показываем текущее значение
        if user_form_data[user_id].get("edit_mode"):
            current_location = user_form_data[user_id].get("location") or tlgbot.i18n.t('not_specified', lang=lang) or "Не указано"
            
            # Исправляем вызов метода локализации, передавая параметр location напрямую
            edit_location_message = f"Вчерашнее местоположение:\n\n{current_location}\n\nВыберите новое местоположение:"
            
            await event.respond(
                edit_location_message,
                buttons=get_location_keyboard(lang)
            )
        else:
            await event.respond(
                "Где вы находились вчера?",
                buttons=get_location_keyboard(lang)
            )
        
    elif state == FormState.WAITING_LOCATION and user_form_data[user_id].get("manual_location"):
        # Пользователь вводит местоположение вручную
        logger.debug(f"Manual location input. User ID: {user_id}, Input: '{event.text}'")
        user_form_data[user_id]["location"] = event.text
        user_form_data[user_id]["manual_location"] = False
        
        # Переходим к следующему шагу - события
        user_states[user_id] = FormState.WAITING_EVENTS
        
        # Для режима редактирования показываем текущее значение
        edit_mode = user_form_data[user_id].get("edit_mode", False)
        current_events = user_form_data[user_id].get("events", "")
        
        # Отладочное сообщение
        logger.debug(f"Showing events edit form with edit_mode=True. User ID: {user_id}, Current events: {current_events}")
        
        if edit_mode:
            edit_events_message = f"Вчерашние события:\n{current_events}.\n\nОпишите события вчерашнего дня (или нажмите 'Пропустить'):"
                
            await event.respond(
                edit_events_message,
                buttons=get_events_keyboard(lang, edit_mode=True)
            )
        else:
            await event.respond(
                "Опишите события вчерашнего дня (или нажмите 'Пропустить'):",
                buttons=get_events_keyboard(lang, edit_mode=False)
            )
    
    elif state == FormState.WAITING_EVENTS:
        # Определяем, это обычный ввод событий или специальный режим редактирования
        edit_mode = user_form_data[user_id].get("edit_mode", False)
        edit_events_only = user_form_data[user_id].get("edit_events_only", False)
        replace_mode = user_form_data[user_id].get("replace_mode", False)
        append_mode = user_form_data[user_id].get("append_mode", False)
        edit_text_mode = user_form_data[user_id].get("edit_text_mode", False)
        
        if replace_mode:
            # Полностью заменяем текст
            user_form_data[user_id]["events"] = event.text
            user_form_data[user_id]["replace_mode"] = False
        elif append_mode:
            # Добавляем текст к существующему
            current_events = user_form_data[user_id].get("events", "")
            logger.debug(f"Append mode. User ID: {user_id}, Current events: '{current_events}', New text: '{event.text}'")
            user_form_data[user_id]["events"] = f"{current_events}\n{event.text}" if current_events else event.text
            user_form_data[user_id]["append_mode"] = False
        elif edit_text_mode:
            # Заменяем текст отредактированным
            user_form_data[user_id]["events"] = event.text
            user_form_data[user_id]["edit_text_mode"] = False
        else:
            # Обычный ввод текста событий
            user_form_data[user_id]["events"] = event.text
        
        # Определяем, это обычное редактирование или только редактирование событий
        edit_events_only = user_form_data[user_id].get("edit_events_only", False)
        
        # Выводим отладочную информацию
        logger.debug(f"edit_events_only={edit_events_only}, edit_mode={edit_mode}")
        
        # Завершаем форму и сохраняем данные в БД
        try:
            from core.database.manager import DatabaseManager
            from cfg.config_tlg import DAYLOG_DB_PATH
            
            db = DatabaseManager(db_path=DAYLOG_DB_PATH)
            
            # Собираем данные из формы
            entry_date = user_form_data[user_id]["entry_date"]
            mood = user_form_data[user_id].get("mood")
            weather = user_form_data[user_id].get("weather")
            location = user_form_data[user_id].get("location")
            events = user_form_data[user_id].get("events", "")
            
            # Создаем словарь с данными для сохранения
            entry_data = {
                "mood": mood,
                "weather": weather,
                "location": location,
                "events": events
            }
            
            # Проверяем, существует ли уже запись за этот день
            existing_entry = db.get_diary_entry(user_id, entry_date)
            
            if existing_entry or edit_mode:
                # Обновляем существующую запись
                success = db.update_diary_entry(
                    user_id, 
                    entry_date,
                    **entry_data
                )
                if success:
                    await event.respond(tlgbot.i18n.t('yesterday_entry_updated', lang=lang) or "Запись за вчерашний день успешно обновлена!")
                    # Отображаем содержимое обновленной записи
                    await display_entry_content(event, user_id, entry_date, lang)
                else:
                    await event.respond(tlgbot.i18n.t('yesterday_entry_update_error', lang=lang) or "Ошибка обновления записи")
            else:
                # Создаем новую запись
                created = db.create_diary_entry(
                    user_id, 
                    entry_date,
                    **entry_data
                )
                if created:
                    await event.respond(tlgbot.i18n.t('yesterday_entry_created', lang=lang) or "Новая запись за вчерашний день создана.")
                    # Отображаем содержимое новой записи
                    await display_entry_content(event, user_id, entry_date, lang)
                else:
                    await event.respond(tlgbot.i18n.t('yesterday_entry_error', lang=lang) or "Ошибка создания записи")
            
            # Очищаем данные пользователя
            if user_id in user_states:
                del user_states[user_id]
            if user_id in user_form_data:
                del user_form_data[user_id]
            
        except Exception as e:
            import traceback
            traceback_str = traceback.format_exc()
            logger.error(f"ERROR saving entry: {traceback_str}")
            if edit_mode:
                await event.respond(tlgbot.i18n.t('yesterday_entry_update_error', lang=lang) or f"Ошибка при обновлении записи: {str(e)}")
            else:
                await event.respond(tlgbot.i18n.t('yesterday_entry_error', lang=lang) or f"Ошибка при создании записи: {str(e)}")

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
    logger.debug(f"[YESTERDAY] Event type: {type(event)}")
    logger.debug(f"[YESTERDAY] Event sender_id: {event.sender_id}")
    logger.debug(f"[YESTERDAY] Event chat: {getattr(event, 'chat', None)}")
    logger.debug(f"[YESTERDAY] Event message ID: {getattr(event.message, 'id', None) if hasattr(event, 'message') else None}")
    
    if data == "cancel_edit_yesterday":
        # Пользователь отменил редактирование
        logger.debug(f"[YESTERDAY] Processing cancel_edit_yesterday action")
        try:
            await event.edit(tlgbot.i18n.t('edit_canceled', lang=lang) or "Редактирование отменено.")
            logger.debug(f"[YESTERDAY] Successfully edited message with cancel confirmation")
        except Exception as e:
            logger.error(f"[YESTERDAY] Error in cancel_edit_yesterday: {str(e)}")
            try:
                # Если не удалось отредактировать сообщение, попробуем ответить новым
                await event.respond(tlgbot.i18n.t('edit_canceled', lang=lang) or "Редактирование отменено.")
                logger.debug(f"[YESTERDAY] Sent new message as fallback for cancel confirmation")
            except Exception as e2:
                logger.error(f"[YESTERDAY] Failed to send response message: {str(e2)}")
        
        # Очищаем данные пользователя, чтобы предотвратить переход к другим обработчикам
        if user_id in user_states:
            del user_states[user_id]
        if user_id in user_form_data:
            del user_form_data[user_id]
            
        # Предотвращаем выполнение других callback-обработчиков, завершая событие
        await event.answer("Отменено")
        return True  # Обозначаем, что событие обработано
    
    # Начинаем редактирование
    try:
        from core.database.manager import DatabaseManager
        from cfg.config_tlg import DAYLOG_DB_PATH
        
        db = DatabaseManager(db_path=DAYLOG_DB_PATH)
        yesterday_date = date.today() - timedelta(days=1)
        
        # Получаем текущую запись и сохраняем ее данные
        entry = db.get_diary_entry(user_id, yesterday_date)
        
        if not entry:
            await event.edit(tlgbot.i18n.t('entry_not_found', lang=lang) or "Запись не найдена.")
            return
            
        # Если это редактирование только событий
        if data == "edit_yesterday_events":
            # Сохраняем текущие данные, но переходим сразу к редактированию событий
            user_form_data[user_id] = {
                "entry_date": yesterday_date,
                "edit_mode": True,
                "edit_events_only": True,  # Маркер редактирования только событий
                "mood": entry.get("mood", ""),
                "weather": entry.get("weather", ""),
                "location": entry.get("location", ""),
                "events": entry.get("events", "")
            }
            
            # Начинаем с шага редактирования событий
            user_states[user_id] = FormState.WAITING_EVENTS
            
            # Получаем текущее значение событий безопасно
            current_events = user_form_data[user_id].get("events", "")
            if not current_events:
                current_events = tlgbot.i18n.t('not_specified', lang=lang) or "Не указано"
            
            edit_events_message = tlgbot.i18n.t('edit_events_prompt', lang=lang, events=current_events)
            if not edit_events_message:
                edit_events_message = f"Вчерашние события:\n{current_events}.\n\nОпишите события вчерашнего дня (или нажмите 'Пропустить'):"
            
            logger.debug(f"Showing events edit form in main handler for user {user_id} with edit_events_only=True")
            
            await event.edit(
                edit_events_message,
                buttons=get_events_keyboard(lang, edit_mode=True)
            )
            return
        
        # Иначе полное редактирование
        user_form_data[user_id] = {
            "entry_date": yesterday_date,
            "edit_mode": True,
            "mood": entry.get("mood", ""),
            "weather": entry.get("weather", ""),
            "location": entry.get("location", ""),
            "events": entry.get("events", "")
        }
        
        # Начинаем мастер заполнения с первого шага - настроение
        user_states[user_id] = FormState.WAITING_MOOD
        
        # Получаем текущее значение настроения безопасно
        current_mood = user_form_data[user_id].get("mood", "")
        if not current_mood:
            current_mood = tlgbot.i18n.t('not_specified', lang=lang) or "Не указано"
        
        edit_mood_message = f"Вчерашнее настроение:\n\n{current_mood}\n\nВыберите новое настроение:"
            
        await event.edit(
            edit_mood_message,
            buttons=get_mood_keyboard(lang)
        )
        
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        logger.error(f"ERROR in edit handler: {traceback_str}")
        await event.edit(f"Произошла ошибка: {str(e)}")

# Обработчик для отмены создания/редактирования записи на любом этапе
@tlgbot.on(events.CallbackQuery(pattern="cancel_creation"))
async def cancel_creation_handler(event):
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    # Отладочное сообщение
    logger.debug(f"[YESTERDAY] Cancel creation handler called for user {user_id}")
    
    # Очищаем данные пользователя
    if user_id in user_states:
        del user_states[user_id]
    if user_id in user_form_data:
        del user_form_data[user_id]
    
    # Сообщаем об отмене
    await event.edit(tlgbot.i18n.t('creation_canceled', lang=lang) or "👌 Создание записи отменено. Данные не сохранены.")
    return