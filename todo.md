# TODO - Исправление ошибок в тестах базы данных

## Выполненные задачи ✅

### 1. Исправление ошибки импорта
**Проблема**: `ImportError: attempted relative import with no known parent package`
- **Файл**: `tests/test_database.py`
- **Решение**: 
  - Заменил относительный импорт `from ..core.database.manager import DatabaseManager` на абсолютный
  - Добавил код для добавления корневой директории проекта в `sys.path`
  - Добавил импорт `sys` и `os` модулей

```python
# Добавлено в начало файла
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database.manager import DatabaseManager
```

### 2. Исправление ошибки отступов в DatabaseManager
**Проблема**: `IndentationError: expected an indented block after function definition`
- **Файл**: `core/database/manager.py`
- **Функция**: `create_diary_entry`
- **Решение**: Исправил неправильные отступы в docstring и теле функции

### 3. Исправление логики обновления записей
**Проблема**: Тест `test_diary_entry_crud` падал при обновлении записи
- **Файл**: `core/database/manager.py`
- **Функция**: `update_diary_entry`
- **Решение**: Исправил порядок параметров в SQL запросе
  - `values.append(datetime.now())` для `updated_at`
  - `values.extend([user_id, entry_date])` для WHERE условия

### 4. Устранение предупреждений SQLite (Python 3.12+)
**Проблема**: `DeprecationWarning: The default date adapter is deprecated`
- **Файл**: `core/database/manager.py`
- **Решение**: 
  - Добавил кастомные адаптеры для `date` и `datetime`
  - Зарегистрировал адаптеры и конвертеры для SQLite
  - Обновил метод `get_connection()` для использования `detect_types`

```python
# Добавленные адаптеры
def adapt_date_iso(val):
    return val.isoformat()

def adapt_datetime_iso(val):
    return val.isoformat()

def convert_date(val):
    return date.fromisoformat(val.decode())

def convert_datetime(val):
    return datetime.fromisoformat(val.decode())

# Регистрация
sqlite3.register_adapter(date, adapt_date_iso)
sqlite3.register_adapter(datetime, adapt_datetime_iso)
sqlite3.register_converter("date", convert_date)
sqlite3.register_converter("datetime", convert_datetime)
```

### 5. Добавление недостающего метода get_entries_by_period
**Проблема**: `AttributeError: 'DatabaseManager' object has no attribute 'get_entries_by_period'`
- **Файл**: `core/database/manager.py`
- **Решение**: Добавил метод `get_entries_by_period` для получения записей за определенный период

```python
def get_entries_by_period(self, user_id: int, start_date: date, end_date: date) -> List[Dict]:
    """Получение записей дневника за определенный период"""
    try:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM diary_entries 
                WHERE user_id = ? AND entry_date BETWEEN ? AND ?
                ORDER BY entry_date DESC
            ''', (user_id, start_date, end_date))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
    except sqlite3.Error as e:
        logger.error(f"Ошибка получения записей за период {start_date}-{end_date}: {e}")
        return []
```

## Результат
- ✅ Все 3 теста проходят успешно
- ✅ Нет ошибок импорта
- ✅ Нет предупреждений о deprecated функциях
- ✅ Тесты можно запускать командой `uv run tests/test_database.py`
- ✅ Performance тест работает корректно

## Структура тестов
Тесты покрывают следующие функции:
1. `test_create_user` - создание пользователя
2. `test_diary_entry_crud` - CRUD операции с записями дневника
3. `test_unique_constraint` - проверка уникальности записей на дату
4. `performance_test.py` - тест производительности (365 записей, поиск, получение за период)

## Файлы изменены
- `tests/test_database.py` - исправлен импорт
- `core/database/manager.py` - исправлены отступы, логика обновления, добавлены SQLite адаптеры и метод get_entries_by_period
