'''Юзер-кейсы - логика всех команд из interface.py'''

import secrets
from datetime import datetime, timedelta

from valutatrade_hub.core import constants, currencies, models, utils
from valutatrade_hub.decorators import log_action
from valutatrade_hub.infra.database import db
from valutatrade_hub.infra.settings import settings


def load_user_portfolio(user_id):
    '''Загружает портфель пользователя по его user_id, возвращает Portfolio
    Если ошибка, то возвращает ValueError'''
    portfolios = db.read('portfolios')
    user_portfolio = None
    for portfolio in portfolios:
        if portfolio['user_id'] == user_id:
            user_portfolio = portfolio
            break
    if not user_portfolio:
        raise ValueError('К сожалению, мы не нашли Ваш портфель, извините(')
    
    wallets = {}
    for currency_code, balance in user_portfolio['wallets'].items():
        wallets[currency_code] = models.Wallet(currency_code, balance.get('balance'))

    portfolio = models.Portfolio(user_portfolio['user_id'],
                                 wallets)

    return portfolio

def save_user_portfolio(portfolio: models.Portfolio):
    '''Сохраняет кошельки портфеля в portfolios.json'''
    wallets_data = {}
    for currency_code, wallet in portfolio.wallets.items():
        wallets_data[currency_code] = {'balance': wallet.balance}

    portfolios = db.read('portfolios')
    for record in portfolios:
        if record['user_id'] == portfolio.user:
            record['wallets'] = wallets_data
            break
    else:
        raise ValueError('К сожалению, мы не нашли Ваш портфель, извините(')

    db.write('portfolios', portfolios)

def check_essential_arguments(comand_name: str, essensial_comands: list[str], comands: dict):
    '''Проверяет все ли неоходимые команды есть в передаваемой команде
    Если нет, то выбрасывает ValueError'''
    if len(comands) < len(essensial_comands):
            raise ValueError(f'Недостаточно аргументов для команды {comand_name}')
    for comand in essensial_comands:
        if comand not in comands:
            raise ValueError(f'Команда не увидела аргумент {comand}. Проверьте, пожалуйста, аргументы\n'
                            f'Обязательные аргументы для {comand_name}: {", ".join(essensial_comands)}')

    
@log_action('REGISTER')
def register(comands: list[str]):
    '''Регистрирует пользователя, если что-то не так, то возвращает ошибку
    ValueError'''
    comands = utils.parse_comand(comands)
    check_essential_arguments('register', 
                               constants.ESSENTIAL_ARGUMENTS.get('register'),
                               comands)


    utils.check_unique_users(comands.get('--username'))
    username = comands.get('--username').strip()
    user_id = utils.generate_user_id()

    utils.validate_password(comands.get('--password'))
    salt = secrets.token_hex(16)
    hashed_password = utils.hash_password(comands.get('--password'), salt)
    user = models.User(user_id, username, hashed_password, salt, registration_date=datetime.now())
    utils.save_user_to_json(user_id=user.user_id,
                            username=user.username,
                            hashed_password=user.hashed_password,
                            salt=user.salt,
                            registration_date=user.registration_date.isoformat())
    utils.create_portfoilio(user_id=user.user_id)
    return(f'Пользователь {user.username} зарегистрирован (id={user.user_id}). ' 
          f'Войдите: login --username {user.username} --password <пароль>')


@log_action('LOGIN')
def login(comands: list[str]):
    '''Логинит пользователя, если совпадает пароль и логин и возвращает объект класса
    В противном случае выбрасывает ValueError'''
    comands = utils.parse_comand(comands)
    check_essential_arguments('login', 
                               constants.ESSENTIAL_ARGUMENTS.get('login'),
                               comands)

    username = comands.get('--username').strip()
    users = db.read('users')

    user_info = None
    for record in users:
        if record['username'] == username:
             user_info = record
             break
    if not user_info:
        raise ValueError(f'Пользователь {username} не найден')

    user = models.User(user_info['user_id'],
                       user_info['username'],
                       user_info['hashed_password'],
                       user_info['salt'],
                       datetime.fromisoformat(user_info['registration_date']))
    
    if not user.verify_password(comands.get('--password')): 
        raise ValueError('Неверный пароль')
    return user

