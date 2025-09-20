
# Плагин для команды /today с мастером заполнения записи

from datetime import date
from enum import Enum
from telethon import events, Button
from bot.require_diary_user import require_diary_user

# tlgbot глобально доступен в плагинах через динамическую загрузку
tlgbot = globals().get('tlgbot')
# Логгер доступен через глобальные переменные
logger = globals().get('logger')

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
        logger.error(f"Error displaying entry: {traceback_str}")
        await event.respond(f"Ошибка при отображении записи: {str(e)}")

# Inline-клавиатуры для каждого поля
def get_mood_keyboard(lang="ru"):
    return [
        [
            Button.inline(tlgbot.i18n.t('mood_excellent', lang=lang) or "Отлично", data=f"mood_excellent"),
            Button.inline(tlgbot.i18n.t('mood_good', lang=lang) or "Хорошо", data=f"mood_good"),
        ],
        [
            Button.inline(tlgbot.i18n.t('mood_normal', lang=lang) or "Нормально", data=f"mood_normal"),
            Button.inline(tlgbot.i18n.t('mood_bad', lang=lang) or "Плохо", data=f"mood_bad"),
        ],
        [
            Button.inline(tlgbot.i18n.t('mood_terrible', lang=lang) or "Ужасно", data=f"mood_terrible"),
        ],
        [
            Button.inline(tlgbot.i18n.t('btn_skip', lang=lang) or "Пропустить", data=f"mood_skip"),
            Button.inline(tlgbot.i18n.t('btn_cancel', lang=lang) or "Отмена", data=f"cancel_creation"),
        ]
    ]

def get_weather_keyboard(lang="ru"):
    return [
        [
            Button.inline(tlgbot.i18n.t('weather_sunny', lang=lang) or "Солнечно", data=f"weather_sunny"),
            Button.inline(tlgbot.i18n.t('weather_cloudy', lang=lang) or "Облачно", data=f"weather_cloudy"),
        ],
        [
            Button.inline(tlgbot.i18n.t('weather_rainy', lang=lang) or "Дождь", data=f"weather_rainy"),
            Button.inline(tlgbot.i18n.t('weather_snowy', lang=lang) or "Снег", data=f"weather_snowy"),
        ],
        [
            Button.inline(tlgbot.i18n.t('weather_foggy', lang=lang) or "Туман", data=f"weather_foggy"),
            Button.inline(tlgbot.i18n.t('btn_manual', lang=lang) or "Ввести вручную", data=f"weather_manual"),
        ],
        [
            Button.inline(tlgbot.i18n.t('btn_skip', lang=lang) or "Пропустить", data=f"weather_skip"),
            Button.inline(tlgbot.i18n.t('btn_back', lang=lang) or "Назад", data=f"weather_back"),
            Button.inline(tlgbot.i18n.t('btn_cancel', lang=lang) or "Отмена", data=f"cancel_creation"),
        ]
    ]

def get_location_keyboard(lang="ru"):
    return [
        [
            Button.inline(tlgbot.i18n.t('location_home', lang=lang) or "Дом", data=f"location_home"),
            Button.inline(tlgbot.i18n.t('location_work', lang=lang) or "Работа", data=f"location_work"),
        ],
        [
            Button.inline(tlgbot.i18n.t('location_street', lang=lang) or "Улица", data=f"location_street"),
            Button.inline(tlgbot.i18n.t('btn_manual', lang=lang) or "Ввести вручную", data=f"location_manual"),
        ],
        [
            Button.inline(tlgbot.i18n.t('btn_skip', lang=lang) or "Пропустить", data=f"location_skip"),
            Button.inline(tlgbot.i18n.t('btn_back', lang=lang) or "Назад", data=f"location_back"),
            Button.inline(tlgbot.i18n.t('btn_cancel', lang=lang) or "Отмена", data=f"cancel_creation"),
        ]
    ]

