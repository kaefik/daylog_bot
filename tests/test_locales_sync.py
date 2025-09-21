import json
import pathlib

LOCALES_DIR = pathlib.Path(__file__).parent.parent / 'bot' / 'locales'

# Если добавите новую локаль, тест автоматически её подхватит

def load_locales():
    locales = {}
    for path in LOCALES_DIR.glob('*.json'):
        with path.open('r', encoding='utf-8') as f:
            locales[path.stem] = json.load(f)
    return locales

def test_locales_keys_in_sync():
    locales = load_locales()
    assert locales, 'Не найдены файлы локалей.'

    # Базовой возьмём ru если есть, иначе первую
    base_name = 'ru' if 'ru' in locales else next(iter(locales))
    base_keys = set(locales[base_name].keys())

    problems = []
    for name, data in sorted(locales.items()):
        keys = set(data.keys())
        missing = base_keys - keys
        extra = keys - base_keys
        if missing or extra:
            problems.append(
                f"Локаль {name}: отсутствуют ({len(missing)}): {sorted(missing)}; лишние ({len(extra)}): {sorted(extra)}"
            )
    if problems:
        all_keys_union = set().union(*[set(d.keys()) for d in locales.values()])
        # Также покажем локали с неполным покрытием union (редко, но полезно)
        coverage = []
        for name, data in sorted(locales.items()):
            missing_union = all_keys_union - set(data.keys())
            if missing_union:
                coverage.append(f"Локаль {name} не содержит {len(missing_union)} ключей union: {sorted(missing_union)}")
        msg = '\n'.join(problems + coverage)
        raise AssertionError('Несинхронизированные ключи локалей:\n' + msg)


def test_locales_no_empty_values():
    locales = load_locales()
    empty_values = []
    for name, data in locales.items():
        for k, v in data.items():
            if v is None or (isinstance(v, str) and v.strip() == ''):
                empty_values.append(f"{name}:{k}")
    if empty_values:
        raise AssertionError('Пустые значения переводов: ' + ', '.join(empty_values))
