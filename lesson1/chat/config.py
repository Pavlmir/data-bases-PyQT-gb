server_address = 'localhost'
server_port = 7777

ACTION = 'action'
TIME = 'time'
USER = 'user'
MAX_CONNECTIONS = 5  # Максимальная очередь подключений

ACCOUNT_NAME = 'account_name'
RESPONSE = 'response'
ERROR = 'error'
PRESENCE = 'presence'
MAIN_CHANNEL = '#all'
SERVER = 'server'
MSG = 'msg'
TO = 'to'
FROM = 'from'
MESSAGE = 'message'
alive = True
SHUTDOWN = 0 #Выключение сервера

BASIC_NOTICE = 100
OK = 200
ACCEPTED = 202
WRONG_REQUEST = 400
SERVER_ERROR = 500
IMPORTANT_NOTICE = 101  # важное уведомление.
CREATED = 201  # объект создан;
NO_AUTH = 401  # не авторизован;
WRONG_PASSWORD = 402  # неправильный логин/пароль;
BANNED = 403  # (forbidden) — пользователь заблокирован;
NOT_FOUND = 404  # (not found) — пользователь/чат отсутствует на сервере;
CONFLICT = 409  # (conflict) — уже имеется подключение с указанным логином;
GONE = 410  # (gone) — адресат существует, но недоступен (offline).
INTERNAL_ERROR = 500  # ошибка сервера.

StandartServerCodes = BASIC_NOTICE, OK, ACCEPTED,\
                      WRONG_REQUEST, SERVER_ERROR,\
                      IMPORTANT_NOTICE, CREATED, NO_AUTH, \
                      WRONG_PASSWORD, BANNED, NOT_FOUND,\
                      GONE, INTERNAL_ERROR


class UnknownCode(Exception):
    def __init__(self, code):
        self.code = code

    def __str__(self):
        return f'Неизвестный код ответа {self.code}'
