import argparse
import sys

sys.path.append('.')

from valutatrade_hub.core import usecases

from valutatrade_hub.core.exceptions import (
    InsufficientFundsError,
    CurrencyNotFoundError,
    ApiRequestError
)
from valutatrade_hub.core.currencies import get_supported_currencies

def create_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        prog='ValutaTrade Hub',
        description='Платформа для управления виртуальным портфелем валют',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # создаём subпарсеры для команд
    subparsers = parser.add_subparsers(dest='command', help='Доступные команды')

    # команда register
    register_parser = subparsers.add_parser(
        'register',
        help='Зарегистрировать нового пользователя'
    )
    register_parser.add_argument(
        '--username',
        required=True,
        help='Имя пользователя (уникальное)'
    )
    register_parser.add_argument(
        '--password',
        required=True,
        help='Пароль (минимум 4 символа)'
    )

    # команда login
    login_parser = subparsers.add_parser(
        'login',
        help='Войти в систему'
    )
    login_parser.add_argument(
        '--username',
        required=True,
        help='Имя пользователя'
    )
    login_parser.add_argument(
        '--password',
        required=True,
        help='Пароль'
    )

    # команда show-portfolio
    portfolio_parser = subparsers.add_parser(
        'show-portfolio',
        help='Показать портфель пользователя'
    )
    portfolio_parser.add_argument(
        '--base',
        default='USD',
        help='Базовая валюта для расчёта (по умолчанию USD)'
    )

    # команда buy
    buy_parser = subparsers.add_parser(
        'buy',
        help='Купить валюту'
    )
    buy_parser.add_argument(
        '--currency',
        required=True,
        help='Код покупаемой валюты (например, BTC, EUR)'
    )
    buy_parser.add_argument(
        '--amount',
        required=True,
        type=float,
        help='Количество валюты для покупки'
    )

    # команда sell
    sell_parser = subparsers.add_parser(
        'sell',
        help='Продать валюту'
    )
    sell_parser.add_argument(
        '--currency',
        required=True,
        help='Код продаваемой валюты'
    )
    sell_parser.add_argument(
        '--amount',
        required=True,
        type=float,
        help='Количество валюты для продажи'
    )

    # команда get-rate
    rate_parser = subparsers.add_parser(
        'get-rate',
        help='Получить курс обмена валют'
    )
    rate_parser.add_argument(
        '--from',
        dest='from_currency',
        required=True,
        help='Исходная валюта'
    )
    rate_parser.add_argument(
        '--to',
        dest='to_currency',
        required=True,
        help='Целевая валюта'
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

def handle_buy(args):
    try:
        success, message = usecases.buy_currency(args.currency, args.amount)
        print(message)
        return 0 if success else 1
    except CurrencyNotFoundError as e:
        print(f"❌ {e}")
        print(f"💡 Поддерживаемые валюты: {', '.join(get_supported_currencies())}")
        print("   Используйте: get-rate --from USD --to <ВАЛЮТА> для проверки курса")
        return 1
    except InsufficientFundsError as e:
        print(f"❌ {e}")
        print("💡 Пополните USD кошелёк или продайте другие валюты")
        return 1
    except ApiRequestError as e:
        print(f"❌ {e}")
        print("💡 Повторите попытку позже или проверьте подключение к сети")
        return 1

def handle_sell(args):
    try:
        success, message = usecases.sell_currency(args.currency, args.amount)
        print(message)
        return 0 if success else 1
    except CurrencyNotFoundError as e:
        print(f"❌ {e}")
        print(f"💡 Поддерживаемые валюты: {', '.join(get_supported_currencies())}")
        print("   Используйте: get-rate --from USD --to <ВАЛЮТА> для проверки курса")
        return 1
    except InsufficientFundsError as e:
        print(f"❌ {e}")
        print("💡 Пополните USD кошелёк или продайте другие валюты")
        return 1
    except ApiRequestError as e:
        print(f"❌ {e}")
        print("💡 Повторите попытку позже или проверьте подключение к сети")
        return 1

def handle_get_rate(args):
    try:
        success, message = usecases.get_exchange_rate(args.from_currency, args.to_currency)
        print(message)
        return 0 if success else 1
    except CurrencyNotFoundError as e:
        print(f"❌ {e}")
        print(f"💡 Поддерживаемые валюты: {', '.join(get_supported_currencies())}")
        print("   Используйте: get-rate --from USD --to <ВАЛЮТА> для проверки курса")
        return 1
    except InsufficientFundsError as e:
        print(f"❌ {e}")
        print("💡 Пополните USD кошелёк или продайте другие валюты")
        return 1
    except ApiRequestError as e:
        print(f"❌ {e}")
        print("💡 Повторите попытку позже или проверьте подключение к сети")
        return 1

def run():

    parser = create_parser()

    # если нет аргументов - показываем help
    if len(sys.argv) == 1:
        parser.print_help()
        return 0

    args = parser.parse_args()

    # маршрутизация команд
    if args.command == 'register':
        return handle_register(args)
    elif args.command == 'login':
        return handle_login(args)
    elif args.command == 'show-portfolio':
        return handle_show_portfolio(args)
    elif args.command == 'buy':
        return handle_buy(args)
    elif args.command == 'sell':
        return handle_sell(args)
    elif args.command == 'get-rate':
        return handle_get_rate(args)
    else:
        parser.print_help()
        return 1

if __name__ == '__main__':
    sys.exit(run())

def run_interactive():

    print("=" * 70)
    print("Добро пожаловать в ValutaTrade Hub!")
    print("=" * 70)
    print("\nИнтерактивный режим. Доступные команды:")
    print("  register --username <имя> --password <пароль>")
    print("  login --username <имя> --password <пароль>")
    print("  show-portfolio [--base <валюта>]")
    print("  buy --currency <код> --amount <количество>")
    print("  sell --currency <код> --amount <количество>")
    print("  get-rate --from <валюта> --to <валюта>")
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
            if command_line.lower() in ['exit', 'quit', 'q']:
                print("\n До свидания!")
                break

            if command_line.lower() == 'help':
                print("\nДоступные команды:")
                print("  register --username <имя> --password <пароль>")
                print("  login --username <имя> --password <пароль>")
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

            if command_line.lower() == 'clear':
                import os
                os.system('clear' if os.name != 'nt' else 'cls')
                continue

            # парсим и выполняем команду
            args_list = command_line.split()
            parser = create_parser()

            try:
                args = parser.parse_args(args_list)

                # маршрутизация команд
                if args.command == 'register':
                    handle_register(args)
                elif args.command == 'login':
                    handle_login(args)
                elif args.command == 'show-portfolio':
                    handle_show_portfolio(args)
                elif args.command == 'buy':
                    handle_buy(args)
                elif args.command == 'sell':
                    handle_sell(args)
                elif args.command == 'get-rate':
                    handle_get_rate(args)
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
