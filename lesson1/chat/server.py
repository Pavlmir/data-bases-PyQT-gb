"""
Урок 3. Основы сетевого программирования
1. Реализовать простое клиент-серверное взаимодействие по протоколу JIM (JSON instant messaging):
a. клиент отправляет запрос серверу;
b. сервер отвечает соответствующим кодом результата.
Клиент и сервер должны быть реализованы в виде отдельных скриптов, содержащих соответствующие функции.
Функции сервера:
1. Принимает сообщение клиента;
2. Формирует ответ клиенту;
3. Отправляет ответ клиенту.
Имеет параметры командной строки:
-p <port> — TCP-порт для работы (по умолчанию использует 7777);
-a <addr> — IP-адрес для прослушивания (по умолчанию слушает все доступные адреса).
"""
import logging
import select
import sys
from config import ACTION, PRESENCE, TIME, RESPONSE, OK, WRONG_REQUEST, \
    ERROR, server_port, server_address, FROM, SHUTDOWN, \
    MSG, TO, MESSAGE, SERVER, MAIN_CHANNEL
import socket
import decorators
import argparse
import pickle

log = logging.getLogger('Server_log')
logger = decorators.Log(log)


@logger
def check_correct_presence_and_response(presence_message):
    log.info('Запуск функции проверки корректности запроса')
    if ACTION in presence_message and \
            presence_message[ACTION] == PRESENCE and \
            TIME in presence_message and \
            isinstance(presence_message[TIME], str):
        return {RESPONSE: OK}
    else:
        return {RESPONSE: WRONG_REQUEST, ERROR: 'Не верный запрос'}


@logger
def start_server():
    alive = True
    global clients, names
    clients = []
    names = dict()

    # создаем сокет для работы с клиентами
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:  # создаем сокет
        if not isinstance(server_address, str) or not isinstance(server_port, int):
            log.error('Полученный адрес сервера или порт не является строкой или числом!')
            raise ValueError

        sock.bind((server_address, server_port))  # связываем сокет с портом, где он будет ожидать сообщения
        sock.listen(1)
        sock.settimeout(0.1)

        log.info('Запуск сервера! Готов к приему клиентов! \n')

        while alive:
            try:
                # Прием запросов на подключение, проверка приветственного сообщения и ответ
                client, address = sock.accept()
                data_bytes = client.recv(1024)  # принимаем данные от клиента, по 1024 байт
                client_message = pickle.loads(data_bytes)  # Преобразование строки JSON в объекты Python
                log.info(f'Принято сообщение от клиента: {client_message}')
                answer = check_correct_presence_and_response(client_message)
                client_name = client_message.get('user').get('account_name')
                log.info(f"Приветствуем пользователя {client_name}!")
                log.info(f'Отправка ответа клиенту: {answer}')
                data_bytes = pickle.dumps(answer)  # Преобразование объекта Python в строку JSON
                client.send(data_bytes)
            except OSError as e:
                # за время socket timeout не было подключений
                pass
            else:
                log.info(f'Получен запрос на соединение от {str(address)}')
                names[client_name] = client
                clients.append(client)
            finally:
                r = []
                w = []
                e = []
                select_timeout = 0
            try:
                r, w, e = select.select(clients, clients, e, select_timeout)
            except:
                # исключение в случае дисконнекта любого из клиентов
                pass

            req = read_messages(r, clients)
            if req == {RESPONSE: SHUTDOWN}:
                alive = False
                log.info(f'Завершение работы сервера по команде от Admin')
            write_messages(req, w, clients)


# Функция чтения сообщений с сокетов клиентов
def read_messages(from_clients, client_list):
    # log.debug('Запуск функции получения сообщений от клиентов')
    global names
    # список всех полученных сообщений
    message_list = []
    for connection in from_clients:
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
                return {RESPONSE: SHUTDOWN}
            message_list.append((client_message, connection))
        except:
            log.debug(
                f'Клиент {connection.fileno()} {connection.getpeername()} отключился до передачи сообщения по таймауту ')
            names = {key: val for key, val in names.items() if val != connection}
            client_list.remove(connection)
    return message_list


# Функция записи сообщений в сокеты клиентов
def write_messages(messages, to_clients, client_list):
    global names
    # log.debug('Запуск функции отправки сообщений клиентам')

    for message, sender in messages:
        # Если приватный канал, то отправка только одному получателю
        if message[ACTION] == MSG and message[TO] != MAIN_CHANNEL and message[TO] != message[FROM]:
            # получаем пользователя, которому отправляем сообщение
            to = message[TO]
            # обработка сервером команды who
            if message[MESSAGE] != 'who':
                message[MESSAGE] = f'(private){message[FROM]}:> {message[MESSAGE]}'
            try:
                connection = names[to]
            except:
                connection = names[message[FROM]]
                if message[TO] == SERVER and message[MESSAGE] == 'who':
                    message[TO] = message[FROM]
                    client_names = [key for key in names.keys()]
                    message[MESSAGE] = f'<:SERVER:> Список клиентов в онлайн: {client_names}'
                    log.debug(f'Пользователем {message[FROM]} запрошен список пользователей онлайн: {message[MESSAGE]}')
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
                log.warning(f'Сокет клиента {connection.fileno()} {connection.getpeername()} '
                            f'недоступен для отправки. Вероятно он отключился')
                names = {key: val for key, val in names.items() if val != connection}
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
                    log.warning(f'Сокет клиента {connection.fileno()} {connection.getpeername()}'
                                f' недоступен для отправки. Вероятно он отключился')
                    names = {key: val for key, val in names.items() if val != connection}
                    connection.close()
                    client_list.remove(connection)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', type=int, help='Port server', default=server_port)
    parser.add_argument('-a', '--address', type=str, help='Address server', default=server_address)
    args = parser.parse_args()

    server_port = args.port
    server_address = args.address

    # Показывать лог в консоль при запуске сервера напрямую
    server_stream_handler = logging.StreamHandler(sys.stdout)
    server_stream_handler.setLevel(logging.INFO)
    server_stream_handler.setFormatter(lesson1.chat.logs.server_config_log.log_format)
    log.addHandler(server_stream_handler)

    start_server()
