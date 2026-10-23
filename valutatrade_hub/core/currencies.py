from abc import ABC, abstractmethod

from valutatrade_hub.core import exceptions


class Currency(ABC):
    def __init__(self, name:str, code:str):
        self.name = name
        self.code = code

    @abstractmethod
    def get_display_info(self):
        '''Строковое представление валюты'''

    @property
    def name(self):
        return self._name
    @name.setter
    def name(self, name):
        if name is None:
            raise ValueError('Имя не может быть None')
        if name.strip() == '':
            raise ValueError('Имя не может быть пустым')
        self._name = name.strip()
    @property
    def code(self):
        return self._code
    @code.setter
    def code(self, code):
        if not isinstance(code, str) or not code.strip().isalpha():
            raise ValueError('Код валюты должен быть типа str и не должен содержать пробелы')
        if not (2 <= len(code.strip()) <= 5):
            raise ValueError('Код валюты должен быть от 2 до 5 символов')
        self._code = code.upper().strip()


class FiatCurrency(Currency):
    def __init__(self, name:str, code:str, issuing_country: str):
        super().__init__(name, code)
        self.issuing_country = issuing_country

    def get_display_info(self):
        return f'[FIAT] {self.code} - {self.name} (Issuing: {self.issuing_country})'

class CryptoCurrency(Currency):
    def __init__(self, name:str, code:str, algorithm: str, market_cap: float):
        super().__init__(name, code)
        self.algorithm = algorithm
        self.market_cap = market_cap

    def get_display_info(self):
        return (f'[CRYPTO] {self.code} - {self.name} '  
            f'(Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})')

    @property
    def market_cap(self):
        return self._market_cap
    @market_cap.setter
    def market_cap(self, market_cap:float):
        try:
            market_cap = float(market_cap)
        except ValueError:
            raise ValueError('Рыночная капитализация должна быть типа float')
        except TypeError:
            raise TypeError('Рыночная капитализация не может быть None')
        if market_cap < 0:
            raise ValueError('Рыночная капитализация не может быть отрицательной')
        self._market_cap = market_cap

_REGISTRY = [
    FiatCurrency('US Dollar', 'USD', 'United States'),
    FiatCurrency('Euro', 'EUR', 'Eurozone'),
    FiatCurrency('Russian Ruble', 'RUB', 'Russia'),
    CryptoCurrency('Bitcoin', 'BTC', 'SHA-256', 1.12e12),
    CryptoCurrency('Ethereum', 'ETH', 'PoS', 4.5e11),
]

def get_currency(code:str):
    '''Возвращает Currency, если нашел
    Если нет, то выбрасывает ошибку CurrencyNotFoundError'''
    if not isinstance(code, str):
        raise TypeError(f'Код валюты должен быть str, а не {type(code).__name__}')
    for currency in _REGISTRY:
        if code.upper().strip() == currency.code:
            return currency
    raise exceptions.CurrencyNotFoundError(code.upper().strip(), [c.code for c in _REGISTRY])