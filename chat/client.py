"""
Урок 3. Основы сетевого программирования
1. Реализовать простое клиент-серверное взаимодействие по протоколу JIM (JSON instant messaging):
a. клиент отправляет запрос серверу;
b. сервер отвечает соответствующим кодом результата.
Клиент и сервер должны быть реализованы в виде отдельных скриптов, содержащих соответствующие функции.
Функции клиента:
1. Сформировать presence-сообщение;
2. Отправить сообщение серверу;
3. Получить ответ сервера;
4. Разобрать сообщение сервера;
5. Параметры командной строки скрипта client.py <addr> [<port>]:
6. Addr — ip-адрес сервера;
7. Port — tcp-порт на сервере, по умолчанию 7777.
"""
import re
import sys
import time

import logs.config.client_config_log
import argparse
import logging
import decorators
from datetime import datetime
import pickle
import threading

import socket
from config import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, \
    OK, server_port, server_address, StandartServerCodes, UnknownCode, \
    MAIN_CHANNEL, SERVER, MSG, TO, FROM, MESSAGE, alive

log = logging.getLogger('Client_log')
logger = decorators.Log(log)

# Общая переменная для читателя и писателя сообщений
# Последний пользователь, писавший в лс:
last_private_user = ''


@logger
def create_presence_message(user_name):
    log.info('Формирование сообщения')
    if len(user_name) > 25:
        log.error('Имя пользователя более 25 символов!')
        raise ValueError

    if not isinstance(user_name, str):
        log.error('Полученное имя пользователя не является строкой символов')
        raise TypeError

    message = {
        ACTION: PRESENCE,
        TIME: datetime.today().strftime("%Y-%m-%d-%H.%M.%S"),
        USER: {
            ACCOUNT_NAME: user_name
        }
    }
    return message


@logger
def start_client(user_name, mode):
    log.info('Запуск клиента')
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if server_address != '0.0.0.0':
        s.connect((server_address, server_port))
    else:
        s.connect(('localhost', server_port))

    # создание приветственного сообщения для сервера
    message = create_presence_message(user_name)
    if isinstance(message, dict):
        data_string = pickle.dumps(message)

    log.info(f'Отправляю сообщение "{message}" на сервер')

    s.send(data_string)
    log.info('жду ответа')

    data_bytes = s.recv(1024)
    server_response = pickle.loads(data_bytes)
    log.info('Ответ:', server_response)

    # Если сервер ответил нестандартным кодом, то завершаем работу
    if server_response.get('response') not in StandartServerCodes:
        log.error(f'Неизвестный код ответа от сервера: {server_response.get("response")}')
        raise UnknownCode(server_response.get('response'))
    # Если все хорошо, то переключаем режим клиента в переданный в параметре или оставляем по-умолчанию - полный
    if server_response.get('response') == OK:
        print('Соединение установлено!')
        log.info('Авторизация успешна. Соединение установлено!')
        if mode == 'r':
            print('Клиент в режиме чтения сообщений с сервера')
            log.debug('Клиент в режиме чтения')
            client_reader(s, user_name)
        elif mode == 'w':
            print('Клиент в режиме написания сообщений на сервер')
            log.debug('Клиент в режиме записи')
            client_writer(s, user_name)
        elif mode == 'f':
            log.debug('Клиент в полнофункциональном режиме')
            print(f'Отправка сообщений всем пользователям в канал {MAIN_CHANNEL}')
            print('Для получения помощи наберите help')
            # читаем сообщения в отдельном потоке
            read_thread = threading.Thread(target=client_reader, args=(s, user_name))
            read_thread.daemon = True
            read_thread.start()
            client_writer(s, user_name)
        else:
            s.close()
            raise Exception('Не верный режим клиента')
    else:
        log.error('Что-то пошло не так..')
    s.close()


