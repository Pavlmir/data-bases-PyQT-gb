import re
import sys

import argparse
import logging
import lesson8.package_messenger.src.decorators as decorators
import time
from datetime import datetime
import pickle
import threading
import socket
from lesson8.package_messenger.src.config import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, \
    OK, server_port, server_address, StandartServerCodes, UnknownCode, \
    MAIN_CHANNEL, SERVER, MSG, TO, FROM, MESSAGE, RESPONSE, account, GET_CONTACTS
from lesson8.package_messenger.src.meta import ClientVerifier
from lesson8.package_messenger.src.logs import client_config_log

# Общая переменная для читателя и писателя сообщений
# Последний пользователь, писавший в лс:
last_private_user = ''

# Инициализация логирования клиента
log = logging.getLogger('Client_log')
logger = decorators.Log(log)


# Основная функция клиента
class Client(metaclass=ClientVerifier):
    global log, logger

    def __init__(self, serv_address=server_address, serv_port=server_port, action=PRESENCE, mode='f', acc=account):
        self.serv_address = serv_address
        self.serv_port = serv_port
        self.action = action
        self.mode = mode
        self.account = acc
        # Последний пользователь, писавший в лс:
        self.last_private_user = ''
        self.alive = True

    # функция получения списка контактов
    @staticmethod
    def get_contact_list(message_to, account, show_progress='Y') -> dict:
        if show_progress == 'Y':
            print('Обновление списка контактов с сервера..')

        return {ACTION: GET_CONTACTS,
                TIME: datetime.today().strftime("%Y-%m-%d-%H.%M.%S"),
                TO: message_to,
                FROM: account,
                MESSAGE: ''}

    # функция создания сообщения в чате
    @staticmethod
    def create_message(message_to, text, account_name='Guest'):
        return {ACTION: MSG,
                TIME: datetime.today().strftime("%Y-%m-%d-%H.%M.%S"),
                TO: message_to,
                FROM: account_name,
                MESSAGE: text}

    # функция спец сообщения для пользователя Admin
    @staticmethod
    def create_admin_message(text, account_name):
        return {ACTION: 'Stop server', TIME: datetime.today().strftime("%Y-%m-%d-%H.%M.%S"), TO: SERVER,
                FROM: account_name, MESSAGE: text}

    # процедура чтения сообщений с сервера
    def client_reader(self, sock, account_arg):
        # в цикле опрашиваем сокет на предмет наличия новых сообщений
        while self.alive:
            try:
                message = pickle.loads(sock.recv(1024))
                log.info(f'Получено сообщение с сервера: {message}')
                if message[FROM] == account_arg:
                    # TODO
                    print(message[MESSAGE].replace(f'{account_arg}:> ', '(me)', 1))
                else:
                    print(f'{message[MESSAGE]}')
                if message[TO] != MAIN_CHANNEL and re.findall('[^\(private\)]+', message[FROM]):
                    self.last_private_user = message[FROM]
            except:
                if self.alive:
                    print('Сервер разорвал соединение или получен некорректный ответ! Приложение завершает работу')
                    log.error('Reader: Сервер разорвал соединение или получен некорректный ответ!')
                    sock.close()
                self.alive = False
                break
        sys.exit(0)

    # процедура отправки сообщений на сервер
    def client_writer(self, sock, account_arg):
        send_to = MAIN_CHANNEL
        console_prefix = f':> '
        # в цикле запрашиваем у пользователя ввод нового сообщения
        while self.alive:
            message_to_send = ""
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
                        console_prefix = f'{account_arg} to {destination[1]}:> '
                    log.debug(f'Получатель установлен на: {send_to}')
                    continue
                except IndexError:
                    print('Не задан получатель')
            if user_message == 'help':
                print(f'{account_arg}! Для отправки личного сообщения напишите: to имя_получателя')
                print(
                    'Для отправки всем напишите to all. Быстрый выбор клиента для ответа на последнее лс r.'
                    'Для получения списка подключенных клиентов who. Для выхода напишите exit')
                log.debug('Вывод справки пользователю по команде help')
                continue
            if user_message == 'exit':
                log.info('Пользователь вызвал закрытие клиента - exit')
                print('Выход из программы..')
                self.alive = False
                # sock.close()
                break
            if user_message == 'r':
                if self.last_private_user:
                    send_to = self.last_private_user
                    console_prefix = f'{account_arg} to {self.last_private_user}:> '
                    log.debug(f'Получатель установлен на последнего писавшего в лс: {self.last_private_user}')
                    continue
            if user_message == 'who':
                message_to_send = self.create_message(SERVER, user_message, account_arg)
                log.debug('Вывод списка пользователей в онлайн - who')
            if account_arg == 'Admin' and re.findall('^[!]{3} stop', user_message):
                # Если админ написал !!! stop, то останавливаем сервер
                message_to_send = self.create_admin_message(user_message, account_arg)
                log.info(f'Админ послал команду выключения сервера и сообщение {user_message}')
            elif user_message != 'who':
                # Формирование обычного сообщения
                message_to_send = self.create_message(send_to, user_message, account_arg)
                log.debug('Формирование обычного сообщения')

            if user_message == '!get contact':
                log.debug('Запрос списка контактов с сервера - !get contact')
                message_to_send = self.get_contact_list(send_to, self.account)

            # Отправка сообщения
            try:
                if self.alive:
                    sock.send(pickle.dumps(message_to_send))
                    log.info(f'Отправлено сообщение на сервер: {message_to_send}')
                else:
                    break
            except:
                if self.alive:
                    print('Сервер разорвал соединение! Приложение завершает работу')
                    log.error('Writer: Сервер разорвал соединение!')
                    sock.close()
                self.alive = False
                break

    @logger
    def create_presence_message(self, account_name, action=PRESENCE):
        log.debug('Формирование приветственного сообщения')

        # Проверка параметров на соответствие протоколу
        if len(account_name) > 25:
            log.error('Имя пользователя более 25 символов!')
            raise ValueError

        if not isinstance(account_name, str):
            log.error('Полученное имя пользователя не является строкой символов')
            raise TypeError

        # Приветственное сообщение
        message = {
            ACTION: action,
            TIME: datetime.today().strftime("%Y-%m-%d-%H.%M.%S"),
            USER: {
                ACCOUNT_NAME: account_name,
                'account_password': 123
            }
        }
        return message

    @logger
    def start_client(self):
        log.info('Запуск клиента')
        print('<<< Console IM >>>')
        # Если имя аккаунта не передано, то спросим
        if len(sys.argv) < 3 and self.account == account:
            self.account = input('Введите имя аккаунта: ')
            if len(self.account) == 0:  # Если пустой ввод, то имя по-умолчанию
                self.account = 'Guest'

        print(f'Здравствуйте {self.account}!')
        # Создаем сокет для общения с сервером
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

            if not isinstance(self.serv_address, str) or not isinstance(self.serv_port, int):
                log.error('Полученный адрес сервера или порт не является строкой или числом!')
                raise ValueError

            # установка связи с сервером
            try:
                if self.serv_address == '0.0.0.0':
                    self.serv_address = 'localhost'
                log.info(f' Попытка подключения к {self.serv_address} {self.serv_port}')
                s.connect((self.serv_address, self.serv_port))
            except Exception as e:
                print('Ошибка подключения:', e)
                log.error(f'Ошибка подключения: {e}')
                raise

            # создание приветственного сообщения для сервера
            message = self.create_presence_message(self.account, self.action)

            if isinstance(message, dict):
                data_bytes = pickle.dumps(message)
                log.debug(f'Отправляю приветственное сообщение "{message}" на сервер')
                s.send(data_bytes)
                log.debug('и жду ответа')
                server_response = pickle.loads(s.recv(1024))
                log.debug(f'Ответ: {server_response}')
                # Если сервер ответил нестандартным кодом, то завершаем работу
                if server_response.get(RESPONSE) not in StandartServerCodes:
                    log.error(f'Неизвестный код ответа от сервера: {server_response.get(RESPONSE)}')
                    raise UnknownCode(server_response.get(RESPONSE))
                # Если все хорошо, то переключаем режим клиента в переданный в параметре
                # или оставляем по-умолчанию - полный
                if server_response.get('response') == OK:
                    print('Соединение установлено!')
                    log.info('Авторизация успешна. Соединение установлено!')
                    if self.mode == 'r':
                        print('Клиент в режиме чтения')
                        log.debug('Клиент в режиме чтения')
                        self.client_reader(s, self.account)
                    elif self.mode == 'w':
                        print('Клиент в режиме записи')
                        log.debug('Клиент в режиме записи')
                        self.client_writer(s, self.account)
                    elif self.mode == 'f':
                        log.debug('Клиент в полнофункциональном режиме')
                        print(f'Отправка сообщений всем пользователям в канал {MAIN_CHANNEL}')
                        print('Для получения помощи наберите help')
                        # читаем сообщения в отдельном потоке
                        read_thread = threading.Thread(target=self.client_reader, args=(s, self.account))
                        read_thread.daemon = True
                        read_thread.start()
                        # read_thread.join()
                        write_thread = threading.Thread(target=self.client_writer, args=(s, self.account))
                        write_thread.daemon = True
                        write_thread.start()
                        # self.client_writer(s, self.account)
                        while self.alive:
                            time.sleep(1)
                            continue
                    else:
                        s.close()
                        raise Exception('Не верный режим клиента')
                else:
                    # print('Что-то пошло не так..')
                    log.error('Что-то пошло не так..')
        s.close()
        exit(0)


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
    mode_current = args.mode

    # Показывать лог в консоль при запуске напрямую
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(client_config_log.log_format)
    log.addHandler(stream_handler)

    # запуск основного кода клиента
    c = Client(acc='Simper', mode=mode_current)
    c.start_client()
    # sys.exit(0)