def get_events_keyboard(lang="ru", edit_mode=False):
    buttons = [
        [
            Button.inline(tlgbot.i18n.t('btn_skip', lang=lang) or "Пропустить", data="events_skip"),
            Button.inline(tlgbot.i18n.t('btn_back', lang=lang) or "Назад", data="events_back"),
            Button.inline(tlgbot.i18n.t('btn_cancel', lang=lang) or "Отмена", data="cancel_creation"),
        ]
    ]
    
    # Если в режиме редактирования, добавляем кнопки "Заменить", "Добавить" и "Правка"
    if edit_mode:
        # Отладочное сообщение при создании кнопок
        logger.debug(f"Creating edit mode buttons with data: events_replace, events_append and events_edit")
        
        replace_btn = Button.inline(tlgbot.i18n.t('btn_replace', lang=lang) or "Заменить текст", data="events_replace")
        append_btn = Button.inline(tlgbot.i18n.t('btn_append', lang=lang) or "Добавить к тексту", data="events_append")
        edit_btn = Button.inline(tlgbot.i18n.t('btn_edit_text', lang=lang) or "Правка", data="events_edit")
        buttons.insert(0, [replace_btn, append_btn, edit_btn])
        
    return buttons

@tlgbot.on(tlgbot.cmd('today'))
@require_diary_user
async def today_handler(event):
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
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
    today = date.today()
    entry = db.get_diary_entry(user_id, today)
    
    # Добавляем отладочную информацию
    logger.debug(f"Entry from DB for today command: {entry}")
    
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
                Button.inline(tlgbot.i18n.t('btn_edit', lang=lang) or "Редактировать", data="edit_today"),
                Button.inline(tlgbot.i18n.t('btn_edit_events_only', lang=lang) or "Редактировать событие", data="edit_today_events"),
                Button.inline(tlgbot.i18n.t('btn_cancel', lang=lang) or "Отмена", data="cancel_edit_today")
            ]
        ]
        await event.reply(
            tlgbot.i18n.t('today_entry_exists_edit', lang=lang) or "Запись за сегодня уже существует. Хотите отредактировать её?",
            buttons=buttons
        )
        return
    
    # Начинаем мастер заполнения с первого шага - настроение
    user_states[user_id] = FormState.WAITING_MOOD
    user_form_data[user_id] = {"entry_date": today}
    
    await event.reply(
        tlgbot.i18n.t('today_mood_prompt', lang=lang) or "Какое у вас сегодня настроение?",
        buttons=get_mood_keyboard(lang)
    )

# Обработчики для инлайн-кнопок формы
@tlgbot.on(events.CallbackQuery(pattern="mood_.*"))
async def mood_callback_handler(event):
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    if user_id not in user_states or user_states[user_id] != FormState.WAITING_MOOD:
        await event.answer(tlgbot.i18n.t('form_invalid_state', lang=lang) or "Неверное состояние формы")
        return
    
    data = event.data.decode("utf-8")
    choice = data.split("_")[1]
    
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
        edit_weather_message = tlgbot.i18n.t('edit_weather_prompt', lang=lang, weather=current_weather)
        if not edit_weather_message:
            edit_weather_message = f"Текущая погода:\n\n{current_weather}\n\nВыберите новую погоду:"
            
        await event.edit(
            edit_weather_message,
            buttons=get_weather_keyboard(lang)
        )
    else:
        await event.edit(
            tlgbot.i18n.t('today_weather_prompt', lang=lang) or "Какая сегодня погода?",
            buttons=get_weather_keyboard(lang)
        )

