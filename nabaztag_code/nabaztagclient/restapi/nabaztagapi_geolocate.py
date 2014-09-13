from wifi import Cell
import json
import requests

GOOGLE_LOCATION_URL = 'https://www.googleapis.com/geolocation/v1/geolocate?key={0}'
GOOGLE_API_KEY = ''
JSON_REQUEST_HEADERS = {'Content-type': 'application/json', 'Accept': 'text/plain'}


class GeoLocate():

    """A class providing access to the physical location of the Nabaztag

    The MAC addresses of nearby Wi-Fi access points are passed to Google's
    Geolocation API, which returns a reasonably accurate latitude and longitude.
    """

    def __init__(self, interface):

        """Create an instance of the GeoLocate class.

        :params interface: The Wi-Fi interface to use for scanning, e.g. 'wlan0'
        """

        self.interface = interface

    def get_location(self):

        """Obtains the physical location using nearby Wi-Fi networks.

        :returns: a Dict containing the lat & lon for the current location.

        According to Google's API specification, two or more access points are
        required for a result to be returned. In case a result is not returned,
        or another error occurs, a LocationError is raised.
        """

        # Get full information for all visible access points
        networks = Cell.all(self.interface)
        addresses = []

        # Extract just the MAC addresses
        for network in networks:
            addresses.append({'macAddress': network.address})

        json_response = requests.post(
            GOOGLE_LOCATION_URL.format(GOOGLE_API_KEY),
            data=json.dumps({'wifiAccessPoints': addresses}),
            headers=JSON_REQUEST_HEADERS
        ).json()

        # Handle Google returning an error.
        if "error" in json_response:
            raise LocationError("Unable to determine location")
        else:
            return {
                'lat': json_response['location']['lat'],
                'lon': json_response['location']['lng']
            }


class LocationError(Exception):
    pass
