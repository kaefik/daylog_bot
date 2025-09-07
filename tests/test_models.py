"""
Тесты для моделей данных
"""

import unittest
from datetime import date, datetime
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.models import (
    User, UserCreate, UserUpdate,
    DiaryEntry, DiaryEntryCreate, DiaryEntryUpdate,
    UserSettings, UserSettingsCreate, UserSettingsUpdate,
    MoodLevel, WeatherType, ExportFormat, DateFormat,
    DiaryEntryPeriod, UserStatistics, ErrorResponse
)


class TestModels(unittest.TestCase):
    """Тесты моделей данных"""
    
    def test_user_creation(self):
        """Тест создания пользователя"""
        user_data = {
            "user_id": 12345,
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "language_code": "ru",
            "timezone": "Europe/Moscow"
        }
        
        user = UserCreate(**user_data)
        self.assertEqual(user.user_id, 12345)
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.language_code, "ru")
    
    def test_diary_entry_creation(self):
        """Тест создания записи дневника"""
        entry_data = {
            "user_id": 12345,
            "entry_date": date.today(),
            "mood": MoodLevel.GOOD,
            "weather": WeatherType.SUNNY,
            "location": "Дом",
            "events": "Тестовый день"
        }
        
        entry = DiaryEntryCreate(**entry_data)
        self.assertEqual(entry.user_id, 12345)
        self.assertEqual(entry.mood, MoodLevel.GOOD)
        self.assertEqual(entry.weather, WeatherType.SUNNY)
    
    def test_user_settings_creation(self):
        """Тест создания настроек пользователя"""
        settings_data = {
            "user_id": 12345,
            "reminder_time": "21:00",
            "reminder_enabled": True,
            "export_format": ExportFormat.MARKDOWN,
            "date_format": DateFormat.DD_MM_YYYY
        }
        
        settings = UserSettingsCreate(**settings_data)
        self.assertEqual(settings.user_id, 12345)
        self.assertEqual(settings.reminder_time, "21:00")
        self.assertEqual(settings.export_format, ExportFormat.MARKDOWN)
    
    def test_diary_entry_period_validation(self):
        """Тест валидации периода записей"""
        # Валидный период
        period = DiaryEntryPeriod(
            user_id=12345,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        self.assertEqual(period.user_id, 12345)
        
        # Невалидный период (начальная дата больше конечной)
        with self.assertRaises(ValueError):
            DiaryEntryPeriod(
                user_id=12345,
                start_date=date(2024, 1, 31),
                end_date=date(2024, 1, 1)
            )
    
    def test_enum_values(self):
        """Тест значений enum"""
        self.assertEqual(MoodLevel.EXCELLENT.value, "Отлично")
        self.assertEqual(WeatherType.SUNNY.value, "Солнечно")
        self.assertEqual(ExportFormat.MARKDOWN.value, "markdown")
        self.assertEqual(DateFormat.DD_MM_YYYY.value, "DD.MM.YYYY")
    
    def test_user_statistics(self):
        """Тест статистики пользователя"""
        stats = UserStatistics(
            total_entries=100,
            first_entry=date(2024, 1, 1),
            last_entry=date.today(),
            months_active=12,
            mood_distribution=[
                {"mood": "Хорошо", "count": 50},
                {"mood": "Отлично", "count": 30}
            ]
        )
        
        self.assertEqual(stats.total_entries, 100)
        self.assertEqual(len(stats.mood_distribution), 2)
    
    def test_error_response(self):
        """Тест модели ошибки"""
        error = ErrorResponse(
            error="ValidationError",
            message="Неверные данные",
            details={"field": "user_id", "value": "invalid"}
        )
        
        self.assertEqual(error.error, "ValidationError")
        self.assertIsNotNone(error.details)
    
    def test_model_serialization(self):
        """Тест сериализации моделей"""
        user = UserCreate(
            user_id=12345,
            username="testuser",
            first_name="Test"
        )
        
        # Проверяем, что модель можно сериализовать в словарь
        user_dict = user.model_dump()
        self.assertIn("user_id", user_dict)
        self.assertIn("username", user_dict)
        
        # Проверяем, что модель можно сериализовать в JSON
        user_json = user.model_dump_json()
        self.assertIsInstance(user_json, str)
        self.assertIn("12345", user_json)


if __name__ == '__main__':
    unittest.main()
