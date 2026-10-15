'''Реализация всех классов проекта'''
import hashlib
import math
from datetime import datetime

from valutatrade_hub.core import constants


class User:
    def __init__(self, user_id: int, username: str, hashed_password: str,
                 salt: str, registration_date: datetime):
        self._user_id = user_id
        self.username = username
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date

    def get_user_info(self):
        '''Выводит информацию о пользователе
        user_id, username, registration_date'''
        print(f'ID: {self._user_id}\n'
              f'Имя пользователя: {self._username}\n'
              f'Дата регистрации: {self._registration_date:%d.%m.%Y %H:%M}\n')

    def change_password(self, new_password: str):
        '''Изменяет пароль пользователя, хешируя новый пароль
        Если пароль не проходит проверки, то выкидывается ValueError'''
        if len(new_password) < constants.MINIMAL_LEN_PASSWORD:
            raise ValueError(
                f'Пароль должен быть не короче ' 
                f'{constants.MINIMAL_LEN_PASSWORD} символов'
            )
        data = (new_password + self._salt).encode()
        self._hashed_password = hashlib.sha256(data).hexdigest()

    def verify_password(self, password: str):
        '''Проверяет, совпадает ли введённый пароль с сохранённым
        Возвращает True/False'''
        data = (password + self._salt).encode()
        return hashlib.sha256(data).hexdigest() == self._hashed_password

    @property
    def user_id(self):
        '''Возвращает _user_id'''
        return self._user_id

    @property
    def username(self):
        '''Возвращает username'''
        return self._username

    @username.setter
    def username(self, new_username):
        '''Присваивает новое имя пользователя, если оно проходит проверку
        (имя не является пустым)'''
        if not new_username.strip():
            raise ValueError('Имя не может быть пустым')
        self._username = new_username.strip()

    @property
    def hashed_password(self):
        '''Возвращает захэшированный пароль'''
        return self._hashed_password

    @property
    def salt(self):
        '''Возвращает соль от пароля пользователя'''
        return self._salt
    
    @property
    def registration_date(self):
        '''Возвращает дату регистрации пользователя'''
        return self._registration_date


class Wallet:
    def __init__(self, currency_code: str, balance: float = 0):
        self.currency_code = currency_code
        self.balance = balance

    @staticmethod
    def _check_amount(amount: float):
        '''Проверяет тип и конечность amount и выбрасывает ошибку
        Если все хорошо, то ничего не делает'''
        if isinstance(amount, bool) or not isinstance(amount, (int, float)):
            raise TypeError(f'Неправильный тип {type(amount).__name__}. ' 
                            'Разрешены только int и float')
        if not math.isfinite(amount):
            raise ValueError('Сумма должна быть конечным числом')

    def deposit(self, amount: float):
        '''Прибавляет баланс кошелька, если amount > 0 и он float
        В противном случае выбрасывает ValueError или TypeError'''
        self._check_amount(amount)
        if amount <= 0:
            raise ValueError('Сумма должна быть больше 0')
        self._balance += amount

    def withdraw(self, amount: float):
        '''Убавляет баланс кошелька, если amount > 0 и сумма вывода не больше баланса
        В противном случае выбрасывает ValueError'''
        self._check_amount(amount)
        if amount <= 0:
            raise ValueError('Сумма должна быть больше 0')
        if amount > self._balance:
            raise ValueError('Недостаточно средств')
        self._balance -= amount

    def get_balance_info(self):
        '''Выводит информацию о балансе'''
        print(f'Валюта: "{self.currency_code}" - Количество: {self._balance}')

    @property
    def balance(self):
        '''Возвращает текущее значение баланса'''
        return self._balance

    @balance.setter
    def balance(self, new_balance):
        '''Устанавливает новый баланс, проверяя валидность нового баланса
        (тип данных и неотрицательность)'''
        self._check_amount(new_balance)
        if new_balance < 0:
            raise ValueError(f'Баланс не может быть отрицательным')
        self._balance = new_balance


class Portfolio:
    def __init__(self, user_id: int, wallets: dict[str, Wallet]):
        self._user_id = user_id
        self._wallets = wallets

    @staticmethod
    def _check_currency(currency):
        '''Проверяет тип currency и возвращает нормализованное значение, 
        если что-то не так, то выбрасывает 
        TypeError или ValueError'''
        if not isinstance(currency, str):
            raise TypeError(f'Валюта должна быть str, а не {type(currency).__name__}')
        if currency.strip() == '':
            raise ValueError('Валюта не может быть пустой')
        return currency.upper().strip()
        

    def add_currency(self, currency_code: str):
        '''Добавляет новый кошелек в портфель, если его еще нет
        Если есть, то выбрасывает ошибку ValueError'''
        norm_currency_code = self._check_currency(currency_code)
        if norm_currency_code in self._wallets.keys():
            raise ValueError('Кошелек с такой валютой уже существует')
        self._wallets[norm_currency_code] = Wallet(norm_currency_code)
    
    def get_total_value(self, base_currency = 'USD'):
        '''Возвращает общую стоимость всех валют пользователя в указанной валюте
        По курсам, полученным из API
        Если курса нет, то выбрасывает ValueError или TypeError'''
        exchange_rates = {'USD': 1,
                          'BTC': 80000,
                          'EUR': 1.04,
                          'SOL': 84} # пока как заглушку, потом надо будет брать из JSON файла, который нам API будет возвращать 
        norm_base_currency = self._check_currency(base_currency)
        if norm_base_currency not in exchange_rates.keys():
            raise ValueError('Обменного курса для такой валюты нет, к сожалению')

        portfolio = 0
        for currency, wallet in self._wallets.items():
            if currency not in exchange_rates.keys():
                raise ValueError(f'К сожалению, обменного курса для {currency} сейчас нет')
            portfolio += wallet.balance * exchange_rates[currency] / exchange_rates[norm_base_currency]

        return portfolio

    def get_wallet(self, currency_code):
        '''Возвращает Wallet по коду валюты'''
        norm_currency_code = self._check_currency(currency_code)
        if norm_currency_code not in self._wallets.keys():
            raise ValueError('Такой валюты нет в портфеле')
        return self._wallets[norm_currency_code]
        

    @property
    def user(self):
        '''Возвращает user_id, потому что ничего другого у нас нет'''
        return self._user_id

    @property
    def wallets(self):
        '''Возвращает копию словаря кошельков'''
        return dict(self._wallets)
    
