# Система меню DayLog Bot

Документ описывает предложенные улучшения для главного меню бота и маршрутизации команд.

## 1. Цели
- Стабильность: избавиться от сравнения локализованных текстов.
- Расширяемость: добавить пункт меню без ручного редактирования массивов.
- Производительность: уменьшить повторную генерацию кнопок.
- Единообразие вызова обработчиков.

## 2. Кэш меню (MENU_CACHE)
Хранить готовые наборы кнопок по языку.
```
MENU_CACHE = { 'ru': [[Button...], ...], 'en': ... }
```
Инвалидация:
- Смена языка пользователем (/setlang) — локально можно очищать только запись нужного языка.
- Перезагрузка/добавление плагинов.
- Добавление/изменение переводов (ручной вызов invalidate).

### API (предложение)
```
def get_menu(lang: str):
    if lang in MENU_CACHE: return MENU_CACHE[lang]
    buttons = build_menu(lang)
    MENU_CACHE[lang] = buttons
    return buttons

def invalidate_menu(lang: str | None = None):
    if lang: MENU_CACHE.pop(lang, None)
    else: MENU_CACHE.clear()
```

## 3. Mapping (меню → команды)
Избежать сравнения локализованных строк. Два подхода:

### 3.1 Inline-кнопки с callback data
```
Button.inline(label, data=f"menu:today")
```
Обработчик:
```
@tlgbot.on(events.CallbackQuery(pattern=r'^menu:'))
async def menu_router(event):
    key = event.data.decode().split(':',1)[1]
    await dispatch_command(key, event)
```
Плюсы: устойчиво, не зависит от текста; минус — меняется UX (inline вместо reply).

### 3.2 Reply-клавиатура + registry
Хранить реестр:
```
MENU_REGISTRY = {
  'today': {'tr_key': 'menu_today', 'handler': ('today','today_handler'), 'order': 10},
  ...
}
```
При генерации меню подставляется перевод. В обработчике — преобразование текста в ключ через обратный словарь, собранный для текущего языка. (Есть риск коллизий/изменений перевода.)
Рекомендуемый путь: переход на inline.

## 4. Авто-генерация меню (registry)
Плагин объявляет словарь:
```
MENU_ENTRY = {
    'key': 'today',
    'tr_key': 'menu_today',
    'handler': 'today_handler',
    'order': 10,
    'row': 0  # опционально: фиксированная строка
}
```
При загрузке плагинов ядро проверяет `hasattr(mod, 'MENU_ENTRY')` и регистрирует.

### Алгоритм build_menu
1. Собрать все entries.
2. Отсортировать по `order`.
3. Сгруппировать по `row` (если указан) или разложить по N в строке (напр. 2).
4. Создать inline-кнопки.

## 5. Унифицированный роутер команд
```
COMMAND_ROUTER = {
  'today': ('today', 'today_handler'),
  'yesterday': ('yesterday','yesterday_handler'),
  'view': ('view','view_command_handler'),
  'export': ('export','export_command_handler'),
}

async def dispatch_command(key: str, event):
    plugin_name, handler_name = COMMAND_ROUTER[key]
    mod = tlgbot._plugins.get(plugin_name)
    if not mod:
        logger.error(f"dispatch_command: plugin {plugin_name} not loaded")
        return
    handler = getattr(mod, handler_name, None)
    if not handler:
        logger.error(f"dispatch_command: handler {handler_name} missing in {plugin_name}")
        return
    await handler(event)
```
`menu_router` или callback handler дергает `dispatch_command`.

## 6. Инвалидация / события
Точки для очистки кэша / перестроения меню:
- `/setlang` (только конкретный язык, опционально просто не кэшировать локально для юзера).
- Reload плагинов (существует в core).
- Добавление нового `MENU_ENTRY` (при hot reload — пересоздать).

## 7. Последовательность миграции (пошагово)
1. Ввести `COMMAND_ROUTER` и заменить текущий `safe_call_command` на `dispatch_command`.
2. Добавить поддержку inline-кнопок меню в `start_cmd` (параллельно оставить старую клавиатуру как fallback).
3. Перенести генерацию меню в отдельный модуль `bot/menu_system.py`.
4. Добавить поддержку `MENU_ENTRY` в плагинах (`today`, `yesterday`, `view`, `export`).
5. Внедрить кэш + invalidate.
6. Удалить устаревший `menu_handlers.py` (когда inline полностью перейдет).

## 8. Риски и смягчение
| Риск | Смягчение |
|------|-----------|
| Несовместимость старых кнопок | Стадия перехода: отправлять обе клавиатуры (reply + inline) временно |
| Коллизия ключей | Проверка уникальности при регистрации MENU_ENTRY |
| Забыли добавить handler | Логгер + пропуск, не ломает меню |
| Утечки кэша при смене языков | Тонкая инвалидация по ключу lang |

## 9. Быстрый MVP реализации
Минимум для старта: пункты 1 (COMMAND_ROUTER) + 5 (dispatch_command) + 2 (подмена reply на inline) без registry (жестко прописать список). Далее расширять до registry.

## 10. Пример будущего модуля menu_system.py (скелет)
```python
# bot/menu_system.py
from telethon import Button, events

MENU_REGISTRY = []
MENU_CACHE = {}

def register_menu(entry):
    MENU_REGISTRY.append(entry)

def build_menu(lang: str):
    if lang in MENU_CACHE:
        return MENU_CACHE[lang]
    rows = []
    ordered = sorted(MENU_REGISTRY, key=lambda e: e.get('order', 100))
    current_row = []
    for i, entry in enumerate(ordered):
        label = tlgbot.i18n.t(entry['tr_key'], lang=lang)
        current_row.append(Button.inline(label, data=f"menu:{entry['key']}"))
        if len(current_row) == 2:
            rows.append(current_row)
            current_row = []
    if current_row:
        rows.append(current_row)
    MENU_CACHE[lang] = rows
    return rows

async def dispatch_command(key: str, event):
    from bot.plugins_bot.menu_handlers.menu_handlers import COMMAND_ROUTER  # или централизованно
    plugin, handler_name = COMMAND_ROUTER.get(key, (None, None))
    if not plugin:
        logger.error(f"dispatch_command: unknown key {key}")
        return
    mod = tlgbot._plugins.get(plugin)
    if not mod:
        logger.error(f"dispatch_command: plugin {plugin} not loaded")
        return
    handler = getattr(mod, handler_name, None)
    if not handler:
        logger.error(f"dispatch_command: handler {handler_name} missing in {plugin}")
        return
    await handler(event)
```

## 11. Итог
Документ фиксирует архитектурные улучшения меню: кэширование, data-driven генерация, устойчивое сопоставление кнопок и унифицированный роутер. Реализация может вноситься поэтапно без ломки текущего UX.
