# ValutaTrade Hub

**Торговая платформа для работы с валютами (фиатными и криптовалютами)**

CLI-приложение для управления портфелем валют с автоматическим обновлением курсов из внешних API.

---

## Содержание

- [Описание проекта](#описание-проекта)
- [Функциональность](#функциональность)
- [Структура проекта](#структура-проекта)
- [Установка](#установка)
- [Конфигурация](#конфигурация)
- [Запуск](#запуск)
- [Примеры использования](#примеры-использования)
- [Parser Service и кэш курсов](#parser-service-и-кэш-курсов)
- [Тестовая функция пополнения](#тестовая-функция-пополнения)
- [Логирование](#логирование)
- [Демонстрация](#демонстрация)

---

## Описание проекта

**ValutaTrade Hub** — это CLI-приложение для торговли валютами, которое позволяет:

- Регистрироваться и авторизовываться
- Покупать и продавать валюты (фиатные и крипто)
- Просматривать портфель с конвертацией в любую валюту
- Получать актуальные курсы валют из внешних API
- Хранить данные локально в JSON-файлах
- Автоматически обновлять курсы с поддержкой TTL (Time To Live)

### Архитектура проекта

- **Модульная архитектура**: Разделение приложения на "слои" (Core, Infrastructure, CLI, Parser Service)
- **Singleton Pattern**: Единственный экземпляр для настроек и управления состоянием
- **Логирование**: Детальное логирование всех операций
- **Сервис парсинга**: Модульная система получения курсов из разных источников
- **Треугольная конвертация**: Автоматическая конвертация через USD для пар без прямого курса

---

## Функциональность

### Основные возможности

- **Аутентификация**: Регистрация и вход с хешированием паролей
- **Управление портфелем**: Покупка, продажа, просмотр баланса
- **Курсы валют**: Автоматическое получение курсов из CoinGecko и ExchangeRate-API
- **Кэширование**: Локальное хранение курсов с проверкой TTL
- **Мультивалютность**: Поддержка 10 валют (5 фиатных и 5 криптовалют)
- **Конвертация**: Просмотр портфеля в любой валюте с треугольной конвертацией
- **История**: Хранение истории курсов валют

### Поддерживаемые валюты

**Фиатные**: USD, EUR, RUB, GBP, JPY, CNY  
**Криптовалюты**: BTC, ETH, BNB, SOL, XRP

---

## Структура проекта

```
finalproject
│  
├── data/
│    ├── users.json          
│    ├── portfolios.json       
│    ├── rates.json               
│    └── exchange_rates.json     
├── valutatrade_hub/
│    ├── __init__.py
│    ├── logging_config.py         
│    ├── decorators.py            
│    ├── core/
│    │    ├── __init__.py
│    │    ├── currencies.py         
│    │    ├── exceptions.py         
│    │    ├── models.py           
│    │    ├── usecases.py          
│    │    └── utils.py             
│    ├── infra/
│    │    ├─ __init__.py
│    │    ├── settings.py           
│    │    └── database.py          
│    ├── parser_service/
│    │    ├── __init__.py
│    │    ├── config.py            
│    │    ├── api_clients.py        
│    │    ├── updater.py            
│    │    ├── storage.py            
│    │    └── scheduler.py         
│    └── cli/
│         ├─ __init__.py
│         └─ interface.py     
│
├── main.py
├── Makefile
├── poetry.lock
├── pyproject.toml
├── README.md
├── config.json
└── .gitignore               
```
---
## Установка

### Требования

- **Python**: 3.10 или выше
- **Poetry**: 1.6 или выше

### 1. Клонирование репозитория

```
git clone https://github.com/fenrirg6/finalproject_Elskas_M25_555
cd <директория>
```

### 2. Установка зависимостей

Через Poetry:
```
poetry install
```

Или через Makefile:
```
make package-install
make install
```

## Конфигурация

### 1. API ключ ExchangeRate-API

Для получения курсов фиатных валют требуется API ключ от [ExchangeRate-API](https://www.exchangerate-api.com/).

#### Получение ключа

1. Зарегистрируйтесь на [ExchangeRate-API](https://www.exchangerate-api.com/sign-up)
2. Получите бесплатный API ключ (~1500 запросов/месяц)

#### Установка ключа

При запуске проекта необходимо выполнить в командной строке:

```
export EXCHANGERATE_API_KEY=<ваш_ключ>
```

### 2. Конфигурационный файл `config.json`

При первом запуске автоматически создаётся файл `config.json` с настройками по умолчанию:

```
{
"DATA_DIR": "data",
"USERS_FILE": "data/users.json",
"PORTFOLIOS_FILE": "data/portfolios.json",
"RATES_FILE": "data/rates.json",

"CACHE_TTL_SECONDS": 300,
"BASE_CURRENCY": "USD",

"LOG_DIR": "logs",
"LOG_FILE": "logs/actions.log",
"LOG_LEVEL": "INFO",
"LOG_FORMAT": "%(asctime)s - %(levelname)s - %(message)s",
"LOG_MAX_BYTES": 10485760,
"LOG_BACKUP_COUNT": 5
}
```

#### Настройка TTL кэша

**По умолчанию**: `CACHE_TTL_SECONDS = 300` (5 минут)

Для демонстрации можно установить короткий TTL:

```
{
"CACHE_TTL_SECONDS": 10
}
```

**Как работает TTL**:
- Курсы считаются актуальными, если их возраст меньше TTL
- При превышении TTL выводится предупреждение в логах
- Рекомендуется выполнить `update-rates` для обновления

## Запуск

Рекомендуется запускать проект через Makefile:

```
make build
```

После чего можно зайти в REPL-режим выполнив в командной строке:

```
valutatrade
```

или

```
make project
```

## Примеры использования

### Базовый сценарий

1. Запустите приложение
```
poetry run python main.py
```

2. Зарегистрируйтесь
```
register --username trader --password 1234
```

3. Войдите
```
login --username trader --password 1234
```

4. Обновите курсы валют
```
[trader] > update-rates
```

5. Пополните счёт (тестовая функция)
```
[trader] > demo-deposit --currency USD --amount 10000
```

6. Купите криптовалюту
```
[trader] > buy --currency BTC --amount 0.01
```

7. Просмотрите портфель
```
[trader] > show-portfolio
```

8. Просмотрите портфель в другой валюте
```
[trader] > show-portfolio --base RUB
```

9. Продайте часть криптовалюты
```
[trader] > sell --currency BTC --amount 0.005
```

10. Выход
```
[trader] > exit
```

### Команды

#### Аутентификация

Регистрация
```
register --username <логин> --password <пароль>
```

Вход
```
login --username <логин> --password <пароль>
```

Выход
```
logout
```

---

#### Управление курсами

Обновить все курсы
```
update-rates
```

Обновить курсы от конкретного источника
```
update-rates --source coingecko
update-rates --source exchangerate
```

Показать курсы
```
show-rates
```

Показать топ-5 курсов
```
show-rates --top 5
```

Фильтр по валюте
```
show-rates --currency BTC
```

Получить конкретный курс
```
get-rate --from BTC --to USD
```

---

#### Торговля

Покупка (за USD)
```
buy --currency BTC --amount 0.01
buy --currency EUR --amount 100
```

Продажа (за USD)
```
sell --currency BTC --amount 0.005
sell --currency EUR --amount 50
```

---

#### Портфель

Просмотр портфеля (в USD)
```
show-portfolio
```

Просмотр в другой валюте
```
show-portfolio --base RUB
show-portfolio --base EUR
```

---

#### Тестовая функция пополнения

Пополнение USD (по умолчанию 10000)
```
demo-deposit
```

Пополнение конкретной валюты
```
demo-deposit --currency EUR --amount 5000
demo-deposit --currency BTC --amount 0.5
```

---

## Parser Service и кэш курсов

### Источники курсов

**1. CoinGecko API** (криптовалюты)
- BTC, ETH, BNB, SOL, XRP → USD
- Бесплатный API, не требует ключа
- Лимит: 10-30 запросов/минуту

**2. ExchangeRate-API** (фиатные валюты)
- EUR, RUB, GBP, JPY, CNY → USD
- Требует API ключ
- Лимит: 1500 запросов/месяц (бесплатный план)

### Кэширование

Курсы сохраняются в `data/rates.json`:
```
{
"pairs": {
"BTC_USD": {
"rate": 101868.0,
"source": "CoinGecko",
"updated_at": "2025-11-07T13:09:50.387858+00:00"
},
"EUR_USD": {
"rate": 1.15393492,
"source": "ExchangeRate-API",
"updated_at": "2025-11-07T13:09:50.783945+00:00"
}
},
"last_refresh": "2025-11-07T13:09:50.806298+00:00"
}
```

### TTL (Time To Live)

**Настройка**: `config.json` → `CACHE_TTL_SECONDS`

**По умолчанию**: 300 секунд (5 минут)

**Для демонстрации**: 10 секунд (в asciinema)

**Как работает**:
1. При запросе курса проверяется его возраст
2. Если возраст > TTL, выводится предупреждение в логи
3. Курс всё равно используется (не блокирует работу)
4. Рекомендуется выполнить `update-rates`

**Пример проверки TTL**:

Установите короткий TTL
```
echo '{"CACHE_TTL_SECONDS": 10}' > config.json
```

Обновите курсы
```
[trader] > update-rates
```

Подождите 11 секунд или выполните в окне терминала
```
sleep 11
```

Просмотрите портфель
```
[trader] > show-portfolio
```

Проверьте логи
```
cat logs/actions.log | grep TTL
```

Вывод: 
```
WARNING - Курс BTC → USD устарел: возраст 11с > TTL 10с
```

### История курсов

Все обновления курсов сохраняются в `data/exchange_rates.json` с метками времени.

---

## Тестовая функция пополнения

### Описание

Функция `demo-deposit` **не входила в ТЗ**, но добавлена для удобства тестирования и демонстрации.

### Назначение

- Быстрое пополнение счёта для тестирования покупки/продажи
- Пополнение любой валюты (USD, EUR, BTC, и т.д.)
- Указание произвольной суммы

### Использование

Пополнение USD (по умолчанию 10000)
```
[trader] > demo-deposit
```

Пополнение конкретной валюты
```
[trader] > demo-deposit --currency EUR --amount 5000
[trader] > demo-deposit --currency BTC --amount 0.5
```

### Вывод
```
Пополнение выполнено: 10000.0000 USD
Валюта: [FIAT] USD — US Dollar (Issuing: United States)

Изменения в кошельке:

Было: 0.0000 USD

Стало: 10000.0000 USD

Изменение: +10000.0000 USD
```

---

## Логирование

### Файлы логов

**1. `logs/actions.log`** - Основное приложение
- Регистрация, вход, покупка, продажа
- Просмотр портфеля, получение курсов
- Ошибки и исключения

**2. `logs/parser.log`** - Parser Service
- Запросы к API
- Обновление курсов
- Ошибки API

### Уровни логирования

- **INFO**: Основные действия (покупка, продажа, обновление курсов)
- **DEBUG**: Детальная информация (курсы, конвертации, TTL)
- **WARNING**: Предупреждения (устаревшие курсы, неоптимальные операции)
- **ERROR**: Ошибки (недостаточно средств, ошибки API)

### Настройка

В `config.json`:

```
{
"LOG_LEVEL": "DEBUG", // INFO, DEBUG, WARNING, ERROR
"LOG_FILE": "logs/actions.log",
"LOG_MAX_BYTES": 10485760 // 10 MB
}
```

---

## Демонстрация

### asciinema

Ссылка на демонстрацию:

[![asciicast](https://asciinema.org/a/bBlKSuBtLC2ZU9PBQd7Vja8IL.svg)](https://asciinema.org/a/bBlKSuBtLC2ZU9PBQd7Vja8IL)

**В демонстрации**:
- `CACHE_TTL_SECONDS` установлен в **10 секунд** для наглядности
- Показано предупреждение об устаревших курсах
- Треугольная конвертация USD→RUB через курсы

**В коде (settings.py)**:
- По умолчанию `CACHE_TTL_SECONDS = 300` (5 минут)

---