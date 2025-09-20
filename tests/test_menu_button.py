from bot.tlgbotcore.i18n import I18n


def test_menu_show_button_localized():
    i18n = I18n(locales_path="bot/locales", default_lang="ru")
    missing = []
    empty = []
    for lang, data in i18n.locales.items():
        if 'menu_show_button' not in data:
            missing.append(lang)
        elif not str(data['menu_show_button']).strip():
            empty.append(lang)
    assert not missing, f"Отсутствует ключ menu_show_button в локалях: {missing}"
    assert not empty, f"Пустой перевод menu_show_button в локалях: {empty}"
