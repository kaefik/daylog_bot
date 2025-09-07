"""
Модуль для работы с базой данных SQLite
Содержит все операции CRUD для дневникового бота
Основной DatabaseManager
"""

import sqlite3
import logging
from datetime import datetime, date
from typing import Optional, Dict, List, Tuple
from contextlib import contextmanager
import os

# Настройка логирования
logger = logging.getLogger(__name__)

# Настройка адаптеров для SQLite (исправляет deprecation warnings в Python 3.12+)
def adapt_date_iso(val):
    """Адаптер для преобразования date в ISO формат"""
    return val.isoformat()

def adapt_datetime_iso(val):
    """Адаптер для преобразования datetime в ISO формат"""
    return val.isoformat()

def convert_date(val):
    """Конвертер для преобразования ISO строки обратно в date"""
    return date.fromisoformat(val.decode())

def convert_datetime(val):
    """Конвертер для преобразования ISO строки обратно в datetime"""
    return datetime.fromisoformat(val.decode())

# Регистрация адаптеров
sqlite3.register_adapter(date, adapt_date_iso)
sqlite3.register_adapter(datetime, adapt_datetime_iso)
sqlite3.register_converter("date", convert_date)
sqlite3.register_converter("datetime", convert_datetime)

class DatabaseManager:
    """Основной класс для работы с базой данных"""
    
    def __init__(self, db_path: str = "diary_bot.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Создание всех необходимых таблиц"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Создание таблицы users
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        language_code TEXT DEFAULT 'ru',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1,
                        timezone TEXT DEFAULT 'Europe/Moscow'
                    )
                ''')
                
                # Создание таблицы diary_entries
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS diary_entries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        entry_date DATE NOT NULL,
                        mood TEXT,
                        weather TEXT,
                        location TEXT,
                        events TEXT,
                        additional_notes TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        
                        FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
                        CONSTRAINT unique_user_date UNIQUE (user_id, entry_date)
                    )
                ''')
                
                # Создание индексов для оптимизации
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_diary_entries_user_date 
                    ON diary_entries (user_id, entry_date DESC)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_diary_entries_date 
                    ON diary_entries (entry_date DESC)
                ''')
                
                # Создание таблицы настроек
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_settings (
                        user_id INTEGER PRIMARY KEY,
                        reminder_time TEXT DEFAULT '21:00',
                        reminder_enabled BOOLEAN DEFAULT 1,
                        auto_backup_enabled BOOLEAN DEFAULT 0,
                        backup_frequency INTEGER DEFAULT 7,
                        export_format TEXT DEFAULT 'markdown',
                        date_format TEXT DEFAULT 'DD.MM.YYYY',
                        
                        FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
                    )
                ''')
                
                # Создание системной таблицы
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_info (
                        key TEXT PRIMARY KEY,
                        value TEXT,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Вставка начальных системных данных
                cursor.execute('''
                    INSERT OR IGNORE INTO system_info (key, value) VALUES 
                        ('db_version', '1.0'),
                        ('created_at', datetime('now'))
                ''')
                
                conn.commit()
                logger.info("База данных успешно инициализирована")
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка инициализации БД: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Безопасное подключение к базе данных"""
        conn = None
        try:
            conn = sqlite3.connect(
                self.db_path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            conn.row_factory = sqlite3.Row  # Доступ к колонкам по имени
            
            # Включение внешних ключей
            conn.execute("PRAGMA foreign_keys = ON")
            
            yield conn
            
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Ошибка подключения к БД: {e}")
            raise
        finally:
            if conn:
                conn.close()
        
    # Методы для работы с пользователями
    def create_user(self, user_id: int, username: str = None, 
                first_name: str = None, last_name: str = None) -> bool:
        """Создание нового пользователя"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO users 
                    (user_id, username, first_name, last_name, last_activity)
                    VALUES (?, ?, ?, ?, datetime('now'))
                ''', (user_id, username, first_name, last_name))
                
                # Создание настроек по умолчанию
                cursor.execute('''
                    INSERT OR IGNORE INTO user_settings (user_id) VALUES (?)
                ''', (user_id,))
                
                conn.commit()
                logger.info(f"Пользователь {user_id} создан/обновлен")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка создания пользователя {user_id}: {e}")
            return False

    def get_user(self, user_id: int) -> Optional[Dict]:
        """Получение информации о пользователе"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT u.*, s.reminder_time, s.reminder_enabled, s.date_format
                    FROM users u
                    LEFT JOIN user_settings s ON u.user_id = s.user_id
                    WHERE u.user_id = ?
                ''', (user_id,))
                
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения пользователя {user_id}: {e}")
            return None

    def update_user_activity(self, user_id: int):
        """Обновление времени последней активности"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE users SET last_activity = datetime('now')
                    WHERE user_id = ?
                ''', (user_id,))
                
                conn.commit()
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка обновления активности {user_id}: {e}")
    
    # Методы для работы с записями дневника
    def create_diary_entry(self, user_id: int, entry_date: date, 
                      mood: str = None, weather: str = None,
                      location: str = None, events: str = None) -> bool:
        """Создание новой записи дневника"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO diary_entries 
                    (user_id, entry_date, mood, weather, location, events, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                ''', (user_id, entry_date, mood, weather, location, events))
                
                conn.commit()
                logger.info(f"Запись {entry_date} для пользователя {user_id} создана")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка создания записи {entry_date}: {e}")
            return False

    def get_diary_entry(self, user_id: int, entry_date: date) -> Optional[Dict]:
        """Получение записи дневника за конкретную дату"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM diary_entries 
                    WHERE user_id = ? AND entry_date = ?
                ''', (user_id, entry_date))
                
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения записи {entry_date}: {e}")
            return None

    def update_diary_entry(self, user_id: int, entry_date: date, **kwargs) -> bool:
        """Обновление существующей записи дневника"""
        if not kwargs:
            return False
        
        # Построение динамического запроса
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values())
        values.append(datetime.now())  # для updated_at
        values.extend([user_id, entry_date])  # для WHERE условия
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = f'''
                    UPDATE diary_entries 
                    SET {set_clause}, updated_at = ?
                    WHERE user_id = ? AND entry_date = ?
                '''
                
                cursor.execute(query, values)
                
                if cursor.rowcount == 0:
                    logger.warning(f"Запись {entry_date} не найдена для обновления")
                    return False
                
                conn.commit()
                logger.info(f"Запись {entry_date} обновлена")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка обновления записи {entry_date}: {e}")
            return False
    
    def delete_diary_entry(self, user_id: int, entry_date: date) -> bool:
        pass
    
    # Методы для работы с настройками
    def get_user_settings(self, user_id: int) -> Dict:
        pass
    
    def update_user_settings(self, user_id: int, **kwargs) -> bool:
        pass

    def get_user_statistics(self, user_id: int) -> Dict:
        """Получение статистики пользователя"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Общая статистика
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_entries,
                        MIN(entry_date) as first_entry,
                        MAX(entry_date) as last_entry,
                        COUNT(DISTINCT strftime('%Y-%m', entry_date)) as months_active
                    FROM diary_entries 
                    WHERE user_id = ?
                ''', (user_id,))
                
                stats = dict(cursor.fetchone()) if cursor.rowcount > 0 else {}
                
                # Статистика по настроениям (если записываются)
                cursor.execute('''
                    SELECT mood, COUNT(*) as count
                    FROM diary_entries 
                    WHERE user_id = ? AND mood IS NOT NULL
                    GROUP BY mood
                    ORDER BY count DESC
                ''', (user_id,))
                
                mood_stats = [dict(row) for row in cursor.fetchall()]
                stats['mood_distribution'] = mood_stats
                
                return stats
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {}
