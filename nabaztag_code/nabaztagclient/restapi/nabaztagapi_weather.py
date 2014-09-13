import requests

JSON_REQUEST_HEADERS = {'Content-type': 'application/json', 'Accept': 'text/plain'}
WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather"
WEATHER_API_KEY = {'APPID': ""}


class Weather():

    """A class providing access to the weather service of the Nabaztag

    A location in terms of lat & lon must be provided, e.g. from the GeoLocate class.
    """

    def __init__(self, lat_lon, units=None):

        """Create an instance of the GeoLocate class.

        :params lat_lon: A Dict object containing the lat and lon values of the Nabaztag's location.
        :params units: A Dict object containing the units to use for temperature. Default is metric.
        """

        self.lat_lon = lat_lon
        if units is None:
            self.units = {'units': "metric"}
        else:
            self.units = units

    def get_weather(self):

        """Obtain the weather information using the lat & lon.

        :returns: A Dict containing weather information.

        If the information returned by the openweather API is incorrect, a WeatherError is raised.
        """

        # Package parameters for the request to openweather API.
        params = {}
        params.update(self.lat_lon)
        params.update(WEATHER_API_KEY)
        params.update(self.units)

        response = requests.get(WEATHER_URL, params=params).json()

        weather = {}

        # Extract some information from the returned information.
        try:
            weather.update(
                {
                    'name': response['name'],
                    'sunrise': response['sys']['sunrise'],
                    'sunset': response['sys']['sunset'],
                    'temp': response['main']['temp'],
                    'condition': response['weather'][0]['main'],
                    'humidity': response['main']['humidity']
                }
            )
            return weather
        except KeyError:
            raise WeatherError("Weather service temporarily unavilable")


class WeatherError(Exception):
    pass
