'''Настройка логирования проекта'''
import logging
from logging.handlers import RotatingFileHandler

from valutatrade_hub.infra.settings import settings

LOG_FILE_NAME = 'actions.log'
MAX_BYTES = 1_000_000 
BACKUP_COUNT = 5       


def setup_logging(debug: bool = False) -> None:
    '''Настраивает логгер проекта: запись в logs/actions.log с ротацией по размеру'''
    logger = logging.getLogger('valutatrade')
    if logger.handlers:  # уже настроен — второй обработчик не добавляем
        return

    log_dir = settings.get('log_dir')
    log_dir.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        log_dir / LOG_FILE_NAME,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding='utf-8',
    )
    handler.setFormatter(logging.Formatter(settings.get('log_format')))

    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.propagate = False