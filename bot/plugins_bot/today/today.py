
# Плагин для команды /today с мастером заполнения записи

from datetime import date
from enum import Enum
from telethon import events, Button
from bot.require_diary_user import require_diary_user

# tlgbot глобально доступен в плагинах через динамическую загрузку
tlgbot = globals().get('tlgbot')

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
        ]
    ]

def get_events_keyboard(lang="ru"):
    return [
        [
            Button.inline(tlgbot.i18n.t('btn_skip', lang=lang) or "Пропустить", data=f"events_skip"),
            Button.inline(tlgbot.i18n.t('btn_back', lang=lang) or "Назад", data=f"events_back"),
        ]
    ]

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
    if entry:
        await event.reply(tlgbot.i18n.t('today_entry_exists', lang=lang))
        return
    
    # Начинаем мастер заполнения с первого шага - настроение
    user_states[user_id] = FormState.WAITING_MOOD
    user_form_data[user_id] = {"entry_date": today}
    
    await event.reply(
        tlgbot.i18n.t('today_mood_prompt', lang=lang) or "Какое у вас сегодня настроение?",
        buttons=get_mood_keyboard(lang)
    )

# Обработчики для инлайн-кнопок формы
@tlgbot.on(events.CallbackQuery(pattern=b"mood_.*"))
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
    
    await event.edit(
        tlgbot.i18n.t('today_weather_prompt', lang=lang) or "Какая сегодня погода?",
        buttons=get_weather_keyboard(lang)
    )

@tlgbot.on(events.CallbackQuery(pattern=b"weather_.*"))
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
        await event.edit(
            tlgbot.i18n.t('today_mood_prompt', lang=lang) or "Какое у вас сегодня настроение?",
            buttons=get_mood_keyboard(lang)
        )
        return
    
    if choice == "manual":
        await event.edit(tlgbot.i18n.t('today_weather_manual', lang=lang) or "Введите описание погоды:")
        # Здесь должен быть код для ожидания текстового ответа
        # Для простоты реализации пропустим его
        user_form_data[user_id]["weather"] = None
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
    
    await event.edit(
        tlgbot.i18n.t('today_location_prompt', lang=lang) or "Где вы находитесь?",
        buttons=get_location_keyboard(lang)
    )

@tlgbot.on(events.CallbackQuery(pattern=b"location_.*"))
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
        await event.edit(
            tlgbot.i18n.t('today_weather_prompt', lang=lang) or "Какая сегодня погода?",
            buttons=get_weather_keyboard(lang)
        )
        return
    
    if choice == "manual":
        await event.edit(tlgbot.i18n.t('today_location_manual', lang=lang) or "Введите ваше местоположение:")
        # Здесь должен быть код для ожидания текстового ответа
        # Для простоты реализации пропустим его
        user_form_data[user_id]["location"] = None
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
    
    await event.edit(
        tlgbot.i18n.t('today_events_prompt', lang=lang) or "Опишите события дня (или нажмите 'Пропустить'):",
        buttons=get_events_keyboard(lang)
    )

@tlgbot.on(events.CallbackQuery(pattern=b"events_.*"))
async def events_callback_handler(event):
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    if user_id not in user_states or user_states[user_id] != FormState.WAITING_EVENTS:
        await event.answer(tlgbot.i18n.t('form_invalid_state', lang=lang) or "Неверное состояние формы")
        return
    
    data = event.data.decode("utf-8")
    choice = data.split("_")[1]
    
    if choice == "back":
        # Возвращаемся к предыдущему шагу - местоположение
        user_states[user_id] = FormState.WAITING_LOCATION
        await event.edit(
            tlgbot.i18n.t('today_location_prompt', lang=lang) or "Где вы находитесь?",
            buttons=get_location_keyboard(lang)
        )
        return
    
    if choice != "skip":
        # Здесь должен быть код для обработки ввода событий
        # Для простоты реализации пропустим его
        user_form_data[user_id]["events"] = None
    
    # Сохраняем все данные в БД
    try:
        from core.database.manager import DatabaseManager
        from cfg.config_tlg import DAYLOG_DB_PATH
        
        db = DatabaseManager(db_path=DAYLOG_DB_PATH)
        form_data = user_form_data[user_id]
        
        created = db.create_diary_entry(
            user_id, 
            form_data["entry_date"],
            mood=form_data.get("mood"),
            weather=form_data.get("weather"),
            location=form_data.get("location"),
            events=form_data.get("events")
        )
        
        if created:
            await event.edit(tlgbot.i18n.t('today_entry_created', lang=lang) or "Запись за сегодня создана успешно!")
        else:
            await event.edit(tlgbot.i18n.t('today_entry_error', lang=lang) or "Ошибка создания записи")
        
        # Очищаем данные пользователя
        if user_id in user_states:
            del user_states[user_id]
        if user_id in user_form_data:
            del user_form_data[user_id]
            
    except Exception as e:
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
    
    if current_state == FormState.WAITING_WEATHER and "weather" not in user_form_data[user_id]:
        user_form_data[user_id]["weather"] = text
        # Переходим к следующему шагу
        user_states[user_id] = FormState.WAITING_LOCATION
        await event.reply(
            tlgbot.i18n.t('today_location_prompt', lang=lang) or "Где вы находитесь?",
            buttons=get_location_keyboard(lang)
        )
    elif current_state == FormState.WAITING_LOCATION and "location" not in user_form_data[user_id]:
        user_form_data[user_id]["location"] = text
        # Переходим к следующему шагу
        user_states[user_id] = FormState.WAITING_EVENTS
        await event.reply(
            tlgbot.i18n.t('today_events_prompt', lang=lang) or "Опишите события дня (или нажмите 'Пропустить'):",
            buttons=get_events_keyboard(lang)
        )
    elif current_state == FormState.WAITING_EVENTS:
        user_form_data[user_id]["events"] = text
        # Завершаем заполнение формы и сохраняем данные
        try:
            from core.database.manager import DatabaseManager
            from cfg.config_tlg import DAYLOG_DB_PATH
            
            db = DatabaseManager(db_path=DAYLOG_DB_PATH)
            form_data = user_form_data[user_id]
            
            created = db.create_diary_entry(
                user_id, 
                form_data["entry_date"],
                mood=form_data.get("mood"),
                weather=form_data.get("weather"),
                location=form_data.get("location"),
                events=form_data.get("events")
            )
            
            if created:
                await event.reply(tlgbot.i18n.t('today_entry_created', lang=lang) or "Запись за сегодня создана успешно!")
            else:
                await event.reply(tlgbot.i18n.t('today_entry_error', lang=lang) or "Ошибка создания записи")
            
            # Очищаем данные пользователя
            if user_id in user_states:
                del user_states[user_id]
            if user_id in user_form_data:
                del user_form_data[user_id]
                
        except Exception as e:
            await event.reply(f"Ошибка: {str(e)}")
