import time
import traceback
from functools import wraps
import socket


class Log:
    def __init__(self, logger):
        self.logger = logger

    def __call__(self, func):
        @wraps(func)
        def deco_log_call(*args, **kwargs):
            res = func(*args, **kwargs)
            message = f'{time.asctime()} Вызван декоратор {Log.__name__} для {func.__name__}'
            if args or kwargs:
                message += ' с параметрами'
            if args:
                message += f' {args}'
            if kwargs:
                message += f' {kwargs}'
            message += f' из функции {traceback.format_stack()[0].strip().split()[-1]}'
            print(message)
            self.logger.info(message)
            return res

        return deco_log_call


def login_required(func):
    """
    Функция проверки, что клиент авторизован на сервере
    Проверяет, что передаваемый объект сокета находится в списке клиентов.
    Если его там нет закрывает сокет
    """

    @wraps(func)
    def checker(*args, **kwargs):
        from lesson6.server.server import Server
        from lesson6.config import ACTION, PRESENCE
        if isinstance(args[0], Server):
            found = False
            for arg in args:
                if isinstance(arg, socket.socket):
                    # Проверяем, что данный сокет есть в списке names класса
                    # MessageProcessor
                    for client in args[0].names:
                        if args[0].names[client] == arg:
                            found = True

            # Теперь надо проверить, что передаваемые аргументы не presence
            # сообщение
            for arg in args:
                if isinstance(arg, dict):
                    if ACTION in arg and arg[ACTION] == PRESENCE:
                        found = True
            # Если не не авторизован и не сообщение начала авторизации, то
            # вызываем исключение.
            if not found:
                print('login_required: Клиент не авторизован!')
                raise TypeError

        return func(*args, **kwargs)

    return checker
