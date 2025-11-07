import argparse
import sys

sys.path.append('.')

from valutatrade_hub.core import usecases
from valutatrade_hub.core.currencies import FiatCurrency
from valutatrade_hub.decorators import handle_command_errors


def create_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        prog="ValutaTrade Hub",
        description="Платформа для управления виртуальным портфелем валют",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # создаем subпарсеры для команд
    subparsers = parser.add_subparsers(dest="command", help="Доступные команды")

    # команда register
    register_parser = subparsers.add_parser(
        "register",
        help="Зарегистрировать нового пользователя"
    )
    register_parser.add_argument(
        "--username",
        required=True,
        help="Имя пользователя (уникальное)"
    )
    register_parser.add_argument(
        "--password",
        required=True,
        help="Пароль (минимум 4 символа)"
    )
    # команда login
    login_parser = subparsers.add_parser(
        "login",
        help="Войти в систему"
    )
    login_parser.add_argument(
        "--username",
        required=True,
        help="Имя пользователя"
    )
    login_parser.add_argument(
        "--password",
        required=True,
        help="Пароль"
    )
    # команда show-portfolio
    portfolio_parser = subparsers.add_parser(
        "show-portfolio",
        help="Показать портфель пользователя"
    )
    portfolio_parser.add_argument(
        "--base",
        default="USD",
        help="Базовая валюта для расчета (по умолчанию USD)"
    )
    # команда buy
    buy_parser = subparsers.add_parser(
        "buy",
        help="Купить валюту"
    )
    buy_parser.add_argument(
        "--currency",
        required=True,
        help="Код покупаемой валюты (например, BTC, EUR)"
    )
    buy_parser.add_argument(
        "--amount",
        required=True,
        type=float,
        help="Количество валюты для покупки"
    )
    # команда sell
    sell_parser = subparsers.add_parser(
        "sell",
        help="Продать валюту"
    )
    sell_parser.add_argument(
        "--currency",
        required=True,
        help="Код продаваемой валюты"
    )
    sell_parser.add_argument(
        "--amount",
        required=True,
        type=float,
        help="Количество валюты для продажи"
    )
    # команда get-rate
    rate_parser = subparsers.add_parser(
        "get-rate",
        help="Получить курс обмена валют"
    )
    rate_parser.add_argument(
        "--from",
        dest="from_currency",
        required=True,
        help="Исходная валюта"
    )
    rate_parser.add_argument(
        "--to",
        dest="to_currency",
        required=True,
        help="Целевая валюта"
    )
    # Команда update-rates
    update_rates_parser = subparsers.add_parser(
        "update-rates",
        help="Обновить курсы валют из внешних API"
    )
    update_rates_parser.add_argument(
        "--source",
        choices=["coingecko", "exchangerate"],
        help="Обновить только указанный источник"
    )
    # Команда show-rates
    show_rates_parser = subparsers.add_parser(
        "show-rates",
        help="Показать актуальные курсы из кэша"
    )
    show_rates_parser.add_argument(
        "--currency",
        help="Показать курс только для указанной валюты"
    )
    show_rates_parser.add_argument(
        "--top",
        type=int,
        help="Показать N самых дорогих валют"
    )
    # demo deposit
    demo_parser = subparsers.add_parser(
        'demo-deposit',
        help='Тестовое пополнение счета (демо-режим)'
    )
    demo_parser.add_argument(
        '--currency',
        type=str,
        default='USD',
        help='Валюта для пополнения (по умолчанию: USD)'
    )
    demo_parser.add_argument(
        '--amount',
        type=float,
        default=10000.0,
        help='Сумма пополнения (по умолчанию: 10000.0)'
    )

    return parser

def handle_register(args):
    success, message = usecases.register_user(args.username, args.password)
    print(message)
    return 0 if success else 1

def handle_login(args):
    success, message = usecases.login_user(args.username, args.password)
    print(message)
    return 0 if success else 1

def handle_show_portfolio(args):

    success, message = usecases.show_portfolio(args.base)
    print(message)
    return 0 if success else 1

@handle_command_errors
def handle_buy(args):
    success, message = usecases.buy_currency(args.currency, args.amount)
    print(message)
    return 0 if success else 1

