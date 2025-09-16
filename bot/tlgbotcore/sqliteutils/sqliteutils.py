"""
модуль для работы с sqlite в качестве хранилища настройки бота

БД настроек состоит из следующих таблиц
    1) таблица пользователей USERS
    2) таблица ролей (прав доступа к боту)
"""

import os
import sqlite3
from typing import Optional, List, Union
from enum import Enum
from ..models import User, Role
from cfg import config_tlg as config  # Добавьте импорт конфига для доступа к DEFAULT_LANG





class SettingUser:

    def __init__(self, namedb: str = 'settings.db', force: bool = False) -> None:
        """
            инициализация БД настроек бота
                namedb - название БД
                force  - если True, то даже если БД существует, оно перезапишет его
        """
        self.db = namedb  # имя БД настроек бота
        dir_name = os.path.dirname(self.db)
        if not dir_name == "":
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
        self.connect = self.__createnewdb(force)  # коннект в БД

    def open(self) -> bool:
        """
            открыть файл настроек
        """
        try:
            conn = sqlite3.connect(self.db)
        except sqlite3.Error as error:
            print("Ошибка при подключении к sqlite", error)
            return False
        finally:
            return True

    def close(self) -> None:
        """
            закрытие подключения к БД
        """
        if self.connect is not None:
            self.connect.close()

    def __createnewdb(self, force: bool = False) -> sqlite3.Connection:
        """
            создание БД настроек бота
            возвращает True, если операция создания успешно.
        """
        try:
            if os.path.exists(self.db):
                if force:
                    # print('Файл существует')
                    os.remove(self.db)
                else:
                    connect = sqlite3.connect(self.db)
                    return connect

            connect = sqlite3.connect(self.db)
            cursor = connect.cursor()

            """
                Создание таблицы USER - информация о пользователях
                поля: 
                    id - id пользователя из телеграмма
                    name - имя пользователя
                    active - если 0, пользователь неактивный, иначе пользователь активный
            """
            cursor.execute("""CREATE TABLE user 
                (id INTEGER, name text, active INTEGER, lang text)
                   """)

            """
                Создание таблицы settings  - информация о настройках бота
                поля:
                    id - id пользователя из телеграмма (связана с полем id таблицы USER 
                    role - роль пользователя: admin - администратор бота, user - обычный пользователь бота
            """
            cursor.execute("""CREATE TABLE settings 
                      (id INTEGER, role text)
               """)
        except sqlite3.Error as error:
            print("Ошибка при подключении к sqlite", error)
            raise

        return connect

    def add_user(self, new_user: User) -> bool:
        """
            добавление нового пользователя new_user (тип User)
            возвращает: True - операция добавления пользователя удалась, False - ошибка при добавлении или пользователь существует
        """
        cursor = self.connect.cursor()

        id_exist = self.is_exist_user(new_user.id)

        if id_exist:
            return False



        # Используем язык по умолчанию из конфига, если не задан явно
        lang = getattr(new_user, "lang", None) or getattr(config, "DEFAULT_LANG", "ru")

        print(f"{config.DEFAULT_LANG=}")
        print(f"Добавление пользователя {new_user.id} с языком {lang}")

        cursor.execute(
            "INSERT INTO user (id, name, active, lang) VALUES (?, ?, ?, ?)",
            (new_user.id, new_user.name, int(new_user.active), lang),
        )

        cursor.execute(
            "INSERT INTO settings (id, role) VALUES (?, ?)",
            (new_user.id, str(new_user.role)),
        )
        self.connect.commit()
        cursor.close()
        return True

    def is_exist_user(self, idd: int) -> bool:
        """
            проверить есть ли БД пользователь с id
            тест: есть
        """
        result = self.get_user(idd=idd)
        if result is not None:
            return True
        else:
            return False

    def del_user(self, idd: int) -> bool:
        """
            удаление пользователя с id
            тест: есть
        """
        cursor = self.connect.cursor()

        cursor.execute("DELETE FROM user WHERE id = ?", (idd,))
        cursor.execute("DELETE FROM settings WHERE id = ?", (idd,))

        self.connect.commit()
        cursor.close()
        return True

    def update_user(self, new_user: User) -> bool:
        """
            обновить данные пользователя User, если такого пользователя нет, то добавляется новый пользователь
        """
        if not self.is_exist_user(new_user.id):
            self.add_user(new_user)

        cursor = self.connect.cursor()

        # Используем язык по умолчанию из конфига, если не задан явно
        lang = getattr(new_user, "lang", None) or getattr(config, "DEFAULT_LANG", "ru")

        cursor.execute(
            "UPDATE user SET name = ?, active = ?, lang = ? WHERE id = ?",
            (new_user.name, int(new_user.active), lang, new_user.id),
        )

        cursor.execute(
            "UPDATE settings SET role = ? WHERE id = ?",
            (str(new_user.role), new_user.id),
        )

        self.connect.commit()
        cursor.close()
        return True

    def get_user(self, idd: int) -> Optional[User]:
        """
            получить информацию о пользователе по id
        """
        result = None

        cursor = self.connect.cursor()
        cursor.execute("SELECT * FROM user WHERE id = ?", (idd,))
        result_user = cursor.fetchone()

        if result_user is None:
            return result

        cursor.execute("SELECT * FROM settings WHERE id = ?", (idd,))
        result_settings = cursor.fetchone()

        if result_settings is None:
            return result

        # result_user: (id, name, active, lang)
        lang = result_user[3] if len(result_user) > 3 and result_user[3] else getattr(config, "DEFAULT_LANG", "ru")
        result = User(
            id=result_user[0],
            name=result_user[1],
            active=result_user[2],
            role=result_settings[1],
            lang=lang
        )
        return result

    def get_all_user(self) -> List[User]:
        """
            получить всех пользователей
        """
        cursor = self.connect.cursor()
        cursor.execute("SELECT * from user")
        result_user = cursor.fetchall()

        cursor.execute("SELECT * from settings")
        result_settings = cursor.fetchall()

        result = []
        # result_user: (id, name, active, lang)
        for row in result_user:
            lang = row[3] if len(row) > 3 and row[3] else getattr(config, "DEFAULT_LANG", "ru")
            result.append(User(id=row[0], name=row[1], active=row[2], lang=lang))

        for i in range(0, len(result)):
            for row in result_settings:
                if result[i].id == row[0]:
                    result[i].role = row[1]

        return result

    def get_all_user_id(self) -> List[int]:
        """
            получить все ID пользователей
            тест: -
        """
        result = []
        users = self.get_all_user()
        for user in users:
            result.append(user.id)
        return result

    def get_user_type(self, type_user: Role) -> List[User]:
        """
            получение всех пользователей с типом type_user (тип Role)
            возвращает: массив пользователей, если пользователей нет, то пустой массив
            тест: есть
        """
        result: List[User] = []

        cursor = self.connect.cursor()
        # Поддерживаем оба формата: 'admin' и 'Role.admin'
        role_str = str(type_user)
        role_name = type_user.name  # 'admin' для Role.admin
        cursor.execute("SELECT * FROM settings WHERE role = ? OR role = ?", (role_str, role_name))
        result_setting = cursor.fetchall()

        if len(result_setting) == 0:
            return result

        for row in result_setting:
            idd = row[0]

            cursor.execute("SELECT * FROM user WHERE id = ?", (idd,))
            result_user = cursor.fetchone()

            if len(result_user) == 0:
                continue

            result.append(User(id=result_user[0], name=result_user[1], active=result_user[2],
                               role=row[1]))

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
    # user1.typeresult = SettingOne.sound
    # user1.qualityresult = SettingTwo.medium
    #
    # user2 = User()
    # user2.name = 'User1'
    # user2.id = 123456
    # user2.active = True
    # user2.role = Role.admin
    # user2.typeresult = SettingOne.sound
    # user2.qualityresult = SettingTwo.medium
    # print(user1 == user2)
    #
    # print(ord(user2.typeresult))

    # for name, member in SettingOne.__members__.items():
    #     print(name, member)

    pass
