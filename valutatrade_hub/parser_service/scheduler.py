import logging
import time

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.updater import RatesUpdater

logger = logging.getLogger('valutatrade.parser')


class RatesScheduler:
    def __init__(self, updater: RatesUpdater, interval_seconds: int):
        if interval_seconds <= 0:
            raise ValueError('Интервал обновления должен быть больше 0')
        self.updater = updater
        self.interval_seconds = interval_seconds

    def run_once(self) -> dict | None:
        '''Одно обновление; ошибка API логируется и не останавливает планировщик'''
        try:
            return self.updater.run_update()
        except ApiRequestError as e:
            logger.error('Scheduled update failed: %s', e)
            return None

    def run_forever(self, max_runs: int | None = None) -> None:
        '''Обновляет курсы каждые interval_seconds секунд до Ctrl+C
        (или max_runs раз — удобно для проверки)'''
        logger.info('Scheduler started: every %d s', self.interval_seconds)
        runs = 0
        try:
            while max_runs is None or runs < max_runs:
                self.run_once()
                runs += 1
                if max_runs is None or runs < max_runs:
                    time.sleep(self.interval_seconds)
        except KeyboardInterrupt:
            logger.info('Scheduler stopped by user')


if __name__ == '__main__':
    from valutatrade_hub.infra.settings import settings
    from valutatrade_hub.logging_config import setup_logging
    from valutatrade_hub.parser_service.api_clients import create_clients
    from valutatrade_hub.parser_service.config import ParserConfig
    from valutatrade_hub.parser_service.storage import RatesStorage

    setup_logging()
    config = ParserConfig()
    updater = RatesUpdater(
        clients=create_clients(config),
        storage=RatesStorage(config.RATES_FILE_PATH, config.HISTORY_FILE_PATH),
        base_currency=config.BASE_CURRENCY,
    )
    RatesScheduler(updater, settings.get('rates_ttl_seconds')).run_forever()