@handle_command_errors
def handle_sell(args):
    success, message = usecases.sell_currency(args.currency, args.amount)
    print(message)
    return 0 if success else 1

@handle_command_errors
def handle_get_rate(args):
    success, message = usecases.get_exchange_rate(args.from_currency, args.to_currency)
    print(message)
    return 0 if success else 1


def handle_update_rates(args):
    """Обработать команду update-rates"""
    try:
        from valutatrade_hub.parser_service.updater import RatesUpdater

        print("Начинается обновление курсов...")
        print()

        updater = RatesUpdater()
        result = updater.run_update(source_filter=args.source)

        print()
        if result["success"]:
            print("Обновление успешно завершено!")
        else:
            print("Обновление завершено с ошибками")

        print(f"   Всего курсов обновлено: {result['total_rates']}")
        print(f"   Время выполнения: {result['duration']:.2f}с")
        print()
        print("По источникам:")
        for source, count in result["by_source"].items():
            status = "✓" if count > 0 else "✗"
            print(f"  {status} {source}: {count} курсов")

        if result["errors"]:
            print()
            print("Ошибки:")
            for error in result["errors"]:
                print(f"  ✗ {error}")

        print()
        print("Данные сохранены:")
        print("   - Кэш: data/rates.json")
        print("   - История: data/exchange_rates.json")

        return 0 if result["success"] else 1

    except Exception as e:
        print(f"✗ Критическая ошибка: {e}")
        print("   Проверьте logs/parser.log для подробностей")
        return 1


def handle_show_rates(args):
    """Обработать команду show-rates"""
    try:
        from valutatrade_hub.core.currencies import get_currency
        from valutatrade_hub.core.exceptions import CurrencyNotFoundError
        from valutatrade_hub.parser_service.storage import RatesStorage

        storage = RatesStorage()
        data = storage.get_all_rates()
        pairs = data.get("pairs", {})
        last_refresh = data.get("last_refresh")

        if not pairs:
            print("✗ Локальный кэш курсов пуст.")
            print("Выполните 'update-rates' для загрузки данных.")
            return 1

        print("Курсы валют из кэша")
        print(f"Последнее обновление: {last_refresh}")
        print()

        # фильтруем и сортируем
        filtered_pairs = pairs

        if args.currency:
            currency_upper = args.currency.upper()
            filtered_pairs = {
                k: v for k, v in pairs.items()
                if currency_upper in k
            }

            if not filtered_pairs:
                print(f"✗ Курсов для валюты '{args.currency}' не найдено.")
                return 1

        # сортируем по значению для --top
        if args.top:
            sorted_pairs = sorted(
                filtered_pairs.items(),
                key=lambda item: item[1]["rate"],
                reverse=True
            )
            filtered_pairs = dict(sorted_pairs[:args.top])
        else:
            # обычная сортировка по названию
            filtered_pairs = dict(sorted(filtered_pairs.items()))

        # выводим таблицу
        print(f"{'Пара':<15} {'Курс':>15} {'Источник':<20} {'Обновлено'}")
        print("-" * 75)

        for pair_key, info in filtered_pairs.items():
            rate = info["rate"]
            source = info["source"]
            updated = info["updated_at"][:19]  # обрезаем миллисекунды

            # добавляем информацию о валюте
            try:
                from_curr = pair_key.split('_')[0]
                currency = get_currency(from_curr)
                currency_type = "F" if isinstance(currency, FiatCurrency) else "C"
                pair_display = f"{pair_key} ({currency_type})"
            except (CurrencyNotFoundError, IndexError):
                pair_display = pair_key

            print(f"{pair_display:<15} {rate:>15.8f} {source:<20} {updated}")

        print()
        print(f"Всего курсов: {len(filtered_pairs)}")

        return 0

    except Exception as e:
        print(f"✗ Ошибка отображения курсов: {e}")
        return 1

@handle_command_errors
def handle_demo_deposit(args):
    """
    Обработать команду demo-deposit
    """
    success, message = usecases.demo_deposit(args.currency, args.amount)
    print(message)
    return 0 if success else 1

