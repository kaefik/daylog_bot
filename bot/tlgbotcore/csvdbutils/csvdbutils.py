"""
модуль для работы с набора csv файлов эмулирующих работы в таблицами в качестве хранилища настройки бота

БД охраняется в папке названием самой БД , внутри папки находятся файлы csv с названиями таблиц:
    1) таблица пользователей USERS.csv
    2) таблица ролей (прав доступа к боту)
"""

import os
from enum import Enum

from tlgbotcore.csvdbutils.csvdb.csvdb import CSVDB

from icecream import ic


# доступные роли пользователя
class Role(Enum):
    admin = 1
    user = 2


# --------- Здесь должны описываться настройки пользователей в виде перечислений
# типы результата работы
# class SettingOne(Enum):
#     video = 1
#     sound = 2
#
#
# class SettingTwo(Enum):
#     low = 1
#     medium = 2
#     high = 3


# --------- END Здесь должны описываться настройки пользователей в виде перечислений

# данные конкретного пользователя
class User:

    def __init__(self, id=-1):
        self._id = id
        self._name = ''
        self._active = False
        self._role = Role.user
        self._typeresult = SettingOne.sound
        self._qualityresult = SettingTwo.medium

    def __init__(self, id=-1, name='', active=False, role=Role.user):
        self._id = id
        self._name = name
        self._active = active
        # if active == 0:
        #     self._active = False
        # else:
        #     self._active = True

        # TODO: понять как из строки перевести в тип enum без бесконечных if
        if type(role) is Role:
            self._role = role
        elif type(role) is str:
            if role == 'Role.admin':
                self._role = Role.admin
            elif role == 'Role.user':
                self._role = Role.user
        else:
            self._role = Role.user

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

    def __init__(self, namedb='settings_db', force=False):
        """
            инициализация БД настроек бота
                namedb - название БД
                force  - если True, то даже если БД существует, оно перезапишет его
        """
        self.db = namedb  # имя БД настроек бота
        self.__createnewdb(force)  # коннект в БД

    def open(self):
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

    def close(self):
        """
            закрытие подключения к БД
        """
        # if not (self.connect is None):
        #     self.connect.close()
        pass

    def __createnewdb(self, force=False):
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
        """
        headers_user = ['id', 'name', 'active', 'role']
        self.connect.create_table(name_table='user', colums=headers_user)

        return True

    def add_user(self, new_user):
        """
            добавление нового пользователя new_user (тип User)
            возвращает: True - операция добавления пользователя удалась, False - ошибка при добавлении или пользователь существует
            тест: ok
        """

        id_exist = self.is_exist_user(new_user.id)
        if id_exist:  # проверка на то что пользователь с данным id есть пользователь
            return False
        data = {'id': new_user.id, 'name': new_user.name, 'active': new_user.active, 'role': new_user.role}
        self.connect.insert_data(name_table='user', data=data)

        return True

    def is_exist_user(self, idd):
        """
            проверить есть ли БД пользователь с id
            тест: ok
        """
        result = self.get_user(idd=idd)
        if result is not None:
            return True
        else:
            return False

    def del_user(self, idd):
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

    def update_user(self, new_user):
        """
            обновить данные пользователя  User, если такого пользователя нет, то добавляется новый пользователь
            тест: ok
        """
        # """Update sqlitedb_developers set salary = 10000 where id = 4"""

        if not self.is_exist_user(new_user.id):
            self.add_user(new_user)

        all_data = self.connect.getall(name_table='user')

        self.__createnewdb(force=True)

        for el in all_data:
            if int(el['id']) == new_user.id:
                # ic(new_user.active)
                self.connect.insert_data(name_table='user',
                                         data={'id': new_user.id, 'name': new_user.name, 'active': new_user.active,
                                               'role': new_user.role})
            else:
                self.connect.insert_data(name_table='user', data=el)

        return True

    def get_user(self, idd):
        """
            получить информацию о пользователе по id
            тест: ok
        """
        result = None

        all_data = self.connect.getall(name_table='user')

        for el in all_data:
            if int(el['id']) == idd:
                result = User(id=int(el['id']), name=el['name'], active=eval(el['active']), role=el['role'])
                return result

        return result

    def get_all_user(self):
        """
            получить всех пользователей
            тест: ok
        """
        result = []
        all_data = self.connect.getall(name_table='user')

        for el in all_data:
            usr = User(id=int(el['id']), name=el['name'], active=eval(el['active']), role=el['role'])
            result.append(usr)

        return result

    def get_all_user_id(self):
        """
            получить все ID пользователей
            тест: -
        """
        result = []
        all_data = self.connect.getall(name_table='user')

        for el in all_data:
            result.append(int(el['id']))

        return result

    def get_user_type(self, type_user):
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
                usr = User(id=int(el['id']), name=el['name'], active=el['active'], role=el['role'])
                result.append(usr)

        return result

    def get_user_type_id(self, type_user):
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

    def fix_settings(self):
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
