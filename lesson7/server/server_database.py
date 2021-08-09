from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Text, Boolean, or_
from sqlalchemy.orm import sessionmaker
from lesson7.config import SERVER_DATABASE, COMMON_CHAT, COMMON_CHAT_PWD
from sqlalchemy.orm import declarative_base

import datetime
import hashlib

Base = declarative_base()


class ServerStorage:
    # Отображение таблицы всех пользователей
    class AllUsers(Base):
        __tablename__ = 'all_users'
        id = Column(Integer, primary_key=True)
        username = Column(String, unique=True)
        last_login = Column(DateTime)
        password = Column(String)

        def __init__(self, username, last_login, password):
            self.username = username
            self.last_login = last_login
            self.password = password

        def __repr__(self):
            return f'<User({self.username}, {self.last_login}, {self.password})>'

    # Контакты пользователей
    class UsersContacts(Base):
        __tablename__ = 'users_contacts'
        id = Column(Integer, primary_key=True)
        username = Column(ForeignKey('all_users.id'))
        contact = Column(String)
        last_msg = Column(DateTime)

        def __init__(self, username, contact, last_msg):
            self.username = username
            self.contact = contact
            self.last_msg = last_msg

        def __repr__(self):
            return f'<User({self.username}, {self.contact}, {self.last_msg})>'

    # История входов пользователей
    class LoginHistory(Base):
        __tablename__ = 'users_login_history'
        id = Column(Integer, primary_key=True)
        username = Column(ForeignKey('all_users.id'))
        login_time = Column(DateTime)
        ip_address = Column(String)
        port = Column(Integer)

        def __init__(self, username, login_time, ip_address, port):
            self.username = username
            self.login_time = login_time
            self.ip_address = ip_address
            self.port = port

        def __repr__(self):
            return f'<User({self.username}, {self.login_time}, {self.ip_address}, {self.port})>'

    class MessagesHistory(Base):
        __tablename__ = 'messages_history'
        id = Column(Integer, primary_key=True)
        from_ = Column(String)
        to = Column(String)
        message = Column(Text)
        message_id = Column(Integer)
        date = Column(DateTime)
        accepted = Column(Boolean)

        def __init__(self, contact, direction, message, message_id, date, accepted):
            self.from_ = contact
            self.to = direction
            self.message = message
            self.message_id = message_id
            self.date = date
            self.accepted = accepted

        def __repr__(self):
            return f'<User({self.from_}, {self.to}, {self.message}, {self.message_id}, {self.date}, {self.accepted})>'

    def __init__(self):
        # Чтобы это не случилось нужно добавить опцию pool_recycle = 7200 (переустановка через 2 часа)
        self.engine = create_engine(SERVER_DATABASE,
                                    echo=False,
                                    pool_recycle=7200,
                                    connect_args={'check_same_thread': False})

        # Создаём таблицы
        Base.metadata.create_all(self.engine)

        # Создаём сессию
        session = sessionmaker(bind=self.engine)
        self.session = session()
        self.add_common_chat_when_creating_db()

    def add_common_chat_when_creating_db(self):
        if not self.session.query(self.AllUsers).filter_by(username=COMMON_CHAT).count():
            self.user_registration(COMMON_CHAT, COMMON_CHAT_PWD)
            self.session.commit()

    def user_registration(self, name, password):

        check_user = self.session.query(self.AllUsers).filter_by(username=name)
        # если логин пользователя используется, создаем ошибку
        if check_user.count():
            return print(f'Пользователь с логином "{name}" уже существует')

        # если нет, добавляем его в список пользователей
        else:
            b_pass = bytes(password, encoding='utf-8')

            salt = name.lower().encode('utf-8')
            sha_pass = hashlib.pbkdf2_hmac('sha1', b_pass, salt, 1000)
            sha_pass_str = sha_pass.hex()

            user = self.AllUsers(name, datetime.datetime.now(), sha_pass_str)
            self.session.add(user)
            self.session.commit()

            self.add_contact(name, COMMON_CHAT)
            self.session.commit()

    def user_login(self, name, ip_address, port, password):
        # --------------------- проверка наличия пользователя в списке пользователей // начало --------------------- #
        check_user = self.session.query(self.AllUsers).filter_by(username=name)
        # если пользователь уже подключался ранее, обновляем дату последнего логина
        if check_user.count():
            user = check_user.first()

            b_pass = bytes(password, encoding='utf-8')

            salt = name.lower().encode('utf-8')
            sha_pass = hashlib.pbkdf2_hmac('sha1', b_pass, salt, 1000)
            sha_pass_str = sha_pass.hex()

            if user.password == sha_pass_str:
                user.last_login = datetime.datetime.now()
            else:
                return print('Введенные логин и пароль не совпадают')

        # если нет, возвращаем ошибку
        else:
            return print(f'Пользователь с логином "{name}" не существует. Зарегистрируйтесь')

        # --------------------- проверка наличия пользователя в списке пользователей // конец --------------------- #

        # добавляем текущий заход пользователя в общий список логинов
        user_history = self.LoginHistory(user.id, datetime.datetime.now(), ip_address, port)
        self.session.add(user_history)

        # сохраняем всю информацию в базу
        self.session.commit()

    def get_all_users(self):
        # Возвращаем список имен всех пользователей
        return [user[0] for user in self.session.query(self.AllUsers.username).all()]

    def add_contact(self, user, contact):
        # Получаем ID пользователей
        user = self.session.query(self.AllUsers).filter_by(username=user).first()
        contact = self.session.query(self.AllUsers).filter_by(username=contact).first()

        # Проверяем что не дубль и что контакт может существовать (полю пользователь мы доверяем)
        if not contact \
                or self.session.query(self.UsersContacts).filter_by(username=user.id,
                                                                    contact=contact.id).count():
            return

        # Создаём объект и заносим его в базу
        new_contact = self.UsersContacts(user.id, contact.id, datetime.datetime.now())
        self.session.add(new_contact)
        self.session.commit()

    def remove_contact(self, user, contact):
        # Получаем ID пользователей
        user = self.session.query(self.AllUsers).filter_by(username=user).first()
        contact = self.session.query(self.AllUsers).filter_by(username=contact).first()

        # Если контакт существует, удаляем его
        if contact:
            self.session.query(self.UsersContacts).filter(
                self.UsersContacts.username == user.id,
                self.UsersContacts.contact == contact.id
            ).delete()
            self.session.commit()

    def get_contacts(self, username):
        q = self.session.query(self.AllUsers).filter_by(username=username)
        if q.count() != 0:
            user = q.one()
            contacts = self.session.query(self.UsersContacts, self.AllUsers.username). \
                filter_by(username=user.id).join(self.AllUsers, self.UsersContacts.contact == self.AllUsers.id)

            return [contact[1] for contact in contacts.all()]
        else:
            return f"Нет такого пользователя {username}"

    def save_message(self, from_, to, message, message_id, date, accepted=False):
        new_msg = self.MessagesHistory(from_, to, message, message_id, date, accepted)
        self.session.add(new_msg)
        self.session.commit()

    def get_messages_history(self, contact):
        msgs_history = self.session.query(self.MessagesHistory).filter(
            or_(self.MessagesHistory.from_ == contact,
                self.MessagesHistory.to == contact,
                self.MessagesHistory.from_ == COMMON_CHAT,
                self.MessagesHistory.to == COMMON_CHAT),
        )

        return [
            [history_row.from_,
             history_row.to,
             history_row.message,
             history_row.date.strftime("%Y-%m-%d-%H.%M.%S")]
            for history_row in msgs_history.all()
        ]


# Отладка
if __name__ == '__main__':
    server_db = ServerStorage()
    server_db.user_registration("User1", '123')
    server_db.user_login("User1", '192.168.1.4', 8888, '123')
    print(server_db.get_contacts('Test1'))
    print(server_db.get_all_users())
    server_db.save_message('from_', 'to', 'message', 1, datetime.datetime.now())
    print(server_db.get_messages_history('t2'))
