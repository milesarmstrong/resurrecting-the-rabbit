#Resurrecting The Rabbit

An invidual project carried out in my 3rd year in [ECS](http://www.ecs.soton.ac.uk) at The University of Southampton, as part of my Masters in Computer Science.

##Project Abstract

The [Nabaztag](http://en.wikipedia.org/wiki/Nabaztag), a Wi-Fi enabled smart rabbit, was a once popular foray into the world of Pervasive Computing. Part toy, part personal assistant, it was designed to be a friendly electronic companion that could convey a variety of information to the user using lights, sound, and motion. Whilst it was a reasonably successful product, technical issues plagued the cloud architecture supporting it, until eventually its creator Violet filed for bankruptcy. This report details the process of resurrecting a single Nabaztag:tag device through a combination of replacement hardware and software. By using the emerging WebSocket protocol as a medium for publish-subscribe communication, and by developing a RESTful API for the device itself, the Nabaztag:tag is brought up to date as a modern, internet connected 'thing'.

##Architecture
- The internal circuitry of the Nabaztag was replaced with a BeagleBone Black connected via a serial connection to a custom built AVR circuit which controlled the ear motors and LEDs..
	- The [AVR code](https://github.com/milesarmstrong/resurrecting-rabbit/blob/master/avr_setup/nabaztag_avr.ino).
	- Detailed setup [instructions](https://github.com/milesarmstrong/resurrecting-rabbit/tree/master/beaglebone_setup) for the BeagleBone Black.
	- [Code](https://github.com/milesarmstrong/resurrecting-rabbit/tree/master/nabaztag_code/nabaztagclient/beaglebone) for the Python client running on the BeagleBone Black.
	- An [API](https://github.com/milesarmstrong/resurrecting-rabbit/tree/master/nabaztag_code/nabaztagclient/restapi) was created, running on the BeagleBone Black, to allow direct control of the Nabaztag.

- A [web application](https://github.com/milesarmstrong/resurrecting-rabbit/tree/master/nabaztag_code/nabaztagserver) was created to allow control of the Nabaztag from a browser, over a WebSocket connection.


##Report
The final report submitted upon completion of the project is available [here](https://github.com/milesarmstrong/resurrecting-rabbit/blob/master/reports/final/report/finalreport.pdf?raw=tru). Full references for any open-source projects used are available at the end of the report.

