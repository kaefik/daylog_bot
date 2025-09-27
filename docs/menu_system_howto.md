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
    'order': 10,             # порядок (меньше -> раньше)
    # 'admin_only': True     # (необязательно) показать только администраторам
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
Особенность с админскими кнопками: для администратора кэшируется отдельно (`<lang>|admin`). Полная очистка (`invalidate_menu()`) нужна если менялись admin_only пункты.
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
- [ ] (если нужно только для админов) `admin_only: True`
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

Q: Почему админские кнопки не видны обычному пользователю?  
A: У пункта стоит `admin_only: True`, отображаются только если Telegram ID есть в списке админов.

Q: Как определяется что пользователь админ?  
A: Через helper `_is_admin_user(user_id, admins)` — он нормализует типы (int/str) и сравнивает.

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

## 16. Админские пункты меню
Добавлено поле `admin_only` в `MenuEntry`.

### 16.1 Регистрация
```python
register_menu({
    'key': 'listusers',
    'tr_key': 'menu_listusers',
    'plugin': '_core',
    'handler': 'info_user_admin',
    'order': 900,
    'admin_only': True,
})
```

### 16.2 Локализация
Добавь ключи `menu_<key>` во все JSON локали. Для трёх стандартных админских:
```
menu_listusers / menu_adduser / menu_deluser
```

### 16.3 Отрисовка и кэш
`build_menu(lang, is_admin)` формирует список. Ключ кэша:
```
lang            # обычные пользователи
f"{lang}|admin"  # администраторы
```
Это исключает утечки: админ не «зашумляет» меню обычного пользователя и наоборот.

### 16.4 Определение администратора
В `send_main_menu` вызывается `_is_admin_user(user_id, admins)`:
```
def _is_admin_user(user_id, admins):
        # приводит всё к int/str сопоставимому виду, логирует результат
```
Обрабатывает смешанные типы (например строка в БД и int в апдейте).

### 16.5 Тестирование
Пример из `tests/test_admin_menu.py` (упрощённо):
```python
buttons_admin = build_menu('ru', is_admin=True)
flat_admin = [b[0].data for row in buttons_admin for b in row]
assert any(d.endswith(':listusers') for d in flat_admin)

buttons_user = build_menu('ru', is_admin=False)
flat_user = [b[0].data for row in buttons_user for b in row]
assert not any(d.endswith(':listusers') for d in flat_user)
```

### 16.6 Инвалидация
При добавлении/удалении админского пункта после деплоя достаточно рестарта. Для горячего изменения:
```
from bot.menu_system import invalidate_menu
invalidate_menu()  # очистит оба слоя (обычный и admin)
```

### 16.7 Частые проблемы
| Симптом | Причина | Решение |
|---------|---------|---------|
| Админ не видит кнопку | Его ID не в списке админов / кэш не очищен | Добавь ID, вызови `invalidate_menu()` |
| Обычный видит админскую | Смесь тестовых данных: пользователь стал админом, кэш не сброшен | `invalidate_menu()` и перепроверить роль |
| Кнопка есть, но клик не работает | Неверный handler в регистрации | Исправить имя async функции |

### 16.8 Рекомендации
- Не ставить `order` админских вплотную к пользовательским (используй диапазон > 800).
- Локализуй коротко: кнопка не должна ломать ширину строки.
- Логи смотри по префиксу `menu_system` при отладке.

### 16.9 Дальнейшие улучшения *(идеи)*
- Динамическая перезагрузка списка админов без рестарта (команда `/refresh_admins`).
- Команда для вывода текущего набора пунктов меню и их флагов.

---
Так добавляются и контролируются админские пункты.

## 17. Структура данных MenuEntry

Класс `MenuEntry` содержит всю информацию о пункте меню:

```python
@dataclass
class MenuEntry:
    key: str  # Уникальный идентификатор
    tr_key: str  # Ключ перевода
    plugin: str  # Имя плагина для поиска обработчика
    handler: str  # Имя функции-обработчика
    order: int  # Порядок сортировки
    admin_only: bool = False  # Только для админов
    # Возможные расширения:
    # enabled: bool = True  # Динамическая видимость
    # custom_data: Dict[str, Any] = None  # Дополнительные данные
```

При вызове `register_menu` происходит преобразование словаря в этот класс, проверка уникальности `key` и добавление в `MENU_REGISTRY`.

