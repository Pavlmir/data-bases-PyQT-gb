import unittest

from server import check_correct_presence_and_response, start_server


class TestCheckMessages(unittest.TestCase):

    def testTimeIsFloat(self):
        self.assertEqual(check_correct_presence_and_response(
            {'action': 'presence',
             'time': 2353453,
             'user': {'account_name': 'SuperUser'}}),
            {'response': 400,
             'error': 'Не верный запрос'}
        )

    def testCorrectMessage(self):
        self.assertEqual(check_correct_presence_and_response(
            {'action': 'presence',
             'time': 325345.675,
             'user': {'account_name': 'SuperUser'}}),
            {'response': 200})

    def testHaveAction(self):
        self.assertEqual(
            check_correct_presence_and_response(
                {'time': 12423.4564,
                 'user': {'account_name': 'SuperUser'}}),
            {'response': 400,
             'error': 'Не верный запрос'})

    def testAccountIsPresence(self):
        self.assertEqual(check_correct_presence_and_response(
            {'action': 'goodbye',
             'time': 2114.456456,
             'user': {'account_name': 'SuperUser'}}),
            {'response': 400,
             'error': 'Не верный запрос'})


class TestStartServer(unittest.TestCase):

    def testUnknownServerReq(self):
        with self.assertRaises(ValueError):
            start_server()


if __name__ == "__main__":
    unittest.main()
