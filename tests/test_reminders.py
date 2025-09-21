import asyncio
from datetime import date
import types

from bot.reminders.manager import send_reminder_job

class DummyDB:
    def __init__(self, *, entry_exists=False, last_reminder_date=None):
        self._entry_exists = entry_exists
        self._last_reminder_date = last_reminder_date
        self.updated_last_date = None
        self.updates = []

    def get_user(self, user_id: int):
        return {
            "user_id": user_id,
            "language_code": "ru",
            "timezone": "Europe/Moscow",
            "last_reminder_date": self._last_reminder_date,
        }

    def get_diary_entry(self, user_id: int, entry_date: date):
        return {"id": 1} if self._entry_exists else None

    def update_last_reminder_date(self, user_id: int, date_str: str):
        self.updated_last_date = date_str
        self.updates.append((user_id, date_str))

class DummyBot:
    def __init__(self):
        self.sent = []
        self.i18n = types.SimpleNamespace(t=lambda key, lang='ru', **kwargs: f"{key}:{lang}")
    async def send_message(self, user_id, text):
        self.sent.append((user_id, text))

def test_send_reminder_skip_entry_exists():
    db = DummyDB(entry_exists=True, last_reminder_date=None)
    bot = DummyBot()
    asyncio.run(send_reminder_job(1, bot, db))
    assert bot.sent == []
    assert db.updated_last_date is None

def test_send_reminder_skip_already_sent():
    today = date.today().isoformat()
    db = DummyDB(entry_exists=False, last_reminder_date=today)
    bot = DummyBot()
    asyncio.run(send_reminder_job(2, bot, db))
    assert bot.sent == []
    assert db.updated_last_date is None

def test_send_reminder_sent():
    db = DummyDB(entry_exists=False, last_reminder_date=None)
    bot = DummyBot()
    asyncio.run(send_reminder_job(3, bot, db))
    assert len(bot.sent) == 1
    assert db.updated_last_date is not None