## 18. Внутреннее устройство кэширования

### 18.1 Структура кэша
```python
MENU_CACHE: Dict[str, List[List[Button]]] = {}
```

Ключи кэша имеют два формата:
- `ru`, `en`, `tt` и т.д. — для обычных пользователей
- `ru|admin`, `en|admin` — для администраторов

Значения — готовые списки кнопок для отправки.

### 18.2 Когда происходит инвалидация кэша
1. При явном вызове `invalidate_menu()`
2. При перезапуске бота
3. При регистрации нового пункта меню не происходит (!)

### 18.3 Отложенная сборка меню
Меню строится в момент первого запроса для конкретного языка (ленивая инициализация):

```python
def build_menu(lang, is_admin=False):
    cache_key = f"{lang}|admin" if is_admin else lang
    if cache_key in MENU_CACHE:
        return MENU_CACHE[cache_key]
    
    # Здесь происходит формирование меню
    # ...
    
    MENU_CACHE[cache_key] = buttons
    return buttons
```

## 19. Рекомендации по UI/UX меню

### 19.1 Эффективные тексты кнопок
- Используй эмодзи в начале для визуальной категоризации: `🗓 Календарь`, `📝 Запись`, `⚙️ Настройки`
- Группируй похожие функции схожими эмодзи (📊📈📉 для аналитики)
- Оптимальная длина текста: 1-3 слова (до 20 символов)
- Единообразие стиля: все с заглавной/строчной, все с эмодзи/без эмодзи

### 19.2 Структура меню
- Располагай часто используемые функции в начале (с низким `order`)
- Логически связанные функции размещай с последовательными `order`
- При большом количестве кнопок (>6) рассмотри создание подменю или категорий
- Рекомендуемые диапазоны `order`:
  - 1-199: основные повседневные функции
  - 200-599: второстепенные функции
  - 600-799: редко используемые функции
  - 800+: админские функции

### 19.3 Адаптивность
- Проверяй отображение меню в разных клиентах Telegram (iOS/Android/Desktop/Web)
- Учитывай, что в мобильных клиентах длинный текст может сжиматься или переноситься
- Тестируй во всех поддерживаемых языках (особенно в языках с длинными словами)

### 19.4 Группировка кнопок
Стандартная компоновка — 2 кнопки в строке, но логическое разделение можно обеспечить:
- Выделяя отдельные строки для особых функций (например, одна кнопка в строке для "Настройки")
- Визуальными маркерами (эмодзи, стиль текста) для обозначения групп
- Использованием похожих префиксов для связанных кнопок

## 20. Примеры расширения системы меню

### 20.1 Добавление счетчиков в кнопки
Счетчики могут использоваться для отображения непрочитанных сообщений, количества задач и т.д.:

```python
async def build_menu_with_counters(user_id, lang):
    base_buttons = build_menu(lang, is_admin=_is_admin_user(user_id, ADMINS))
    
    # Получаем счетчики
    unread = await get_unread_count(user_id)
    tasks = await get_task_count(user_id)
    
    # Обновляем тексты кнопок
    for row in base_buttons:
        for btn in row:
            if "menu:messages" in btn.data and unread > 0:
                btn.text = f"{btn.text} ({unread})"
            elif "menu:tasks" in btn.data and tasks > 0:
                btn.text = f"{btn.text} ({tasks})"
    
    return base_buttons
```

### 20.2 Динамические кнопки на основе состояния пользователя
Расширение меню для отображения разных наборов кнопок в зависимости от статуса:

```python
async def build_contextual_menu(user_id, lang):
    # Базовое меню
    buttons = build_menu(lang, is_admin=_is_admin_user(user_id, ADMINS))
    
    # Проверка наличия анкеты
    has_profile = await check_user_profile(user_id)
    
    # Добавляем кнопку заполнения анкеты для новых пользователей
    if not has_profile:
        profile_btn = Button.inline(
            i18n.t('menu_complete_profile', lang=lang),
            data="menu:complete_profile"
        )
        buttons.insert(0, [profile_btn])
    
    return buttons
```

### 20.3 Персонализация меню
Возможность пользователям настраивать собственное меню:

