import threading
import json
import RPi.GPIO as GPIO
import time

PRESSED = 1
BUTTON_PIN = 7


class ButtonThread(threading.Thread):

    """A class to monitor the status of the button on the pi.

    Enables access to button status without blocking update thread.
    """

    def __init__(self, update_queue, name):

        """Create an instance of the ButtonThread class.

        :params update_queue: An instance of Queue.Queue() to place button press updates onto.
        :params name: The name of the thread for identification in the logs.
        """

        threading.Thread.__init__(self, name=name)
        self.update_queue = update_queue
        
    def run(self):

        """Start the ButtonThread thread.

        Polls the button input pin for high state, waits half a second after detecting a button press to debounce.
        """

        while True:
            if GPIO.input(BUTTON_PIN) == PRESSED:
                press = json.loads('{"button": 1}')
                self.update_queue.put(press)
                time.sleep(0.5)