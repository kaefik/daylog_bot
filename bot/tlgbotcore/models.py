from typing import Union, Any
from enum import Enum


class Role(Enum):
    admin = 1
    user = 2


class User:

    def __init__(self, id: int = -1, name: str = '', active: bool = False, role: Union[Role, str] = Role.user, lang: str = "ru") -> None:
        self._id = id
        self._name = name
        self._active = bool(active)
        self._lang = lang  # поле языка

        if isinstance(role, Role):
            self._role = role
        elif isinstance(role, str):
            if role == 'Role.admin' or role == 'admin':
                self._role = Role.admin
            elif role == 'Role.user' or role == 'user':
                self._role = Role.user
            else:
                self._role = Role.user
        else:
            self._role = Role.user  # pragma: no cover

    @property
    def id(self) -> int:
        return self._id

    @id.setter
    def id(self, my_id: int) -> None:
        self._id = my_id

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, new_name: str) -> None:
        self._name = new_name

    @property
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, flag: Any) -> None:
        self._active = bool(flag)

    @property
    def role(self) -> Role:
        return self._role

    @role.setter
    def role(self, new_role: Union[Role, str]) -> None:
        if isinstance(new_role, Role):
            self._role = new_role
        elif isinstance(new_role, str):
            if new_role == 'Role.admin' or new_role == 'admin':
                self._role = Role.admin
            elif new_role == 'Role.user' or new_role == 'user':
                self._role = Role.user

    @property
    def lang(self) -> str:
        """Получить язык пользователя"""
        return self._lang

    @lang.setter
    def lang(self, value: str) -> None:
        """Установить язык пользователя"""
        self._lang = value

    def __str__(self) -> str:
        return (
            f"User -> id: {self.id}\t{type(self.id)}\n\t"
            f"name: {self.name}\t{type(self.name)}\n\t"
            f"active: {self.active}\t{type(self.active)}\n\t"
            f"role: {self.role}\t{type(self.role)}\n\t"
            f"lang: {self.lang}\t{type(self.lang)}\n"
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, User):
            return False
        return (
            self.id == other.id and self.name == other.name and self.active == other.active and self.role is other.role
        )


