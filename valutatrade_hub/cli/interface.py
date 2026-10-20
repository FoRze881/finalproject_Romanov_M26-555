'''Клиентский CLI. единственная точка входа'''
import shlex

from valutatrade_hub.core import usecases


def greetings(user_info=None):
    '''Возвращает приветствие пользователя'''
    if user_info:
        return(f'Добро пожаловать в Wallet, {user_info.get('username')}!\n '
              'Потом можно подумать какую информацию еще здесь можно вывести\n'
              'Возможно список доступных кошельков')
    return('Добро пожаловать в Wallet. Зарегистрируетесь?')

def return_help():
    '''Вовзращает помощь и информацию по каждой команде'''
    return('Команда exit - выход из приложения\n\n'
           'Команда register - зарегистрироватся (если еще не зарегистрированы)\n'
           '\tОбязательные аргументы:\n'
           '\t\t--username <str> - уникальное имя пользователя\n'
           '\t\t--password <str> - пароль\n\n'
           'Команда login - войти в профиль\n'
           'Обязательные аргументы:\n'
           '\t\t--username <str> - имя пользователя\n'
           '\t\t--password <str> - пароль\n\n'
           'Команда show-portfolio - показать все кошельки и '
           'итоговую стоимость в базовой валюте (USD по умолчанию)\n'
           '\tАргументы (необязательно)\n'
           '\t\t--base <str> - базовая валюта конвертации\n\n'
           'Команда buy - купить валюту\n'
           '\tОбязательные аргументы:\n'
           '\t\t--currency <str> - код покупаемой валюты\n'
           '\t\t--amount <float> - количество покупаемой валюты (в штуках, не в USD)\n\n'
           'Команда sell - продать валюту\n'
           '\tОбязательные аргументы:\n'
           '\t\t--currency <str> - код продаваемой валюты\n'
           '\t\t--amount <float> - количество продаваемой валюты (в штуках, не в USD)\n\n')

def main():
    print(greetings())
    print('Если нужна помощь с командами, то напишите help')
    current_user = None
    while True:
        comand = input()
        try:
            comand = shlex.split(comand)
        except ValueError:
            print('Ошибка в команде (возможно, незакрытая кавычка)')
            continue
        if not comand:
            continue

        match comand[0].lower().strip():
            case 'help':
                print(return_help())
            case 'exit':
                print('Выход из приложения')
                break

            case 'register': 
                if len(comand) < 2:
                    print('Не хватает аргументов')
                    continue

                try:
                    print(usecases.register(comand[1:]))
                except ValueError as e:
                    print(e)

            case 'login':
                if len(comand) < 2:
                    print('Не хватает аргументов')
                    continue

                try:
                    current_user = usecases.login(comand[1:])
                    print(f'Вы вошли как {current_user.username}')
                except ValueError as e:
                    print(e)

            case 'show-portfolio':
                if current_user is None:
                    print('Сначала войдите в профиль.\n' \
                    'Команда login --username <str> --password <str>')
                    continue

                try:
                    print(usecases.show_portfolio(current_user, comand[1:]))
                except ValueError as e:
                    print(e)


            case 'buy':
                if current_user is None:
                    print('Сначала войдите в профиль.\n' \
                    'Команда login --username <str> --password <str>')
                    continue

                try:
                    print(usecases.buy(current_user, comand[1:]))
                except ValueError as e:
                    print(e)

            case 'sell':
                if current_user is None:
                    print('Сначала войдите в профиль.\n' \
                    'Команда login --username <str> --password <str>')
                    continue

                try:
                    print(usecases.sell(current_user, comand[1:]))
                except ValueError as e:
                    print(e)
            
            case _:
                print('Не знаем такой команды. Если нужна помощь '
                      'то можно вызвать help')



if __name__ == "__main__":
    main()
