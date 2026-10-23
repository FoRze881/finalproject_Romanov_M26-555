'''Декораторы проекта'''
import functools
import logging
from datetime import datetime

from valutatrade_hub.core import utils

logger = logging.getLogger('valutatrade.actions')


def _extract_context(action: str, args: tuple) -> dict:
    '''Достаёт из аргументов вызова данные для лога'''
    try:
        if action in ('BUY', 'SELL'):
            user, comands = args[0], args[1]
            params = utils.parse_comand(comands)
            return {
                'username': user.username,
                'user_id': user.user_id,
                'currency_code': params.get('--currency'),
                'amount': params.get('--amount'),
            }
        params = utils.parse_comand(args[0])  # REGISTER / LOGIN: на входе только токены
        return {'username': params.get('--username')}
    except (ValueError, IndexError, AttributeError):
        return {}


def _wallet_balance(context: dict):
    '''Баланс кошелька операции - для режима verbose (было - стало)'''
    # Импорт внутри функции: usecases сам импортирует этот модуль,
    # и импорт наверху файла дал бы циклический импорт
    from valutatrade_hub.core.usecases import load_user_portfolio

    code = (context.get('currency_code') or '').upper().strip()
    try:
        wallet = load_user_portfolio(context['user_id']).wallets.get(code)
    except (KeyError, ValueError):
        return None
    return wallet.balance if wallet else 0.0


def _format_record(action: str, context: dict, result: str, error=None) -> str:
    parts = [f'timestamp={datetime.now().isoformat(timespec="seconds")}', f'action={action}']
    parts += [f'{key}={value}' for key, value in context.items() if value is not None]
    parts.append(f'result={result}')
    if error is not None:
        parts.append(f'error_type={type(error).__name__}')
        parts.append(f"error_message='{error}'")
    return ' '.join(parts)


def log_action(action: str, verbose: bool = False):
    '''Логирует доменную операцию: кто, что, с какими данными и чем закончилось'''
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            context = _extract_context(action, args)
            before = _wallet_balance(context) if verbose else None
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                logger.info(_format_record(action, context, 'ERROR', error=e))
                raise
            if verbose:
                context['state'] = f'{before}->{_wallet_balance(context)}'
            logger.info(_format_record(action, context, 'OK'))
            return result
        return wrapper
    return decorator