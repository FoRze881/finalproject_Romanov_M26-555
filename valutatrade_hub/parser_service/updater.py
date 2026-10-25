'''Координация обновления курсов'''
import logging
from datetime import UTC, datetime

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.api_clients import BaseApiClient
from valutatrade_hub.parser_service.storage import RatesStorage

logger = logging.getLogger('valutatrade.parser')


def local_now_iso() -> str:
    '''Время для rates.json. Ядро сравнивает его с datetime.now() — местным временем
    без часового пояса, поэтому и записывать нужно так же'''
    return datetime.now().isoformat(timespec='seconds')


def utc_now_iso() -> str:
    '''Время для id и timestamp в истории exchange_rates.json (по заданию — ISO-UTC)'''
    return datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')


class RatesUpdater:
    def __init__(self, clients: list[BaseApiClient], storage: RatesStorage,
                 base_currency: str = 'USD'):
        self.clients = clients
        self.storage = storage
        self.base_currency = base_currency

    def run_update(self):
        '''Опрашивает всех клиентов и сохраняет курсы.
        Ошибка одного клиента не останавливает остальных.
        Если не ответил ни один — ApiRequestError.'''
        logger.info('Starting rates update...')
        updates, history, errors = {}, [], []

        for client in self.clients:
            try:
                rates = client.fetch_rates()
            except ApiRequestError as e:
                logger.error('Failed to fetch from %s: %s', client.name, e)
                errors.append(f'{client.name}: {e}')
                continue

            fetched_local, fetched_utc = local_now_iso(), utc_now_iso()
            logger.info('Fetching from %s... OK (%d rates)', client.name, len(rates))
            for pair, rate in rates.items():
                from_code, to_code = pair.split('_')
                updates[pair] = {'rate': rate, 'updated_at': fetched_local}
                history.append({
                    'id': f'{pair}_{fetched_utc}',
                    'from_currency': from_code,
                    'to_currency': to_code,
                    'rate': rate,
                    'timestamp': fetched_utc,
                    'source': client.name,
                    'meta': dict(client.last_meta),
                })

        if not updates:
            raise ApiRequestError('не удалось получить курсы ни из одного источника')

        fetched_count = len(updates)
        # Ядро ищет курс по ключу «<валюта>_USD» — в том числе для самого USD
        last_refresh = local_now_iso()
        base = self.base_currency
        updates[f'{base}_{base}'] = {'rate': 1.0, 'updated_at': last_refresh}

        logger.info('Writing %d rates to %s...', fetched_count, self.storage.rates_path.name)
        self.storage.append_history(history)
        self.storage.save_snapshot(updates, last_refresh, source='ParserService')
        logger.info('Update finished: %d rates, %d errors', fetched_count, len(errors))
        return {'updated': fetched_count, 'errors': errors, 'last_refresh': last_refresh}