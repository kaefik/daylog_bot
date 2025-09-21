import os
from core.database.manager import DatabaseManager
from cfg.config_tlg import DAYLOG_DB_PATH


def test_update_language_code_persist():
    db = DatabaseManager(db_path=DAYLOG_DB_PATH)
    user_id = 99999999  # тестовый
    # создаём пользователя если нет
    db.create_user(user_id, username="testuser", first_name="Test", last_name="User")
    before = db.get_user(user_id)
    assert before is not None
    # меняем язык
    assert db.update_user_settings(user_id, language_code='en') is True
    after = db.get_user(user_id)
    assert after is not None
    assert after['language_code'] == 'en'
    # возвращаем обратно
    db.update_user_settings(user_id, language_code='ru')
