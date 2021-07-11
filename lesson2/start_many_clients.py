from subprocess import Popen, CREATE_NEW_CONSOLE
import time

process_list = []
user_lists = ['User1', 'User2', 'User3', 'User4', 'User5', 'User6', 'User7', 'User8']
while True:
    user_command = input("Запустить несколько клиентов (s) / Закрыть всех клиентов (x) / Выйти (q) ")

    if user_command == 'q':
        break
    elif user_command == 's':
        process_list.append(Popen(f'python server.py',
                                  creationflags=CREATE_NEW_CONSOLE))
        time.sleep(2)
        for user in user_lists:
            process_list.append(Popen(f'python -i client.py -a localhost -p 7777 -u {user}',
                                      creationflags=CREATE_NEW_CONSOLE))
            # process_list[-1].communicate('pause')

        print(' Запущено 8 клиентов и сервер')
    elif user_command == 'x':
        for p in process_list:
            p.kill()
        process_list.clear()
