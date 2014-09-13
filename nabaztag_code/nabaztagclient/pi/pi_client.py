import Queue
import yaml
import logging
import RPi.GPIO as GPIO
import netifaces
import atexit

from pi_update import UpdateThread
from pi_websocket import WSClient
from pi_button import ButtonThread

# Load settings from configuration file
config_file = open('/etc/nabaztag/nabaztagconfig.yaml', 'r')
config = yaml.load(config_file)

HOST = config['server']['hostname']
PORT = config['server']['port']
INTERFACE = config['interface']

WS_URL = config['urls']['wsurl']
POST_URL = config['urls']['posturl']

LOGFILE = config['logs']['client']

# Set up logging
logging.basicConfig(
    filename=LOGFILE,
    format='%(levelname)s: %(asctime)s %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p -',
    level=logging.INFO,
    filemode='w'
)


def getid(interface):

    """Get the MAC address of the specified network interface.

    :param interface: The interface name from ifconfig, e.g. 'wlan0'
    """

    return netifaces.ifaddresses(interface)[netifaces.AF_LINK][0]['addr']


def main():

    """Entry point to pi_client application.

    Initialises the Serial port, starts all application threads, and initiates the websocket connection
    """

    # Refer to GPIO by Broadcom SOC Channel Number
    GPIO.setmode(GPIO.BCM)

    # Setup LED outputs
    LEDS = [4, 17, 22, 10, 9, 11]
    for x in range(6):
        GPIO.setup(LEDS[x], GPIO.OUT)
        GPIO.output(LEDS[x], False)

    # Setup Button input
    GPIO.setup(7, GPIO.IN)
    post_queue = Queue.Queue()

    update_thread = UpdateThread(
        POST_URL.format(
            host=HOST,
            port=PORT,
            identifier=getid(INTERFACE)
        ),
        post_queue,
        name="postupdate"
    )
                                 
    button_thread = ButtonThread(
        post_queue,
        name="button"
    )

    update_thread.start()
    button_thread.start()

    websocket_thread = WSClient(
        WS_URL.format(
            host=HOST,
            port=PORT,
            identifier=getid(INTERFACE)
        ),
        name="websocket"
    )

    websocket_thread.connect()
    websocket_thread.run_forever()


def cleanup():

    """Called on exit, cleans up GPIO settings to avoid errors.
    """

    GPIO.cleanup()

if __name__ == "__main__":
    main()
    atexit.register(cleanup)
