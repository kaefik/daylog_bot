"""
Модуль для управления дневниковыми записями
Содержит логику создания, редактирования и отображения записей
"""

from datetime import date, timedelta
from enum import Enum
from typing import Dict, Any, Optional, Callable, List, Union, Tuple
from telethon import events, Button, TelegramClient

from core.database.manager import DatabaseManager
from cfg.config_tlg import DAYLOG_DB_PATH


class FormState(str, Enum):
    """Состояния формы для создания/редактирования записи"""
    WAITING_MOOD = "waiting_mood"
    WAITING_WEATHER = "waiting_weather"
    WAITING_LOCATION = "waiting_location"
    WAITING_EVENTS = "waiting_events"


class DiaryManager:
    """
    Класс для управления дневниковыми записями
    Инкапсулирует логику создания, редактирования и отображения записей
    """
    
    # Словари для хранения временных данных пользователей (в памяти)
    _user_states: Dict[int, FormState] = {}
    _user_form_data: Dict[int, Dict[str, Any]] = {}
    
    def __init__(self, client, logger, i18n=None):
        """
        Инициализация менеджера дневника
        
        Args:
            client: Клиент Telegram (tlgbot)
            logger: Логгер
            i18n: Объект для интернационализации
        """
        self.client = client
        self.logger = logger
        self.i18n = i18n
        self.db = DatabaseManager(db_path=DAYLOG_DB_PATH)
    
    def _t(self, key: str, lang: str = "ru", **kwargs) -> str:
        """
        Получение локализованной строки
        
        Args:
            key: Ключ строки
            lang: Язык
            **kwargs: Параметры для форматирования строки
            
        Returns:
            Локализованная строка
        """
        if self.i18n:
            result = self.i18n.t(key, lang=lang, **kwargs)
            if result:
                return result
                
        # Запасные значения для случая, если перевод не найден
        fallbacks = {
            'entry_not_found': "Запись не найдена.",
            'not_specified': "Не указано",
            'entry_title': f"📝 Запись от {kwargs.get('date', '')}",
            'entry_mood': f"🙂 Настроение: {kwargs.get('mood', '')}",
            'entry_weather': f"🌤 Погода: {kwargs.get('weather', '')}",
            'entry_location': f"📍 Местоположение: {kwargs.get('location', '')}",
            'entry_events': f"📌 События: {kwargs.get('events', '')}",
            'form_invalid_state': "Неверное состояние формы",
            'form_first_step': "Это первый шаг",
            'type_cancel_to_abort': "Напишите 'отмена' для отмены создания записи.",
            'creation_canceled': "👌 Создание записи отменено. Данные не сохранены.",
            'today_entry_created': "Запись создана успешно!",
            'today_entry_updated': "Запись успешно обновлена!",
            'today_entry_error': "Ошибка создания записи",
            'today_entry_update_error': "Ошибка обновления записи",
            'edit_events_prompt': f"Текущие события:\n{kwargs.get('events', '')}\n\nОпишите новые события (или нажмите 'Пропустить'):",
            'today_events_prompt': "Опишите события (или нажмите 'Пропустить'):",
            'edit_location_prompt': f"Текущее местоположение:\n\n{kwargs.get('location', '')}\n\nВыберите новое местоположение:",
            'today_location_prompt': "Где вы находитесь?",
            'today_location_manual': "Введите ваше местоположение:",
            'events_replace_prompt': f"Текущие события:\n\"{kwargs.get('events', '')}\"\n\nВведите новый текст, который полностью заменит текущий:",
            'events_append_prompt': f"Текущие события:\n\"{kwargs.get('events', '')}\"\n\nВведите текст, который будет добавлен к текущему:",
            'events_edit_prompt': f"Текущие события:\n\"{kwargs.get('events', '')}\"\n\nОтредактируйте текст:",
            'mood_excellent': "Отлично",
            'mood_good': "Хорошо", 
            'mood_normal': "Нормально", 
            'mood_bad': "Плохо", 
            'mood_terrible': "Ужасно",
            'weather_sunny': "Солнечно",
            'weather_cloudy': "Облачно",
            'weather_rainy': "Дождь",
            'weather_snowy': "Снег",
            'weather_foggy': "Туман",
            'location_home': "Дом",
            'location_work': "Работа",
            'location_street': "Улица",
            'btn_manual': "Ввести вручную",
            'btn_skip': "Пропустить",
            'btn_back': "Назад",
            'btn_cancel': "Отмена",
            'btn_replace': "Заменить текст",
            'btn_append': "Добавить к тексту",
            'btn_edit_text': "Правка",
            'btn_edit': "Редактировать",
            'btn_edit_events_only': "Редактировать событие",
            'today_entry_exists_edit': "Запись за сегодня уже существует. Хотите отредактировать её?",
            'yesterday_entry_exists_edit': "Запись за вчерашний день уже существует. Хотите отредактировать её?",
            'edit_canceled': "Редактирование отменено.",
        }
        
        return fallbacks.get(key, key)
    
    async def display_entry_content(self, event, user_id: int, entry_date: date, lang: str = "ru") -> None:
        """
        Отображает содержимое записи дневника
        
        Args:
            event: Событие Telegram
            user_id: ID пользователя
            entry_date: Дата записи
            lang: Язык
        """
        try:
            entry = self.db.get_diary_entry(user_id, entry_date)
            
            if not entry:
                await event.respond(self._t('entry_not_found', lang=lang))
                return
                
            # Формируем сообщение с содержимым записи
            mood = entry.get("mood") or self._t('not_specified', lang=lang)
            weather = entry.get("weather") or self._t('not_specified', lang=lang)
            location = entry.get("location") or self._t('not_specified', lang=lang)
            events = entry.get("events") or self._t('not_specified', lang=lang)
            
            # Используем локализованные строки для каждой части сообщения
            date_str = str(entry_date)
            message = self._t('entry_title', lang=lang, date=date_str) + "\n\n"
            message += self._t('entry_mood', lang=lang, mood=mood) + "\n"
            message += self._t('entry_weather', lang=lang, weather=weather) + "\n"
            message += self._t('entry_location', lang=lang, location=location) + "\n"
            message += self._t('entry_events', lang=lang, events=events) + "\n"
            
            await event.respond(message, parse_mode='markdown')
        except Exception as e:
            import traceback
            traceback_str = traceback.format_exc()
            self.logger.error(f"ERROR displaying entry: {traceback_str}")
            await event.respond(f"Ошибка при отображении записи: {str(e)}")
    
    def get_mood_keyboard(self, lang: str = "ru", prefix: str = "") -> List[List[Button]]:
        """
        Создает inline-клавиатуру для выбора настроения
        
        Args:
            lang: Язык
            prefix: Префикс для данных кнопок (например, 'yesterday_')
            
        Returns:
            Список кнопок
        """
        return [
            [
                Button.inline(self._t('mood_excellent', lang=lang), data=f"{prefix}mood_excellent"),
                Button.inline(self._t('mood_good', lang=lang), data=f"{prefix}mood_good"),
            ],
            [
                Button.inline(self._t('mood_normal', lang=lang), data=f"{prefix}mood_normal"),
                Button.inline(self._t('mood_bad', lang=lang), data=f"{prefix}mood_bad"),
            ],
            [
                Button.inline(self._t('mood_terrible', lang=lang), data=f"{prefix}mood_terrible"),
            ],
            [
                Button.inline(self._t('btn_skip', lang=lang), data=f"{prefix}mood_skip"),
                Button.inline(self._t('btn_cancel', lang=lang), data=f"cancel_creation"),
            ]
        ]

    def get_weather_keyboard(self, lang: str = "ru", prefix: str = "") -> List[List[Button]]:
        """
        Создает inline-клавиатуру для выбора погоды
        
        Args:
            lang: Язык
            prefix: Префикс для данных кнопок
            
        Returns:
            Список кнопок
        """
        return [
            [
                Button.inline(self._t('weather_sunny', lang=lang), data=f"{prefix}weather_sunny"),
                Button.inline(self._t('weather_cloudy', lang=lang), data=f"{prefix}weather_cloudy"),
            ],
            [
                Button.inline(self._t('weather_rainy', lang=lang), data=f"{prefix}weather_rainy"),
                Button.inline(self._t('weather_snowy', lang=lang), data=f"{prefix}weather_snowy"),
            ],
            [
                Button.inline(self._t('weather_foggy', lang=lang), data=f"{prefix}weather_foggy"),
                Button.inline(self._t('btn_manual', lang=lang), data=f"{prefix}weather_manual"),
            ],
            [
                Button.inline(self._t('btn_skip', lang=lang), data=f"{prefix}weather_skip"),
                Button.inline(self._t('btn_back', lang=lang), data=f"{prefix}weather_back"),
                Button.inline(self._t('btn_cancel', lang=lang), data=f"cancel_creation"),
            ]
        ]

    def get_location_keyboard(self, lang: str = "ru", prefix: str = "") -> List[List[Button]]:
        """
        Создает inline-клавиатуру для выбора местоположения
        
        Args:
            lang: Язык
            prefix: Префикс для данных кнопок
            
        Returns:
            Список кнопок
        """
        return [
            [
                Button.inline(self._t('location_home', lang=lang), data=f"{prefix}location_home"),
                Button.inline(self._t('location_work', lang=lang), data=f"{prefix}location_work"),
            ],
            [
                Button.inline(self._t('location_street', lang=lang), data=f"{prefix}location_street"),
                Button.inline(self._t('btn_manual', lang=lang), data=f"{prefix}location_manual"),
            ],
            [
                Button.inline(self._t('btn_skip', lang=lang), data=f"{prefix}location_skip"),
                Button.inline(self._t('btn_back', lang=lang), data=f"{prefix}location_back"),
                Button.inline(self._t('btn_cancel', lang=lang), data=f"cancel_creation"),
            ]
        ]

    def get_events_keyboard(self, lang: str = "ru", prefix: str = "", edit_mode: bool = False) -> List[List[Button]]:
        """
        Создает inline-клавиатуру для ввода событий
        
        Args:
            lang: Язык
            prefix: Префикс для данных кнопок
            edit_mode: Режим редактирования
            
        Returns:
            Список кнопок
        """
        buttons = [
            [
                Button.inline(self._t('btn_skip', lang=lang), data=f"{prefix}events_skip"),
                Button.inline(self._t('btn_back', lang=lang), data=f"{prefix}events_back"),
                Button.inline(self._t('btn_cancel', lang=lang), data="cancel_creation"),
            ]
        ]
        
        # Если в режиме редактирования, добавляем кнопки "Заменить", "Добавить" и "Правка"
        if edit_mode:
            # Отладочное сообщение при создании кнопок
            self.logger.debug(f"Creating edit mode buttons with data: {prefix}events_replace, {prefix}events_append and {prefix}events_edit")
            
            replace_btn = Button.inline(self._t('btn_replace', lang=lang), data=f"{prefix}events_replace")
            append_btn = Button.inline(self._t('btn_append', lang=lang), data=f"{prefix}events_append")
            edit_btn = Button.inline(self._t('btn_edit_text', lang=lang), data=f"{prefix}events_edit")
            buttons.insert(0, [replace_btn, append_btn, edit_btn])
            
        return buttons
    
    def get_user_state(self, user_id: int) -> Optional[FormState]:
        """
        Получает текущее состояние формы пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Состояние формы или None, если пользователь не заполняет форму
        """
        return self._user_states.get(user_id)
    
    def set_user_state(self, user_id: int, state: FormState) -> None:
        """
        Устанавливает состояние формы пользователя
        
        Args:
            user_id: ID пользователя
            state: Состояние формы
        """
        self._user_states[user_id] = state
    
    def get_user_form_data(self, user_id: int) -> Dict[str, Any]:
        """
        Получает данные формы пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Данные формы пользователя
        """
        if user_id not in self._user_form_data:
            self._user_form_data[user_id] = {}
        return self._user_form_data[user_id]
    
    def set_user_form_data(self, user_id: int, data: Dict[str, Any]) -> None:
        """
        Устанавливает данные формы пользователя
        
        Args:
            user_id: ID пользователя
            data: Данные формы
        """
        self._user_form_data[user_id] = data
    
    def update_user_form_data(self, user_id: int, **kwargs) -> None:
        """
        Обновляет данные формы пользователя
        
        Args:
            user_id: ID пользователя
            **kwargs: Данные для обновления
        """
        if user_id not in self._user_form_data:
            self._user_form_data[user_id] = {}
        self._user_form_data[user_id].update(kwargs)
    
    def clear_user_data(self, user_id: int) -> None:
        """
        Очищает данные пользователя
        
        Args:
            user_id: ID пользователя
        """
        if user_id in self._user_states:
            del self._user_states[user_id]
        if user_id in self._user_form_data:
            del self._user_form_data[user_id]
    
    async def start_form(self, event, user_id: int, entry_date: date, lang: str = "ru", prefix: str = "") -> None:
        """
        Запускает форму для создания/редактирования записи
        
        Args:
            event: Событие Telegram
            user_id: ID пользователя
            entry_date: Дата записи
            lang: Язык
            prefix: Префикс для данных кнопок
        """
        # Начинаем мастер заполнения с первого шага - настроение
        self.set_user_state(user_id, FormState.WAITING_MOOD)
        self.set_user_form_data(user_id, {"entry_date": entry_date})
        
        await event.reply(
            self._t('today_mood_prompt', lang=lang) or "Какое у вас настроение?",
            buttons=self.get_mood_keyboard(lang, prefix)
        )
    
    async def start_edit_form(self, event, user_id: int, entry_date: date, lang: str = "ru", prefix: str = "", events_only: bool = False) -> None:
        """
        Запускает форму для редактирования записи
        
        Args:
            event: Событие Telegram
            user_id: ID пользователя
            entry_date: Дата записи
            lang: Язык
            prefix: Префикс для данных кнопок
            events_only: Только редактирование событий
        """
        try:
            entry = self.db.get_diary_entry(user_id, entry_date)
            
            if not entry:
                await event.edit(self._t('entry_not_found', lang=lang))
                return
            
            # Загружаем данные из существующей записи
            form_data = {
                "entry_date": entry_date,
                "edit_mode": True,
                "mood": entry.get("mood", ""),
                "weather": entry.get("weather", ""),
                "location": entry.get("location", ""),
                "events": entry.get("events", "")
            }
            
            self.set_user_form_data(user_id, form_data)
            
            # Если нужно только редактирование событий, переходим сразу к этому шагу
            if events_only:
                self.set_user_state(user_id, FormState.WAITING_EVENTS)
                
                # Отображаем текущие события
                current_events = form_data.get("events") or self._t('not_specified', lang=lang)
                
                # Отладочное сообщение
                self.logger.debug(f"Showing events form with edit_mode=True. User ID: {user_id}, Current events: {current_events}")
                
                edit_events_message = self._t('edit_events_prompt', lang=lang, events=current_events)
                await event.edit(
                    edit_events_message,
                    buttons=self.get_events_keyboard(lang, prefix, edit_mode=True)
                )
            else:
                # Начинаем с редактирования настроения
                self.set_user_state(user_id, FormState.WAITING_MOOD)
                
                # Отображаем текущее настроение
                current_mood = form_data.get("mood") or self._t('not_specified', lang=lang)
                
                edit_mood_message = self._t('edit_mood_prompt', lang=lang, mood=current_mood) or f"Текущее настроение: {current_mood}\n\nВыберите новое настроение:"
                await event.edit(
                    edit_mood_message,
                    buttons=self.get_mood_keyboard(lang, prefix)
                )
        except Exception as e:
            import traceback
            traceback_str = traceback.format_exc()
            self.logger.error(f"ERROR starting edit form: {traceback_str}")
            await event.edit(f"Ошибка при начале редактирования: {str(e)}")
    
    async def process_mood_callback(self, event, user_id: int, choice: str, lang: str = "ru", prefix: str = "") -> None:
        """
        Обрабатывает выбор настроения
        
        Args:
            event: Событие Telegram
            user_id: ID пользователя
            choice: Выбранное значение
            lang: Язык
            prefix: Префикс для данных кнопок
        """
        if self.get_user_state(user_id) != FormState.WAITING_MOOD:
            await event.answer(self._t('form_invalid_state', lang=lang))
            return
        
        # Обработка выбора
        if choice == "back":
            # Для настроения нет предыдущего шага
            await event.answer(self._t('form_first_step', lang=lang))
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
            self.update_user_form_data(user_id, mood=mood_mapping.get(choice))
        
        # Переходим к следующему шагу - погода
        self.set_user_state(user_id, FormState.WAITING_WEATHER)
        
        # Для режима редактирования показываем текущее значение
        form_data = self.get_user_form_data(user_id)
        if form_data.get("edit_mode"):
            # Безопасно получаем текущее значение погоды
            current_weather = form_data.get("weather") or self._t('not_specified', lang=lang)
                
            # Исправляем вызов метода локализации, передавая параметр weather напрямую
            edit_weather_message = self._t('edit_weather_prompt', lang=lang, weather=current_weather)
            if not edit_weather_message:
                edit_weather_message = f"Текущая погода:\n\n{current_weather}\n\nВыберите новую погоду:"
                
            await event.edit(
                edit_weather_message,
                buttons=self.get_weather_keyboard(lang, prefix)
            )
        else:
            await event.edit(
                self._t('today_weather_prompt', lang=lang) or "Какая погода?",
                buttons=self.get_weather_keyboard(lang, prefix)
            )
    
    async def process_weather_callback(self, event, user_id: int, choice: str, lang: str = "ru", prefix: str = "") -> None:
        """
        Обрабатывает выбор погоды
        
        Args:
            event: Событие Telegram
            user_id: ID пользователя
            choice: Выбранное значение
            lang: Язык
            prefix: Префикс для данных кнопок
        """
        if self.get_user_state(user_id) != FormState.WAITING_WEATHER:
            await event.answer(self._t('form_invalid_state', lang=lang))
            return
        
        # Обработка выбора
        if choice == "back":
            # Возвращаемся к предыдущему шагу - настроение
            self.set_user_state(user_id, FormState.WAITING_MOOD)
            
            # Для режима редактирования показываем текущее значение
            form_data = self.get_user_form_data(user_id)
            if form_data.get("edit_mode"):
                current_mood = form_data.get("mood") or self._t('not_specified', lang=lang)
                
                edit_mood_message = self._t('edit_mood_prompt', lang=lang, mood=current_mood)
                if not edit_mood_message:
                    edit_mood_message = f"Текущее настроение:\n\n{current_mood}\n\nВыберите новое настроение:"
                    
                await event.edit(
                    edit_mood_message,
                    buttons=self.get_mood_keyboard(lang, prefix)
                )
            else:
                await event.edit(
                    self._t('today_mood_prompt', lang=lang) or "Какое у вас настроение?",
                    buttons=self.get_mood_keyboard(lang, prefix)
                )
            return
        
        if choice == "manual":
            # Обработка ввода погоды вручную
            self.update_user_form_data(user_id, waiting_manual_weather=True)
            self.logger.debug(f"Manual weather input mode activated. User ID: {user_id}")
            await event.edit(
                (self._t('today_weather_manual', lang=lang) or "Введите описание погоды:") + 
                "\n\n" + self._t('type_cancel_to_abort', lang=lang)
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
            self.update_user_form_data(user_id, weather=weather_mapping.get(choice))
        
        # Переходим к следующему шагу - местоположение
        self.set_user_state(user_id, FormState.WAITING_LOCATION)
        
        # Для режима редактирования показываем текущее значение
        form_data = self.get_user_form_data(user_id)
        if form_data.get("edit_mode"):
            current_location = form_data.get("location") or self._t('not_specified', lang=lang)
            
            # Исправляем вызов метода локализации, передавая параметр location напрямую
            edit_location_message = self._t('edit_location_prompt', lang=lang, location=current_location)
            if not edit_location_message:
                edit_location_message = f"Текущее местоположение:\n\n{current_location}\n\nВыберите новое местоположение:"
                
            await event.edit(
                edit_location_message,
                buttons=self.get_location_keyboard(lang, prefix)
            )
        else:
            await event.edit(
                self._t('today_location_prompt', lang=lang) or "Где вы находитесь?",
                buttons=self.get_location_keyboard(lang, prefix)
            )
    
    async def process_location_callback(self, event, user_id: int, choice: str, lang: str = "ru", prefix: str = "") -> None:
        """
        Обрабатывает выбор местоположения
        
        Args:
            event: Событие Telegram
            user_id: ID пользователя
            choice: Выбранное значение
            lang: Язык
            prefix: Префикс для данных кнопок
        """
        if self.get_user_state(user_id) != FormState.WAITING_LOCATION:
            await event.answer(self._t('form_invalid_state', lang=lang))
            return
        
        # Обработка выбора
        if choice == "back":
            # Возвращаемся к предыдущему шагу - погода
            self.set_user_state(user_id, FormState.WAITING_WEATHER)
            
            # Для режима редактирования показываем текущее значение
            form_data = self.get_user_form_data(user_id)
            if form_data.get("edit_mode"):
                current_weather = form_data.get("weather") or self._t('not_specified', lang=lang)
                
                # Исправляем вызов метода локализации, передавая параметр weather напрямую
                edit_weather_message = self._t('edit_weather_prompt', lang=lang, weather=current_weather)
                if not edit_weather_message:
                    edit_weather_message = f"Текущая погода:\n\n{current_weather}\n\nВыберите новую погоду:"
                    
                await event.edit(
                    edit_weather_message,
                    buttons=self.get_weather_keyboard(lang, prefix)
                )
            else:
                await event.edit(
                    self._t('today_weather_prompt', lang=lang) or "Какая погода?",
                    buttons=self.get_weather_keyboard(lang, prefix)
                )
            return
        
        if choice == "manual":
            # Устанавливаем флаг ожидания ручного ввода местоположения
            self.update_user_form_data(user_id, waiting_manual_location=True)
            await event.edit(
                (self._t('today_location_manual', lang=lang) or "Введите ваше местоположение:") + 
                "\n\n" + self._t('type_cancel_to_abort', lang=lang)
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
            self.update_user_form_data(user_id, location=location_mapping.get(choice))
        
        # Переходим к следующему шагу - события
        self.set_user_state(user_id, FormState.WAITING_EVENTS)
        
        # Для режима редактирования показываем текущее значение
        form_data = self.get_user_form_data(user_id)
        edit_mode = form_data.get("edit_mode", False)
        
        if edit_mode:
            # Безопасно получаем текущее значение событий
            current_events = form_data.get("events") or self._t('not_specified', lang=lang)
                
            # Отладочное сообщение
            self.logger.debug(f"Showing events form with edit_mode=True. User ID: {user_id}, Current events: {current_events}")
                
            # Исправляем вызов метода локализации, передавая параметр events напрямую
            edit_events_message = self._t('edit_events_prompt', lang=lang, events=current_events)
            if not edit_events_message:
                edit_events_message = f"Текущие события:\n{current_events}.\n\nОпишите новые события (или нажмите 'Пропустить'):"
                
            await event.edit(
                edit_events_message,
                buttons=self.get_events_keyboard(lang, prefix, edit_mode=True)
            )
        else:
            await event.edit(
                self._t('today_events_prompt', lang=lang) or "Опишите события (или нажмите 'Пропустить'):",
                buttons=self.get_events_keyboard(lang, prefix, edit_mode=False)
            )
    
    async def process_events_callback(self, event, user_id: int, choice: str, lang: str = "ru", prefix: str = "") -> None:
        """
        Обрабатывает выбор для событий
        
        Args:
            event: Событие Telegram
            user_id: ID пользователя
            choice: Выбранное значение
            lang: Язык
            prefix: Префикс для данных кнопок
        """
        if self.get_user_state(user_id) != FormState.WAITING_EVENTS:
            await event.answer(self._t('form_invalid_state', lang=lang))
            return
        
        # Отладочное сообщение для всех кнопок
        self.logger.debug(f"Events callback handler called. User ID: {user_id}, Choice: {choice}")
        
        if choice == "back":
            # Возвращаемся к предыдущему шагу - местоположение
            self.set_user_state(user_id, FormState.WAITING_LOCATION)
            
            # Для режима редактирования показываем текущее значение
            form_data = self.get_user_form_data(user_id)
            if form_data.get("edit_mode"):
                current_location = form_data.get("location") or self._t('not_specified', lang=lang)
                
                # Исправляем вызов метода локализации, передавая параметр location напрямую
                edit_location_message = self._t('edit_location_prompt', lang=lang, location=current_location)
                if not edit_location_message:
                    edit_location_message = f"Текущее местоположение:\n\n{current_location}\n\nВыберите новое местоположение:"
                    
                await event.edit(
                    edit_location_message,
                    buttons=self.get_location_keyboard(lang, prefix)
                )
            else:
                await event.edit(
                    self._t('today_location_prompt', lang=lang) or "Где вы находитесь?",
                    buttons=self.get_location_keyboard(lang, prefix)
                )
            return
        
        # Новые обработчики для режима редактирования
        if choice == "replace":
            self.logger.debug(f"REPLACE button was clicked! User ID: {user_id}")
            # Устанавливаем флаг режима замены
            self.update_user_form_data(user_id, events_mode="replace")
            form_data = self.get_user_form_data(user_id)
            current_events = form_data.get("events") or ""
            
            # Отладочное сообщение
            self.logger.debug(f"Replace button clicked. User ID: {user_id}, Current events: {current_events}")
            
            replace_message = self._t('events_replace_prompt', lang=lang, events=current_events)
            if not replace_message:
                replace_message = f"Текущие события:\n\"{current_events}\"\n\nВведите новый текст, который полностью заменит текущий:"
                
            await event.edit(replace_message + "\n\n" + self._t('type_cancel_to_abort', lang=lang))
            # Ожидаем ввод пользователя, который будет обработан в handle_manual_input
            return
            
        elif choice == "append":
            # Устанавливаем флаг режима добавления
            self.update_user_form_data(user_id, events_mode="append")
            form_data = self.get_user_form_data(user_id)
            current_events = form_data.get("events") or ""
            
            append_message = self._t('events_append_prompt', lang=lang, events=current_events)
            if not append_message:
                append_message = f"Текущие события:\n\"{current_events}\"\n\nВведите текст, который будет добавлен к текущему:"
                
            await event.edit(append_message + "\n\n" + self._t('type_cancel_to_abort', lang=lang))
            # Ожидаем ввод пользователя, который будет обработан в handle_manual_input
            return
            
        elif choice == "edit":
            # Устанавливаем флаг режима редактирования
            self.update_user_form_data(user_id, events_mode="edit")
            form_data = self.get_user_form_data(user_id)
            current_events = form_data.get("events") or ""
            
            # Отладочное сообщение
            self.logger.debug(f"Edit button clicked. User ID: {user_id}, Current events: {current_events}")
            
            edit_message = self._t('events_edit_prompt', lang=lang, events=current_events)
            if not edit_message:
                edit_message = f"Текущие события:\n\"{current_events}\"\n\nОтредактируйте текст:"
                
            # Устанавливаем начальный текст для ввода пользователя
            # В Telethon нельзя напрямую установить текст в поле ввода,
            # поэтому мы просто показываем сообщение с текущим текстом,
            # который пользователь может скопировать и отредактировать
            
            await event.edit(edit_message + "\n\n" + self._t('type_cancel_to_abort', lang=lang))
            
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
            form_data = self.get_user_form_data(user_id)
            
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
            self.logger.debug(f"Saving data: {entry_data}, edit_mode: {edit_mode}")
            
            if edit_mode:
                # Обновляем существующую запись
                success = self.db.update_diary_entry(
                    user_id, 
                    form_data["entry_date"],
                    **entry_data
                )
                
                if success:
                    await event.edit(self._t('today_entry_updated', lang=lang))
                    # Отображаем содержимое обновленной записи
                    await self.display_entry_content(event, user_id, form_data["entry_date"], lang)
                else:
                    await event.edit(self._t('today_entry_update_error', lang=lang))
            else:
                # Создаем новую запись
                created = self.db.create_diary_entry(
                    user_id, 
                    form_data["entry_date"],
                    mood=entry_data.get("mood"),
                    weather=entry_data.get("weather"),
                    location=entry_data.get("location"),
                    events=entry_data.get("events")
                )
                
                if created:
                    await event.edit(self._t('today_entry_created', lang=lang))
                    # Отображаем содержимое новой записи
                    await self.display_entry_content(event, user_id, form_data["entry_date"], lang)
                else:
                    await event.edit(self._t('today_entry_error', lang=lang))
            
            # Очищаем данные пользователя
            self.clear_user_data(user_id)
                
        except Exception as e:
            import traceback
            traceback_str = traceback.format_exc()
            self.logger.error(f"{traceback_str}")
            await event.edit(f"Ошибка: {str(e)}")
    
    async def process_manual_input(self, event, user_id: int, text: str, lang: str = "ru", prefix: str = "") -> bool:
        """
        Обрабатывает ручной ввод текста
        
        Args:
            event: Событие Telegram
            user_id: ID пользователя
            text: Введенный текст
            lang: Язык
            prefix: Префикс для данных кнопок
            
        Returns:
            True, если ввод был обработан, False в противном случае
        """
        # Проверяем, что пользователь находится в процессе заполнения формы
        if user_id not in self._user_states:
            return False
        
        # Получаем текущее состояние пользователя
        state = self._user_states[user_id]
        form_data = self.get_user_form_data(user_id)
        edit_mode = form_data.get("edit_mode", False)
        
        # Проверяем, есть ли у нас команда (начинается с /)
        if text.startswith('/'):
            # Это команда, не обрабатываем ее здесь
            return False
            
        # Проверяем, ввёл ли пользователь команду отмены
        if text.lower() in ['отмена', 'cancel', '/cancel']:
            # Очищаем данные пользователя
            self.clear_user_data(user_id)
            
            # Сообщаем об отмене
            await event.reply(self._t('creation_canceled', lang=lang))
            return True
        
        # Проверяем ожидание ручного ввода погоды
        if state == FormState.WAITING_WEATHER and form_data.get("waiting_manual_weather"):
            # Сохраняем введенную погоду
            self.update_user_form_data(user_id, weather=text)
            # Удаляем флаг ожидания
            form_data = self.get_user_form_data(user_id)
            if "waiting_manual_weather" in form_data:
                del form_data["waiting_manual_weather"]
                self.set_user_form_data(user_id, form_data)
            
            # Переходим к следующему шагу - местоположение
            self.set_user_state(user_id, FormState.WAITING_LOCATION)
            
            # Для режима редактирования показываем текущее значение
            if edit_mode:
                current_location = form_data.get("location") or self._t('not_specified', lang=lang)
                
                # Исправляем вызов метода локализации, передавая параметр location напрямую
                edit_location_message = self._t('edit_location_prompt', lang=lang, location=current_location)
                if not edit_location_message:
                    edit_location_message = f"Текущее местоположение:\n\n{current_location}\n\nВыберите новое местоположение:"
                    
                await event.reply(
                    edit_location_message,
                    buttons=self.get_location_keyboard(lang, prefix)
                )
            else:
                await event.reply(
                    self._t('today_location_prompt', lang=lang) or "Где вы находитесь?",
                    buttons=self.get_location_keyboard(lang, prefix)
                )
            return True
            
        # Проверяем ожидание ручного ввода местоположения
        elif state == FormState.WAITING_LOCATION and form_data.get("waiting_manual_location"):
            # Сохраняем введенное местоположение
            self.update_user_form_data(user_id, location=text)
            # Удаляем флаг ожидания
            form_data = self.get_user_form_data(user_id)
            if "waiting_manual_location" in form_data:
                del form_data["waiting_manual_location"]
                self.set_user_form_data(user_id, form_data)
            
            # Переходим к следующему шагу - события
            self.set_user_state(user_id, FormState.WAITING_EVENTS)
            
            # Для режима редактирования показываем текущее значение
            if edit_mode:
                current_events = form_data.get("events") or self._t('not_specified', lang=lang)
                
                # Отладочное сообщение
                self.logger.debug(f"Showing events edit form with edit_mode=True. User ID: {user_id}, Current events: {current_events}")
                
                # Исправляем вызов метода локализации, передавая параметр events напрямую
                edit_events_message = self._t('edit_events_prompt', lang=lang, events=current_events)
                if not edit_events_message:
                    edit_events_message = f"Текущие события:\n{current_events}.\n\nОпишите новые события (или нажмите 'Пропустить'):"
                    
                await event.reply(
                    edit_events_message,
                    buttons=self.get_events_keyboard(lang, prefix, edit_mode=True)
                )
            else:
                await event.reply(
                    self._t('today_events_prompt', lang=lang) or "Опишите события (или нажмите 'Пропустить'):",
                    buttons=self.get_events_keyboard(lang, prefix, edit_mode=False)
                )
            return True
            
        # Если мы ожидаем ввод событий
        elif state == FormState.WAITING_EVENTS:
            # Проверяем режим редактирования событий
            events_mode = form_data.get("events_mode", "replace")
            
            if events_mode == "append" and "events" in form_data and form_data["events"]:
                # Добавляем текст к существующему
                current_events = form_data["events"]
                self.update_user_form_data(user_id, events=current_events + "\n" + text)
            elif events_mode == "edit":
                # Просто заменяем текст на введенный пользователем
                self.update_user_form_data(user_id, events=text)
            else:
                # Заменяем текст или создаем новый (для режима "replace")
                self.update_user_form_data(user_id, events=text)
                
            # Удаляем флаг режима редактирования событий, если он есть
            form_data = self.get_user_form_data(user_id)
            if "events_mode" in form_data:
                del form_data["events_mode"]
                self.set_user_form_data(user_id, form_data)
            
            # Завершаем заполнение формы и сохраняем данные
            try:
                form_data = self.get_user_form_data(user_id)
                
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
                self.logger.debug(f"Saving data from text input: {entry_data}, edit_mode: {edit_mode}")
                
                if edit_mode:
                    # Обновляем существующую запись
                    success = self.db.update_diary_entry(
                        user_id, 
                        form_data["entry_date"],
                        **entry_data
                    )
                    
                    if success:
                        await event.reply(self._t('today_entry_updated', lang=lang))
                        # Отображаем содержимое обновленной записи
                        await self.display_entry_content(event, user_id, form_data["entry_date"], lang)
                    else:
                        await event.reply(self._t('today_entry_update_error', lang=lang))
                else:
                    # Создаем новую запись
                    created = self.db.create_diary_entry(
                        user_id, 
                        form_data["entry_date"],
                        mood=entry_data.get("mood"),
                        weather=entry_data.get("weather"),
                        location=entry_data.get("location"),
                        events=entry_data.get("events")
                    )
                    
                    if created:
                        await event.reply(self._t('today_entry_created', lang=lang))
                        # Отображаем содержимое новой записи
                        await self.display_entry_content(event, user_id, form_data["entry_date"], lang)
                    else:
                        await event.reply(self._t('today_entry_error', lang=lang))
                
                # Очищаем данные пользователя
                self.clear_user_data(user_id)
                    
            except Exception as e:
                await event.reply(f"Ошибка: {str(e)}")
                
            return True
        
        return False
    
    async def check_existing_entry(self, event, user_id: int, entry_date: date, lang: str = "ru", prefix: str = "") -> bool:
        """
        Проверяет наличие существующей записи и предлагает ее редактирование
        
        Args:
            event: Событие Telegram
            user_id: ID пользователя
            entry_date: Дата записи
            lang: Язык
            prefix: Префикс для данных кнопок
            
        Returns:
            True, если запись существует, False в противном случае
        """
        entry = self.db.get_diary_entry(user_id, entry_date)
        
        # Добавляем отладочную информацию
        self.logger.debug(f"Entry from DB for {entry_date} command: {entry}")
        
        if entry:
            # Добавляем inline-кнопки для редактирования существующей записи
            buttons = [
                [
                    Button.inline(self._t('btn_edit', lang=lang), data=f"edit_{prefix}"),
                    Button.inline(self._t('btn_edit_events_only', lang=lang), data=f"edit_{prefix}_events"),
                    Button.inline(self._t('btn_cancel', lang=lang), data=f"cancel_edit_{prefix}")
                ]
            ]
            
            # Добавляем отладочную информацию для кнопок
            self.logger.debug(f"Creating buttons for edit options. User ID: {user_id}")
            
            # Определяем правильный ключ для сообщения в зависимости от префикса
            entry_exists_key = f'{prefix.rstrip("_")}_entry_exists_edit' if prefix else 'today_entry_exists_edit'
            
            await event.reply(
                self._t(entry_exists_key, lang=lang) or f"Запись уже существует. Хотите отредактировать её?",
                buttons=buttons
            )
            return True
        
        return False