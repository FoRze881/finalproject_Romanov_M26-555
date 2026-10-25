'''Клиенты внешних API курсов валют'''
import math
import time
from abc import ABC, abstractmethod

import requests

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.config import ParserConfig


class BaseApiClient(ABC):
    '''Общий интерфейс для всех источников курсов'''
    name = 'base'

    def __init__(self, config: ParserConfig):
        self.config = config
        self.last_meta: dict = {}

    @abstractmethod
    def fetch_rates(self) -> dict:
        '''Возвращает курсы в виде {"BTC_USD": 59337.21, ...}:
        сколько единиц второй валюты стоит одна единица первой'''

    def _get_json(self, url: str, params: dict | None = None):
        '''GET-запрос: сетевые ошибки и плохие коды ответа превращаются в ApiRequestError'''
        started = time.perf_counter()
        try:
            response = requests.get(url, params=params, timeout=self.config.REQUEST_TIMEOUT)
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f'сетевая ошибка ({type(e).__name__})') from None

        self.last_meta = {
            'status_code': response.status_code,
            'request_ms': round((time.perf_counter() - started) * 1000),
        }
        if response.status_code == 429:
            raise ApiRequestError('превышен лимит запросов (429 Too Many Requests)')
        try:
            data = response.json()
        except ValueError:
            raise ApiRequestError(
                f'ответ не является JSON (HTTP {response.status_code})') from None
        if response.status_code != 200:
            detail = data.get('error-type') if isinstance(data, dict) else None
            reason = f'HTTP {response.status_code}' + (f' ({detail})' if detail else '')
            raise ApiRequestError(reason)
        if not isinstance(data, dict):
            raise ApiRequestError('неожиданный формат ответа')
        return data

    @staticmethod
    def _is_valid_rate(value) -> bool:
        '''Курс — положительное конечное число (bool отсекается отдельно: это подкласс int)'''
        return (isinstance(value, (int, float)) and not isinstance(value, bool)
                and math.isfinite(value) and value > 0)


class CoinGeckoClient(BaseApiClient):
    '''Криптовалюты. Запрос по ID монет: https://.../simple/price?ids=bitcoin&vs_currencies=usd'''
    name = 'CoinGecko'

    def fetch_rates(self) -> dict:
        base = self.config.BASE_CURRENCY
        ids = {code: self.config.CRYPTO_ID_MAP[code] for code in self.config.CRYPTO_CURRENCIES}
        data = self._get_json(
            self.config.COINGECKO_URL,
            params={'ids': ','.join(ids.values()), 'vs_currencies': base.lower()},
        )

        rates = {}
        for code, coin_id in ids.items():
            value = data.get(coin_id, {}).get(base.lower())
            if self._is_valid_rate(value):
                rates[f'{code}_{base}'] = float(value)
        if not rates:
            raise ApiRequestError('в ответе нет ни одного корректного курса')
        return rates


class ExchangeRateApiClient(BaseApiClient):
    '''Фиатные валюты. Запрос: https://v6.exchangerate-api.com/v6/<КЛЮЧ>/latest/USD'''
    name = 'ExchangeRate-API'

    def fetch_rates(self) -> dict:
        key = self.config.EXCHANGERATE_API_KEY
        if not key:
            raise ApiRequestError('не задан ключ EXCHANGERATE_API_KEY (переменная окружения '
                                  'или файл .env)')
        base = self.config.BASE_CURRENCY
        data = self._get_json(f'{self.config.EXCHANGERATE_API_URL}/{key}/latest/{base}')
        if data.get('result') != 'success':
            raise ApiRequestError(data.get('error-type', 'неизвестная ошибка API'))

        api_rates = data.get('conversion_rates') or data.get('rates') or {}
        rates = {}
        for code in self.config.FIAT_CURRENCIES:
            value = api_rates.get(code)  # сколько единиц code дают за 1 USD (например, EUR: 0.927)
            if self._is_valid_rate(value):
                rates[f'{code}_{base}'] = 1 / value  # а нам нужно, сколько USD стоит 1 code
        if not rates:
            raise ApiRequestError('в ответе нет ни одного корректного курса')
        return rates


# Имя источника для --source -> класс клиента
CLIENTS = {
    'coingecko': CoinGeckoClient,
    'exchangerate': ExchangeRateApiClient,
}


def create_clients(config: ParserConfig, source: str | None = None) -> list[BaseApiClient]:
    '''Все клиенты или один, если указан source (coingecko / exchangerate)'''
    if source is None:
        return [client_class(config) for client_class in CLIENTS.values()]
    key = source.strip().lower()
    if key not in CLIENTS:
        raise ValueError(f"Неизвестный источник '{source}'. Доступны: {', '.join(CLIENTS)}")
    return [CLIENTS[key](config)]