@tlgbot.on(events.CallbackQuery(pattern="weather_.*"))
async def weather_callback_handler(event):
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    if user_id not in user_states or user_states[user_id] != FormState.WAITING_WEATHER:
        await event.answer(tlgbot.i18n.t('form_invalid_state', lang=lang) or "Неверное состояние формы")
        return
    
    data = event.data.decode("utf-8")
    choice = data.split("_")[1]
    
    if choice == "back":
        # Возвращаемся к предыдущему шагу - настроение
        user_states[user_id] = FormState.WAITING_MOOD
        
        # Для режима редактирования показываем текущее значение
        if user_form_data[user_id].get("edit_mode"):
            current_mood = user_form_data[user_id].get("mood") or tlgbot.i18n.t('not_specified', lang=lang) or "Не указано"
            await event.edit(
                (tlgbot.i18n.t('edit_mood_prompt', lang=lang) or "Текущее настроение:\n\n{mood}\n\nВыберите новое настроение:").format(mood=current_mood),
                buttons=get_mood_keyboard(lang)
            )
        else:
            await event.edit(
                tlgbot.i18n.t('today_mood_prompt', lang=lang) or "Какое у вас сегодня настроение?",
                buttons=get_mood_keyboard(lang)
            )
        return
    
    if choice == "manual":
        # Устанавливаем флаг ожидания ручного ввода погоды
        user_form_data[user_id]["waiting_manual_weather"] = True
        await event.edit(
            (tlgbot.i18n.t('today_weather_manual', lang=lang) or "Введите описание погоды:") + 
            "\n\n" + (tlgbot.i18n.t('type_cancel_to_abort', lang=lang) or "Напишите 'отмена' для отмены создания записи.")
        )
        # Не переходим к следующему шагу, ждем ввода
        return
    elif choice != "skip":
        # Преобразуем выбор в соответствующее значение для БД
        weather_mapping = {
            "sunny": "Солнечно",
            "cloudy": "Облачно",
            "rainy": "Дождливо",
            "snowy": "Снежно",
            "foggy": "Туманно"
        }
        user_form_data[user_id]["weather"] = weather_mapping.get(choice)
    
    # Переходим к следующему шагу - местоположение
    user_states[user_id] = FormState.WAITING_LOCATION
    
    # Для режима редактирования показываем текущее значение
    if user_form_data[user_id].get("edit_mode"):
        # Безопасно получаем текущее значение местоположения
        current_location = "Не указано"
        if "location" in user_form_data[user_id] and user_form_data[user_id]["location"]:
            current_location = user_form_data[user_id]["location"]
        else:
            current_location = tlgbot.i18n.t('not_specified', lang=lang) or "Не указано"
            
        # Исправляем вызов метода локализации, передавая параметр location напрямую
        edit_location_message = tlgbot.i18n.t('edit_location_prompt', lang=lang, location=current_location)
        if not edit_location_message:
            edit_location_message = f"Текущее местоположение:\n\n{current_location}\n\nВыберите новое местоположение:"
            
        await event.edit(
            edit_location_message,
            buttons=get_location_keyboard(lang)
        )
    else:
        await event.edit(
            tlgbot.i18n.t('today_location_prompt', lang=lang) or "Где вы находитесь?",
            buttons=get_location_keyboard(lang)
        )

