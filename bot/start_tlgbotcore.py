from cfg import config_tlg as config
from bot.tlgbotcore.di_container import DIContainer, BotFactory, IConfig, ISettingsStorage
from bot.tlgbotcore.storage_factory import StorageFactory
from bot.tlgbotcore.logging_config import setup_prod_logging
from bot.tlgbotcore.i18n import I18n
import asyncio


class ConfigAdapter:
    """Адаптер для существующего конфига."""
    
    def __init__(self, config_module):
        self.TLG_APP_NAME = config_module.TLG_APP_NAME
        self.TLG_APP_API_ID = config_module.TLG_APP_API_ID
        self.TLG_APP_API_HASH = config_module.TLG_APP_API_HASH
        self.I_BOT_TOKEN = config_module.I_BOT_TOKEN
        self.TLG_ADMIN_ID_CLIENT = config_module.TLG_ADMIN_ID_CLIENT
        self.TYPE_DB = config_module.TYPE_DB
        self.SETTINGS_DB_PATH = config_module.SETTINGS_DB_PATH


async def _main_async():
    # Настройка DI-контейнера
    container = DIContainer()
    
    # Регистрация конфига
    config_adapter = ConfigAdapter(config)
    container.register_instance(IConfig, config_adapter)
    
    # Регистрация i18n (глобально или через DI)
    i18n = I18n(locales_path="bot/locales", default_lang=config.DEFAULT_LANG)
    container.register_instance(I18n, i18n)
    
    # Регистрация хранилища через фабрику
    def create_storage():
        return StorageFactory.create_storage(
            config_adapter.TYPE_DB,
            config_adapter.SETTINGS_DB_PATH,
            config_adapter.TLG_ADMIN_ID_CLIENT
        )
    
    container.register_factory(ISettingsStorage, create_storage)
    
    # Создание бота через фабрику
    bot_factory = BotFactory(container)
    tlg = bot_factory.create_bot()

    # Делаем i18n глобально доступным для плагинов (например, через атрибут бота)
    tlg.i18n = i18n

    await tlg.start_core(bot_token=config.I_BOT_TOKEN)
    await tlg.disconnected


def main():
    setup_prod_logging()
    asyncio.run(_main_async())


if __name__ == "__main__":
    main()
