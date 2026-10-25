'''Конфигурация Parser Service'''
import os
from dataclasses import dataclass, field
from pathlib import Path

from valutatrade_hub.infra.settings import PROJECT_ROOT, settings

ENV_FILE = PROJECT_ROOT / '.env'


def _load_env_file(path: Path = ENV_FILE) -> None:
    '''Переносит строки KEY=VALUE из файла .env в переменные окружения.
    Уже заданные переменные окружения не перезаписываются.'''
    if not path.exists():
        return
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"\''))


def _read_api_key() -> str | None:
    _load_env_file()
    return os.getenv('EXCHANGERATE_API_KEY')


@dataclass(frozen=True)
class ParserConfig:
    # Ключ не хранится в коде: берётся из переменной окружения или из .env.
    # repr=False — чтобы ключ не попал в print(config) или в лог
    EXCHANGERATE_API_KEY: str | None = field(default_factory=_read_api_key, repr=False)

    # Эндпоинты
    COINGECKO_URL: str = 'https://api.coingecko.com/api/v3/simple/price'
    EXCHANGERATE_API_URL: str = 'https://v6.exchangerate-api.com/v6'

    # Списки валют (совпадают с реестром валют в core/currencies.py)
    BASE_CURRENCY: str = 'USD'
    FIAT_CURRENCIES: tuple = ('EUR', 'RUB')
    CRYPTO_CURRENCIES: tuple = ('BTC', 'ETH')
    # Изменяемое значение по умолчанию (dict) в dataclass задаётся только через default_factory
    CRYPTO_ID_MAP: dict = field(default_factory=lambda: {
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'SOL': 'solana',
    })

    # Пути берутся из SettingsLoader — они уже абсолютные
    RATES_FILE_PATH: Path = field(default_factory=lambda: settings.get('rates_file'))
    HISTORY_FILE_PATH: Path = field(
        default_factory=lambda: settings.get('data_dir') / 'exchange_rates.json')

    # Сетевые параметры
    REQUEST_TIMEOUT: int = 10