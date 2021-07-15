import unittest
from multiprocessing import Process

from client import create_presence_message, start_client
from config import UnknownCode
from server import start_server


class TestCreateMessage(unittest.TestCase):

    def testAccountNameLen(self):
        with self.assertRaises(ValueError):
            create_presence_message('Petrov1234567890123456789123')

    def testAccountNameType(self):
        with self.assertRaises(TypeError):
            create_presence_message(46346)

    def testDefaultUsername(self):
        self.assertEqual(create_presence_message()['user']['account_name'], "Guest")


class TestStartClient(unittest.TestCase):

    def testConnectError(self):
        with self.assertRaises(Exception):
            start_client()

    def testUnknownResponseCode(self):
        server_process = Process(target=start_server)
        server_process.start()
        with self.assertRaises(UnknownCode):
            start_client()
        server_process.terminate()


if __name__ == "__main__":
    unittest.main()
