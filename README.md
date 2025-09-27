# 📝 daylog_bot

Телеграм-бот для ведения личного дневника с поддержкой мультиязычности, напоминаниями и экспортом данных. Бот построен на модульной архитектуре с плагинами, что позволяет легко расширять функциональность.

![license](https://img.shields.io/badge/license-MIT-green)

## 📋 Возможности

- **Ведение дневника** — запись и просмотр ежедневных заметок
- **Многоязычность** — поддержка русского, английского, татарского, башкирского языков
- **Экспорт данных** — выгрузка записей в различные форматы
- **Напоминания** — уведомления о необходимости вести дневник
- **Админ-функции** — управление пользователями и системой

## ⚙️ Быстрый старт

1. **Клонируйте и установите зависимости:**
   ```bash
   git clone git@github.com:kaefik/daylog_bot.git
   cd daylog_bot
   uv sync
   # Для разработки:
   uv sync --extra dev
   ```

2. **Создайте конфиг:**
   ```bash
   cp cfg/config_tlg_example.py cfg/config_tlg.py
   # и заполните свои значения (API_ID, HASH, TOKEN, ADMINS...)
   ```

3. **Запуск:**
   ```bash
   uv run -m bot.start_tlgbotcore
   ```

## 🏗️ Архитектура

Проект построен на плагинной архитектуре с использованием инверсии зависимостей:

```
┌───────────────────┐     ┌──────────────┐     ┌───────────────┐
│  Telegram API     │────▶│  tlgbotcore  │────▶│    Plugins    │
│  (через Telethon) │     │ (фреймворк)  │     │  (команды)    │
└───────────────────┘     └──────────────┘     └───────┬───────┘
                                │                      │
                                │                      │
                                ▼                      ▼
                          ┌──────────────┐     ┌───────────────┐
                          │    Core      │◀────│  Database     │
                          │ (бизнес-     │     │  (SQLite)     │
                          │  логика)     │     │               │
                          └──────────────┘     └───────────────┘
```

### Основные компоненты

- **tlgbotcore** — фреймворк для Telegram-ботов с плагинной системой и контейнером внедрения зависимостей
- **plugins_bot** — отдельные плагины для команд и функциональности бота
- **core** — бизнес-логика и модели данных для приложения дневника
- **database** — слой доступа к данным через SQLite

## 🔧 Разработка

### Качество кода

```bash
uv run ruff check .        # линтер
uv run ruff format .       # автоформат
uv run mypy bot/           # типизация
uv run pytest              # тесты
```

### Структура плагинов

Плагины загружаются из директории `bot/plugins_bot/`. Каждый плагин получает доступ к глобальному объекту `tlgbot`:

```python
# Пример структуры плагина (plugins_bot/today/today.py)
from telethon import events, Button
from bot.require_diary_user import require_diary_user

tlgbot = globals().get('tlgbot')
logger = globals().get('logger')

@tlgbot.on(events.NewMessage(pattern=r'/today'))
@require_diary_user  # Декоратор авторизации
async def handler(event):
    # Реализация команды
```

### Система меню

Проект использует inline-меню для удобной навигации. Подробная документация в [docs/menu_system_howto.md](docs/menu_system_howto.md).

Пример добавления пункта меню:

```python
from bot.menu_system import register_menu

register_menu({
    'key': 'new_feature',         # Уникальный ключ
    'tr_key': 'menu_new_feature', # Ключ локализации
    'plugin': 'my_plugin',        # Имя плагина
    'handler': 'feature_handler', # Функция-обработчик
    'order': 100                  # Порядок отображения
})
```

### Локализация (i18n)

Переводы хранятся в JSON файлах в `bot/locales/`. Использование в коде:

```python
message = tlgbot.i18n.t('entry_title', lang=lang, date=date_str)
```

### База данных

Бот использует SQLite для хранения настроек и записей дневника:

```python
from core.database.manager import DatabaseManager
from cfg.config_tlg import DAYLOG_DB_PATH

db = DatabaseManager(db_path=DAYLOG_DB_PATH)
entry = db.get_diary_entry(user_id, entry_date)
```

## 📁 Важные файлы

- `/bot/tlgbotcore/_core.py` — ядро фреймворка для бота
- `/core/models.py` — модели данных для записей дневника
- `/core/database/manager.py` — операции с базой данных
- `/bot/plugins_bot/` — все команды/функции бота в виде плагинов
- `/cfg/config_tlg.py` — конфигурация (создается из примера)

## 🚀 Добавление новой функциональности

### Создание нового плагина

1. Создайте директорию в `bot/plugins_bot/`
2. Добавьте файлы плагина с обработчиками команд
3. Используйте глобальный объект `tlgbot` для регистрации обработчиков
4. Добавьте переводы в JSON файлы в `bot/locales/`

### Создание новой команды

Пример минимального плагина с новой командой:

```python
# bot/plugins_bot/myfeature/myfeature.py
from telethon import events

tlgbot = globals().get('tlgbot')
logger = globals().get('logger')

@tlgbot.on(events.NewMessage(pattern=r'/myfeature'))
async def myfeature_handler(event):
    """Обработка команды /myfeature"""
    user_id = event.sender_id
    await event.respond("Новая функция работает!")
    
    # Для доступа к базе данных:
    # from core.database.manager import DatabaseManager
    # from cfg.config_tlg import DAYLOG_DB_PATH
    # db = DatabaseManager(db_path=DAYLOG_DB_PATH)
```

## 📄 Лицензия

Проект распространяется под лицензией MIT. См. файл [LICENSE](LICENSE) для деталей.