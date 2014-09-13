# Flask imports
import re
from flask import Flask, jsonify
from flask.ext.restful import Api, Resource, reqparse
import flask_restful


# Serial imports for AVR communication
import Adafruit_BBIO.UART as UART
import subprocess
import serial as pyserial

# API imports
from nabaztagapi_geolocate import GeoLocate, LocationError
from nabaztagapi_weather import Weather, WeatherError

# Tornado server imports
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

# Other imports
import logging
import json
import yaml

# Templates for serial commands
EAR_SERIAL_STRING = "EARMOV {ear} {pos}\r\n"
LED_SERIAL_STRING = "LED {led} {red} {green} {blue}\r\n"

# Dicts to convert URL slugs to serial parameters
ears = {"left": "L", "right": "R"}
leds = {"top": "T", "bottom": "B"}

# Load settings from configuration file
config_file = open('/etc/nabaztag/nabaztagconfig.yaml', 'r')
config = yaml.load(config_file)

INTERFACE = config['interface']
SERIAL = config['serial']['port']
RATE = config['serial']['rate']
LOGFILE = config['logs']['api']

# Set up logging
logging.basicConfig(
    filename=LOGFILE,
    format='%(levelname)s: %(asctime)s %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p -',
    level=logging.INFO,
    filemode='w'
)


############ REST API Resource Classes ############

class NabaztagEar(Resource):

    """A class to make the Nabaztag's ears available through a RESTful API.
    """

    parser = reqparse.RequestParser()
    parser.add_argument('pos', type=int, required=True, help="Invalid or no position specified for ear")

    def put(self, ear):

        """Called when a PUT request is made to /nabaztag/api/ear/<string:ear>

        :param ear: The ear to move.
        :returns: An HTTP response.

        The value given in the body is extracted and checked that is is both an int
        (done automatically by RequestParser), and in the range 0-17. The request
        is logged, and the serial command is sent to the AVR
        """

        args = self.parser.parse_args()

        if args['pos'] < 0 or args['pos'] > 17:
            return {"status": 400, "message": "Value of pos not in range 0-17."}, 400

        serial.write(
            EAR_SERIAL_STRING.format(
                ear=ears[ear],
                pos=str(args['pos'])
            )
        )

        logging.info(
            "Parameters: {body}".format(
                body=json.dumps(args)
            )
        )

        logging.info(
            EAR_SERIAL_STRING.format(
                ear=ears[ear],
                pos=str(args['pos'])
            ).rstrip('\r\n')
        )

        return {"status": 201, "message": "Success"}, 201


class NabaztagLED(Resource):

    """A class to make the Nabaztag's LEDs available through a RESTful API.
    """

    parser = reqparse.RequestParser()
    parser.add_argument('red', type=int, required=True, help="Invalid or no value specified for red")
    parser.add_argument('green', type=int, required=True, help="Invalid or no value specified for green")
    parser.add_argument('blue', type=int, required=True, help="Invalid or no value specified for blue")

    def put(self, led):

        """Called when a PUT request is made to /nabaztag/api/led/<string:led>

        :param led: The LED to control.
        :returns: An HTTP response.

        The value for red, green and blue in the body are extracted and checked that
        are integers (done automatically by RequestParser), and in the range 0-255.
        The request is logged, and the serial command is sent to the AVR.
        """

        args = self.parser.parse_args()

        message = ""
        send_400 = False

        if args['red'] < 0 or args['red'] > 255:
            message += "Value of red not in range 0-255."
            send_400 = True

        if args['green'] < 0 or args['green'] > 255:
            message += "Value of green not in range 0-255."
            send_400 = True

        if args['blue'] < 0 or args['blue'] > 255:
            message += "Value of blue not in range 0-255."
            send_400 = True

        if send_400:
            # Return a sentence for each error (regex separates them with full stops and spaces).
            return {"status": 400, "message": re.sub(r'\.([a-zA-Z])', r'. \1', message)}, 400

        serial.write(
            LED_SERIAL_STRING.format(
                led=leds[led],
                red=args['red'],
                green=args['green'],
                blue=args['blue']
            )
        )

        logging.info(
            "Parameters: {body}".format(
                body=json.dumps(args)
            )
        )

        logging.info(
            LED_SERIAL_STRING.format(
                led=leds[led],
                red=args['red'],
                green=args['green'],
                blue=args['blue']
            ).rstrip('\r\n')
        )

        return {"status": 201, "message": "Success"}, 201


class NabaztagLocation(Resource):

    """A class to make the Nabaztag's weather information available through a RESTful API.
    """

    def get(self):

        """Called when a GET request is made to /nabaztag/api/location

        :returns: An HTTP response.

        An attempt is made to obtain the Nabaztag's physical location from an
        instance of the GeoLocate class. If successful, the location is returned
        as JSON, if not, an error is returned.
        """

        locator = GeoLocate(INTERFACE)
        try:
            location = locator.get_location()
            return location, 200
        except LocationError:
            return {"status": 503, "message": "Location service temporarily unavailable"}, 503


class NabaztagWeather(Resource):

    """A class to make the Nabaztag's weather information available through a RESTful API.
    """

    def get(self):

        """Called when a GET request is made to /nabaztag/api/weather

        :returns: An HTTP response.

        An attempt is made to obtain the weather for the Nabaztag's location from an
        instance of the Weather class. If successful, the weather is returned
        as JSON, if not (due to either the location or weather APIs being unavailable),
        an error is returned.
        """

        locator = GeoLocate(INTERFACE)
        try:
            location = locator.get_location()
            weather = Weather(location)
            return weather.get_weather(), 200
        except LocationError:
            return {"status": 503, "message": "Could not determine location. Weather service temporarily unavailable."}, 503
        except WeatherError:
            return {"status": 503, "message": "Weather service temporarily unavailable."}, 503


class NabaztagSpeech(Resource):

    """A class to make the Nabaztag's text-to-speech service available through a RESTful API.
    """

    parser = reqparse.RequestParser()
    parser.add_argument('text', type=str, required=True)

    def put(self):

        """Called when a PUT request is made to /nabaztag/api/speech

        :returns: An HTTP response.

        The body of the request is checked by RequestParser for valid text, then
        the text is passed an instance of the SpeechThread.
        """

        args = self.parser.parse_args()

        logging.info(
            "Parameters: {body}".format(
                body=json.dumps(args)
            )
        )

        subprocess.Popen('echo '+self.text+'|festival --tts', shell=True)
        return {"status": 201, "message": "Success"}, 201


if __name__ == '__main__':
    # Set up serial connection to AVR
    UART.setup("UART1")
    serial = pyserial.Serial(port=SERIAL, baudrate=RATE)

    # Set up Flask endpoints
    app = Flask('NabaztagAPIServer')
    api = Api(app)

    api.add_resource(NabaztagEar, '/nabaztag/api/ear/<string:ear>')
    api.add_resource(NabaztagLED, '/nabaztag/api/led/<string:led>')
    api.add_resource(NabaztagLocation, '/nabaztag/api/location')
    api.add_resource(NabaztagSpeech, '/nabaztag/api/speech')
    api.add_resource(NabaztagWeather, '/nabaztag/api/weather')

    # Run REST API server
    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(8000, address='127.0.0.1')
    IOLoop.instance().start()