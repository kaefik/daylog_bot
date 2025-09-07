import unittest
from datetime import date, datetime
import os
import sys
import tempfile

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database.manager import DatabaseManager

class TestDatabaseManager(unittest.TestCase):
    
    def setUp(self):
        """Создание временной БД для тестов"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db = DatabaseManager(self.temp_db.name)
        
    def tearDown(self):
        """Удаление временной БД"""
        os.unlink(self.temp_db.name)
    
    def test_create_user(self):
        """Тест создания пользователя"""
        result = self.db.create_user(12345, "testuser", "Test", "User")
        self.assertTrue(result)
        
        user = self.db.get_user(12345)
        self.assertIsNotNone(user)
        self.assertEqual(user['username'], "testuser")
    
    def test_diary_entry_crud(self):
        """Тест CRUD операций с записями"""
        user_id = 12345
        test_date = date.today()
        
        # Создание пользователя
        self.db.create_user(user_id)
        
        # Создание записи
        result = self.db.create_diary_entry(
            user_id, test_date,
            mood="Отлично", weather="Солнечно", 
            location="Дом", events="Тестовый день"
        )
        self.assertTrue(result)
        
        # Получение записи
        entry = self.db.get_diary_entry(user_id, test_date)
        self.assertIsNotNone(entry)
        self.assertEqual(entry['mood'], "Отлично")
        
        # Обновление записи
        result = self.db.update_diary_entry(
            user_id, test_date, mood="Хорошо"
        )
        self.assertTrue(result)
        
        # Проверка обновления
        entry = self.db.get_diary_entry(user_id, test_date)
        self.assertEqual(entry['mood'], "Хорошо")
    
    def test_unique_constraint(self):
        """Тест уникальности записи на дату"""
        user_id = 12345
        test_date = date.today()
        
        self.db.create_user(user_id)
        
        # Первая запись
        result1 = self.db.create_diary_entry(user_id, test_date, mood="Первая")
        self.assertTrue(result1)
        
        # Вторая запись на ту же дату (должна заменить первую)
        result2 = self.db.create_diary_entry(user_id, test_date, mood="Вторая")
        self.assertTrue(result2)
        
        entry = self.db.get_diary_entry(user_id, test_date)
        self.assertEqual(entry['mood'], "Вторая")

if __name__ == '__main__':
    unittest.main()