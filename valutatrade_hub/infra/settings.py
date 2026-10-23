'''Единая точка конфигурации проекта (Singleton)'''
import tomllib
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT_FILE = PROJECT_ROOT / 'pyproject.toml'

DEFAULTS = {
    'data_dir': 'data',
    'users_file': 'data/users.json',
    'portfolios_file': 'data/portfolios.json',
    'rates_file': 'data/rates.json',
    'rates_ttl_seconds': 300,
    'default_base_currency': 'USD',
    'log_dir': 'logs',
    'log_format': '%(asctime)s %(levelname)s %(message)s',
}
PATH_KEYS = ('data_dir', 'users_file', 'portfolios_file', 'rates_file', 'log_dir')


class SettingsLoader:
    '''Загружает настройки один раз и отдаёт их всему приложению.

    Singleton сделан через __new__, а не через метакласс: так проще и
    нагляднее — вся логика «одного экземпляра» видна прямо в классе.
    '''
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self):
        config = dict(DEFAULTS)
        if PYPROJECT_FILE.exists():
            with open(PYPROJECT_FILE, 'rb') as f:
                pyproject = tomllib.load(f)
            config.update(pyproject.get('tool', {}).get('valutatrade', {}))

        for key in PATH_KEYS:
            path = Path(config[key])
            if not path.is_absolute():
                path = PROJECT_ROOT / path
            config[key] = path

        self._config = config

    def get(self, key: str, default: Any = None):
        '''Возвращает значение настройки или default, если ключа нет'''
        return self._config.get(key, default)

    def reload(self) -> None:
        '''Перечитывает конфигурацию из файла'''
        self._load()


settings = SettingsLoader()