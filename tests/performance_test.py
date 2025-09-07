"""
Скрипт для проверки производительности

"""

import time
from datetime import date, timedelta
from database import DatabaseManager

def test_performance():
    """Тест производительности операций с БД"""
    db = DatabaseManager("test_performance.db")
    user_id = 12345
    
    db.create_user(user_id)
    
    # Тест вставки множества записей
    start_time = time.time()
    start_date = date.today() - timedelta(days=365)
    
    for i in range(365):
        test_date = start_date + timedelta(days=i)
        db.create_diary_entry(
            user_id, test_date,
            mood=f"День {i}",
            weather="Переменно",
            location="Тест",
            events=f"События дня {i}"
        )
    
    insert_time = time.time() - start_time
    print(f"Вставка 365 записей: {insert_time:.2f} секунд")
    
    # Тест поиска записей
    start_time = time.time()
    
    for i in range(50):
        test_date = start_date + timedelta(days=i * 7)
        entry = db.get_diary_entry(user_id, test_date)
    
    search_time = time.time() - start_time
    print(f"Поиск 50 записей: {search_time:.2f} секунд")
    
    # Тест получения периода
    start_time = time.time()
    entries = db.get_entries_by_period(
        user_id, 
        date.today() - timedelta(days=30), 
        date.today()
    )
    period_time = time.time() - start_time
    print(f"Получение записей за месяц ({len(entries)} записей): {period_time:.2f} секунд")

if __name__ == '__main__':
    test_performance()