@tlgbot.on(events.CallbackQuery(pattern="location_.*"))
async def location_callback_handler(event):
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    if user_id not in user_states or user_states[user_id] != FormState.WAITING_LOCATION:
        await event.answer(tlgbot.i18n.t('form_invalid_state', lang=lang) or "Неверное состояние формы")
        return
    
    data = event.data.decode("utf-8")
    choice = data.split("_")[1]
    
    if choice == "back":
        # Возвращаемся к предыдущему шагу - погода
        user_states[user_id] = FormState.WAITING_WEATHER
        
        # Для режима редактирования показываем текущее значение
        if user_form_data[user_id].get("edit_mode"):
            current_weather = user_form_data[user_id].get("weather") or tlgbot.i18n.t('not_specified', lang=lang) or "Не указано"
            
            # Исправляем вызов метода локализации, передавая параметр weather напрямую
            edit_weather_message = tlgbot.i18n.t('edit_weather_prompt', lang=lang, weather=current_weather)
            if not edit_weather_message:
                edit_weather_message = f"Текущая погода:\n\n{current_weather}\n\nВыберите новую погоду:"
                
            await event.edit(
                edit_weather_message,
                buttons=get_weather_keyboard(lang)
            )
        else:
            await event.edit(
                tlgbot.i18n.t('today_weather_prompt', lang=lang) or "Какая сегодня погода?",
                buttons=get_weather_keyboard(lang)
            )
        return
    
    if choice == "manual":
        # Устанавливаем флаг ожидания ручного ввода местоположения
        user_form_data[user_id]["waiting_manual_location"] = True
        await event.edit(
            (tlgbot.i18n.t('today_location_manual', lang=lang) or "Введите ваше местоположение:") + 
            "\n\n" + (tlgbot.i18n.t('type_cancel_to_abort', lang=lang) or "Напишите 'отмена' для отмены создания записи.")
        )
        # Не переходим к следующему шагу, ждем ввода
        return
    elif choice != "skip":
        # Преобразуем выбор в соответствующее значение для БД
        location_mapping = {
            "home": "Дом",
            "work": "Работа",
            "street": "Улица"
        }
        user_form_data[user_id]["location"] = location_mapping.get(choice)
    
    # Переходим к следующему шагу - события
    user_states[user_id] = FormState.WAITING_EVENTS
    
        # Переходим к следующему шагу - события
    user_states[user_id] = FormState.WAITING_EVENTS
    
    # Для режима редактирования показываем текущее значение
    if user_form_data[user_id].get("edit_mode"):
        # Безопасно получаем текущее значение событий
        current_events = "Не указано"
        if "events" in user_form_data[user_id] and user_form_data[user_id]["events"]:
            current_events = user_form_data[user_id]["events"]
        else:
            current_events = tlgbot.i18n.t('not_specified', lang=lang) or "Не указано"
            
        # Отладочное сообщение
        logger.debug(f"Showing events form with edit_mode=True in location_callback. User ID: {user_id}, Current events: {current_events}")
            
        # Исправляем вызов метода локализации, передавая параметр events напрямую
        edit_events_message = tlgbot.i18n.t('edit_events_prompt', lang=lang, events=current_events)
        if not edit_events_message:
            edit_events_message = f"Текущие события:\n{current_events}.\n\nОпишите новые события дня (или нажмите 'Пропустить'):"
            
        await event.edit(
            edit_events_message,
            buttons=get_events_keyboard(lang, edit_mode=True)
        )
    else:
        await event.edit(
            tlgbot.i18n.t('today_events_prompt', lang=lang) or "Опишите события дня (или нажмите 'Пропустить'):",
            buttons=get_events_keyboard(lang, edit_mode=False)
        )

