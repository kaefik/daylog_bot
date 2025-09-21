import logging
from datetime import date, datetime
from zoneinfo import ZoneInfo
from typing import Optional

from core.database.manager import DatabaseManager

logger = logging.getLogger(__name__)

def parse_hhmm(value: str) -> Optional[tuple[int, int]]:
    try:
        parts = value.strip().split(":")
        if len(parts) != 2:
            return None
        h, m = int(parts[0]), int(parts[1])
        if 0 <= h <= 23 and 0 <= m <= 59:
            return h, m
    except Exception:
        return None
    return None

async def send_reminder_job(user_id: int, tlgbot, db: DatabaseManager):
    try:
        user_row = db.get_user(user_id)
        tz_name = (user_row.get("timezone") if user_row else "Europe/Moscow") or "Europe/Moscow"
        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            tz = ZoneInfo("Europe/Moscow")
        now_local = datetime.now(tz)
        local_date = now_local.date()
        # если уже отправляли сегодня (перезапуск бота после времени) — не слать повторно
        last_rem = user_row.get("last_reminder_date") if user_row else None
        if last_rem == local_date.isoformat():
            logger.debug(f"[reminder] skip user={user_id} reason=already_sent date={local_date}")
            return
        entry = db.get_diary_entry(user_id=user_id, entry_date=local_date)
        if entry:
            logger.debug(f"[reminder] skip user={user_id} reason=entry_exists")
            return
        lang = user_row.get("language_code", "ru") if user_row else "ru"
        # tlgbot уже является Telethon client; используем прямой вызов
        await tlgbot.send_message(user_id, tlgbot.i18n.t("reminder_no_entry", lang=lang))
        db.update_last_reminder_date(user_id, local_date.isoformat())
        logger.info(f"[reminder] sent user={user_id} date={local_date} tz={tz.key}")
    except Exception as e:
        logger.error(f"[reminder] error user={user_id}: {e}")


def schedule_user_reminder(tlgbot, db: DatabaseManager, user_id: int, hhmm: str):
    if not hasattr(tlgbot, "scheduler"):
        logger.error("[reminder] scheduler not attached to bot")
        return
    job_id = str(user_id)
    scheduler = tlgbot.scheduler
    # remove existing
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass
    parsed = parse_hhmm(hhmm)
    if not parsed:
        logger.error(f"[reminder] invalid time '{hhmm}' for user={user_id}")
        return
    hour, minute = parsed
    # timezone per user
    user_row = db.get_user(user_id)
    tz_name = (user_row.get("timezone") if user_row else "Europe/Moscow") or "Europe/Moscow"
    scheduler.add_job(
        send_reminder_job,
        "cron",
        hour=hour,
        minute=minute,
        id=job_id,
        kwargs={"user_id": user_id, "tlgbot": tlgbot, "db": db},
        replace_existing=True,
        misfire_grace_time=300,
        timezone=tz_name,
    )
    logger.info(f"[reminder] rescheduled user={user_id} time={hhmm} tz={tz_name}")


def disable_user_reminder(tlgbot, user_id: int):
    if not hasattr(tlgbot, "scheduler"):
        return
    try:
        tlgbot.scheduler.remove_job(str(user_id))
        logger.info(f"[reminder] disabled user={user_id}")
    except Exception:
        pass
