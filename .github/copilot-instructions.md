# daylog_bot Copilot Instructions

## Project Overview
daylog_bot is a Telegram bot that helps users maintain a personal diary. It uses Python with the Telethon library for Telegram API interaction and follows a plugin-based architecture.

## Architecture

### Core Components
- **tlgbotcore**: A framework for Telegram bots with plugin system, DI container, and i18n support
- **core**: Core business logic and data models for the diary application
- **plugins_bot**: Individual plugins that implement bot commands and features
- **cfg**: Configuration for the bot

### Data Flow
1. User sends a command to the Telegram bot
2. tlgbotcore routes the command to the appropriate plugin
3. Plugin handles the command, accessing data through the core/database
4. Responses are localized using the i18n system before sending back to the user

## Key Patterns

### Plugin System
Plugins are loaded dynamically from `plugins_bot/` directory. Each plugin has access to the global `tlgbot` object:

```python
# Example plugin structure (from plugins_bot/today/today.py)
from telethon import events, Button
from bot.require_diary_user import require_diary_user

# tlgbot is injected during loading
tlgbot = globals().get('tlgbot')
logger = globals().get('logger')

@tlgbot.on(events.NewMessage(pattern=r'/today'))
@require_diary_user  # Authentication decorator
async def handler(event):
    # Command implementation
```
### Dependency Injection
The bot uses a DI container to manage dependencies:

```python
# Registration example
container = DIContainer()
container.register_instance(IConfig, config_adapter)
container.register_instance(I18n, i18n)
container.register_factory(ISettingsStorage, create_storage)
```

### Internationalization (i18n)
The bot supports multiple languages. Translations are stored in JSON files in `bot/locales/`:

```python
# Using translations in code
message = tlgbot.i18n.t('entry_title', lang=lang, date=date_str)
```

## Development Workflow

### Environment Setup
```bash
# Clone and install dependencies
git clone git@github.com:kaefik/daylog_bot.git
cd daylog_bot
uv sync
# For development:
uv sync --extra dev

# Create config
cp cfg/config_tlg_example.py cfg/config_tlg.py
# Fill in API_ID, HASH, TOKEN, ADMINS...
```

### Running the Bot
```bash
uv run -m bot.start_tlgbotcore
```

### Code Quality
```bash
uv run ruff check .        # linter
uv run ruff format .       # auto-format
uv run mypy bot/           # type checking
uv run pytest              # tests
```

### Database
The bot uses SQLite for both settings and diary entries. Database initialization happens automatically on first run.

## Important Files

- `/bot/tlgbotcore/_core.py`: Core functionality for the bot framework
- `/core/models.py`: Data models for diary entries
- `/core/database/manager.py`: Database operations
- `/bot/plugins_bot/`: Contains all bot commands/features as plugins
- `/cfg/config_tlg.py`: Configuration (created from example)

## Common Tasks

### Adding a New Plugin
1. Create a new directory in `bot/plugins_bot/`
2. Add plugin files with handlers for commands
3. Access the global `tlgbot` object to register handlers

### Adding New Translations
1. Add keys and translations to the JSON files in `bot/locales/`
2. Access translations in code using `tlgbot.i18n.t('key', lang=lang)`

### Database Queries
Use the DatabaseManager for diary operations:
```python
from core.database.manager import DatabaseManager
from cfg.config_tlg import DAYLOG_DB_PATH

db = DatabaseManager(db_path=DAYLOG_DB_PATH)
entry = db.get_diary_entry(user_id, entry_date)
```

---

# Copilot Usage Guidelines

## Стиль ответов
- Отвечай только на русском, неформально.
- Кратко и конкретно, без воды.
- Формат: План (если нужно) → Код/Решение → Краткое «зачем» (если неочевидно).
- Никаких «можно так» — только одно конкретное решение.
- Ограничения (например, политика контента) — дай максимум допустимого и объясни почему.
- Девиз: «Чем короче, тем лучше, но без потери смысла».

## Код и технологии
- Соблюдай линтеры (`ruff`, `mypy`, `pytest`).
- Используй современные практики (async/await, typing, dataclasses/pydantic).
- Предпочитай:
  - Telethon для Telegram API
  - SQLite через `DatabaseManager`
  - Плагины через `tlgbotcore`
- Не использовать:
  - jQuery, eval, небезопасные конструкции
- Улучшающие или нетривиальные подходы помечай как *(спекуляция)*.

## Документация проекта
- Все изменения фиксируй в `TODO.md` в формате markdown.
- Формат записи в `TODO.md`:
  - Заголовок `# TODO`
  - Раздел `## Журнал`
  - Под каждый день: `### YYYY-MM-DD`
  - Список изменений в виде маркеров:
    - `[tag] Краткое описание (1–2 строки)`
    - Можно добавить хэш коммита или ветку.

## Git и коммиты
- Все коммиты должны быть **на русском языке**.
- Формат коммита:
  - первая строка — коротко и по делу (≤ 72 символов),
  - дальше (опционально) — подробности изменений через пустую строку.
- Используй повелительное наклонение: «Добавить», «Исправить», «Удалить».
- Примеры:
  - `Добавить поддержку /today в плагине`
  - `Исправить падение при пустом сообщении`
  - `Обновить зависимости и форматирование`
- Группируй изменения по смыслу — один коммит = одна задача.
- Ветки именуй на латинице: `feature/...`, `fix/...`.
- Pull Request — описание на русском, с чеклистом «что сделал» и «как проверить».
- Автолинтер в CI: коммиты не проходят без `ruff`, `mypy`, `pytest`.
- Конвенция тегов для TODO.md и коммитов: `[feat]`, `[fix]`, `[refactor]`, `[docs]`.

### Шаблон Pull Request
```markdown
# Что сделано
- [ ] Краткий список изменений

# Как проверить
1. Шаг 1
2. Шаг 2

# Дополнительно
- Ссылка на issue или задачу (если есть)
- Замечания или вопросы
```