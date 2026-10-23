'''Файл с константами проекта, чтобы легко их менять, а не искать по всем функциям'''

MINIMAL_LEN_PASSWORD = 4
ESSENTIAL_ARGUMENTS = {
    'register': ('--username', '--password'),
    'login': ('--username', '--password'),
    'buy': ('--currency', '--amount'),
    'sell': ('--currency', '--amount'),
    'get-rate': ('--from', '--to'),
}
API_EXCHANGE_RATE = '491f2b9d0b9ae7b3a3fa04ea'