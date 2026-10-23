'''Единая точка доступа к JSON-хранилищу (Singleton)'''
import json
import os
import tempfile
from pathlib import Path

from valutatrade_hub.infra.settings import settings

_STORAGES = {
    'users': ('users_file', []),
    'portfolios': ('portfolios_file', []),
    'rates': ('rates_file', {}),
}


class DatabaseManager:
    '''Читает и записывает JSON-файлы проекта'''
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @staticmethod
    def _path(name: str) -> Path:
        if name not in _STORAGES:
            raise ValueError(f'Неизвестное хранилище: {name}')
        return Path(settings.get(_STORAGES[name][0]))

    def read(self, name: str):
        '''Возвращает данные хранилища (список или словарь)'''
        path = self._path(name)
        if not path.exists():
            return _STORAGES[name][1].copy()
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def write(self, name: str, data) -> None:
        '''Безопасно перезаписывает хранилище целиком'''
        path = self._path(name)
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


db = DatabaseManager()