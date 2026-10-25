'''Файл с константами проекта, чтобы легко их менять, а не искать по всем функциям'''

MINIMAL_LEN_PASSWORD = 4
ESSENTIAL_ARGUMENTS = {
    'register': ('--username', '--password'),
    'login': ('--username', '--password'),
    'buy': ('--currency', '--amount'),
    'sell': ('--currency', '--amount'),
    'get-rate': ('--from', '--to'),
}