# процедура отправки сообщений на сервер
def client_writer(sock, account):
    global alive
    send_to = MAIN_CHANNEL
    console_prefix = f':> '
    # в цикле запрашиваем у пользователя ввод нового сообщения
    while alive:
        user_message = input(console_prefix)
        # Обработка служебных команд пользователя
        if user_message.startswith('to'):  # выбор получателя для отправки
            destination = user_message.split()
            try:
                send_to = destination[1]
                if destination[1] == 'all':
                    send_to = MAIN_CHANNEL
                    console_prefix = f':> '
                else:
                    console_prefix = f'{account} to {destination[1]}:> '
                log.debug(f'Получатель установлен на: {send_to}')
                continue
            except IndexError:
                print('Не задан получатель')
        if user_message == 'help':
            print(f'{account}! Для отправки личного сообщения напишите: to имя_получателя')
            print(
                'Для отправки всем напишите to all. Быстрый выбор клиента для ответа на '
                'последнее лс r. Для получения списка подключенных клиентов who. Для выхода напишите exit')
            log.debug('Вывод справки пользователю по команде help')
            continue
        if user_message == 'exit':
            log.info('Пользователь вызвал закрытие клиента - exit')
            alive = False
            sock.close()
            break
        if user_message == 'r':
            if last_private_user:
                send_to = last_private_user
                console_prefix = f'{account} to {last_private_user}:> '
                log.debug(f'Получатель установлен на последнего писавшего в лс: {last_private_user}')
                continue
        if user_message == 'who':
            message_to_send = create_message(SERVER, user_message, account)
            log.debug('Вывод списка пользователей в онлайн - who')
        if account == 'Admin' and re.findall('^[!]{3} stop', user_message):
            # Если админ написал !!! stop, то останавливаем сервер
            message_to_send = create_admin_message(user_message, account)
            log.info(f'Админ послал команду выключения сервера и сообщение {user_message}')
        elif user_message != 'who':
            # Формирование обычного сообщения
            message_to_send = create_message(send_to, user_message, account)
            log.debug('Формирование обычного сообщения')

        # Отправка сообщения
        try:
            if alive:
                sock.send(pickle.dumps(message_to_send))
                log.info(f'Отправлено сообщение на сервер: {message_to_send}')
            else:
                break
        except:
            if alive:
                print('Сервер разорвал соединение! Приложение завершает работу')
                log.error('Writer: Сервер разорвал соединение!')
                sock.close()
            alive = False
            break


# функция создания сообщения в чате
def create_message(message_to, text, account_name='Guest'):
    return {ACTION: MSG, TIME: datetime.today().strftime("%Y-%m-%d-%H.%M.%S"),
            TO: message_to, FROM: account_name, MESSAGE: text}


# функция спец сообщения для пользователя Admin
def create_admin_message(text, account_name):
    return {ACTION: 'Stop server', TIME: datetime.today().strftime("%Y-%m-%d-%H.%M.%S"),
            TO: SERVER, FROM: account_name, MESSAGE: text}


# процедура чтения сообщений с сервера
def client_reader(sock, account):
    global alive, last_private_user
    # в цикле оправшиваем сокет на предмет наличия новых сообщений
    while alive:
        try:
            data_bytes = sock.recv(1024)
            message = pickle.loads(data_bytes)
            log.info(f'Получено сообщение с сервера: {message}')
            if message[FROM] == account:
                # TODO
                print(message[MESSAGE].replace(f'{account}:> ', '(me)', 1))
            else:
                print(f'{message[MESSAGE]}')
            if message[TO] != MAIN_CHANNEL and re.findall('[^\(private\)]+', message[FROM]):
                last_private_user = message[FROM]
        except:
            if alive:
                print('Cервер разорвал соединение или получен некорректный ответ! Приложение завершает работу')
                log.error('Reader: Сервер разорвал соединение или получен некорректный ответ!')
                sock.close()
            alive = False
            break
    sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', type=int, help='Port server', default=server_port)
    parser.add_argument('-a', '--address', type=str, help='Address server', default=server_address)
    parser.add_argument('-u', '--user', type=str, help='User name', default='Guest')
    parser.add_argument('-m', '--mode', type=str, help='r - режим чтения,'
                                                       'w - написать сообщение,'
                                                       'f - полный режим', default='f')

    args = parser.parse_args()

    server_port = args.port
    server_address = args.address
    user_name = args.user
    mode = args.mode

    start_client(user_name, mode)