def show_portfolio(user: models.User, comands: list[str]):
    '''Показывает все валюты портфеля пользователя в базовой валюте
    Если валюты нет, то возвращает ValueError'''

    comands = utils.parse_comand(comands)
    base_currency = currencies.get_currency(comands.get('--base', 
                                                        settings.get('default_base_currency'))).code
    portfolio = load_user_portfolio(user.user_id)
    if not portfolio.wallets:
        raise ValueError('У Вас пока нет кошельков. Давайте создадим?')
    wallets_value = portfolio.get_wallets_value(base_currency)
    result = []
    result.append(f'Портфель пользователя: {user.username} (база {base_currency})')
    porfolio_value = 0
    for currency_code, wallet in wallets_value.items():
        porfolio_value += wallet[1]
        result.append(f'- {currency_code}: {wallet[0]:.2f} -> {wallet[1]:.2f} {base_currency}')
    result.append('----------------------------------')
    result.append(f'ИТОГО: {porfolio_value:,.2f} {base_currency}')
    result = '\n'.join(result)
    return result

@log_action('BUY', verbose=True)
def buy(user: models.User, comands: list[str]):
    '''Добавляет покупаемую валюту пользователем
    Если что-то не так, то выбрасывает ValueError'''

    comands = utils.parse_comand(comands)
    check_essential_arguments('buy', 
                              constants.ESSENTIAL_ARGUMENTS.get('buy'),
                              comands)
    currency_code = currencies.get_currency(comands.get('--currency')).code
    amount = None
    try:
        amount = float(comands.get('--amount'))
    except ValueError:
        raise ValueError('Не удалось конвертировать в числовое значение то, что '
        'Вы передали в --amount')
    if amount <= 0:
        raise ValueError('Сумма в штуках должна быть больше 0')
    portfolio = load_user_portfolio(user_id=user.user_id)
    if currency_code not in portfolio.wallets:
        portfolio.add_currency(currency_code)

    wallet = portfolio.get_wallet(currency_code)
    wallet.deposit(amount)
    rates = db.read('rates')
    full_currency_code = f'{currency_code}_USD'
    rate_value = None
    if full_currency_code in rates:
        rate_value = rates[full_currency_code]['rate']

    if rate_value is not None:
        result = [(f'Покупка выполнена: {amount:.4f} {currency_code} '  
                  f'по курсу {rate_value} USD/{currency_code}')]
        result.append(f'Изменения в портфеле:\n'
                   f'- {currency_code}: было {wallet.balance - amount:.4f} -> '
                   f'стало {wallet.balance:.4f}')
        result.append(f'Оценочная стоимость покупки: {amount * rate_value:,.2f} USD')
    else:
        result = [f'Покупка выполнена: {amount:.4f} {currency_code} ']
        result.append(f'Изменения в портфеле:\n'
                           f'- {currency_code}: было {wallet.balance - amount:.4f} -> '
                           f'стало {wallet.balance:.4f}')
    save_user_portfolio(portfolio)
    result = '\n'.join(result)
    return result

