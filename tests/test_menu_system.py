import types
import pytest

from bot import tlgbotcore  # noqa: F401  # гарантирует наличие структуры, если нужно

# Импортируем после возможной инициализации
from bot.menu_system import (
    register_menu,
    MENU_REGISTRY,
    build_menu,
    invalidate_menu,
    disable_menu,
    enable_menu,
)


class DummyI18n:
    def t(self, key, lang=None, **kwargs):  # pragma: no cover - простая заглушка
        return key


class DummyBot:
    def __init__(self):
        self._plugins = {}
        self.i18n = DummyI18n()

    def on(self, *args, **kwargs):  # decorator stub
        def wrap(fn):
            return fn
        return wrap

    def cmd(self, name):  # simple pattern stub
        import re
        return re.compile(rf'^/{name}')


def make_dummy_plugin(handler_name):
    mod = types.SimpleNamespace()
    async def _handler(event):  # noqa: D401
        return f"handled:{handler_name}"
    setattr(mod, handler_name, _handler)
    return mod


def setup_function(_):
    # очистим реестр и кэш
    MENU_REGISTRY.clear()
    invalidate_menu()


def test_register_and_build(monkeypatch):
    bot = DummyBot()
    monkeypatch.setitem(globals(), 'tlgbot', bot)
    register_menu({'key': 'a', 'tr_key': 'menu_a', 'plugin': 'plugA', 'handler': 'h', 'order': 10})
    bot._plugins['plugA'] = make_dummy_plugin('h')
    buttons = build_menu('ru')
    assert buttons and buttons[0][0].data.decode().startswith('menu:a')


def test_disable_enable(monkeypatch):
    bot = DummyBot()
    monkeypatch.setitem(globals(), 'tlgbot', bot)
    register_menu({'key': 'x', 'tr_key': 'menu_x', 'plugin': 'plugX', 'handler': 'h', 'order': 10})
    bot._plugins['plugX'] = make_dummy_plugin('h')
    buttons_before = build_menu('ru')
    assert any(b.data.decode() == 'menu:x' for row in buttons_before for b in row)
    disable_menu('x')
    buttons_after = build_menu('ru')
    assert not any(b.data.decode() == 'menu:x' for row in buttons_after for b in row)
    enable_menu('x')
    buttons_after2 = build_menu('ru')
    assert any(b.data.decode() == 'menu:x' for row in buttons_after2 for b in row)


def test_duplicate_ignored(monkeypatch):
    bot = DummyBot()
    monkeypatch.setitem(globals(), 'tlgbot', bot)
    register_menu({'key': 'd', 'tr_key': 'menu_d', 'plugin': 'plugD', 'handler': 'h', 'order': 10})
    before = len(MENU_REGISTRY)
    register_menu({'key': 'd', 'tr_key': 'menu_d', 'plugin': 'plugD', 'handler': 'h', 'order': 20})
    assert len(MENU_REGISTRY) == before
