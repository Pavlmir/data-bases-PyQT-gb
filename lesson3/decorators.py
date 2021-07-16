import time
import traceback
from functools import wraps


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
