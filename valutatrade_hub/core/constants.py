'''Файл с константами проекта, чтобы легко их менять, а не искать по всем функциям'''
import os
from pathlib import Path

MINIMAL_LEN_PASSWORD = 4
DATA_DIR = Path(__file__).resolve().parents[2] / 'data'
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
RATES_FILE = os.path.join(DATA_DIR, 'rates.json')
PORTFOLIOS_FILE = os.path.join(DATA_DIR, 'portfolios.json')
REFRESH_RATES = 5
ESSENTIAL_ARGUMENTS = {
    'register': ('--username', '--password'),
    'login': ('--username', '--password'),
    'buy': ('--currency', '--amount'),
    'sell': ('--currency', '--amount'),
    'get-rate': ('--from', '--to'),
}