@tlgbot.on(events.CallbackQuery(pattern="events_.*"))
async def events_callback_handler(event):
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    if user_id not in user_states or user_states[user_id] != FormState.WAITING_EVENTS:
        await event.answer(tlgbot.i18n.t('form_invalid_state', lang=lang) or "Неверное состояние формы")
        return
    
    data = event.data.decode("utf-8")
    choice = data.split("_")[1]
    
    # Отладочное сообщение для всех кнопок
    logger.debug(f"Events callback handler called. User ID: {user_id}, Choice: {choice}, Data: {data}, Raw data: {event.data}")
    
    if choice == "back":
        # Возвращаемся к предыдущему шагу - местоположение
        user_states[user_id] = FormState.WAITING_LOCATION
        
        # Для режима редактирования показываем текущее значение
        if user_form_data[user_id].get("edit_mode"):
            current_location = user_form_data[user_id].get("location") or tlgbot.i18n.t('not_specified', lang=lang) or "Не указано"
            
            # Исправляем вызов метода локализации, передавая параметр location напрямую
            edit_location_message = tlgbot.i18n.t('edit_location_prompt', lang=lang, location=current_location)
            if not edit_location_message:
                edit_location_message = f"Текущее местоположение:\n\n{current_location}\n\nВыберите новое местоположение:"
                
            await event.edit(
                edit_location_message,
                buttons=get_location_keyboard(lang)
            )
        else:
            await event.edit(
                tlgbot.i18n.t('today_location_prompt', lang=lang) or "Где вы находитесь?",
                buttons=get_location_keyboard(lang)
            )
        return
    
    # Новые обработчики для режима редактирования
    if choice == "replace":
        logger.debug(f"REPLACE button was clicked! User ID: {user_id}")
        # Устанавливаем флаг режима замены
        user_form_data[user_id]["events_mode"] = "replace"
        current_events = user_form_data[user_id].get("events") or ""
        
        # Отладочное сообщение
        logger.debug(f"Replace button clicked. User ID: {user_id}, Current events: {current_events}")
        
        replace_message = tlgbot.i18n.t('events_replace_prompt', lang=lang, events=current_events)
        if not replace_message:
            replace_message = f"Текущие события:\n\"{current_events}\"\n\nВведите новый текст, который полностью заменит текущий:"
            
        await event.edit(replace_message + "\n\n" + (tlgbot.i18n.t('type_cancel_to_abort', lang=lang) or "Напишите 'отмена' для отмены создания записи."))
        # Ожидаем ввод пользователя, который будет обработан в handle_manual_input
        return
        
    elif choice == "append":
        # Устанавливаем флаг режима добавления
        user_form_data[user_id]["events_mode"] = "append"
        current_events = user_form_data[user_id].get("events") or ""
        
        append_message = tlgbot.i18n.t('events_append_prompt', lang=lang, events=current_events)
        if not append_message:
            append_message = f"Текущие события:\n\"{current_events}\"\n\nВведите текст, который будет добавлен к текущему:"
            
        await event.edit(append_message + "\n\n" + (tlgbot.i18n.t('type_cancel_to_abort', lang=lang) or "Напишите 'отмена' для отмены создания записи."))
        # Ожидаем ввод пользователя, который будет обработан в handle_manual_input
        return
        
    elif choice == "edit":
        # Устанавливаем флаг режима редактирования
        user_form_data[user_id]["events_mode"] = "edit"
        current_events = user_form_data[user_id].get("events") or ""
        
        # Отладочное сообщение
        logger.debug(f"Edit button clicked. User ID: {user_id}, Current events: {current_events}")
        
        edit_message = tlgbot.i18n.t('events_edit_prompt', lang=lang, events=current_events)
        if not edit_message:
            edit_message = f"Текущие события:\n\"{current_events}\"\n\nОтредактируйте текст:"
            
        # Устанавливаем начальный текст для ввода пользователя
        # В Telethon нельзя напрямую установить текст в поле ввода,
        # поэтому мы просто показываем сообщение с текущим текстом,
        # который пользователь может скопировать и отредактировать
        
        await event.edit(edit_message + "\n\n" + (tlgbot.i18n.t('type_cancel_to_abort', lang=lang) or "Напишите 'отмена' для отмены создания записи."))
        
        # Отправляем второе сообщение только с текстом событий, чтобы пользователю было легче скопировать
        await event.respond(current_events)
        
        # Ожидаем ввод пользователя, который будет обработан в handle_manual_input
        return
    
    if choice != "skip":
        # Если пользователь не нажал "Пропустить", сохраняем текущие события
        # В случае с events_callback, мы обычно здесь ничего не делаем,
        # так как текст событий вводится отдельно
        pass
    
    # Сохраняем все данные в БД
    try:
        from core.database.manager import DatabaseManager
        from cfg.config_tlg import DAYLOG_DB_PATH
        
        db = DatabaseManager(db_path=DAYLOG_DB_PATH)
        form_data = user_form_data[user_id]
        
        # Извлекаем флаг режима редактирования
        edit_mode = False
        if "edit_mode" in form_data:
            edit_mode = form_data.pop("edit_mode")
            
        # Создаем копию словаря только с необходимыми полями
        entry_data = {
            "mood": form_data.get("mood"),
            "weather": form_data.get("weather"),
            "location": form_data.get("location"),
            "events": form_data.get("events")
        }
        
        # Отладочная информация
        logger.debug(f"Saving data: {entry_data}, edit_mode: {edit_mode}")
        
        if edit_mode:
            # Обновляем существующую запись
            success = db.update_diary_entry(
                user_id, 
                form_data["entry_date"],
                **entry_data
            )
            
            if success:
                await event.edit(tlgbot.i18n.t('today_entry_updated', lang=lang) or "Запись за сегодня успешно обновлена!")
                # Отображаем содержимое обновленной записи
                await display_entry_content(event, user_id, form_data["entry_date"], lang)
            else:
                await event.edit(tlgbot.i18n.t('today_entry_update_error', lang=lang) or "Ошибка обновления записи")
        else:
            # Создаем новую запись
            created = db.create_diary_entry(
                user_id, 
                form_data["entry_date"],
                mood=entry_data.get("mood"),
                weather=entry_data.get("weather"),
                location=entry_data.get("location"),
                events=entry_data.get("events")
            )
            
            if created:
                await event.edit(tlgbot.i18n.t('today_entry_created', lang=lang) or "Запись за сегодня создана успешно!")
                # Отображаем содержимое новой записи
                await display_entry_content(event, user_id, form_data["entry_date"], lang)
            else:
                await event.edit(tlgbot.i18n.t('today_entry_error', lang=lang) or "Ошибка создания записи")
        
        # Очищаем данные пользователя
        if user_id in user_states:
            del user_states[user_id]
        if user_id in user_form_data:
            del user_form_data[user_id]
            
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        logger.error(f"{traceback_str}")
        await event.edit(f"Ошибка: {str(e)}")

