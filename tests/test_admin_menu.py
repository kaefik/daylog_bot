import types

from bot.menu_system import (
    MENU_REGISTRY,
    MENU_CACHE,
    register_menu,
    build_menu,
    MenuEntry,
    _is_admin_user,
)


class DummyBot:
    def __init__(self, admins):
        self.admins = admins
        # минимальный i18n мок
        class _I18N:
            def t(self, key, lang=None, **kw):
                return key
        self.i18n = _I18N()


def setup_function(_func):  # pytest style function-scoped reset
    MENU_REGISTRY.clear()
    MENU_CACHE.clear()
    # базовые 2 пункта
    register_menu(MenuEntry(key="today", tr_key="menu_today", plugin="p", handler="h", order=10))
    register_menu(MenuEntry(key="export", tr_key="menu_export", plugin="p", handler="h", order=20))
    # админские
    register_menu(MenuEntry(key="listusers", tr_key="menu_listusers", plugin="core", handler="h1", order=900, admin_only=True))
    register_menu(MenuEntry(key="adduser", tr_key="menu_adduser", plugin="core", handler="h2", order=910, admin_only=True))


def _extract_keys(button_rows):
    keys = []
    for row in button_rows:
        for btn in row:
            # data формата b"menu:<key>"
            if hasattr(btn, 'data') and btn.data:
                data = btn.data.decode('utf-8') if isinstance(btn.data, (bytes, bytearray)) else str(btn.data)
                if data.startswith('menu:'):
                    keys.append(data.split(':', 1)[1])
    return keys


def test_admin_menu_visible_for_admin(monkeypatch):
    dummy = DummyBot(admins=[123])
    monkeypatch.setitem(globals(), 'tlgbot', dummy)
    # вручную подменяем в модуле bot.menu_system
    import bot.menu_system as ms
    ms.tlgbot = dummy

    rows_admin = build_menu('ru', is_admin=True)
    keys_admin = _extract_keys(rows_admin)
    assert 'listusers' in keys_admin and 'adduser' in keys_admin


def test_admin_menu_hidden_for_user(monkeypatch):
    dummy = DummyBot(admins=[123])
    import bot.menu_system as ms
    ms.tlgbot = dummy

    rows_user = build_menu('ru', is_admin=False)
    keys_user = _extract_keys(rows_user)
    assert 'listusers' not in keys_user and 'adduser' not in keys_user


def test_is_admin_user_helper(monkeypatch):
    dummy = DummyBot(admins=['123', 456])  # смешанные типы
    import bot.menu_system as ms
    ms.tlgbot = dummy
    assert _is_admin_user(123) is True
    assert _is_admin_user('456') is True
    assert _is_admin_user(999) is False
