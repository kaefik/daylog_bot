"""
модуль для работы с набора csv файлов эмулирующих работы в таблицами в качестве хранилища настройки бота

БД охраняется в папке названием самой БД , внутри папки находятся файлы csv с названиями таблиц:
    1) таблица пользователей USERS.csv
    2) таблица ролей (прав доступа к боту)
"""

import os
from typing import Optional, List, Union, Any
from enum import Enum
from ..models import User, Role
from cfg import config_tlg  # Добавьте импорт конфига для доступа к DEFAULT_LANG

from .csvdb.csvdb import CSVDB

# icecream убран из продакшн кода - используем logging


# безопасное преобразование значений в bool и 0/1
def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    return s in ("1", "true", "yes", "y", "on")


def _to_int_flag(value: Any) -> int:
    return 1 if _to_bool(value) else 0

# доступные роли пользователя
# роли берём из общих моделей


# --------- Зарезервировано для пользовательских настроек (перечисления) ---------
# Здесь могут описываться дополнительные настройки пользователей при необходимости.

# данные конкретного пользователя  
# Используем базовый User из models, расширяем только свойства
class CSVUser(User):
    pass

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, my_id):
        self._id = my_id

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new_name):
        self._name = new_name

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, flag):
        if flag == 0:
            self._active = False
        else:
            self._active = True

    @property
    def role(self):
        return self._role

    @role.setter
    def role(self, new_role):
        # проверить соответствует ли new_role классу Role
        if type(new_role) is Role:
            self._role = new_role
        elif type(new_role) is str:
            if new_role == 'Role.admin':
                self._role = Role.admin
            elif new_role == 'Role.user':
                self._role = Role.user

    def __str__(self):
        return f"User -> id: {self.id}\t{type(self.id)}\n\tname: {self.name}\t{type(self.name)}\n\t" \
               f"active: {self.active}\t{type(self.active)}\n\t" \
               f"role: {self.role}\t{type(self.role)}\n\t\n"

    def __eq__(self, other):
        if (self.id == other.id) and (self.name == other.name) and (self.active == other.active) \
                and (self.role is other.role):
            return True
        return False