# Обработчик для ручного ввода текста (для полей с опцией "Ввести вручную")
@tlgbot.on(events.NewMessage)
async def handle_manual_input(event):
    user_id = event.sender_id
    
    # Проверяем, находится ли пользователь в состоянии ожидания ручного ввода
    if user_id not in user_states:
        return
    
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    # Обрабатываем ввод в зависимости от текущего состояния
    current_state = user_states[user_id]
    text = event.text
    edit_mode = user_form_data[user_id].get("edit_mode", False)
    
    # Проверяем, есть ли у нас команда (начинается с /)
    if text.startswith('/'):
        # Это команда, не обрабатываем ее здесь
        return
        
    # Проверяем, ввёл ли пользователь команду отмены
    if text.lower() in ['отмена', 'cancel', '/cancel']:
        # Очищаем данные пользователя
        if user_id in user_states:
            del user_states[user_id]
        if user_id in user_form_data:
            del user_form_data[user_id]
        
        # Сообщаем об отмене
        await event.reply(tlgbot.i18n.t('creation_canceled', lang=lang) or "👌 Создание записи отменено. Данные не сохранены.")
        return
    
    # Проверяем ожидание ручного ввода погоды
    if current_state == FormState.WAITING_WEATHER and user_form_data[user_id].get("waiting_manual_weather"):
        # Сохраняем введенную погоду
        user_form_data[user_id]["weather"] = text
        # Удаляем флаг ожидания
        del user_form_data[user_id]["waiting_manual_weather"]
        
        # Переходим к следующему шагу - местоположение
        user_states[user_id] = FormState.WAITING_LOCATION
        
        # Для режима редактирования показываем текущее значение
        if edit_mode:
            current_location = user_form_data[user_id].get("location") or tlgbot.i18n.t('not_specified', lang=lang) or "Не указано"
            
            # Исправляем вызов метода локализации, передавая параметр location напрямую
            edit_location_message = tlgbot.i18n.t('edit_location_prompt', lang=lang, location=current_location)
            if not edit_location_message:
                edit_location_message = f"Текущее местоположение:\n\n{current_location}\n\nВыберите новое местоположение:"
                
            await event.reply(
                edit_location_message,
                buttons=get_location_keyboard(lang)
            )
        else:
            await event.reply(
                tlgbot.i18n.t('today_location_prompt', lang=lang) or "Где вы находитесь?",
                buttons=get_location_keyboard(lang)
            )
        return
        
    # Проверяем ожидание ручного ввода местоположения
    elif current_state == FormState.WAITING_LOCATION and user_form_data[user_id].get("waiting_manual_location"):
        # Сохраняем введенное местоположение
        user_form_data[user_id]["location"] = text
        # Удаляем флаг ожидания
        del user_form_data[user_id]["waiting_manual_location"]
        
        # Переходим к следующему шагу - события
        user_states[user_id] = FormState.WAITING_EVENTS
        
        # Для режима редактирования показываем текущее значение
        if edit_mode:
            current_events = user_form_data[user_id].get("events") or tlgbot.i18n.t('not_specified', lang=lang) or "Не указано"
            
            # Отладочное сообщение
            logger.debug(f"Showing events edit form with edit_mode=True. User ID: {user_id}, Current events: {current_events}")
            
            # Исправляем вызов метода локализации, передавая параметр events напрямую
            edit_events_message = tlgbot.i18n.t('edit_events_prompt', lang=lang, events=current_events)
            if not edit_events_message:
                edit_events_message = f"Текущие события:\n{current_events}.\n\nОпишите новые события дня (или нажмите 'Пропустить'):"
                
            await event.reply(
                edit_events_message,
                buttons=get_events_keyboard(lang, edit_mode=True)
            )
        else:
            await event.reply(
                tlgbot.i18n.t('today_events_prompt', lang=lang) or "Опишите события дня (или нажмите 'Пропустить'):",
                buttons=get_events_keyboard(lang, edit_mode=False)
            )
        return
        
    # Если мы ожидаем ввод событий
    elif current_state == FormState.WAITING_EVENTS:
        # Проверяем режим редактирования событий
        events_mode = user_form_data[user_id].get("events_mode", "replace")
        
        if events_mode == "append" and "events" in user_form_data[user_id] and user_form_data[user_id]["events"]:
            # Добавляем текст к существующему
            current_events = user_form_data[user_id]["events"]
            user_form_data[user_id]["events"] = current_events + "\n" + text
        elif events_mode == "edit":
            # Просто заменяем текст на введенный пользователем
            user_form_data[user_id]["events"] = text
        else:
            # Заменяем текст или создаем новый (для режима "replace")
            user_form_data[user_id]["events"] = text
            
        # Удаляем флаг режима редактирования событий, если он есть
        if "events_mode" in user_form_data[user_id]:
            del user_form_data[user_id]["events_mode"]
        
        # Завершаем заполнение формы и сохраняем данные
        try:
            from core.database.manager import DatabaseManager
            from cfg.config_tlg import DAYLOG_DB_PATH
            
            db = DatabaseManager(db_path=DAYLOG_DB_PATH)
            form_data = user_form_data[user_id]
            
            # Извлекаем флаг режима редактирования
            edit_mode = False
            if "edit_mode" in form_data:
                edit_mode = form_data.pop("edit_mode")
                
            # Создаем копию словаря только с необходимыми полями
            entry_data = {
                "mood": form_data.get("mood"),
                "weather": form_data.get("weather"),
                "location": form_data.get("location"),
                "events": form_data.get("events")
            }
            
            # Отладочная информация
            logger.debug(f"Saving data from text input: {entry_data}, edit_mode: {edit_mode}")
            
            if edit_mode:
                # Обновляем существующую запись
                success = db.update_diary_entry(
                    user_id, 
                    form_data["entry_date"],
                    **entry_data
                )
                
                if success:
                    await event.reply(tlgbot.i18n.t('today_entry_updated', lang=lang) or "Запись за сегодня успешно обновлена!")
                    # Отображаем содержимое обновленной записи
                    await display_entry_content(event, user_id, form_data["entry_date"], lang)
                else:
                    await event.reply(tlgbot.i18n.t('today_entry_update_error', lang=lang) or "Ошибка обновления записи")
            else:
                # Создаем новую запись
                created = db.create_diary_entry(
                    user_id, 
                    form_data["entry_date"],
                    mood=entry_data.get("mood"),
                    weather=entry_data.get("weather"),
                    location=entry_data.get("location"),
                    events=entry_data.get("events")
                )
                
                if created:
                    await event.reply(tlgbot.i18n.t('today_entry_created', lang=lang) or "Запись за сегодня создана успешно!")
                    # Отображаем содержимое новой записи
                    await display_entry_content(event, user_id, form_data["entry_date"], lang)
                else:
                    await event.reply(tlgbot.i18n.t('today_entry_error', lang=lang) or "Ошибка создания записи")
            
            # Очищаем данные пользователя
            if user_id in user_states:
                del user_states[user_id]
            if user_id in user_form_data:
                del user_form_data[user_id]
                
        except Exception as e:
            await event.reply(f"Ошибка: {str(e)}")

