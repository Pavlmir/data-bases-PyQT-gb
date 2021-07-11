import dis
import re


class ServerVerifier(type):

    def __init__(cls, class_name, bases, class_dict):
        methods = []
        method_attributes = []
        class_attributes = []

        for key, value in class_dict.items():
            # print(key, value)
            if re.search("<function", str(value)):
                # print('func',value)
                instr = dis.get_instructions(value)
                # dis.dis(value)
                for i in instr:
                    # print(i)
                    if i.opname == 'LOAD_GLOBAL' or i.opname == 'LOAD_METHOD':
                        if i.argval not in methods:
                            methods.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in method_attributes:
                            method_attributes.append(i.argval)
            elif key != '__module__' and key != '__qualname__':
                # print('class method',key)
                class_attributes.append(key)
        if 'connect' in methods:
            raise Exception('Серверное приложение не должно использовать вызов connect!')

        # print(methods)
        # print(method_attributes)
        # print(class_attributes)
        super().__init__(class_name, bases, class_dict)


class ClientVerifier(type):
    def __init__(cls, class_name, bases, class_dict):
        methods = []
        method_attributes = []
        class_attributes = []

        for key, value in class_dict.items():
            # print(key, value)
            if re.search("<function", str(value)):
                # print('func',value)
                instr = dis.get_instructions(value)
                # dis.dis(value)
                for i in instr:
                    # print(i)
                    if i.opname == 'LOAD_GLOBAL' or i.opname == 'LOAD_METHOD':
                        if i.argval not in methods:
                            methods.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in method_attributes:
                            method_attributes.append(i.argval)
            elif key != '__module__' and key != '__qualname__':
                # print('class method',key)
                class_attributes.append(key)

        if 'accept' in methods or 'listen' in methods or 'socket' in methods:
            raise Exception('Клиентское приложение не должно использовать вызов accept или listen!')

        # print(methods)
        # print(method_attributes)
        # print(class_attributes)

        super().__init__(class_name, bases, class_dict)
