import threading
import logging
import json
import serial as pyserial


class SerialWriter(threading.Thread):

    """A class providing write access to the serial connection, Beaglebone -> AVR

        Instances of the class should be run as threads using start(), and will
        pass any input given to them by other threads through the
        serial_queue queue to the serial port.
    """

    def __init__(self, port, serial_queue, name):

        """Create an instance of a SerialWriter thread.

            :param port: The serial port to write to, e.g. /dev/ttyO1
            :param serial_queue: An instance of Queue.Queue() for the SerialWriter thread to receive messages from.
            :param name: The name for the SerialWriter thread to identify it in the log.
        """

        threading.Thread.__init__(self, name=name)
        self.port = port
        self.serial_queue = serial_queue

    def run(self):

        """Start the SerialWriter thread.

            Whilst running, the thread does a blocking get from the serial_queue queue,
            passing any messages to the serial port, and logging the message.
        """

        while True:

            try:
                message = self.serial_queue.get()
                logging.info(
                    "{threadname} - Message written: {message}".format(
                        threadname=self.name,
                        # Remove the newline characters from the message or we get lots of blank lines in the logs.
                        message=message.rstrip('\r\n')
                    )
                )
                self.port.write(message)
            except pyserial.SerialException as e:
                log_serial_error(self, "Write to serial port failed.", e)


class SerialReader(threading.Thread):

    """A class proving read access to the serial connection, Beaglebone <- AVR

       Instances of the class should be run as a thread using start(), and will
       poll the given serial port for messages to be read, placing them onto
       the update_queue queue for access from other threads.
    """

    def __init__(self, port, update_queue, name):

        """Creates and instance of a SerialReader thread.

        :param port: The serial port to write to, e.g. /dev/ttyO1
        :param update_queue: An instance of Queue.Queue() for the SerialReader thread to place messages on.
        :param name: The name for the SerialReader thread to identify it in the log.
        """

        threading.Thread.__init__(self, name=name)
        self.port = port
        self.update_queue = update_queue

    def run(self):

        """Start the SerialReader thread.

        Whilst running, the thread does a blocking readline from the serial port.
        When a message is received it is parsed to JSON to confirm it is a valid message,
        then places on the update_queue queue for access by other threads.
        """

        while True:
            try:
                # Serial messages are delimited by newlines, strip the newline so we don't get blank lines in the log.
                read = self.port.readline().rstrip('\n')
                read = json.loads(read)
                logging.info(
                    "{threadname} - Message read: {message}".format(
                        threadname=self.name,
                        message=json.dumps(read)
                    )
                )
                self.update_queue.put(read)

            # If the read from the serial port fails, catch it and log it.
            except pyserial.SerialException as e:
                log_serial_error(self, "Read from serial port failed.", e)

            # If the serial message is not valid JSON, catch the error and log it, without
            # passing the message onto the queue.
            except ValueError as e:
                log_serial_error(self, "Message recieved was not valid JSON.", e)


def log_serial_error(self, message, error):

    """Logs a serial error to the application-wide log.

    :param error: The Exception instance to log.
    """

    logging.exception(
        "{threadname} - Serial exception: {message}. Detail: {error}".format(
            threadname=self.name,
            message=message,
            error=error
        )
    )