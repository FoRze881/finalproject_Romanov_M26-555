class CurrencyNotFoundError(ValueError):
    '''Ошибка, если валюта не найдена'''
    def __init__(self, code, all_codes):
        super().__init__(f'Неизвестный код валюты {code}\n'
                         f'Вот все доступные коды валют: {', '.join(all_codes)}')
    
class InsufficientFundsError(ValueError):
    '''Ошибка, если недостаточно средств'''
    def __init__(self, available, code, required):
        super().__init__(f'Недостаточно средств: доступно {available:.4f} {code}, требуется {required:.4f} {code}')

class ApiRequestError(ValueError):
    '''Ошибка, при обращении к API'''
    def __init__(self, reason):
        super().__init__(f'Ошибка при обращении к внешнему API: {reason}')