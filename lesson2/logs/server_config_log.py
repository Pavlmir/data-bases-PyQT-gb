import logging.handlers
import os

# Создаем экземпляр логгера
server_log = logging.getLogger('Server_log')
server_log.setLevel(logging.INFO)

# Создаем обработчик
SERVER_LOG_CONFIG_FOLDER_PATH = os.path.dirname(os.path.abspath(__file__))
SERVER_LOG_FILE_PATH = os.path.join(SERVER_LOG_CONFIG_FOLDER_PATH, 'server.log')
server_file_hand = logging.handlers.TimedRotatingFileHandler(SERVER_LOG_FILE_PATH, encoding='utf-8', when='D',
                                                             interval=1)
server_file_hand.setLevel(logging.INFO)
# Определяем формат лога
log_format = logging.Formatter("%(asctime)s - %(levelname)s - %(module)s: %(funcName)s - %(message)s ")

# Добавляем формат к обработчику
server_file_hand.setFormatter(log_format)
# Добавляем обработчик логгеру
server_log.addHandler(server_file_hand)

if __name__ == '__main__':
    server_log.info('Информационное сообщение')
    server_log.warning('Внимание!')
    server_log.debug('Отладка')
    server_log.error('Ошибка!')
