"""
Модуль для экспорта данных дневника в различные форматы
"""

import os
import logging
from datetime import datetime, date, timedelta
import calendar
from typing import List, Dict, Optional, Tuple, Any
import json
from pathlib import Path

# Настройка логирования
logger = logging.getLogger(__name__)

class DiaryExportManager:
    """
    Класс для экспорта записей дневника в различные форматы
    """
    
    def __init__(self, database_manager, export_dir: str = "data/exports"):
        """
        Инициализация менеджера экспорта
        
        Args:
            database_manager: Экземпляр DatabaseManager для доступа к записям
            export_dir: Директория для сохранения экспортированных файлов
        """
        self.db_manager = database_manager
        self.export_dir = export_dir
        
        # Создаем директорию для экспорта, если она не существует
        os.makedirs(self.export_dir, exist_ok=True)
    
    def export_markdown(self, user_id: int, entries: List[Dict], 
                       title: str = "Мой дневник") -> Tuple[str, str]:
        """
        Экспорт записей в формате Markdown
        
        Args:
            user_id: ID пользователя
            entries: Список записей для экспорта
            title: Заголовок документа
            
        Returns:
            Tuple[str, str]: (имя файла, путь к файлу)
        """
        if not entries:
            logger.warning(f"Нет записей для экспорта в Markdown для пользователя {user_id}")
            return "", ""
        
        try:
            # Сортируем записи по дате (от новых к старым)
            sorted_entries = sorted(entries, key=lambda x: x.get('entry_date'), reverse=True)
            
            # Форматируем текущую дату для имени файла
            now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"diary_export_{user_id}_{now_str}.md"
            filepath = os.path.join(self.export_dir, filename)
            
            # Создаем содержимое Markdown файла
            content = f"# {title}\n\n"
            content += f"Экспортировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
            
            # Добавляем каждую запись
            for entry in sorted_entries:
                # Обрабатываем дату записи
                entry_date = entry.get('entry_date')
                if isinstance(entry_date, str):
                    entry_date = datetime.fromisoformat(entry_date).date()
                
                date_formatted = entry_date.strftime("%d.%m.%Y")
                
                # Получаем данные из записи
                mood = entry.get("mood") or "Не указано"
                weather = entry.get("weather") or "Не указано"
                location = entry.get("location") or "Не указано"
                events = entry.get("events") or "Не указано"
                additional_notes = entry.get("additional_notes") or ""
                
                # Форматируем запись в Markdown
                content += f"## Запись от {date_formatted}\n\n"
                content += f"### Настроение\n{mood}\n\n"
                content += f"### Погода\n{weather}\n\n"
                content += f"### Местоположение\n{location}\n\n"
                content += f"### События дня\n{events}\n\n"
                
                if additional_notes:
                    content += f"### Дополнительные заметки\n{additional_notes}\n\n"
                
                content += "---\n\n"  # Разделитель между записями
            
            # Записываем в файл
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Экспорт в Markdown успешно создан: {filepath}")
            return filename, filepath
        
        except Exception as e:
            logger.error(f"Ошибка при экспорте в Markdown: {e}")
            return "", ""
    
    def get_today_entries(self, user_id: int) -> List[Dict]:
        """Получение записей за сегодня"""
        today = date.today()
        return self.db_manager.get_entries_by_period(user_id, today, today)
    
    def get_week_entries(self, user_id: int) -> List[Dict]:
        """Получение записей за текущую неделю"""
        today = date.today()
        # Получаем номер дня недели (0 - понедельник, 6 - воскресенье)
        weekday = today.weekday()
        # Начало недели (понедельник)
        start_of_week = today - timedelta(days=weekday)
        # Конец недели (воскресенье)
        end_of_week = start_of_week + timedelta(days=6)
        
        return self.db_manager.get_entries_by_period(user_id, start_of_week, end_of_week)
    
    def get_month_entries(self, user_id: int) -> List[Dict]:
        """Получение записей за текущий месяц"""
        today = date.today()
        # Первый день месяца
        start_of_month = date(today.year, today.month, 1)
        # Последний день месяца
        _, last_day = calendar.monthrange(today.year, today.month)
        end_of_month = date(today.year, today.month, last_day)
        
        return self.db_manager.get_entries_by_period(user_id, start_of_month, end_of_month)
    
    def get_all_entries(self, user_id: int) -> List[Dict]:
        """Получение всех записей пользователя"""
        try:
            # Получаем минимальную и максимальную даты записей пользователя
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT MIN(entry_date) as min_date, MAX(entry_date) as max_date
                    FROM diary_entries 
                    WHERE user_id = ?
                ''', (user_id,))
                
                row = cursor.fetchone()
                if not row or not row['min_date']:
                    return []
                
                min_date = row['min_date']
                max_date = row['max_date']
                
                if isinstance(min_date, str):
                    min_date = datetime.fromisoformat(min_date).date()
                if isinstance(max_date, str):
                    max_date = datetime.fromisoformat(max_date).date()
                
                return self.db_manager.get_entries_by_period(user_id, min_date, max_date)
        
        except Exception as e:
            logger.error(f"Ошибка при получении всех записей: {e}")
            return []
    
    def get_entries_by_custom_period(self, user_id: int, start_date: date, end_date: date) -> List[Dict]:
        """Получение записей за произвольный период"""
        return self.db_manager.get_entries_by_period(user_id, start_date, end_date)