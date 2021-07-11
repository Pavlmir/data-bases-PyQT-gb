from ipaddress import ip_address
import subprocess
import random
import re
from tabulate import tabulate


# 1. Написать функцию host_ping(), в которой с помощью утилиты ping будет проверяться доступность сетевых узлов.
#       Аргументом функции является список,
#       в котором каждый сетевой узел должен быть представлен именем хоста или ip-адресом.
#       В функции необходимо перебирать ip-адреса и проверять их доступность с выводом соответствующего сообщения
#       («Узел доступен», «Узел недоступен»).
#       При этом ip-адрес сетевого узла должен создаваться с помощью функции ip_address().


def random_ipv4(foo: int) -> list:
    """Создает список случайных ip адресов.
    :param foo: число узлов
    :return: список ip
    """
    ip_list = []
    for i in range(foo):
        str_ip = ip_address(
            f'{random.randint(0, 255)}.'
            f'{random.randint(0, 255)}.'
            f'{random.randint(0, 255)}.'
            f'{random.randint(0, 255)}')
        ip_list.append(str_ip)
    return ip_list


def host_ping(bar: list):
    """Проверяет доступность ip адресов.
    -w 2 -- останавливает пинг через 2 сек, на тот случай если ip мертв
    -с 2 -- отправляем 2 пакета больше не нужно для наших целей
    :param bar: список узлов
    :return: Узел доступен/Узел недоступен
    """
    for i in bar:
        p = subprocess.Popen(f'ping {i} -w 2 -c 2', shell=True, stdout=subprocess.PIPE)
        output, errors = p.communicate()
        if re.search('100% packet loss', output.decode('utf-8', 'ignore')):
            print(f'Узел {i} не доступен')
        else:
            print(f'Узел {i} доступен')


# 2. Написать функцию host_range_ping() для перебора ip-адресов из заданного диапазона. Меняться должен только последний
# октет каждого адреса. По результатам проверки должно выводиться соответствующее сообщение.


def host_range_ping(number: int, ip: str) -> list:
    """Функция перебора ip адресов из заданного диапазона. тк меняется только
    последний октет то идет прибавка 1 к последнему октету в ip адресе.
    :param number: целое число - количество ip адресов
    :param ip:  начальный ip адресов
    :return: список ip адресов
    """
    try:
        bar = []
        foo = ip_address(ip)
        for i in range(number):
            bar.append(foo + i)
        return bar
    except TypeError:
        print('Введите целое число')


# 3. Написать функцию host_range_ping_tab(), возможности которой основаны на функции из примера 2. Но в данном случае
# результат должен быть итоговым по всем ip-адресам, представленным в табличном формате (использовать модуль tabulate).


def host_range_ping_tab(bar: list):
    """Функция распределяет переданные аргументом список ip адресов на те
    которые работают и нет.
    :param bar: Список ip адресов
    :return: Две колонки с работающими и не работающими ip адресами
    """
    reach, un_reach = [], []
    try:
        for i in bar:
            p = subprocess.Popen(f'ping {i} -w 2 -c 2',
                                 shell=True, stdout=subprocess.PIPE)
            output, errors = p.communicate()
            if re.search('100% packet loss', output.decode('utf-8', 'ignore')):
                un_reach.append(i)
                print(f'Узел {i} не доступен')
            else:
                reach.append(i)
                print(f'Узел {i} доступен')
        ip = {'Reachable': reach, 'Unreachable': un_reach}
        print(tabulate(ip, headers='keys'))
    except TypeError:
        print('Передайте аргументом список ip адресов')


if __name__ == '__main__':
    bar_current = random_ipv4(5)
    foo_current = (host_range_ping(8, '87.250.250.250'))
    print(host_ping(bar_current))
    print(host_range_ping_tab(foo_current))
