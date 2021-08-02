import logging
import select
import sys
from lesson5.config import ACTION, PRESENCE, TIME, RESPONSE, OK, WRONG_REQUEST, \
    ERROR, server_port, server_address, FROM, SHUTDOWN, \
    MSG, TO, MESSAGE, SERVER, MAIN_CHANNEL, UNKNOWN_ERROR, GET_CONTACTS, USER_LOGIN
import socket
from lesson5.decorators import Log
import argparse
import pickle

from server_database import ServerStorage
from lesson5.logs import server_config_log
from lesson5.descriptors import SockVerify
from lesson5.meta import ServerVerifier

log = logging.getLogger('Server_log')
logger = Log(log)


class ServerSocket(socket.socket):
    port = SockVerify()
    address = SockVerify()

    def __init__(self, p_addr='0.0.0.0', p_port=7777):
        super().__init__()
        self.address = p_addr
        self.port = p_port
        self.bind((self.address, self.port))
        self.listen(1)
        self.settimeout(0.1)


class Server(metaclass=ServerVerifier):
    global log, logger
    # Список сокетов клиентов и словарь аккаунтов клиентов с информацией о сокете
    clients = []
    names = {}
    alive = True

    def __init__(self, database, serv_addr=server_address, serv_port=server_port):
        self.serv_addr = serv_addr
        self.serv_port = serv_port

        # База данных сервера
        self.database = database

    # Функция чтения сообщений с сокетов клиентов
    def read_messages(self, from_clients, client_list):
        # список всех полученных сообщений
        message_list = []
        for connection in from_clients:
            if self.alive:
                try:
                    data_bytes = connection.recv(1024)  # принимаем данные от клиента, по 1024 байт
                    client_message = pickle.loads(data_bytes)  # Преобразование строки JSON в объекты Python
                    log.info(f'Принято сообщение от клиента: {client_message[FROM]}')
                    log.debug(f'{client_message}')
                    # Если спец сообщение от Admin, то вырубаем сервер
                    if ACTION in client_message and \
                            client_message[ACTION] == 'Stop server' and \
                            client_message[FROM] == 'Admin':
                        log.info(f'Получена команда выключения сервера, ответ: {RESPONSE}: {SHUTDOWN}')
                        self.alive = False
                        # return {RESPONSE: SHUTDOWN}
                    message_list.append((client_message, connection))
                except:
                    log.debug(
                        f'Клиент {connection.fileno()} {connection.getpeername()} '
                        f'отключился до передачи сообщения по таймауту')
                    self.names = {key: val for key, val in self.names.items() if val != connection}
                    client_list.remove(connection)
        return message_list

    # Функция записи сообщений в сокеты клиентов
    def write_messages(self, messages, to_clients, client_list):
        for message, sender in messages:
            if self.alive:
                # ------------------- Запроса списка всех пользователей ------------------- #
                if ACTION in message and message[ACTION] == GET_CONTACTS:
                    connection = self.names[message[FROM]]
                    users = [user for user in self.database.get_all_users() if user != message[FROM]]
                    answer = {
                        RESPONSE: 202,
                        ACTION: GET_CONTACTS,
                        "alert": users,
                        FROM: SERVER,
                        MESSAGE: '',
                        TO: message[FROM]
                    }
                    data_bytes = pickle.dumps(answer)  # Преобразование объекта Python в строку JSON
                    connection.send(data_bytes)
                # Если приватный канал, то отправка только одному получателю
                elif message[ACTION] == MSG \
                        and message[TO] != MAIN_CHANNEL \
                        and message[TO] != message[FROM]:
                    # получаем пользователя, которому отправляем сообщение
                    to = message[TO]
                    # обработка сервером команды who
                    if message[MESSAGE] != 'who':
                        message[MESSAGE] = f'(private){message[FROM]}:> {message[MESSAGE]}'
                    try:
                        connection = self.names[to]
                    except:
                        connection = self.names[message[FROM]]
                        if message[TO] == SERVER and message[MESSAGE] == 'who':
                            message[TO] = message[FROM]
                            client_names = [key for key in self.names.keys()]
                            message[MESSAGE] = f'<:SERVER:> Список клиентов в онлайн: {client_names}'
                            log.debug(
                                f'Пользователем {message[FROM]} запрошен список пользователей онлайн: '
                                f'{message[MESSAGE]}')
                        else:
                            message[TO] = message[FROM]
                            message[FROM] = SERVER
                            message[MESSAGE] = f'<:SERVER:> Клиент {to} не подключен. Отправка сообщения не возможна!'
                            log.warning(message)
                    # отправка сообщения
                    try:
                        data_bytes = pickle.dumps(message)  # Преобразование объекта Python в строку JSON
                        connection.send(data_bytes)
                    except:
                        log.warning(
                            f'Сокет клиента {connection.fileno()} {connection.getpeername()} '
                            f'недоступен для отправки. Вероятно он отключился')
                        self.names = {key: val for key, val in self.names.items() if val != connection}
                        connection.close()
                        client_list.remove(connection)
                # если общий канал, то отправка сообщения всем клиентам
                elif message[ACTION] == MSG and message[TO] == MAIN_CHANNEL:
                    message[MESSAGE] = f'{message[FROM]}:> {message[MESSAGE]}'
                    for connection in to_clients:
                        # отправка сообщения
                        try:
                            data_bytes = pickle.dumps(message)  # Преобразование объекта Python в строку JSON
                            connection.send(data_bytes)
                        except:
                            log.warning(
                                f'Сокет клиента {connection.fileno()} {connection.getpeername()} '
                                f'недоступен для отправки. Вероятно он отключился')
                            self.names = {key: val for key, val in self.names.items() if val != connection}
                            connection.close()
                            client_list.remove(connection)

    # Функция проверки корректности приветственного сообщения и формирования ответа
    @logger
    def check_correct_presence_and_response(self, presence_message):
        log.debug('Запуск ф-ии проверки корректности запроса')
        if ACTION in presence_message and presence_message[ACTION] == 'Unknown':
            return {RESPONSE: UNKNOWN_ERROR}
        elif ACTION in presence_message and \
                presence_message[ACTION] == PRESENCE and \
                TIME in presence_message and \
                isinstance(presence_message[TIME], str):
            # Если всё хорошо шлем ОК
            log.debug(f'Проверка успешна, ответ: {RESPONSE}: {OK}')
            return {RESPONSE: OK}
        else:
            # Иначе шлем код ошибки
            log.warning(f'{RESPONSE}: {WRONG_REQUEST}, {ERROR}: "Не верный запрос"')
            return {RESPONSE: WRONG_REQUEST, ERROR: 'Не верный запрос'}

    @logger
    def start_server(self):

        # создаем сокет для работы с клиентами
        s = ServerSocket(self.serv_addr, self.serv_port)

        log.info('Запуск сервера! Готов к приему клиентов! \n')
        while self.alive:
            try:
                # Прием запросов на подключение, проверка приветственного сообщения и ответ
                client, address = s.accept()
                log.info(f'Получен запрос на соединение от {address[0]}:{address[1]}')
                # print(client, address)
                data_bytes = client.recv(1024)  # принимаем данные от клиента, по 1024 байт
                client_message = pickle.loads(data_bytes)  # Преобразование строки JSON в объекты Python
                log.info(f'Принято сообщение от клиента: {client_message}')
                answer = self.check_correct_presence_and_response(client_message)
                client_name = client_message.get('user').get('account_name')
                log.info(f"Приветствуем пользователя {client_name}!")
                log.info(f'Отправка ответа клиенту: {answer}')
                data_bytes = pickle.dumps(answer)  # Преобразование объекта Python в строку JSON
                client.send(data_bytes)
            except OSError as e:
                log.debug(f'За время socket timeout не было подключений: {e}')
                pass
            else:
                self.names[client_name] = client
                self.clients.append(client)
            finally:
                r = []
                w = []
                e = []
                select_timeout = 0
            try:
                r, w, e = select.select(self.clients, self.clients, e, select_timeout)
            except:
                # исключение в случае отключения любого из клиентов
                pass

            req = self.read_messages(r, self.clients)
            self.write_messages(req, w, self.clients)

        s.close()
        exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', type=int, help='Port server', default=server_port)
    parser.add_argument('-a', '--address', type=str, help='Address server', default=server_address)
    args = parser.parse_args()

    server_port = args.port
    server_address = args.address

    # Показывать лог в консоль при запуске сервера напрямую
    server_stream_handler = logging.StreamHandler(sys.stdout)
    server_stream_handler.setLevel(logging.DEBUG)
    server_stream_handler.setFormatter(server_config_log.log_format)
    log.addHandler(server_stream_handler)

    # Инициализация базы данных
    database = ServerStorage()

    my_server = Server(database, server_address, server_port)
    my_server.start_server()
