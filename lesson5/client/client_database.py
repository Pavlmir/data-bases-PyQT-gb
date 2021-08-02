from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from lesson5.config import CLIENT_DATABASE

Base = declarative_base()


class ClientStorage:
    class MessageHistory(Base):
        __tablename__ = 'message_history'
        id = Column(Integer, primary_key=True)
        from_user = Column(String, nullable=False)
        to_user = Column(String)
        message = Column(String)
        date = Column(DateTime)

        def __init__(self, from_user, to_user, message, date):
            self.from_user = from_user
            self.to_user = to_user
            self.message = message
            self.date = date

        def __repr__(self):
            return f'<MessageHistory(' \
                   f'{self.id}, ' \
                   f'{self.from_user}, ' \
                   f'{self.to_user}, ' \
                   f'{self.message}, ' \
                   f'{self.date})>'

    class ContactList(Base):
        __tablename__ = 'contact_list'
        id = Column(Integer, primary_key=True)
        contact_owner = Column(String)  # name of user who has this contact
        contact = Column(String)
        group = Column(String, default='General')

        def __init__(self, contact_owner, contact, group='General'):
            self.contact_owner = contact_owner
            self.contact = contact
            self.group = group

        def __repr__(self):
            return f'<ContactList({self.id}, ' \
                   f'{self.contact_owner}, ' \
                   f'{self.contact}, ' \
                   f'{self.group})>'

    def __init__(self):
        # Чтобы это не случилось нужно добавить опцию pool_recycle = 7200 (переустановка через 2 часа)
        self.engine = create_engine(CLIENT_DATABASE,
                                    echo=False,
                                    pool_recycle=7200,
                                    connect_args={'check_same_thread': False})

        # Создаём сессию
        session = sessionmaker(bind=self.engine)
        self.session = session()

        # Создаём таблицы
        Base.metadata.create_all(self.engine)

    def get_all_users(self):
        # Возвращаем список имен всех пользователей
        return [user[0] for user in self.session.query(self.ContactList.contact).all()]

    # Функция добавления контактов
    def add_contact(self, contact_owner, contact):
        if not self.session.query(self.ContactList).filter_by(contact_owner=contact_owner, contact=contact).count():
            contact_row = self.ContactList(contact_owner, contact)
            self.session.add(contact_row)
            self.session.commit()

    def remove_contact(self, contact_owner, contact):
        # Если контакт существует, удаляем его
        if self.session.query(self.ContactList).filter_by(contact=contact).first():
            self.session.query(self.ContactList).filter_by(contact_owner=contact_owner, contact=contact).delete()
            self.session.commit()

    def find_contacts(self, contact_owner, query):
        return self.session.query(self.ContactList.contact).filter_by(contact_owner=contact_owner).filter(
            self.ContactList.contact.ilike(f"%{query}%")).all()

    # Функция возвращающая контакты
    def get_contacts(self, contact_owner):
        return [contact[0] for contact in
                self.session.query(self.ContactList.contact).filter_by(contact_owner=contact_owner).all()]

    # Функция сохраняющая сообщения
    def save_message(self, from_user, to_user, message):
        message_row = self.MessageHistory(from_user, to_user, message, datetime.now())
        self.session.add(message_row)
        self.session.commit()

    # Функция возвращающая историю переписки
    def get_messages_history(self, from_user=None, to_user=None):
        query = self.session.query(self.MessageHistory)
        if from_user:
            query = query.filter_by(from_user=from_user)
        if to_user:
            query = query.filter_by(to_user=to_user)
        return [
            (history_row.from_user, history_row.to_user, history_row.type, history_row.message, history_row.date,
             history_row.style)
            for history_row in query.all()]


if __name__ == "__main__":
    server_db = ClientStorage()
