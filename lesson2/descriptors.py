# дескриптор для класса серверного сокета
class SockVerify:
    def __get__(self, instance, owner):
        return instance.__dict__[self.my_attr]

    def __set__(self, instance, value):
        if self.my_attr == 'port':
            if not isinstance(value, int) or value <= 0:
                raise ValueError("Порт должен быть положительным числом")
                log.error('Полученный порт не является положительным числом!')
        if self.my_attr == 'address':
            if not isinstance(value, str):
                raise ValueError("Адрес сервера должен быть строкой")
                log.error('Полученный адрес сервера не является строкой!')

        instance.__dict__[self.my_attr] = value

    def __set_name__(self, owner, my_attr):
        self.my_attr = my_attr