```python
async def get_user_menu_config(user_id):
    # Получаем настройки пользователя из БД
    settings = await get_user_settings(user_id)
    return settings.get('menu_config', {})

def filter_menu_by_user_config(buttons, user_config):
    # Оставляем только кнопки, включенные пользователем
    result = []
    for row in buttons:
        filtered_row = []
        for btn in row:
            key = btn.data.split(':', 1)[1]  # menu:key -> key
            if key in user_config.get('enabled_items', []):
                filtered_row.append(btn)
        if filtered_row:
            result.append(filtered_row)
    return result

## 21. Интеграция с другими системами

### 21.1 Логирование пользовательских действий
Система меню может собирать статистику использования для аналитики:

```python
async def dispatch_command(event, key):
    user_id = event.sender_id
    # Логирование в базу данных или файл
    logger.info(f"Menu action: user={user_id}, action={key}")
    
    # Отправка в метрики (например Prometheus)
    menu_usage_counter.labels(menu_item=key).inc()
    
    # Основной код обработчика...
    plugin_name = None
    for entry in MENU_REGISTRY:
        if entry.key == key:
            plugin_name = entry.plugin
            handler_name = entry.handler
            # ...
```

### 21.2 Интеграция с системой уведомлений
Можно реализовать автоматическое обновление меню при появлении уведомлений:

```python
# В системе уведомлений:
async def add_notification(user_id, notification_type):
    # Добавляем уведомление
    await store_notification(user_id, notification_type)
    
    # Инвалидируем кэш меню для пользователя
    invalidate_user_menu(user_id)

# Расширение invalidation:
def invalidate_user_menu(user_id):
    # Получаем язык пользователя
    lang = get_user_language(user_id)
    is_admin = _is_admin_user(user_id, ADMINS)
    
    # Инвалидируем кэш для конкретного языка
    cache_key = f"{lang}|admin" if is_admin else lang
    if cache_key in MENU_CACHE:
        del MENU_CACHE[cache_key]
```

### 21.3 Система прав доступа
Расширение системы меню для поддержки сложной логики прав:

```python
@dataclass
class MenuEntry:
    key: str
    tr_key: str
    plugin: str
    handler: str
    order: int
    admin_only: bool = False
    required_permissions: List[str] = field(default_factory=list)  # Новое поле

def build_menu(lang, is_admin=False, user_permissions=None):
    # ...
    # Фильтруем пункты по правам
    filtered_entries = []
    for entry in sorted_entries:
        if entry.admin_only and not is_admin:
            continue
        
        if entry.required_permissions:
            if not user_permissions:
                continue
            
            if not all(perm in user_permissions for perm in entry.required_permissions):
                continue
                
        filtered_entries.append(entry)
    # ...
```

## 22. Расширенные примеры тестирования

### 22.1 Интеграционные тесты с моками

```python
@pytest.mark.asyncio
async def test_menu_dispatch():
    from bot.menu_system import dispatch_command
    
    # Подготовка тестовой среды
    invalidate_menu()
    register_menu({
        'key': 'test_item',
        'tr_key': 'menu_test',
        'plugin': 'test_plugin',
        'handler': 'test_handler',
        'order': 999
    })
    
    # Создаем мок-объект события
    event = MagicMock()
    event.sender_id = 12345
    event.respond = AsyncMock()
    
    # Мокаем импорт плагина и вызов обработчика
    with patch('bot.menu_system.tlgbot._plugins', {
        'test_plugin': {
            'test_handler': AsyncMock()
        }
    }):
        # Вызываем тестируемый метод
        await dispatch_command(event, 'test_item')
        
        # Проверяем, что был вызван правильный обработчик
        tlgbot._plugins['test_plugin']['test_handler'].assert_called_once_with(event)
```

### 22.2 Тесты безопасности
```python
def test_menu_admin_access():
    """Проверка, что админские кнопки не попадают обычным пользователям"""
    # Регистрируем админскую кнопку
    register_menu({
        'key': 'admin_test',
        'tr_key': 'menu_admin_test',
        'plugin': 'admin',
        'handler': 'admin_handler',
        'order': 999,
        'admin_only': True
    })
    
    # Получаем меню для обычного пользователя
    user_menu = build_menu('ru', is_admin=False)
    user_items = [btn.data for row in user_menu for btn in row]
    
    # Получаем меню для администратора
    admin_menu = build_menu('ru', is_admin=True)
    admin_items = [btn.data for row in admin_menu for btn in row]
    
    # Проверяем, что админская кнопка есть только в меню администратора
    assert 'menu:admin_test' not in user_items
    assert 'menu:admin_test' in admin_items
```
```
