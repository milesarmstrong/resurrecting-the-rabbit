import json
import Queue
import httpretty
import unittest
from testfixtures import LogCapture
from ws4py.framing import OPCODE_TEXT
from ws4py.messaging import Message
from mock import MagicMock, patch

from beaglebone.nabaztag_update import UpdateThread
from beaglebone.nabaztag_websocket import WSClient, InvalidSerialCommandError


class TestJSONtoSerial(unittest.TestCase):
    def test_ear_message(self):
        ear_json = json.loads('{"ear": "L", "pos": 10}')
        ear_serial = "EARMOV L 10\r\n"
        serial = WSClient.json_to_serial(ear_json)
        self.assertEquals(serial, ear_serial)

    def test_led_message(self):
        led_json = json.loads('{"led": "T", "red": 75, "green": 150, "blue": 225}')
        led_serial = "LED T 75 150 225\r\n"
        serial = WSClient.json_to_serial(led_json)
        self.assertEquals(serial, led_serial)

    def test_invalid_message(self):
        invalid_json = json.loads('{"invalid": 1}')
        self.assertRaises(InvalidSerialCommandError, WSClient.json_to_serial, invalid_json)


class TestUpdateServerLocation(unittest.TestCase):
    def setUp(self):
        self.serial_queue = Queue.Queue()
        self.update_queue = Queue.Queue()
        self.websocket = WSClient("ws://echo.websocket.org", self.serial_queue, self.update_queue, "websockettest")
        self.websocket.connect()
        httpretty.enable()

    def tearDown(self):
        self.websocket.close()
        httpretty.disable()
        httpretty.reset()

    def test_api_available(self):
        response = {"lat": 50.936850899999996, "lon": -1.3972685}

        httpretty.register_uri(
            httpretty.GET,
            "http://localhost/nabaztag/api/location",
            body=json.dumps(response),
            content_type="application/json"
        )

        self.websocket.update_server_location()
        update = self.update_queue.get()

        response.update({"location": 1})
        self.assertEquals(update, response)

    def test_api_unavailable(self):
        response = {"status": 503, "message": "Location service temporarily unavailable"}

        httpretty.register_uri(
            httpretty.GET,
            "http://localhost/nabaztag/api/location",
            body=json.dumps(response),
            content_type="application/json"
        )

        self.websocket.update_server_location()
        update = self.update_queue.get()

        self.assertEquals(update, {"location": 1, "unavailable": 1})


class TestWebsocketCallbacks(unittest.TestCase):
    def setUp(self):
        self.serial_queue = Queue.Queue()
        self.update_queue = Queue.Queue()
        self.websocket = WSClient("ws://echo.websocket.org", self.serial_queue, self.update_queue, "websockettest")
        self.websocket.connect()

    def tearDown(self):
        self.websocket.close()

    def test_opened(self):
        WSClient.initialise = MagicMock('mock_init')
        WSClient.update_server_location = MagicMock('mock_location')
        with LogCapture() as l:
            self.websocket.opened()
            l.check(('root', 'INFO', "websockettest - Connection opened: ws://echo.websocket.org"),)
            self.assertTrue(WSClient.initialise.called)
            self.assertTrue(WSClient.update_server_location.called)

    def test_received_valid_serial_message(self):
        ear_serial = "EARMOV L 10\r\n"
        WSClient.json_to_serial = MagicMock('mock_json_to_serial', return_value=ear_serial)
        ear_message = Message(OPCODE_TEXT, data=json.dumps({"ear": "L", "pos": 10}))
        with LogCapture() as l:
            self.websocket.received_message(ear_message)
            l.check(('root', 'INFO', 'websockettest - Message received: {"ear": "L", "pos": 10}'),)
            self.assertTrue(WSClient.json_to_serial.called)
            self.assertEquals(self.serial_queue.get(), ear_serial)

    @patch('subprocess.Popen')
    def test_received_valid_speech_message(self, mock_popen):
        ear_message = Message(OPCODE_TEXT, data=json.dumps({"text": "String to speak", "speak": 1}))
        with LogCapture() as l:
            self.websocket.received_message(ear_message)
            l.check(('root', 'INFO', 'websockettest - Message received: {"text": "String to speak", "speak": 1}'),)
            self.assertTrue(mock_popen.called)

    def test_received_invalid_message(self):
        ear_serial = "EARMOV L 10\r\n"
        WSClient.json_to_serial = MagicMock('mock_json_to_serial', return_value=ear_serial)
        ear_message = Message(OPCODE_TEXT, data='{"ear": "L" "pos": 10}')
        with LogCapture() as l:
            self.websocket.received_message(ear_message)
            l.check(('root', 'INFO', 'websockettest - Message received: {"ear": "L" "pos": 10}'),
                    ('root', 'ERROR', 'websockettest - Error: Expecting , delimiter: line 1 column 13 (char 12)'))

    def test_closed(self):
        with LogCapture() as l:
            self.websocket.closed(1006)
            l.check(('root', 'INFO', 'websockettest - Connection closed with code: 1006'))

class TestGenerateUpdateURL(unittest.TestCase):
    def setUp(self):
        self.baseurl = "http://localhost:80/update/00:0f:54:18:10:35/"

    def test_ear_update(self):
        update = {"ear": "L", "moved": 1}
        url = UpdateThread.generate_url(update, self.baseurl)
        self.assertEquals(url, self.baseurl + 'ear')

    def test_button_update(self):
        update = {"button": 1}
        url = UpdateThread.generate_url(update, self.baseurl)
        self.assertEquals(url, self.baseurl + 'button')

    def test_location_update(self):
        update = {"lat": 50.9367229, "lon": -1.3972372, "location": 1}
        url = UpdateThread.generate_url(update, self.baseurl)
        self.assertEquals(url, self.baseurl + 'location')

    def test_invalid_update(self):
        update = {"invalid": 1}
        url = UpdateThread.generate_url(update, self.baseurl)
        self.assertIsNone(url)


class TestLogResponse(unittest.TestCase):
    def setUp(self):
        self.url = "http://localhost:80/update/00:0f:54:18:10:35/"
        self.update = UpdateThread(
            self.url,
            Queue.Queue(),
            "updatetest"
        )

    def test_logging(self):
        url = self.url + 'ear'
        update = json.loads('{"ear": "L", "moved": 1}')
        response = json.loads('{"status": 200, "message": "OK"}')
        with LogCapture() as l:
            self.update.log_update_reponse(update, response, url)
            l.check(('root', 'INFO', 'updatetest - POSTed ' + json.dumps(update) + ' to ' + url),
                    ('root', 'INFO', 'updatetest - Response: ' + json.dumps(response)))

if __name__ == '__main__':
    unittest.main()