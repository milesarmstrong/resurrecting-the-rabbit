import json
import logging
import subprocess
import time
import requests

from ws4py.client.threadedclient import WebSocketClient


# String templates for serial commands
EAR_SERIAL_STRING = "EARMOV {ear} {pos:d}\r\n"
LED_SERIAL_STRING = "LED {led} {red:d} {green:d} {blue:d}\r\n"

# Location API
LOCATION_API = "http://localhost/nabaztag/api/location"


class WSClient(WebSocketClient):

    """A class providing the Websocket client functionality for the NabaztagClient application.

    Usage::
    wsclient = WSClient(url, serial_queue, update_queue, name)
    wsclient.connect()
    wsclient.run_forever()

    The class defines behaviours when:
    1. A connection to a websocket server is opened.
    2. A message is received on the connection.
    3. The connection is closed.
    """

    def __init__(self, url, serial_queue, update_queue, name):

        """Create an instance of a WSClient

        :param url: The url of the websocket server, e.g. ws://echo.websocket.org
        :param serial_queue: An instance of Queue.Queue(), messages for the AVR are placed in this queue.
        :param update_queue: An instance of Queue.Queue(), messages to be sent to the server are placed in this queue.
        :param name: The name of the thread for identification in the logs.
        """

        super(WSClient, self).__init__(url)
        self.serial_queue = serial_queue
        self.update_queue = update_queue
        self.name = name

    def opened(self):

        """Called once when the websocket connection is first opened.

        Creates and starts an instance of InitThread to initialise the Nabaztag,
        and logs the websocket connection details.
        """

        logging.info(
            "{threadname} - Connection opened: {url}".format(
                threadname=self.name,
                url=self.url
            )
        )

        self.initialise()
        self.update_server_location()

    def received_message(self, message):

        """Called each time a message is received on the websocket connection.

        The message is logged, then, if it is intended for the ears or leds it is converted
        to a serial command and sent to the AVR via the SerialWriter thread, or if it is a
        text-to-speech command, the festival text-to-speech service is called as a subprocess
        """

        message = message.data
        logging.info(
            "{threadname} - Message received: {message}".format(
                threadname=self.name,
                message=message
            )
        )

        try:
            message = json.loads(message)
            if 'speak' in message:
                subprocess.Popen('echo '+message['text']+'|festival --tts', shell=True)
            else:
                self.serial_queue.put(self.json_to_serial(message))
        # If the message received can't be parsed to JSON, log it.
        except ValueError as e:
            logging.error(
                "{threadname} - Error: {error}".format(
                    threadname=self.name,
                    error=e.message
                )
            )

    def closed(self, code, reason=None):

        """Called when the websocket connection is closed.

        The reason for the socket closing, and the code (https://tools.ietf.org/html/rfc6455#section-7.4)
        is logged.
        """

        logging.info(
            "{threadname} - Connection closed with code: {code}".format(
                threadname=self.name,
                code=code
            )
        )

    def initialise(self):
        """Defines the behaviour of the Nabaztag when the websocket connection is first established.

        The initialisation procedure is:
        1. Reset the ears to their zero position.
        2. Set both LEDs to green while the ears are resetting.
        """

        # Zero Ears
        self.serial_queue.put(EAR_SERIAL_STRING.format(ear='L', pos=0))
        self.serial_queue.put(EAR_SERIAL_STRING.format(ear='R', pos=0))

        # Green lights for duration of ear movements
        self.serial_queue.put(LED_SERIAL_STRING.format(led='T', red=0, green=255, blue=0))
        self.serial_queue.put(LED_SERIAL_STRING.format(led='B', red=0, green=255, blue=0))
        time.sleep(5.2)
        self.serial_queue.put(LED_SERIAL_STRING.format(led='T', red=0, green=0, blue=0))
        self.serial_queue.put(LED_SERIAL_STRING.format(led='B', red=0, green=0, blue=0))

    def update_server_location(self):

        """Update the Nabaztag's physical location on the server.
        """

        # Send location to the server
        location = requests.get(LOCATION_API).json()

        # If the location API is unavailable, tell the server the location is unavailable
        if 'status' in location and location['status'] == 503:
            location = {"unavailable": 1}

        location.update({"location": 1})
        self.update_queue.put(location)

    @staticmethod
    def json_to_serial(json_message):

        """Helper function to convert the JSON commands to Serial commands.

        :param json_message: A valid JSON object.

        Raises an InvalidSerialCommandError if the JSON object is not a valid command format.
        """

        if 'ear' in json_message:
            serial_message = EAR_SERIAL_STRING.format(
                ear=json_message['ear'],
                pos=json_message['pos']
            )
        elif 'led' in json_message:
            serial_message = LED_SERIAL_STRING.format(
                led=json_message['led'],
                red=json_message['red'],
                green=json_message['green'],
                blue=json_message['blue']
            )
        else:
            raise InvalidSerialCommandError("Invalid JSON command, can't convert to serial command")

        return serial_message


class InvalidSerialCommandError(Exception):

    """Convenience wrapper to give a nice exception name.
    """

    pass