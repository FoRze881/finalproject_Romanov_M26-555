'''Утилиты для бизнес-логики (файла usercases.py)'''
import hashlib
import json

from valutatrade_hub.core import constants
from valutatrade_hub.infra.settings import settings


def load_json(path):
    '''Загружает данные из users.json и возвращает их
    При ошибку кидает FileNotFoundError'''
    try:
        with open(path, 'r', encoding='utf-8') as f:
            users = json.load(f)
    except FileNotFoundError as e:
        raise FileNotFoundError(f'Файл по адресу {path} не найден.') from e
    return users

def check_unique_users(user_name: str):
    '''Принимает список user'ов, выбрасывает ValueError, если есть ошибка'''
    user_name = user_name.strip()
    if not user_name:
        raise ValueError('Имя пользователя не может быть пустым')
    users = load_json(settings.get('users_file'))
    usernames = []
    for user in users:
        usernames.append(user.get('username'))
    if user_name in usernames:
        raise ValueError(f'Пользователь {user_name} уже существует')

def generate_user_id():
    '''Возвращает новый user_id (последний id из существующих + 1)'''
    users = load_json(settings.get('users_file'))
    if not users: 
        return 1
    last_user_id = users[-1].get('user_id')
    return last_user_id + 1

def hash_password(password: str, salt: str):
    '''Хеширует пароль'''
    data = (password + salt).encode()
    return hashlib.sha256(data).hexdigest()

def save_user_to_json(user_id: int, username: str, hashed_password: str, salt: str,
                      registration_date: str):
    '''Сохраняет нового пользователя в json файл'''
    data = load_json(settings.get('users_file'))
    data.append({'user_id': user_id,
            'username': username,
            'hashed_password': hashed_password,
            'salt': salt,
            'registration_date': registration_date})
    with open(settings.get('users_file'), 'w', encoding='utf-8') as f:
        json.dump(data, f)

def create_portfoilio(user_id: int):
    '''Создает пустой словарь кошельков при регистрации нового пользователя'''
    data = load_json(settings.get('portfolios_file'))
    data.append({'user_id': user_id,
            'wallets': {}})
    with open(settings.get('portfolios_file'), 'w', encoding='utf-8') as f:
        json.dump(data, f)

def parse_comand(comands: list[str]):
    '''Парсит команду и возвращает словарь вида --команда: значение
    Если что-то не получилось распарсить, то ValueError'''
    parsed_comand = {}
    if len(comands) % 2 != 0: # Потому что у нас идет команда и значение
        raise ValueError('Не все элементы переданы')
    for i in range(0, len(comands) - 1, 2):
        if not comands[i].startswith('--'):
            raise ValueError('Не удалось распарсить команду')
        parsed_comand[comands[i]] = comands[i + 1]
    return parsed_comand

def validate_password(password: str):
    '''Проверяет пароль на соответствие условиям'''
    if len(password) < constants.MINIMAL_LEN_PASSWORD:
        raise ValueError(f'Пароль должен быть не короче ' 
                        f'{constants.MINIMAL_LEN_PASSWORD} символов')
    return True