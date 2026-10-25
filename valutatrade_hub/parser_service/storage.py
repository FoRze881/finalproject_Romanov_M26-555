'''Хранилище Parser Service (снимок rates.json и история exchange_rates.json)'''
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

# Служебные ключи rates.json — всё остальное в файле является валютными парами
SERVICE_KEYS = ('source', 'last_refresh')


def _read_json(path: Path, default):
    '''Читает JSON; отсутствующий или пустой файл — значение по умолчанию'''
    if not path.exists() or path.stat().st_size == 0:
        return default
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _write_json_atomic(path: Path, data):
    '''Атомарная запись'''
    text = json.dumps(data, ensure_ascii=False, indent=2)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(text)
        os.replace(tmp_path, path)
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise


def _parse_time(value: str | None):
    return datetime.fromisoformat(value) if value else datetime.min


class RatesStorage:
    '''rates.json хранится в том формате, который читает ядро:
    {"EUR_USD": {"rate": ..., "updated_at": ...}, ..., "source": ..., "last_refresh": ...}'''

    def __init__(self, rates_path: Path, history_path: Path):
        self.rates_path = Path(rates_path)
        self.history_path = Path(history_path)

    def load_pairs(self) -> dict:
        '''Только валютные пары из rates.json, без служебных ключей'''
        data = _read_json(self.rates_path, {})
        return {key: value for key, value in data.items()
                if key not in SERVICE_KEYS and isinstance(value, dict)}

    def save_snapshot(self, updates: dict, refreshed_at: str, source: str) -> int:
        '''Обновляет rates.json. Пара заменяется, если новая запись не старее текущей.
        Возвращает число обновлённых пар.'''
        data = _read_json(self.rates_path, {})
        applied = 0
        for pair, new_value in updates.items():
            old_value = data.get(pair)
            if (not isinstance(old_value, dict) or
                    _parse_time(new_value['updated_at']) >= _parse_time(old_value.get('updated_at'))):
                data[pair] = new_value
                applied += 1
        data['source'] = source
        data['last_refresh'] = refreshed_at
        _write_json_atomic(self.rates_path, data)
        return applied

    def append_history(self, records: list[dict]) -> int:
        '''Дописывает замеры в exchange_rates.json, пропуская уже известные id.
        Возвращает число добавленных записей.'''
        history = _read_json(self.history_path, [])
        known_ids = {record['id'] for record in history}
        new_records = [record for record in records if record['id'] not in known_ids]
        if new_records:
            history.extend(new_records)
            _write_json_atomic(self.history_path, history)
        return len(new_records)