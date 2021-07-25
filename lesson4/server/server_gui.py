import sys
import logging

from PyQt5.QtSql import QSqlRelationalTableModel, QSqlTableModel, QSqlRelationalDelegate, QSqlDatabase
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5 import uic

from lesson4.logs import server_config_log
from lesson4.decorators import Log
from lesson4.config import SERVER_DATABASE_NAME
from server_database import ServerStorage
from server import Server

log = logging.getLogger('Server_log')
logger = Log(log)


class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()
        uic.loadUi('server_window.ui', self)

        self.db = QSqlDatabase()
        self.db = self.db.addDatabase('QSQLITE')
        self.db.setDatabaseName(SERVER_DATABASE_NAME)
        if not self.db.open():
            print(self.db.lastError().text())

        self.table_model = None

        self.pushButton.clicked.connect(self.show_table)
        self.pushButtonConnect.clicked.connect(self.connect)

        self.setWindowTitle('Приложение чат - администратор сервера')

    def show_table(self):
        self.table_model = QSqlRelationalTableModel()
        self.table_model.setTable('all_users')
        self.table_model.select()
        self.table_model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        view = self.tableViewUser
        view.setModel(self.table_model)
        view.setItemDelegate(QSqlRelationalDelegate(view))

    def connect(self):
        database = ServerStorage()

        # Показывать лог в консоль при запуске сервера напрямую
        server_stream_handler = logging.StreamHandler(sys.stdout)
        server_stream_handler.setLevel(logging.DEBUG)
        server_stream_handler.setFormatter(server_config_log.log_format)
        log.addHandler(server_stream_handler)

        my_server = Server(database)
        my_server.start_server()


if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    app = QApplication(sys.argv)  # Новый экземпляр QApplication

    form = UI()  # Создаём объект класса
    form.show()  # Показываем окно
    sys.exit(app.exec_())  # и запускаем приложение
