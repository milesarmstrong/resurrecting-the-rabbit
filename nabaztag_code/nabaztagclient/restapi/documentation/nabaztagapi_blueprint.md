FORMAT: 1A
HOST: http://nabaztag.local

# Nabaztag API
A RESTful API was developed to reside on the Nabaztag, and allow direct interaction with the device, without the need for the server.


# Group Nabaztag Control
There are several API functions available to control the Nabaztag.

## Ears [/nabaztag/api/ear/{ear}]
Functions for interacting with the Nabaztag's ears.

### control ear [PUT]
Move an ear on the Nabaztag. Possible positions are from 0 to 17 inclusive. Position 0 corresponds to the ear pointing vertically upright.

+ Parameters
	+ ear (required, string) ... The ear to move
		+ Values
			+ `left`
			+ `right`

+ Request (application/json)
    + Body

            {
                "pos": 0,
            }

+ Response 201 (application/json)
    + Body
    
            {
	            "status": 201,
	            "message": "Success"
            }

+ Response 400 (application/json)
    + Body
    
			{
				"status": 400, 
				"message": "Value of pos not in range 0-17."
			}

## LEDs [/nabaztag/api/led/{led}]
Functions for interacting with the Nabaztag's LEDs. 

### control led [PUT]
Change an LED on the Nabaztag. Provide a value from 0-255 for each of red, green, and blue values.

+ Parameters
	+ led (required, string) ... The ear to move
		+ Values
			+ `top`
			+ `bottom`

+ Request (application/json)
    + Body

            {
                "red": 150,
                "green": 75,
                "blue": 200,
            }

+ Response 201 (application/json)
	+ Body

            {
	            "status": 201,
	            "message": "Success"
            }

+ Response 400  (application/json)
    + Body
    
			{
				"status": 400,
				"message": "Value of blue not in range 0-255."
			}
            
## Location [/nabaztag/api/location]
Functions for utilising the Nabaztag's location awareness.

### get location [GET]
Returns the current latitude and longitude of the Nabaztag.

+ Response 200 (application/json)
    + Body

			{
				"lat": 50.9229537,
				"lon": -1.3984832
			}

+ Response 503 (application/json)
    + Body

            {
	            "status": 503,
	            "message": "Location service temporarily unavailable"
            }
            
## Weather [/nabaztag/api/weather]
Functions for accessing the Nabaztag's weather information.

### get weather [GET]
Returns the current temperature, sunrise time, and sunset time for the Nabaztag's current location.

+ Response 200 (application/json)
    + Body

			{
				"sunrise": 1394950554,
				"sunset": 1394993539,
				"name": "Southampton",
				"temp": 12.88,
			}

+ Response 503 (application/json)
    + Body

			{
				"status": 503,
				"message": "Weather service temporarily unavailable."
			}			
            
## Speech [/nabaztag/api/speech]
Functions for interacting with the Nabaztag's text-to-speech capabilities.

### use text-to-speech [PUT]
Allows access to the Nabaztag's text-to-speech service, the provided text will be spoken by the Nabaztag.

+ Request (application/json)
    + Body

            {
                "text": "The string for the Nabaztag to speak"
            }

+ Response 201 (application/json)
    + Body

            {
	            "status": 201,
	            "message": "Success"
            }

+ Response 400 (application/json)
    + Body

			{
				"status": 400,
				"message": "Bad Request"
			}