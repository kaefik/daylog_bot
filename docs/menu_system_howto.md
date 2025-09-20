# HowTo: Управление главным меню (/start)

Этот документ описывает как добавить, изменить или удалить пункты главного inline-меню.

## 1. Архитектура кратко
- Код меню: `bot/menu_system.py`
- Реестр пунктов: `MENU_REGISTRY` (список `MenuEntry`)
- Регистрация: через `register_menu({...})` внутри каждого плагина на верхнем уровне (выполняется при загрузке плагина).
- Callback: inline-кнопки имеют `data="menu:<key>"`; общий роутер ловит `'^menu:'` и вызывает `dispatch_command`.
- Кэш кнопок по языку: `MENU_CACHE`.

## 2. Формат пункта меню
Пример при регистрации:
```python
register_menu({
  'key': 'today',          # уникальный внутренний ключ
  'tr_key': 'menu_today',  # ключ локализации текста кнопки
  'plugin': 'today',       # имя папки плагина (ключ в tlgbot._plugins)
  'handler': 'today_handler',  # имя async функции
  'order': 10              # порядок (меньше -> раньше)
})
```

## 3. Добавить новый пункт меню
1. Создай (или открой) файл плагина: `bot/plugins_bot/<newcmd>/<newcmd>.py`.
2. В начале файла после импортов добавь:
```python
try:
    from bot.menu_system import register_menu
    register_menu({
        'key': 'newcmd',
        'tr_key': 'menu_newcmd',
        'plugin': 'newcmd',
        'handler': 'newcmd_handler',
        'order': 50
    })
except Exception:
    pass
```
3. Реализуй обработчик команды:
```python
@tlgbot.on(tlgbot.cmd('newcmd'))
async def newcmd_handler(event):
    await event.respond("Команда newcmd работает!")
```
4. Добавь перевод в каждый файл локали `bot/locales/*.json`:
```json
"menu_newcmd": "🆕 Новое"
```
5. Перезапусти бота. При `/start` пункт появится автоматически.

## 4. Удалить пункт меню
1. Найди регистрацию `register_menu({... 'key': 'X' ...})` в соответствующем плагине.
2. Удали или закомментируй этот блок.
3. Перезапусти бота. (При hot-reload старый пункт может остаться в кэше — очистка: см. раздел 8.)

## 5. Изменить текст кнопки
1. Правь соответствующий ключ локализации (`tr_key`) в JSON файлах локалей.
2. Не меняй `key`, иначе сломается callback сопоставление.
3. Очисти кэш меню (см. раздел 8) или просто нажми `/start` заново — при смене языка/рестарте кэш обновится.

## 6. Переименовать handler или plugin
- Если переименовал файл плагина (директорию) — обнови поле `plugin` в регистрации.
- Если переименовал функцию — обнови `handler`.
- Иначе при нажатии кнопки будет лог `handler missing`.

## 7. Изменить порядок
- Просто скорректируй `order`. Меньшие значения идут первыми.
- Кнопки группируются по 2 в строке (логика в `build_menu`). При необходимости изменить — модифицируй `build_menu`.

## 8. Очистка / инвалидация меню
В коде:
```python
from bot.menu_system import invalidate_menu
invalidate_menu()        # очистить весь кэш
invalidate_menu('ru')    # очистить только для языка
```
Добавь вызов после массовой правки переводов или удаления пунктов.

## 9. Debug / проверки
- Логи при регистрации: `menu_system: registered menu entry <key>`
- Лог при нажатии: `menu_system: callback router attached` (один раз при инициализации)
- Ошибка плагина: `plugin X not loaded` — плагин не загрузился/ошибка в нём.
- Ошибка хендлера: `handler Y missing` — опечатка в имени функции.

## 10. Частые ошибки
| Проблема | Причина | Решение |
|----------|---------|---------|
| Кнопка не реагирует | Нет callback роутера | Убедись что вызван `init_menu_system` (делается в `/start`) |
| Появился старый текст | Кэш не очищен | `invalidate_menu()` или рестарт |
| Падает при нажатии | Неверный handler/plugin | Исправь регистрацию |
| Нет перевода | Отсутствует ключ в локали | Добавь ключ во все JSON |

## 11. Быстрый чеклист добавления
- [ ] Код плагина создан
- [ ] register_menu добавлен
- [ ] handler реализован
- [ ] Локализация добавлена
- [ ] Порядок (order) выставлен
- [ ] Проверено через `/start`

## 12. Расширение (опционально)
- Можно заменить фиксированную ширину строки (2) на настройку.
- Можно добавить скрытые пункты (флаг `enabled` в MenuEntry). *(спекуляция)*
- Можно сделать авто-инвалидацию при изменении файлов локалей (watcher). *(спекуляция)*

## 13. FAQ
Q: Нужно ли вручную добавлять кнопки в start_cmd?  
A: Нет, они строятся автоматически из реестра.

Q: Можно ли кнопке вызывать не команду, а произвольную функцию?  
A: Да, главное чтобы функция была async и имя совпадало с `handler`.

Q: Что если два плагина зарегистрируют одинаковый `key`?  
A: Второй silently игнорируется — смотри логи.

---
Коротко: добавляешь register_menu + handler + перевод — готово.

## 14. Тестирование меню
Минимальные сценарии (можно оформить pytest):
```python
from bot.menu_system import MENU_REGISTRY, register_menu, build_menu, invalidate_menu

def test_register_unique():
    invalidate_menu()
    before = len(MENU_REGISTRY)
    register_menu({'key':'_t1','tr_key':'menu_today','plugin':'today','handler':'today_handler','order':999})
    assert len(MENU_REGISTRY) == before + 1

def test_duplicate_ignored():
    before = len(MENU_REGISTRY)
    register_menu({'key':'_t1','tr_key':'menu_today','plugin':'today','handler':'today_handler','order':999})
    assert len(MENU_REGISTRY) == before  # не увеличилось
```
Проверка кнопок: `buttons = build_menu('ru')` → assert структура (список списков), наличие callback data `menu:`.

## 15. Динамическая видимость *(если внедрён флаг enabled)*
- Расширяем `MenuEntry` полем `enabled: bool = True`.
- В `build_menu` игнорируем записи где `enabled is False`.
- Добавляем функции:
```python
def disable_menu(key: str):
    for e in MENU_REGISTRY:
        if e.key == key:
            e.enabled = False
    MENU_CACHE.clear()

def enable_menu(key: str):
    for e in MENU_REGISTRY:
        if e.key == key:
            e.enabled = True
    MENU_CACHE.clear()
```
Использование: временно скрыть экспорт → `disable_menu('export')`.
