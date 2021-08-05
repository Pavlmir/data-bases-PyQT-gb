server_address = '0.0.0.0'
server_port = 7780
mode = 'f'
account = 'Guest'
alive = True

ACTION = 'action'
TIME = 'time'
USER = 'user'

ACCOUNT_NAME = 'account_name'
RESPONSE = 'response'
ERROR = 'error'
PRESENCE = 'presence'
MSG = 'msg'
TO = 'to'
FROM = 'from'
MESSAGE = 'message'
MAIN_CHANNEL = '#all'
SERVER = 'server'

GET_CONTACTS = 'get_contacts'
USER_LOGIN = 'user_login'

BASIC_NOTICE = 100
OK = 200
ACCEPTED = 202
WRONG_REQUEST = 400
SERVER_ERROR = 500
IMPORTANT_NOTICE = 101  # важное уведомление.
CREATED = 201  # объект создан;
NO_AUTH = 401  # не авторизован;
WRONG_PASSW = 402  # неправильный логин/пароль;
BANNED = 403  # (forbidden) — пользователь заблокирован;
NOT_FOUND = 404  # (not found) — пользователь/чат отсутствует на сервере;
CONFLICT = 409  # (conflict) — уже имеется подключение с указанным логином;
GONE = 410  # (gone) — адресат существует, но недоступен (offline).
INTERNAL_ERROR = 500  # ошибка сервера.
SHUTDOWN = 0  # Выключение сервера
UNKNOWN_ERROR = 999  # Нестандартная ошибка

StandartServerCodes = BASIC_NOTICE, OK, ACCEPTED, WRONG_REQUEST, SERVER_ERROR, IMPORTANT_NOTICE, CREATED, NO_AUTH, WRONG_PASSW, BANNED, NOT_FOUND, GONE, INTERNAL_ERROR, SHUTDOWN

# База данных для хранения данных сервера:
SERVER_DATABASE_NAME = 'server_base.db3'
SERVER_DATABASE = f'sqlite:///{SERVER_DATABASE_NAME}'
COMMON_CHAT = "Общий чат"
COMMON_CHAT_PWD = "11"

CLIENT_DATABASE_NAME = 'client_base.db3'
CLIENT_DATABASE = f'sqlite:///{CLIENT_DATABASE_NAME}'

class UnknownCode(Exception):
    def __init__(self, code):
        self.code = code

    def __str__(self):
        return f'Неизвестный код ответа {self.code}'
