"""
Модели данных для дневникового бота
Использует Pydantic для валидации и сериализации данных
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class MoodLevel(str, Enum):
    """Уровни настроения"""
    EXCELLENT = "Отлично"
    GOOD = "Хорошо"
    NORMAL = "Нормально"
    BAD = "Плохо"
    TERRIBLE = "Ужасно"


class WeatherType(str, Enum):
    """Типы погоды"""
    SUNNY = "Солнечно"
    CLOUDY = "Облачно"
    RAINY = "Дождливо"
    SNOWY = "Снежно"
    WINDY = "Ветрено"
    FOGGY = "Туманно"
    STORMY = "Грозово"


class ExportFormat(str, Enum):
    """Форматы экспорта"""
    MARKDOWN = "markdown"
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"


class DateFormat(str, Enum):
    """Форматы даты"""
    DD_MM_YYYY = "DD.MM.YYYY"
    MM_DD_YYYY = "MM/DD/YYYY"
    YYYY_MM_DD = "YYYY-MM-DD"


class UserBase(BaseModel):
    """Базовая модель пользователя"""
    user_id: int = Field(..., description="Уникальный ID пользователя")
    username: Optional[str] = Field(None, description="Имя пользователя")
    first_name: Optional[str] = Field(None, description="Имя")
    last_name: Optional[str] = Field(None, description="Фамилия")
    language_code: str = Field("ru", description="Код языка")
    timezone: str = Field("Europe/Moscow", description="Часовой пояс")


class UserCreate(UserBase):
    """Модель для создания пользователя"""
    pass


class UserUpdate(BaseModel):
    """Модель для обновления пользователя"""
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None
    timezone: Optional[str] = None


class User(UserBase):
    """Полная модель пользователя"""
    created_at: datetime = Field(..., description="Дата создания")
    last_activity: datetime = Field(..., description="Последняя активность")
    is_active: bool = Field(True, description="Активен ли пользователь")
    
    model_config = ConfigDict(from_attributes=True)


class DiaryEntryBase(BaseModel):
    """Базовая модель записи дневника"""
    user_id: int = Field(..., description="ID пользователя")
    entry_date: date = Field(..., description="Дата записи")
    mood: Optional[MoodLevel] = Field(None, description="Настроение")
    weather: Optional[WeatherType] = Field(None, description="Погода")
    location: Optional[str] = Field(None, max_length=255, description="Местоположение")
    events: Optional[str] = Field(None, description="События дня")
    additional_notes: Optional[str] = Field(None, description="Дополнительные заметки")


class DiaryEntryCreate(DiaryEntryBase):
    """Модель для создания записи дневника"""
    pass


class DiaryEntryUpdate(BaseModel):
    """Модель для обновления записи дневника"""
    mood: Optional[MoodLevel] = None
    weather: Optional[WeatherType] = None
    location: Optional[str] = Field(None, max_length=255)
    events: Optional[str] = None
    additional_notes: Optional[str] = None


class DiaryEntry(DiaryEntryBase):
    """Полная модель записи дневника"""
    id: int = Field(..., description="Уникальный ID записи")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: datetime = Field(..., description="Дата обновления")
    
    model_config = ConfigDict(from_attributes=True)


class UserSettingsBase(BaseModel):
    """Базовая модель настроек пользователя"""
    user_id: int = Field(..., description="ID пользователя")
    reminder_time: str = Field("21:00", pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$", description="Время напоминания")
    reminder_enabled: bool = Field(True, description="Включены ли напоминания")
    auto_backup_enabled: bool = Field(False, description="Включено ли авторезервное копирование")
    backup_frequency: int = Field(7, ge=1, le=30, description="Частота резервного копирования (дни)")
    export_format: ExportFormat = Field(ExportFormat.MARKDOWN, description="Формат экспорта")
    date_format: DateFormat = Field(DateFormat.DD_MM_YYYY, description="Формат даты")


class UserSettingsCreate(UserSettingsBase):
    """Модель для создания настроек пользователя"""
    pass


class UserSettingsUpdate(BaseModel):
    """Модель для обновления настроек пользователя"""
    reminder_time: Optional[str] = Field(None, pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    reminder_enabled: Optional[bool] = None
    auto_backup_enabled: Optional[bool] = None
    backup_frequency: Optional[int] = Field(None, ge=1, le=30)
    export_format: Optional[ExportFormat] = None
    date_format: Optional[DateFormat] = None


class UserSettings(UserSettingsBase):
    """Полная модель настроек пользователя"""
    model_config = ConfigDict(from_attributes=True)


class SystemInfo(BaseModel):
    """Модель системной информации"""
    key: str = Field(..., description="Ключ")
    value: str = Field(..., description="Значение")
    updated_at: datetime = Field(..., description="Дата обновления")
    
    model_config = ConfigDict(from_attributes=True)


class UserStatistics(BaseModel):
    """Модель статистики пользователя"""
    total_entries: int = Field(0, description="Общее количество записей")
    first_entry: Optional[date] = Field(None, description="Дата первой записи")
    last_entry: Optional[date] = Field(None, description="Дата последней записи")
    months_active: int = Field(0, description="Количество активных месяцев")
    mood_distribution: List[Dict[str, Any]] = Field(default_factory=list, description="Распределение настроений")


class DiaryEntryWithUser(DiaryEntry):
    """Модель записи дневника с информацией о пользователе"""
    user: Optional[User] = Field(None, description="Информация о пользователе")


class UserWithSettings(User):
    """Модель пользователя с настройками"""
    settings: Optional[UserSettings] = Field(None, description="Настройки пользователя")


class DiaryEntryPeriod(BaseModel):
    """Модель для запроса записей за период"""
    user_id: int = Field(..., description="ID пользователя")
    start_date: date = Field(..., description="Начальная дата")
    end_date: date = Field(..., description="Конечная дата")
    
    def model_post_init(self, __context: Any) -> None:
        """Валидация периода"""
        if self.start_date > self.end_date:
            raise ValueError("Начальная дата не может быть больше конечной")


class DiaryEntryResponse(BaseModel):
    """Модель ответа с записями дневника"""
    entries: List[DiaryEntry] = Field(..., description="Список записей")
    total_count: int = Field(..., description="Общее количество записей")
    page: int = Field(1, ge=1, description="Номер страницы")
    per_page: int = Field(50, ge=1, le=100, description="Записей на странице")
    has_next: bool = Field(False, description="Есть ли следующая страница")
    has_prev: bool = Field(False, description="Есть ли предыдущая страница")


class DatabaseResponse(BaseModel):
    """Базовая модель ответа базы данных"""
    success: bool = Field(..., description="Успешность операции")
    message: Optional[str] = Field(None, description="Сообщение")
    data: Optional[Any] = Field(None, description="Данные")


class ErrorResponse(BaseModel):
    """Модель ошибки"""
    error: str = Field(..., description="Тип ошибки")
    message: str = Field(..., description="Сообщение об ошибке")
    details: Optional[Dict[str, Any]] = Field(None, description="Детали ошибки")
