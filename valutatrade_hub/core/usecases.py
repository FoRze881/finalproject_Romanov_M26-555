'''Юзер-кейсы - логика всех команд из interface.py'''

import secrets
from datetime import datetime

from valutatrade_hub.core import constants, models, utils


def check_essential_arguments(comand_name: str, essensial_comands: list[str], comands: dict):
    '''Проверяет все ли неоходимые команды есть в передаваемой команде
    Если нет, то выбрасывает ValueError'''
    if len(comands) < len(essensial_comands):
            raise ValueError(f'Недостаточно аргументов для команды {comand_name}')
    for comand in essensial_comands:
        if comand not in comands:
            raise ValueError(f'Команда не увидела аргумент {comand}. Проверьте, пожалуйста, аргументы\n'
                            f'Обязательные аргументы для {comand_name}: {", ".join(essensial_comands)}')
    

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


def login(comands: list[str]):
    '''Логинит пользователя, если совпадает пароль и логин и возвращает объект класса
    В противном случае выбрасывает ValueError'''
    comands = utils.parse_comand(comands)
    check_essential_arguments('login', 
                               constants.ESSENTIAL_ARGUMENTS.get('login'),
                               comands)

    username = comands.get('--username').strip()
    users = utils.load_json(constants.USERS_FILE)

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
    base_currency = comands.get('--base', 'USD').upper().strip()
    portfolios = utils.load_json(constants.PORTFOLIOS_FILE)
    user_portfolio = None
    for portfolio in portfolios:
        if portfolio['user_id'] == user.user_id:
            user_portfolio = portfolio
            break
    if not user_portfolio:
        raise ValueError('Ваши портфели не найдены, извините(')    
    if not user_portfolio['wallets'].items():
        raise ValueError('У Вас пока нет кошельков. Давайте создадим?')

    wallets = {}
    for currency_code, balance in user_portfolio['wallets'].items():
        wallets[currency_code] = models.Wallet(currency_code, balance.get('balance'))

    portfolio = models.Portfolio(user_portfolio['user_id'],
                                 wallets)
    return portfolio.get_total_value(base_currency)