# Обработчик для отмены создания/редактирования записи на любом этапе
@tlgbot.on(events.CallbackQuery(pattern="cancel_creation"))
async def cancel_creation_handler(event):
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    # Очищаем данные пользователя
    if user_id in user_states:
        del user_states[user_id]
    if user_id in user_form_data:
        del user_form_data[user_id]
    
    # Сообщаем об отмене
    await event.edit(tlgbot.i18n.t('creation_canceled', lang=lang) or "👌 Создание записи отменено. Данные не сохранены.")
    return

# Обработчик для кнопок редактирования существующей записи
@tlgbot.on(events.CallbackQuery(pattern="edit_today|edit_today_events|cancel_edit_today"))
async def edit_today_handler(event):
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    data = event.data.decode("utf-8")
    
    if data == "cancel_edit_today":
        # Пользователь отменил редактирование
        await event.edit(tlgbot.i18n.t('edit_canceled', lang=lang) or "👌 Редактирование отменено. Запись осталась без изменений.")
        return
    
    # Начинаем редактирование
    try:
        from core.database.manager import DatabaseManager
        from cfg.config_tlg import DAYLOG_DB_PATH
        import traceback
        
        db = DatabaseManager(db_path=DAYLOG_DB_PATH)
        today = date.today()
        
        # Получаем текущую запись и сохраняем ее данные
        entry = db.get_diary_entry(user_id, today)
        logger.debug(f"Entry data for editing (raw): {entry}")
        
        if not entry:
            await event.edit(tlgbot.i18n.t('entry_not_found', lang=lang) or "Запись не найдена.")
            return
        
        # Проверяем структуру полученной записи
        required_fields = ["mood", "weather", "location", "events"]
        missing_fields = [field for field in required_fields if field not in entry]
        
        if missing_fields:
            logger.warning(f"Missing fields in entry: {missing_fields}")
        
        # Выводим информацию о записи в лог для отладки
        logger.debug(f"Entry data for edit: {entry}")
        
        # Если это редактирование только событий
        if data == "edit_today_events":
            # Сохраняем текущие данные, но переходим сразу к редактированию событий
            user_form_data[user_id] = {
                "entry_date": today,
                "edit_mode": True,
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
            
            # Исправляем вызов метода локализации, передавая параметр events напрямую
            edit_events_message = tlgbot.i18n.t('edit_events_prompt', lang=lang, events=current_events)
            if not edit_events_message:
                edit_events_message = f"Текущие события:\n{current_events}.\n\nОпишите новые события дня (или нажмите 'Пропустить'):"
                
            await event.edit(
                edit_events_message,
                buttons=get_events_keyboard(lang, edit_mode=True)
            )
            return
        
        # Иначе полное редактирование - сохраняем текущие данные для редактирования с безопасными значениями по умолчанию
        user_form_data[user_id] = {
            "entry_date": today,
            "edit_mode": True
        }
        
        # Безопасно добавляем значения, если они существуют
        # Теперь мы можем быть уверены, что все ключи существуют в записи благодаря улучшениям в DatabaseManager
        user_form_data[user_id]["mood"] = entry.get("mood", "")
        user_form_data[user_id]["weather"] = entry.get("weather", "")
        user_form_data[user_id]["location"] = entry.get("location", "")
        user_form_data[user_id]["events"] = entry.get("events", "")
        
        # Начинаем мастер заполнения с первого шага - настроение
        user_states[user_id] = FormState.WAITING_MOOD
        
        # Получаем текущее значение настроения безопасно
        current_mood = user_form_data[user_id].get("mood", "")
        if not current_mood:
            current_mood = tlgbot.i18n.t('not_specified', lang=lang) or "Не указано"
        
        # Исправляем вызов метода локализации, передавая параметр mood напрямую
        edit_mood_message = tlgbot.i18n.t('edit_mood_prompt', lang=lang, mood=current_mood)
        if not edit_mood_message:
            edit_mood_message = f"Текущее настроение:\n\n{current_mood}\n\nВыберите новое настроение:"
            
        await event.edit(
            edit_mood_message,
            buttons=get_mood_keyboard(lang)
        )
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        logger.error(f"{traceback_str}")
        await event.edit(f"Ошибка: {str(e)}")
