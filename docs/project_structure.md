# Структура проекта daylog_bot

## Дерево папок проекта

```
daylog_bot/
├── bot/
│   ├── __init__.py
│   ├── require_diary_user.py
│   ├── start_tlgbotcore.py
│   ├── locales/
│   │   ├── ba_lat.json
│   │   ├── ba.json
│   │   ├── en.json
│   │   ├── ru.json
│   │   ├── tt_lat.json
│   │   └── tt.json
│   ├── plugins_bot/
│   │   ├── admin_commands/
│   │   ├── inline_button/
│   │   ├── noauthbot/
│   │   ├── privet/
│   │   ├── runner_questionnaire/
│   │   ├── runner_questionnaire_inline_button/
│   │   ├── setlang/
│   │   ├── start_cmd/
│   │   ├── today/
│   │   ├── view/
│   │   └── yesterday/
│   └── tlgbotcore/
│       ├── __init__.py
│       ├── _core.md
│       ├── _core.py
│       ├── di_container.py
│       ├── hacks.py
│       ├── i_utils.py
│       ├── i18n.py
│       ├── logging_config.py
│       ├── models.py
│       ├── storage_factory.py
│       ├── tlgbotcore.py
│       ├── csvdbutils/
│       └── sqliteutils/
├── cfg/
│   ├── __init__.py
│   ├── config_tlg_example.py
│   └── config_tlg.py
├── core/
│   ├── __init__.py
│   ├── models.py
│   ├── database/
│   │   ├── __init__.py
│   │   └── manager.py
│   ├── diary/
│   ├── export/
│   └── reminders/
├── data/
│   ├── backups/
│   ├── database/
│   │   ├── daylog.db
│   │   └── settings-tgbot.db
│   ├── exports/
│   └── photos/
├── docs/
│   ├── .gitkeep
│   └── project_structure.md
├── logs/
│   └── tlgbotcore.log
├── scripts/
├── tests/
│   ├── __init__.py
│   ├── performance_test.py
│   ├── test_database.py
│   └── test_models.py
├── diary_bot.db
├── Dockerfile
├── install_libs.sh
├── kaefikapp.session
├── LICENSE
├── pyproject.toml
├── README.md
├── run_bot.py
├── todo.md
└── uv.lock
```

## Обзор проекта

daylog_bot — это Telegram-бот для ведения личного дневника, разработанный на Python с использованием библиотеки Telethon. Бот позволяет пользователям создавать ежедневные записи, в которых можно указывать настроение, погоду, местоположение и события дня. Проект следует плагинной архитектуре, что облегчает его расширение новыми функциями.

## Основные компоненты архитектуры

Проект разделен на следующие основные компоненты:

### 1. tlgbotcore

Это базовый фреймворк для Telegram-ботов, который обеспечивает:
- Систему плагинов для динамической загрузки обработчиков команд
- Контейнер для внедрения зависимостей (DI)
- Поддержку интернационализации (i18n)
- Систему логирования
- Управление настройками и пользователями

Путь: `/bot/tlgbotcore/`

### 2. core

Основная бизнес-логика и модели данных для приложения-дневника:
- Определения моделей данных (Pydantic)
- Управление базой данных SQLite
- Функции для работы с записями дневника

Путь: `/core/`

### 3. plugins_bot

Модули, реализующие конкретные команды и функции бота:
- `/today` - запись за сегодняшний день
- `/yesterday` - запись за вчерашний день
- `/start` - начало работы с ботом
- и другие команды

Путь: `/bot/plugins_bot/`

### 4. cfg

Конфигурация бота с настройками:
- API-ключи Telegram
- Пути к базам данных
- Права администратора
- Язык по умолчанию

Путь: `/cfg/`

## Детальная структура каталогов

### `/bot/`

- **`__init__.py`** - инициализация пакета
- **`require_diary_user.py`** - декоратор для проверки регистрации пользователя
- **`start_tlgbotcore.py`** - точка входа для запуска бота

#### `/bot/locales/`

Файлы локализации для различных языков в формате JSON:
- **`ru.json`** - русский язык
- **`en.json`** - английский язык
- **`tt.json`** - татарский язык
- **`ba.json`** - башкирский язык
- **`tt_lat.json`** - татарский (латиница)
- **`ba_lat.json`** - башкирский (латиница)

#### `/bot/plugins_bot/`

Каждый плагин реализует отдельную команду или функциональность:

- **`admin_commands/`** - команды администратора
- **`inline_button/`** - обработка инлайн-кнопок
- **`noauthbot/`** - взаимодействие с неавторизованными пользователями
- **`privet/`** - простая команда-приветствие
- **`runner_questionnaire/`** - анкетирование для бега
- **`runner_questionnaire_inline_button/`** - анкетирование с инлайн-кнопками
- **`setlang/`** - изменение языка интерфейса
- **`start_cmd/`** - обработка команды /start
- **`today/`** - ведение записи за текущий день
- **`view/`** - просмотр записей
- **`yesterday/`** - ведение записи за вчерашний день

#### `/bot/tlgbotcore/`

Ядро фреймворка для Telegram-ботов:

- **`_core.py`** - основной класс и логика фреймворка
- **`di_container.py`** - контейнер внедрения зависимостей
- **`hacks.py`** - вспомогательные функции
- **`i_utils.py`** - утилиты и интерфейсы
- **`i18n.py`** - интернационализация
- **`logging_config.py`** - настройка логирования
- **`models.py`** - модели данных для фреймворка
- **`storage_factory.py`** - фабрика для хранилища данных
- **`tlgbotcore.py`** - публичный API фреймворка
- **`csvdbutils/`** - утилиты для работы с CSV
- **`sqliteutils/`** - утилиты для работы с SQLite

