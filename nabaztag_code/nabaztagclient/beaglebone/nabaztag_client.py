import Queue
import logging
import yaml
import netifaces
import serial as pyserial
import Adafruit_BBIO.UART as UART

from nabaztag_serial import SerialWriter, SerialReader
from nabaztag_update import UpdateThread
from nabaztag_websocket import WSClient


# Load settings from configuration file
config_file = open('/etc/nabaztag/nabaztagconfig.yaml', 'r')
config = yaml.load(config_file)

HOST = config['server']['hostname']
PORT = config['server']['port']
INTERFACE = config['interface']
SERIAL = config['serial']['port']
RATE = config['serial']['rate']

WS_URL = config['urls']['wsurl']
POST_URL = config['urls']['posturl']

LOGFILE = config['logs']['client']

# Set up application-wide logging
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

    """Entry point to nabaztag_client application.

    Initialises the Serial port, starts all application threads, and initiates the websocket connection
    """

    # Serial setup
    UART.setup("UART1")
    serial = pyserial.Serial(port=SERIAL, baudrate=RATE)

    serial_queue = Queue.Queue()
    update_queue = Queue.Queue()

    serial_write_thread = SerialWriter(
        serial,
        serial_queue,
        name="serialwrite"
    )

    serial_read_thread = SerialReader(
        serial,
        update_queue,
        name="serialread"
    )

    update_thread = UpdateThread(
        POST_URL.format(
            host=HOST,
            port=PORT,
            identifier=getid(INTERFACE)
        ),
        update_queue,
        name="postupdate"
    )

    serial_write_thread.start()
    serial_read_thread.start()
    update_thread.start()

    websocket_thread = WSClient(
        WS_URL.format(
            host=HOST,
            port=PORT,
            identifier=getid(INTERFACE)
        ),
        serial_queue,
        update_queue,
        name="websocket"
    )

    websocket_thread.connect()
    websocket_thread.run_forever()


if __name__ == "__main__":
    main()