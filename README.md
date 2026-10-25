# ValutaTrade Hub

Консольное приложение — кошелёк фиатных валют и криптовалют. Пользователь регистрируется, ведёт портфель из кошельков в разных валютах, покупает и продаёт валюту и смотрит курсы. Курсы загружаются из внешних API (CoinGecko и ExchangeRate-API) и хранятся в локальном кеше.

Итоговый проект по курсу Python, МИФИ. Автор: Романов Владимир, группа М26-555.

## Возможности

- **Пользователи**: регистрация и вход. Пароль хранится только в виде SHA-256-хеша с индивидуальной солью.
- **Портфель**: у каждого пользователя есть набор кошельков (по одному на валюту) и общая стоимость портфеля в USD.
- **Покупка и продажа**: `buy` зачисляет валюту в кошелёк и показывает оценочную стоимость по текущему курсу. `sell` списывает валюту и зачисляет выручку в USD-кошелёк.
- **Курсы валют**: `get-rate` показывает курс из локального кеша. Если кеш старше 5 минут, курсы автоматически обновляются.
- **Parser Service**: команда `update-rates` загружает курсы BTC и ETH из CoinGecko, а EUR и RUB из ExchangeRate-API. Снимок курсов сохраняется в `data/rates.json`, история запросов — в `data/exchange_rates.json`. Ошибка одного источника не мешает получить курсы из другого.
- **Фоновое обновление**: курсы можно обновлять по расписанию отдельным процессом.
- **Логирование**: операции пользователей пишутся в `logs/actions.log`, работа парсера — в `logs/parser.log`.

Поддерживаемые валюты: **USD, EUR, RUB, BTC, ETH**.

## Требования

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

## Установка

```bash
git clone https://github.com/FoRze881/finalproject_Romanov_M26-555.git
cd finalproject_Romanov_M26-555
uv sync
```

`uv sync` создаёт виртуальное окружение `.venv`, ставит зависимости (`requests`, `prettytable`) и устанавливает сам проект.

### Ключ ExchangeRate-API

Курсы фиатных валют (EUR, RUB) загружаются из ExchangeRate-API, для этого нужен ключ.

