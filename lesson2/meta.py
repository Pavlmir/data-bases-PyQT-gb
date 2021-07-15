import dis
import inspect


class ServerVerifier(type):
    def __init__(cls, class_name, bases, class_dict):
        methods = []
        method_attributes = []
        class_attributes = []

        for key, value in class_dict.items():
            if inspect.isfunction(value):
                instr = dis.get_instructions(value)
                for i in instr:
                    if i.opname == 'LOAD_GLOBAL' or i.opname == 'LOAD_METHOD':
                        if i.argval not in methods:
                            methods.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in method_attributes:
                            method_attributes.append(i.argval)
            elif key != '__module__' and key != '__qualname__':
                class_attributes.append(key)
        if 'connect' in methods:
            raise Exception('Серверное приложение не должно использовать вызов connect!')

        super().__init__(class_name, bases, class_dict)


class ClientVerifier(type):
    def __init__(cls, class_name, bases, class_dict):
        methods = []
        method_attributes = []
        class_attributes = []

        for key, value in class_dict.items():
            if inspect.isfunction(value):
                instr = dis.get_instructions(value)
                for i in instr:
                    if i.opname == 'LOAD_GLOBAL' or i.opname == 'LOAD_METHOD':
                        if i.argval not in methods:
                            methods.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in method_attributes:
                            method_attributes.append(i.argval)
            elif key != '__module__' and key != '__qualname__':
                class_attributes.append(key)

        if 'accept' in methods or 'listen' in methods or 'socket' in methods:
            raise Exception('Клиентское приложение не должно использовать вызов accept или listen!')

        super().__init__(class_name, bases, class_dict)