@log_action('SELL', verbose=True)
def sell(user: models.User, comands: list[str]):
    '''Продает валюту с кошелька user
    Если ошибка, то выбрасывает ValueError'''

    comands = utils.parse_comand(comands)
    check_essential_arguments('sell',
                              constants.ESSENTIAL_ARGUMENTS.get('sell'),
                              comands)
    currency_code = currencies.get_currency(comands.get('--currency')).code
    amount = None
    if currency_code == 'USD':
        raise ValueError('Нельзя продать USD за USD')
    try:
        amount = float(comands.get('--amount'))
    except ValueError:
        raise ValueError('Не удалось конвертировать в числовое значение то, что '
        'Вы передали в --amount')
    if amount <= 0:
        raise ValueError('Сумма в штуках должна быть больше 0')
    portfolio = load_user_portfolio(user_id=user.user_id)
    if currency_code not in portfolio.wallets:
        raise ValueError(f'У Вас нет такого кошелька {currency_code}. '
                         'Добавьте валюту: кошелек создается автоматически.')

    wallet = portfolio.get_wallet(currency_code)
    if 'USD' not in portfolio.wallets:
        portfolio.add_currency('USD')
    wallet_in = portfolio.get_wallet('USD')
    wallet.withdraw(amount)
    rates = db.read('rates')
    full_currency_code = f'{currency_code}_USD'
    rate_value = None
    if full_currency_code in rates:
        rate_value = rates[full_currency_code]['rate']

    if rate_value is not None:
        result = [(f'Продажа выполнена: {amount:.4f} {currency_code} '  
                  f'по курсу {rate_value} USD/{currency_code}')]
        result.append(f'Изменения в портфеле:\n'
                   f'- {currency_code}: было {wallet.balance + amount:.4f} -> '
                   f'стало {wallet.balance:.4f}')
        result.append(f'Оценочная выручка: {amount * rate_value:,.2f} USD')
    else:
        result = [(f'Продажа выполнена: {amount:.4f} {currency_code} ')]
        result.append(f'Изменения в портфеле:\n'
                           f'- {currency_code}: было {wallet.balance + amount:.4f} -> '
                           f'стало {wallet.balance:.4f}')
    if rate_value is not None:
        wallet_in.deposit(rate_value * amount)
    save_user_portfolio(portfolio)
    result = '\n'.join(result)
    return result

def get_rate(comands: list[str]):
    '''Возвращает обменный курс 
    Если что-то не так, то выбрасывает ValueError'''
    comands = utils.parse_comand(comands)
    check_essential_arguments('get-rate',
                              constants.ESSENTIAL_ARGUMENTS.get('get-rate'),
                              comands)
    from_comand = currencies.get_currency(comands.get('--from')).code
    to_comand = currencies.get_currency(comands.get('--to')).code
    if not from_comand.strip() or not to_comand.strip():
        raise ValueError('Команды не могут быть пустыми')
    from_comand, to_comand = from_comand.strip(), to_comand.strip()
    full_currency = f'{from_comand}_{to_comand}'
    rates = db.read('rates')
    result = []
    if (datetime.now() - datetime.fromisoformat(rates['last_refresh'])) > \
        timedelta(seconds=settings.get('rates_ttl_seconds')):
        pass # Просим парсер обновить данные в нашем файле. Пока что у нас нет парсера
    if (datetime.now() - datetime.fromisoformat(rates['last_refresh'])) <= \
        timedelta(seconds=settings.get('rates_ttl_seconds')):
        if full_currency in rates:
            update_date = f'{datetime.fromisoformat(rates[full_currency]['updated_at']):%Y-%m-%d %H:%M:%S}'
            result.append(f'Курс {from_comand}/{to_comand}: {rates[full_currency]['rate']} '
                          f'(обновлено {update_date})\n'
                          f'Обратный курс {to_comand}/{from_comand}: {1/rates[full_currency]['rate']}')
        else:
            result.append(f'Курс {from_comand}/{to_comand} недоступен. '
                          'Повторите попытку позже')

        result = '\n'.join(result)
        return result
    
    if full_currency in rates:
        update_date = f'{datetime.fromisoformat(rates[full_currency]['updated_at']):%Y-%m-%d %H:%M:%S}'
        result.append(f'К сожалению, актуального курса нет (который был бы не '
                      f'старше {settings.get('rates_ttl_seconds') // 60} минут)\n'
                      f'Вот последний имеющийся курс {from_comand}/{to_comand}: '
                      f'{rates[full_currency]['rate']} (обновлено '
                      f'{update_date})\n'
                      f'Обратный курс {to_comand}/{from_comand}: {1/rates[full_currency]['rate']}')
    else:
        result.append(f'Курс {from_comand}/{to_comand} недоступен. '
                    'Повторите попытку позже')
    result = '\n'.join(result)
    return result