import sys
import logging

from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtSql import QSqlRelationalTableModel, QSqlTableModel, QSqlRelationalDelegate, QSqlDatabase
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5 import uic

from lesson5.logs import server_config_log
from lesson5.decorators import Log
from lesson5.config import CLIENT_DATABASE_NAME
from client_database import ClientStorage
from client import Client

log = logging.getLogger('Client_log')
logger = Log(log)


class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()
        uic.loadUi('client_window.ui', self)

        self.db = ClientStorage()

        self.current_chat = None
        self.contacts_model = None

        self.btn_get_list.clicked.connect(self.show_table)
        self.setWindowTitle('Приложение чат - клиент')
        self.connect()
        self.show_table()
        self.list_contacts.doubleClicked.connect(self.select_active_user)

    def show_table(self):
        result = self.db.get_all_users()
        self.contacts_model = QStandardItemModel()
        for i in sorted(result):
            item = QStandardItem(i)
            item.setEditable(False)
            self.contacts_model.appendRow(item)

        item = QStandardItem('Global Chat')
        item.setEditable(False)
        self.contacts_model.appendRow(item)
        self.list_contacts.setModel(self.contacts_model)

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

        # Показывать лог в консоль при запуске сервера напрямую
        server_stream_handler = logging.StreamHandler(sys.stdout)
        server_stream_handler.setLevel(logging.DEBUG)
        server_stream_handler.setFormatter(server_config_log.log_format)
        log.addHandler(server_stream_handler)

        my_client = Client(self.db)
        # my_client.start_client()

if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    app = QApplication(sys.argv)  # Новый экземпляр QApplication

    form = UI()  # Создаём объект класса
    form.show()  # Показываем окно
    sys.exit(app.exec_())  # и запускаем приложение
