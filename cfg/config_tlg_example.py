# здесь указывается переменные для запуска телеграмм бота

TLG_APP_NAME = "tlgbotappexample"  # APP NAME get from https://my.telegram.org
TLG_APP_API_ID = 1258887  # APP API ID get from https://my.telegram.org
TLG_APP_API_HASH = "sdsadsadasd45522665f"  # APP API HASH get from https://my.telegram.org
I_BOT_TOKEN = "0000000000:sfdfdsfsdf5s5541sd2f1sd5"  # TOKEN Bot from BotFather
TLG_ADMIN_ID_CLIENT = [1258889]  # admin clients for admin telegram bot
# proxy for Telegram
TLG_PROXY_SERVER = None  # address MTProxy Telegram
TLG_PROXY_PORT = None  # port  MTProxy Telegram
TLG_PROXY_KEY = None  # secret key  MTProxy Telegram

# for save settings user
# CSV - сохранение данных настроек для доступа к боту используя БД в формате CSV
# SQLITE - сохранение данных настроек для доступа к боту используя БД в формате sqlite3
TYPE_DB = "SQLITE"

# путь для БД настроек бота
SETTINGS_DB_PATH = "settings.db"  # путь к файлу БД настроек

# глобальный язык по умолчанию для бота
DEFAULT_LANG = "en"

# Доступные локализации для смены языка клиентами бота
AVAILABLE_LANGS = {
	"ru": "Русский",
	"en": "English",
    "ba": "Башҡортса",
    "tt": "Татарча",
    "tt_lat": "Татарча (латинца)",
    "ba_lat": "Башҡортса (латинца)",
}

DAYLOG_DB_PATH = "./data/database/daylog.db"  # путь к файлу БД дневника

# Уровень логирования для всего приложения
# Допустимые значения: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
# DEBUG - все сообщения, включая отладочные
# INFO - информационные сообщения и выше (без отладочных)
# WARNING - предупреждения и ошибки
# ERROR - только ошибки
# CRITICAL - только критические ошибки
LOG_LEVEL = "INFO"