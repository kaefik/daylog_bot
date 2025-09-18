
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
    
    # Добавляем отладочную информацию
    print(f"DEBUG: Entry from DB for today command: {entry}")
    
    if entry:
        # Проверяем, содержит ли запись все необходимые поля
        required_fields = ["mood", "weather", "location", "events"]
        for field in required_fields:
            if field not in entry:
                print(f"WARNING: Missing field '{field}' in entry from DB")
                # Инициализируем отсутствующие поля
                entry[field] = None
    
    if entry:
        # Добавляем inline-кнопки для редактирования существующей записи
        buttons = [
            [
                Button.inline(tlgbot.i18n.t('btn_edit', lang=lang) or "Редактировать", data="edit_today"),
                Button.inline(tlgbot.i18n.t('btn_cancel', lang=lang) or "Отмена", data="cancel_edit")
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
            edit_weather_message = f"Текущая погода: {current_weather}. Выберите новую погоду:"
            
        await event.edit(
            edit_weather_message,
            buttons=get_weather_keyboard(lang)
        )
    else:
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
        
        # Для режима редактирования показываем текущее значение
        if user_form_data[user_id].get("edit_mode"):
            current_mood = user_form_data[user_id].get("mood") or tlgbot.i18n.t('not_specified', lang=lang) or "Не указано"
            await event.edit(
                (tlgbot.i18n.t('edit_mood_prompt', lang=lang) or "Текущее настроение: {mood}. Выберите новое настроение:").format(mood=current_mood),
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
        await event.edit(tlgbot.i18n.t('today_weather_manual', lang=lang) or "Введите описание погоды:")
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
            edit_location_message = f"Текущее местоположение: {current_location}. Выберите новое местоположение:"
            
        await event.edit(
            edit_location_message,
            buttons=get_location_keyboard(lang)
        )
    else:
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
        
        # Для режима редактирования показываем текущее значение
        if user_form_data[user_id].get("edit_mode"):
            current_weather = user_form_data[user_id].get("weather") or tlgbot.i18n.t('not_specified', lang=lang) or "Не указано"
            
            # Исправляем вызов метода локализации, передавая параметр weather напрямую
            edit_weather_message = tlgbot.i18n.t('edit_weather_prompt', lang=lang, weather=current_weather)
            if not edit_weather_message:
                edit_weather_message = f"Текущая погода: {current_weather}. Выберите новую погоду:"
                
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
        await event.edit(tlgbot.i18n.t('today_location_manual', lang=lang) or "Введите ваше местоположение:")
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
    
    # Для режима редактирования показываем текущее значение
    if user_form_data[user_id].get("edit_mode"):
        # Безопасно получаем текущее значение событий
        current_events = "Не указано"
        if "events" in user_form_data[user_id] and user_form_data[user_id]["events"]:
            current_events = user_form_data[user_id]["events"]
        else:
            current_events = tlgbot.i18n.t('not_specified', lang=lang) or "Не указано"
            
        # Исправляем вызов метода локализации, передавая параметр events напрямую
        edit_events_message = tlgbot.i18n.t('edit_events_prompt', lang=lang, events=current_events)
        if not edit_events_message:
            edit_events_message = f"Текущие события: {current_events}. Опишите новые события дня (или нажмите 'Пропустить'):"
            
        await event.edit(
            edit_events_message,
            buttons=get_events_keyboard(lang)
        )
    else:
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
        
        # Для режима редактирования показываем текущее значение
        if user_form_data[user_id].get("edit_mode"):
            current_location = user_form_data[user_id].get("location") or tlgbot.i18n.t('not_specified', lang=lang) or "Не указано"
            
            # Исправляем вызов метода локализации, передавая параметр location напрямую
            edit_location_message = tlgbot.i18n.t('edit_location_prompt', lang=lang, location=current_location)
            if not edit_location_message:
                edit_location_message = f"Текущее местоположение: {current_location}. Выберите новое местоположение:"
                
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
        print(f"DEBUG: Saving data: {entry_data}, edit_mode: {edit_mode}")
        
        if edit_mode:
            # Обновляем существующую запись
            success = db.update_diary_entry(
                user_id, 
                form_data["entry_date"],
                **entry_data
            )
            
            if success:
                await event.edit(tlgbot.i18n.t('today_entry_updated', lang=lang) or "Запись за сегодня успешно обновлена!")
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
        print(f"ERROR: {traceback_str}")
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
                edit_location_message = f"Текущее местоположение: {current_location}. Выберите новое местоположение:"
                
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
            
            # Исправляем вызов метода локализации, передавая параметр events напрямую
            edit_events_message = tlgbot.i18n.t('edit_events_prompt', lang=lang, events=current_events)
            if not edit_events_message:
                edit_events_message = f"Текущие события: {current_events}. Опишите новые события дня (или нажмите 'Пропустить'):"
                
            await event.reply(
                edit_events_message,
                buttons=get_events_keyboard(lang)
            )
        else:
            await event.reply(
                tlgbot.i18n.t('today_events_prompt', lang=lang) or "Опишите события дня (или нажмите 'Пропустить'):",
                buttons=get_events_keyboard(lang)
            )
        return
        
    # Если мы ожидаем ввод событий
    elif current_state == FormState.WAITING_EVENTS:
        # Сохраняем введенные события
        user_form_data[user_id]["events"] = text
        
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
            print(f"DEBUG: Saving data from text input: {entry_data}, edit_mode: {edit_mode}")
            
            if edit_mode:
                # Обновляем существующую запись
                success = db.update_diary_entry(
                    user_id, 
                    form_data["entry_date"],
                    **entry_data
                )
                
                if success:
                    await event.reply(tlgbot.i18n.t('today_entry_updated', lang=lang) or "Запись за сегодня успешно обновлена!")
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
                else:
                    await event.reply(tlgbot.i18n.t('today_entry_error', lang=lang) or "Ошибка создания записи")
            
            # Очищаем данные пользователя
            if user_id in user_states:
                del user_states[user_id]
            if user_id in user_form_data:
                del user_form_data[user_id]
                
        except Exception as e:
            await event.reply(f"Ошибка: {str(e)}")

# Обработчик для кнопок редактирования существующей записи
@tlgbot.on(events.CallbackQuery(pattern=b"edit_today|cancel_edit"))
async def edit_today_handler(event):
    user_id = event.sender_id
    user = getattr(tlgbot, 'settings', None).get_user(user_id) if getattr(tlgbot, 'settings', None) else None
    lang = getattr(user, 'lang', None) or 'ru'
    
    data = event.data.decode("utf-8")
    
    if data == "cancel_edit":
        # Пользователь отменил редактирование
        await event.edit(tlgbot.i18n.t('edit_canceled', lang=lang) or "Редактирование отменено.")
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
        print(f"DEBUG: Entry data for editing (raw): {entry}")
        
        if not entry:
            await event.edit(tlgbot.i18n.t('entry_not_found', lang=lang) or "Запись не найдена.")
            return
        
        # Проверяем структуру полученной записи
        required_fields = ["mood", "weather", "location", "events"]
        missing_fields = [field for field in required_fields if field not in entry]
        
        if missing_fields:
            print(f"WARNING: Missing fields in entry: {missing_fields}")
        
        # Выводим информацию о записи в лог для отладки
        print(f"DEBUG: Entry data for edit: {entry}")
        
        # Сохраняем текущие данные для редактирования с безопасными значениями по умолчанию
        user_form_data[user_id] = {
            "entry_date": today,
            "edit_mode": True
        }        # Безопасно добавляем значения, если они существуют
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
            edit_mood_message = f"Текущее настроение: {current_mood}. Выберите новое настроение:"
            
        await event.edit(
            edit_mood_message,
            buttons=get_mood_keyboard(lang)
        )
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        print(f"ERROR: {traceback_str}")
        await event.edit(f"Ошибка: {str(e)}")
