"""Фабрика для создания хранилищ настроек."""

import os
import logging
from typing import Any
from .di_container import ISettingsStorage
from .models import User, Role


class StorageFactory:
    """Фабрика для создания хранилищ по типу БД."""
    
    @staticmethod
    def create_storage(type_db: str, db_path: str, admins: list[int]) -> ISettingsStorage:
        """Создание хранилища по типу БД."""
        logger = logging.getLogger(__name__)
        
        if type_db == 'SQLITE':
            from .sqliteutils import SettingUser
            storage = SettingUser(namedb=db_path)
            
        elif type_db == 'CSV':
            from .csvdbutils.csvdbutils import SettingUser
            storage = SettingUser(namedb=db_path)
            
        else:
            raise ValueError(f"Неподдерживаемый тип БД: {type_db}")
        
        # Импортируем конфиг для доступа к DEFAULT_LANG
        from cfg import config_tlg as config

        # Инициализация админов если БД новая или нет админов
        existing_admins = storage.get_user_type_id(Role.admin)
        if not os.path.exists(db_path) or len(existing_admins) == 0:
            logger.info(f'Создаём/дополняем БД настроек с админами: {admins}')
            for admin_id in admins:
                if admin_id not in existing_admins:
                    admin_user = User(id=admin_id, role=Role.admin, active=True, lang=getattr(config, "DEFAULT_LANG", "ru"))
                    storage.add_user(admin_user)
        else:
            logger.info(f'БД существует с админами: {existing_admins}, переданные: {admins}')
        
        return storage
