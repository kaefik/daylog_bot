from bot.reminders.manager import schedule_user_reminder

class DummyDB2:
    def __init__(self, tz="Europe/Moscow"):
        self.tz = tz
    def get_user(self, user_id: int):
        return {"user_id": user_id, "timezone": self.tz, "language_code": "ru"}

class DummyScheduler:
    def __init__(self):
        self.jobs = {}
        self.removed = []
    def remove_job(self, job_id):
        if job_id in self.jobs:
            self.removed.append(job_id)
            self.jobs.pop(job_id)
        else:
            raise Exception("no job")
    def add_job(self, func, trigger, hour, minute, id, kwargs, replace_existing, misfire_grace_time, timezone):
        self.jobs[id] = {
            'func': func,
            'trigger': trigger,
            'hour': hour,
            'minute': minute,
            'kwargs': kwargs,
            'replace_existing': replace_existing,
            'misfire_grace_time': misfire_grace_time,
            'timezone': timezone,
        }

class DummyBot2:
    def __init__(self):
        self.scheduler = DummyScheduler()


def test_schedule_user_reminder_initial():
    db = DummyDB2()
    bot = DummyBot2()
    schedule_user_reminder(bot, db, 10, "21:05")
    assert '10' in bot.scheduler.jobs
    job = bot.scheduler.jobs['10']
    assert job['hour'] == 21 and job['minute'] == 5
    assert job['timezone'] == 'Europe/Moscow'


def test_schedule_user_reminder_reschedule():
    db = DummyDB2()
    bot = DummyBot2()
    schedule_user_reminder(bot, db, 10, "21:05")
    schedule_user_reminder(bot, db, 10, "20:30")
    job = bot.scheduler.jobs['10']
    assert job['hour'] == 20 and job['minute'] == 30


def test_schedule_user_reminder_invalid():
    db = DummyDB2()
    bot = DummyBot2()
    schedule_user_reminder(bot, db, 11, "99:99")
    assert '11' not in bot.scheduler.jobs
