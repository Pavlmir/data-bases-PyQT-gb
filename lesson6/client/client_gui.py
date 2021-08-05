import sys
import logging

from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.uic import loadUi

from lesson6.logs import server_config_log, client_config_log
from lesson6.decorators import Log
from lesson6.config import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, \
    OK, server_port, server_address, StandartServerCodes, UnknownCode, \
    MAIN_CHANNEL, SERVER, MSG, TO, FROM, MESSAGE, RESPONSE, account

from client_database import ClientStorage
from client import Client

log = logging.getLogger('Client_log')
logger = Log(log)


class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()
        loadUi('client_window.ui', self)

        self.db = ClientStorage()

        self.current_chat = None
        self.contacts_model = None
        self.connect()

        self.btn_get_list.clicked.connect(self.show_table)
        self.setWindowTitle('Приложение чат - клиент')

        self.show_table()
        self.list_contacts.doubleClicked.connect(self.select_active_user)

        # Кнопка отправить сообщение
        self.btn_send.clicked.connect(self.send_message)

        transport = Client()
        self.transport = transport.start_client()

    def show_table(self):
        result = self.db.get_all_users()
        self.contacts_model = QStandardItemModel()
        for i in sorted(result):
            item = QStandardItem(i)
            item.setEditable(False)
            self.contacts_model.appendRow(item)

        item = QStandardItem('Общий чат')
        item.setEditable(False)
        self.contacts_model.appendRow(item)
        self.list_contacts.setModel(self.contacts_model)

    # Функция отправки сообщения пользователю.
    def send_message(self):
        message_text = self.text_message.toPlainText()
        self.text_message.clear()
        if not message_text:
            return
        try:
            self.transport.send_message(self.current_chat, message_text)
            pass
        except OSError as err:
            print(err)
            if err.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        except (ConnectionResetError, ConnectionAbortedError):
            self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
            self.close()
        else:
            if self.current_chat == 'Общий чат':
                self.database.save_message_to_global(self.username, message_text, self.is_styled_text)
                logger.debug(f'Отправлено сообщение для {self.current_chat}: {message_text}')
                self.history_list_update()
            else:
                self.database.save_message(self.username, self.current_chat, 'out', message_text,
                                           self.is_styled_text)
                logger.debug(f'Отправлено сообщение для {self.current_chat}: {message_text}')
                self.history_list_update()

    def select_active_user(self):
        try:
            self.current_chat = self.list_contacts.currentIndex().data()
            self.set_active_user()
        except Exception as e:
            print(e)

    def set_active_user(self):
        # Ставим надпись и активируем кнопки
        self.label_new_message.setText(f'Введите сообщение для {self.current_chat}:')
        self.btn_clear.setDisabled(False)
        self.btn_send.setDisabled(False)
        self.text_message.setDisabled(False)

        # Заполняем окно историю сообщений по требуемому пользователю.
        self.history_list_update()

    def connect(self):
        # Показывать лог в консоль при запуске напрямую
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(client_config_log.log_format)
        log.addHandler(stream_handler)

if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    app = QApplication(sys.argv)  # Новый экземпляр QApplication

    form = UI()  # Создаём объект класса
    form.show()  # Показываем окно
    sys.exit(app.exec_())  # и запускаем приложение
