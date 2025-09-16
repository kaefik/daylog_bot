"""DI-контейнер для внедрения зависимостей."""

from typing import Any, Dict, Type, TypeVar, Protocol, Callable
from abc import ABC, abstractmethod

T = TypeVar('T')


class ISettingsStorage(Protocol):
    """Интерфейс для хранилища настроек пользователей."""
    
    def add_user(self, user: Any) -> None: ...
    def get_user_type_id(self, role: Any) -> list[int]: ...


class IConfig(Protocol):
    """Интерфейс для конфигурации."""
    
    TLG_APP_NAME: str
    TLG_APP_API_ID: int
    TLG_APP_API_HASH: str
    I_BOT_TOKEN: str
    TLG_ADMIN_ID_CLIENT: list[int]
    TYPE_DB: str
    SETTINGS_DB_PATH: str


class DIContainer:
    """Простой DI-контейнер."""
    
    def __init__(self) -> None:
        self._services: Dict[Type[Any], Any] = {}
        self._factories: Dict[Type[Any], Callable[[], Any]] = {}
    
    def register_instance(self, interface: Type[T], instance: T) -> None:
        """Регистрация готового экземпляра."""
        self._services[interface] = instance
    
    def register_factory(self, interface: Type[T], factory: Callable[[], T]) -> None:
        """Регистрация фабрики для создания экземпляра."""
        self._factories[interface] = factory
    
    def get(self, interface: Type[T]) -> T:
        """Получение экземпляра по интерфейсу."""
        if interface in self._services:
            return self._services[interface]
        
        if interface in self._factories:
            instance = self._factories[interface]()
            self._services[interface] = instance  # кэшируем
            return instance
        
        raise ValueError(f"Сервис {interface} не зарегистрирован")


class BotFactory:
    """Фабрика для создания бота через DI."""
    
    def __init__(self, container: DIContainer) -> None:
        self.container = container
    
    def create_bot(self) -> 'TlgBotCore':
        """Создание бота с внедрёнными зависимостями."""
        config = self.container.get(IConfig)
        storage = self.container.get(ISettingsStorage)
        
        # Импорт только здесь, избегаем циклических зависимостей
        from .tlgbotcore import TlgBotCore
        
        return TlgBotCore(
            session=config.TLG_APP_NAME,
            plugin_path='bot/plugins_bot',
            api_id=config.TLG_APP_API_ID,
            api_hash=config.TLG_APP_API_HASH,
            bot_token=config.I_BOT_TOKEN,
            admins=config.TLG_ADMIN_ID_CLIENT,
            settings_storage=storage  # внедряем готовое хранилище
        )
