# daylog_bot
телеграмм бот который будет помогать вести личный дневник


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
    `uv run -m bot.start_tlgbotcore`

---

## 🛠️ Качество кода

Проверки и тесты:
```bash
uv run ruff check .        # линтер
uv run ruff format .       # автоформат
uv run mypy bot/           # типизация
uv run pytest              # тесты (добавьте свои)
```