1. Зарегистрируйтесь на [exchangerate-api.com](https://www.exchangerate-api.com/). Бесплатного тарифа достаточно.
2. Создайте в корне проекта файл `.env` и запишите в него ключ:

   ```
   EXCHANGERATE_API_KEY=ваш_ключ
   ```

Файл `.env` добавлен в `.gitignore` и в репозиторий не попадает. Вместо файла можно задать переменную окружения `EXCHANGERATE_API_KEY`.

Без ключа приложение тоже работает: курсы криптовалют обновляются из CoinGecko, а для фиатных валют используются последние сохранённые в кеше значения.

## Запуск

Из корня проекта:

```bash
uv run trade_hub
```

То же самое через `main.py`:

```bash
uv run python main.py
```

Чтобы команда `trade_hub` была доступна в любом терминале без `uv run`, установите проект как инструмент в режиме editable:

```bash
uv tool install --editable .
```

> Флаг `--editable` обязателен. Приложение ищет `.env`, `data/` и `logs/` относительно своего кода. При обычной установке код копируется в отдельную папку uv, и там не будет ни ключа, ни ваших данных.

## Команды

Аргументы передаются парами `--имя значение`. Справка по всем командам выводится командой `help`.

| Команда | Аргументы | Что делает |
|---|---|---|
| `register` | `--username <str> --password <str>` | Регистрирует пользователя. Пароль — не короче 4 символов |
| `login` | `--username <str> --password <str>` | Вход в профиль |
| `show-portfolio` | `[--base <код>]` | Кошельки пользователя и итоговая стоимость портфеля |
| `buy` | `--currency <код> --amount <число>` | Покупка валюты (количество — в единицах валюты, не в USD) |
| `sell` | `--currency <код> --amount <число>` | Продажа валюты, выручка зачисляется в USD-кошелёк |
| `get-rate` | `--from <код> --to <код>` | Курс одной валюты к другой |
| `update-rates` | `[--source coingecko\|exchangerate]` | Немедленное обновление курсов из всех источников или из одного |
| `show-rates` | `[--currency <код>] [--top <N>] [--base <код>]` | Курсы из локального кеша: одна валюта, N самых дорогих криптовалют, пересчёт в другую базу |
| `help` | | Справка по командам |
| `exit` | | Выход |

Команды `show-portfolio`, `buy` и `sell` доступны только после `login`.

Курсы в кеше хранятся относительно USD (пары вида `BTC_USD`), поэтому `get-rate` и `show-portfolio` сейчас считают в USD. Пересчёт в другую базу умеет `show-rates --base`.

### Пример сессии

```
$ uv run trade_hub
Добро пожаловать в Wallet. Зарегистрируетесь?
Если нужна помощь с командами, то напишите help
register --username alice --password 1234
Пользователь alice зарегистрирован (id=1). Войдите: login --username alice --password <пароль>
login --username alice --password 1234
Вы вошли как alice
buy --currency BTC --amount 0.05
Покупка выполнена: 0.0500 BTC по курсу 80308.0 USD/BTC
Изменения в портфеле:
- BTC: было 0.0000 -> стало 0.0500
Оценочная стоимость покупки: 4,015.40 USD
sell --currency BTC --amount 0.01
Продажа выполнена: 0.0100 BTC по курсу 80308.0 USD/BTC
Изменения в портфеле:
- BTC: было 0.0500 -> стало 0.0400
Оценочная выручка: 803.08 USD
show-portfolio
Портфель пользователя: alice (база USD)
- BTC: 0.04 -> 3212.32 USD
- USD: 803.08 -> 803.08 USD
----------------------------------
ИТОГО: 4,015.40 USD
update-rates
INFO: Starting rates update...
INFO: Fetching from CoinGecko... OK (2 rates)
INFO: Fetching from ExchangeRate-API... OK (2 rates)
INFO: Writing 4 rates to rates.json...
INFO: Update finished: 4 rates, 0 errors
Update successful. Total rates updated: 4. Last refresh: 2026-10-25T16:23:15
show-rates --top 2
Rates from cache (updated at 2026-10-25T16:23:15):
- BTC_USD: 80308.00
- ETH_USD: 2332.01
exit
Выход из приложения
```

## Фоновое обновление курсов

Планировщик обновляет курсы каждые `rates_ttl_seconds` секунд (по умолчанию 300):

```bash
uv run python -m valutatrade_hub.parser_service.scheduler
```

Остановка — `Ctrl+C`. Планировщик можно держать запущенным в соседнем терминале, пока работает `trade_hub`.

## Настройки

Настройки задаются в секции `[tool.valutatrade]` файла `pyproject.toml`:

```toml
[tool.valutatrade]
rates_ttl_seconds = 300          # сколько секунд курсы в кеше считаются актуальными
default_base_currency = "USD"    # базовая валюта для show-portfolio
```

Там же можно переопределить пути: `data_dir`, `users_file`, `portfolios_file`, `rates_file`, `log_dir`. Относительные пути считаются от корня проекта.

## Данные и логи

| Файл | Содержимое |
|---|---|
| `data/users.json` | Пользователи: id, имя, хеш пароля, соль, дата регистрации |
| `data/portfolios.json` | Портфели: кошельки и балансы пользователей |
| `data/rates.json` | Текущий кеш курсов — пары `<ВАЛЮТА>_USD`, время обновления, источник |
| `data/exchange_rates.json` | История всех полученных курсов с источником и метаданными запроса |
| `logs/actions.log` | Операции REGISTER, LOGIN, BUY, SELL: кто, что, результат |
| `logs/parser.log` | Работа Parser Service: запросы к API, ошибки, запись курсов |

Запись в JSON-файлы атомарная: данные пишутся во временный файл, который затем заменяет основной. Поэтому сбой во время записи не портит файл. Логи ротируются по 1 МБ, хранится 5 архивных файлов.

## Структура проекта

```
finalproject_Romanov_M26-555/
├── main.py                       # запуск: python main.py
├── pyproject.toml                # зависимости, команда trade_hub, настройки [tool.valutatrade]
├── data/                         # JSON-хранилище
├── logs/                         # логи (создаются при первом запуске)
└── valutatrade_hub/
    ├── cli/
    │   └── interface.py          # командный интерфейс, точка входа run()
    ├── core/
    │   ├── models.py             # User, Wallet, Portfolio
    │   ├── currencies.py         # Currency, FiatCurrency, CryptoCurrency, реестр валют
    │   ├── usecases.py           # логика команд
    │   ├── utils.py              # разбор команд, хеширование паролей
    │   ├── exceptions.py         # собственные исключения
    │   └── constants.py
    ├── infra/
    │   ├── settings.py           # SettingsLoader (Singleton): конфигурация из pyproject.toml
    │   └── database.py           # DatabaseManager (Singleton): чтение и запись JSON
    ├── parser_service/
    │   ├── config.py             # ParserConfig: API-ключ, адреса API, списки валют
    │   ├── api_clients.py        # клиенты CoinGecko и ExchangeRate-API
    │   ├── updater.py            # RatesUpdater: опрос клиентов и сохранение курсов
    │   ├── storage.py            # RatesStorage: работа с rates.json и exchange_rates.json
    │   └── scheduler.py          # RatesScheduler: периодическое обновление
    ├── decorators.py             # @log_action — логирование операций
    └── logging_config.py         # настройка логгеров
```

## Проверка кода

```bash
uv run ruff check .
```