class SettingUser:

    def __init__(self, namedb: str = 'settings_db', force: bool = False) -> None:
        """
            инициализация БД настроек бота
                namedb - название БД
                force  - если True, то даже если БД существует, оно перезапишет его
        """
        self.db = namedb  # имя БД настроек бота
        self.__createnewdb(force)  # коннект в БД

    def open(self) -> None:
        """
            открыть файл настроек
        """
        # try:
        #     conn = sqlite3.connect(self.db)
        # except sqlite3.Error as error:
        #     print("Ошибка при подключении к sqlite", error)
        #     return False
        # finally:
        #     return True
        pass

    def close(self) -> None:
        """
            закрытие подключения к БД
        """
        # if not (self.connect is None):
        #     self.connect.close()
        pass

    def __createnewdb(self, force: bool = False) -> bool:
        """
            создание БД настроек бота
            возвращает True, если операция создания успешно.
        """

        self.connect = CSVDB(name_db=self.db, force=force)

        """
            Создание таблицы USER - информация о пользователях
            поля:
                id - id пользователя из телеграмма (тип: INTEGER)
                name - имя пользователя text
                active - если 0, пользователь неактивный, иначе пользователь активный (тип: INTEGER)
                role - роль пользователя: admin - администратор бота, user - обычный пользователь бота (тип: text)
                lang - язык пользователя (text)
        """
        headers_user = ['id', 'name', 'active', 'role', 'lang']
        self.connect.create_table(name_table='user', colums=headers_user)

        return True

    def add_user(self, new_user: User) -> bool:
        """
            добавление нового пользователя new_user (тип User)
            возвращает: True - операция добавления пользователя удалась, False - ошибка при добавлении или пользователь существует
            тест: ok
        """

        id_exist = self.is_exist_user(new_user.id)
        if id_exist:  # проверка на то что пользователь с данным id есть пользователь
            return False
        data = {
            'id': new_user.id,
            'name': new_user.name,
            'active': _to_int_flag(new_user.active),
            'role': str(new_user.role),
            'lang': getattr(new_user, "lang", None) or getattr(config_tlg, "DEFAULT_LANG", "ru"),
        }
        self.connect.insert_data(name_table='user', data=data)

        return True

    def is_exist_user(self, idd: int) -> bool:
        """
            проверить есть ли БД пользователь с id
            тест: ok
        """
        result = self.get_user(idd=idd)
        if result is not None:
            return True
        else:
            return False

    def del_user(self, idd: int) -> bool:
        """
            удаление пользователя с id
            тест: ok
        """

        all_data = self.connect.getall(name_table='user')

        if not self.is_exist_user(idd):
            return False

        self.__createnewdb(force=True)
        for el in all_data:
            if not (int(el['id']) == idd):
                self.connect.insert_data(name_table='user', data=el)
        return True

    def update_user(self, new_user: User) -> bool:
        """
            обновить данные пользователя  User, если такого пользователя нет, то добавляется новый пользователь
            тест: ok
        """
        if not self.is_exist_user(new_user.id):
            self.add_user(new_user)

        all_data = self.connect.getall(name_table='user')

        self.__createnewdb(force=True)

        for el in all_data:
            if int(el['id']) == new_user.id:
                self.connect.insert_data(
                    name_table='user',
                    data={
                        'id': new_user.id,
                        'name': new_user.name,
                        'active': _to_int_flag(new_user.active),
                        'role': str(new_user.role),
                        'lang': getattr(new_user, "lang", None) or getattr(config_tlg, "DEFAULT_LANG", "ru"),
                    },
                )
            else:
                self.connect.insert_data(name_table='user', data=el)

        return True

    def get_user(self, idd: int) -> Optional[User]:
        """
            получить информацию о пользователе по id
            тест: ok
        """
        result = None

        all_data = self.connect.getall(name_table='user')

        for el in all_data:
            if int(el['id']) == idd:
                result = User(
                    id=int(el['id']),
                    name=el['name'],
                    active=_to_bool(el['active']),
                    role=el['role'],
                    lang=el['lang'] if 'lang' in el and el['lang'] else getattr(config_tlg, "DEFAULT_LANG", "ru")
                )
                return result

        return result

    def get_all_user(self) -> List[User]:
        """
            получить всех пользователей
            тест: ok
        """
        result = []
        all_data = self.connect.getall(name_table='user')

        for el in all_data:
            usr = User(
                id=int(el['id']),
                name=el['name'],
                active=_to_bool(el['active']),
                role=el['role'],
                lang=el['lang'] if 'lang' in el and el['lang'] else getattr(config_tlg, "DEFAULT_LANG", "ru")
            )
            result.append(usr)

        return result

    def get_all_user_id(self) -> List[int]:
        """
            получить все ID пользователей
            тест: -
        """
        result = []
        all_data = self.connect.getall(name_table='user')

        for el in all_data:
            result.append(int(el['id']))

        return result

    def get_user_type(self, type_user: Role) -> List[User]:
        """
            получение всех пользователей с типом type_user (тип Role)
            возвращает: массив пользователей, если пользователей нет, то пустой массив
            тест: ok
        """
        result = []

        all_data = self.connect.getall(name_table='user')

        # ic(all_data)

        for el in all_data:
            if el['role'] == str(type_user):
                usr = User(
                    id=int(el['id']),
                    name=el['name'],
                    active=_to_bool(el['active']),
                    role=el['role'],
                )
                result.append(usr)

        return result

    def get_user_type_id(self, type_user: Role) -> List[int]:
        """
            получение всех пользователей  ID с типом type_user (тип Role)
            возвращает: массив пользователей, если пользователей нет, то пустой массив
            тест: -
        """
        result = []
        users = self.get_user_type(type_user=type_user)
        for user in users:
            result.append(user.id)
        return result

    def fix_settings(self) -> None:
        """
            починка БД настроек пользователя,
            например каким-то образом информация о пользователе есть только в одной таблице
             User или Settings
        """
        pass

    if __name__ == '__main__':
        # user1 = User()
        # user1.name = 'User1'
        # user1.id = 123456
        # user1.active = True
        # user1.role = Role.admin
        # # user1.typeresult = SettingOne.sound
        # # user1.qualityresult = SettingTwo.medium
        # #
        # user2 = User()
        # user2.name = 'User1'
        # user2.id = 123456
        # user2.active = True
        # user2.role = Role.admin
        #
        # db = SettingUser()

        # user2.typeresult = SettingOne.sound
        # user2.qualityresult = SettingTwo.medium
        # print(user1 == user2)
        #
        # print(ord(user2.typeresult))

        # for name, member in SettingOne.__members__.items():
        #     print(name, member)

        # print(os.path.exists('settings_db'))
        pass