### `/cfg/`

- **`__init__.py`** - инициализация пакета конфигурации
- **`config_tlg.py`** - основной файл конфигурации (создается из примера)
- **`config_tlg_example.py`** - пример конфигурации с шаблонными значениями

### `/core/`

- **`__init__.py`** - инициализация пакета
- **`models.py`** - модели данных для дневника (используя Pydantic)

#### `/core/database/`

- **`__init__.py`** - инициализация пакета
- **`manager.py`** - класс DatabaseManager для работы с базой данных

#### `/core/diary/`

Модуль для базовых операций с дневником (будущая реализация)

#### `/core/export/`

Модуль для экспорта данных дневника (будущая реализация)

#### `/core/reminders/`

Модуль для системы напоминаний (будущая реализация)

### `/data/`

Каталог для хранения данных:

- **`backups/`** - резервные копии
- **`database/`** - файлы баз данных SQLite
  - **`daylog.db`** - основная база дневника
  - **`settings-tgbot.db`** - база настроек бота
- **`exports/`** - экспортированные данные
- **`photos/`** - загруженные фотографии

### `/docs/`

Документация проекта (этот файл и другие).

### `/logs/`

Каталог для лог-файлов:
- **`tlgbotcore.log`** - логи работы бота

### `/scripts/`

Вспомогательные скрипты для обслуживания бота.

### `/tests/`

Модульные и интеграционные тесты:
- **`__init__.py`** - инициализация пакета тестов
- **`performance_test.py`** - тесты производительности
- **`test_database.py`** - тесты для базы данных
- **`test_models.py`** - тесты для моделей данных

## Поток данных

1. Пользователь отправляет команду боту в Telegram (например, `/today`)
2. Telethon обрабатывает входящее сообщение и передает его в фреймворк tlgbotcore
3. tlgbotcore маршрутизирует команду к соответствующему плагину (например, `today.py`)
4. Плагин обрабатывает команду:
   - Проверяет авторизацию пользователя через декоратор `@require_diary_user`
   - Взаимодействует с базой данных через `DatabaseManager`
   - Отправляет ответ пользователю с локализацией через `tlgbot.i18n.t()`

## Ключевые шаблоны проектирования

### Система плагинов

Плагины загружаются динамически из директории `plugins_bot/`. Каждый плагин имеет доступ к глобальному объекту `tlgbot`:

```python
# Пример структуры плагина (из plugins_bot/today/today.py)
from telethon import events, Button
from bot.require_diary_user import require_diary_user

# tlgbot внедряется во время загрузки
tlgbot = globals().get('tlgbot')
logger = globals().get('logger')

@tlgbot.on(tlgbot.cmd('today'))
@require_diary_user  # Декоратор аутентификации
async def handler(event):
    # Реализация команды
```

### Внедрение зависимостей (DI)

Бот использует контейнер DI для управления зависимостями:

```python
# Пример регистрации
container = DIContainer()
container.register_instance(IConfig, config_adapter)
container.register_instance(I18n, i18n)
container.register_factory(ISettingsStorage, create_storage)
```

### Интернационализация (i18n)

Бот поддерживает несколько языков. Переводы хранятся в JSON-файлах в `bot/locales/`:

```python
# Использование переводов в коде
message = tlgbot.i18n.t('entry_title', lang=lang, date=date_str)
```

## Модели данных

Основные модели данных определены в `core/models.py` с использованием Pydantic:

- **`User`** - информация о пользователе
- **`DiaryEntry`** - запись дневника
- **`MoodLevel`** - перечисление типов настроения
- **`WeatherType`** - перечисление типов погоды

## База данных

Бот использует SQLite для хранения данных:

- **`users`** - таблица пользователей
- **`diary_entries`** - таблица записей дневника
- **`user_settings`** - таблица настроек пользователя
- **`system_info`** - системная информация

## Запуск проекта

### Быстрый старт

1. **Клонирование и установка зависимостей:**
   ```bash
   git clone git@github.com:kaefik/daylog_bot.git
   cd daylog_bot
   uv sync
   # Для разработки:
   uv sync --extra dev
   ```

2. **Создание конфигурации:**
   ```bash
   cp cfg/config_tlg_example.py cfg/config_tlg.py
   # и заполните свои значения (API_ID, HASH, TOKEN, ADMINS...)
   ```

3. **Запуск:**
   ```bash
   uv run -m bot.start_tlgbotcore
   ```

### Проверки качества кода

```bash
uv run ruff check .        # линтер
uv run ruff format .       # автоформат
uv run mypy bot/           # типизация
uv run pytest              # тесты
```

## Расширение функциональности

### Добавление нового плагина

1. Создайте новую директорию в `bot/plugins_bot/`
2. Добавьте файлы плагина с обработчиками команд
3. Получите доступ к глобальному объекту `tlgbot` для регистрации обработчиков

### Добавление новых переводов

1. Добавьте ключи и переводы в JSON-файлы в `bot/locales/`
2. Используйте переводы в коде: `tlgbot.i18n.t('key', lang=lang)`

### Работа с базой данных

Используйте `DatabaseManager` для операций с дневником:
```python
from core.database.manager import DatabaseManager
from cfg.config_tlg import DAYLOG_DB_PATH

db = DatabaseManager(db_path=DAYLOG_DB_PATH)
entry = db.get_diary_entry(user_id, entry_date)
```

## Будущие улучшения

- Расширение экспорта данных (PDF, HTML)
- Добавление системы напоминаний
- Статистика и аналитика записей
- Интеграция с облачными хранилищами
- Расширение системы плагинов