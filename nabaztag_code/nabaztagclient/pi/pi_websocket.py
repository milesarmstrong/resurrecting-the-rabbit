import json
import threading
import logging
import RPi.GPIO as GPIO
import time
from ws4py.client.threadedclient import WebSocketClient


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

    def __init__(self, url, name):

        """Create an instance of a WSClient

        :param url: The url of the websocket server, e.g. ws://echo.websocket.org
        :param name: The name of the thread for identification in the logs.
        """

        super(WSClient, self).__init__(url)
        self.name = name

    def received_message(self, message):

        """Called each time a message is received on the websocket connection.

        The message is logged, then a LEDBlinkThread is created to illuminate the relevant LEDs.
        """

        try:
            message = json.loads(message.data)
            logging.info(threading.current_thread().name + " - " + json.dumps(message))
            LEDS = [4, 17, 22, 10, 9, 11]

            if 'ear' in message:
                if message['ear'] == "L":
                    blinker = LEDThread(LEDS[0:3], 5, "leftledblinker")
                    blinker.start()
                elif message['ear'] == "R":
                    blinker = LEDThread(LEDS[3:6], 5, "rightledblinker")
                    blinker.start()
        except ValueError as e:
            logging.error(
                "{threadname} - Error: {error}".format(
                    threadname=threading.current_thread().name,
                    error=e.message
                )
            )

    def closed(self, code, reason=None):

        """Called when the websocket connection is closed.

        The reason for the socket closing, and the code (https://tools.ietf.org/html/rfc6455#section-7.4)
        is logged.
        """

        logging.info(
            "{threadname} - Connection closed".format(
                threadname=threading.current_thread().name
            )
        )

    def opened(self):

        """Called once when the websocket connection is first opened.

        Creates and starts an instance of InitThread to initialise the Nabaztag,
        and logs the websocket connection details.
        """

        init = InitThread()
        init.start()
        logging.info(
            "{threadname} - Connection opened: {server}".format(
                threadname=threading.current_thread().name,
                server=self.sock.getpeername()
            )
        )


class LEDThread(threading.Thread):

    """A class to allow illumation of a set of LEDs for a period of time without blocking the websocket thread.
    """

    def __init__(self, leds, lit_time, name):

        """Create an instance of LEDThread

        :params leds: The IO pins to which the desired LEDs are attached.
        :params lit_time: The time to remain illuminated for.
        :params name: The name of the thread for identification in logs.
        """

        threading.Thread.__init__(self, name=name)
        self.leds = leds
        self.lit_time = lit_time

    def run(self):

        """Start the LEDThread thread.

        Turns the specified LEDs on, waits for the specified time, then turns them off.
        """

        for led in self.leds:
            GPIO.output(led, True)

        time.sleep(self.lit_time)

        for led in self.leds:
            GPIO.output(led, False)


class InitThread(threading.Thread):

    """A class defining the behaviour of the Nabaztag when the websocket connection is first established.

    Instances of InitThread are short lived, and only use threading so that the websocket client is able
    to receive commands immediately, rather than waiting for the initialisation process to complete.
    """

    def __init__(self):

        """Create an instance of InitThread
        """

        threading.Thread.__init__(self)

    def run(self):

        """Starts the InitThread.

        All LEDs are illuminated for 5 seconds.
        """

        LEDS = [4, 17, 22, 10, 9, 11]
        all_leds = LEDThread(LEDS, 5, "all_leds")
        all_leds.start()