def run():

    parser = create_parser()

    # если нет аргументов - показываем help
    if len(sys.argv) == 1:
        parser.print_help()
        return 0

    args = parser.parse_args()

    # маршрутизация команд
    if args.command == "register":
        return handle_register(args)
    elif args.command == "login":
        return handle_login(args)
    elif args.command == "show-portfolio":
        return handle_show_portfolio(args)
    elif args.command == "buy":
        return handle_buy(args)
    elif args.command == "sell":
        return handle_sell(args)
    elif args.command == "get-rate":
        return handle_get_rate(args)
    elif args.command == "update-rates":
        return handle_update_rates(args)
    elif args.command == "show-rates":
        return handle_show_rates(args)
    elif args.command == "demo-deposit":
        return handle_demo_deposit(args)
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(run())

def run_interactive():

    print("=" * 70)
    print("Добро пожаловать в ValutaTrade Hub!")
    print("=" * 70)
    print("\nИнтерактивный режим. Доступные команды:")
    print("  register --username <имя> --password <пароль>")
    print("  login --username <имя> --password <пароль>")
    print("  demo-deposit --currency <валюта> --amount <сумма>")
    print("  show-portfolio [--base <валюта>]")
    print("  buy --currency <код> --amount <количество>")
    print("  sell --currency <код> --amount <количество>")
    print("  get-rate --from <валюта> --to <валюта>")
    print("  update-rates [--source <coingecko|exchangerate>]")
    print("  show-rates [--currency <код>] [--top <N>]")
    print("\nСпециальные команды:")
    print("  help    - показать эту справку")
    print("  exit    - выйти из программы")
    print("  clear   - очистить экран\n")
    print("=" * 70)
    print()

    # статус авторизации
    user = usecases.get_current_user()
    if user:
        print(f"✓ Вы вошли как '{user.username}'")
    else:
        print("✗ Вы не авторизованы. Выполните login или register.")
    print()

    while True:
        try:
            # получаем текущего пользователя для промпта
            user = usecases.get_current_user()
            if user:
                prompt = f"[{user.username}] > "
            else:
                prompt = "> "

            # читаем команду
            command_line = input(prompt).strip()

            # пропускаем пустые строки
            if not command_line:
                continue

            # обработка специальных команд
            if command_line.lower() in ["exit", "quit", "q"]:
                print("\nДо свидания!")
                break

            if command_line.lower() == "help":
                print("\nДоступные команды:")
                print("  register --username <имя> --password <пароль>")
                print("  login --username <имя> --password <пароль>")
                print("  demo-deposit --currency <валюта> --amount <сумма>")
                print("  show-portfolio [--base <валюта>]")
                print("  buy --currency <код> --amount <количество>")
                print("  sell --currency <код> --amount <количество>")
                print("  get-rate --from <валюта> --to <валюта>")
                print("\nСпециальные команды:")
                print("  help    - показать эту справку")
                print("  exit    - выйти из программы")
                print("  clear   - очистить экран")
                print()
                continue

            if command_line.lower() == "clear":
                import os
                os.system("clear" if os.name != "nt" else "cls")
                continue

            # парсим и выполняем команду
            args_list = command_line.split()
            parser = create_parser()

            try:
                args = parser.parse_args(args_list)

                # маршрутизация команд
                if args.command == "register":
                    handle_register(args)
                elif args.command == "login":
                    handle_login(args)
                elif args.command == "show-portfolio":
                    handle_show_portfolio(args)
                elif args.command == "buy":
                    handle_buy(args)
                elif args.command == "sell":
                    handle_sell(args)
                elif args.command == "get-rate":
                    handle_get_rate(args)
                elif args.command == "update-rates":
                    handle_update_rates(args)
                elif args.command == "show-rates":
                    handle_show_rates(args)
                elif args.command == "demo-deposit":
                    handle_demo_deposit(args)
                else:
                    print("✗ Неизвестная команда. Введите 'help' для справки.")

                print()  # пустая строка после вывода

            except SystemExit:
                # argparse вызывает sys.exit() при ошибке парсинга
                # в интерактивном режиме игнорируем
                print("✗ Ошибка в команде. Введите 'help' для справки.\n")
                continue

        except KeyboardInterrupt:
            # ctrl+C
            print("\n\nДо свидания!")
            break
        except EOFError:
            # ctrl+D
            print("\n\nДо свидания!")
            break
        except Exception as e:
            print(f"✗ Ошибка: {e}\n")
