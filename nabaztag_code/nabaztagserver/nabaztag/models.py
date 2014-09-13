import json
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from ws4redis.publisher import RedisPublisher

from colorful.fields import RGBColorField


class Nabaztag(models.Model):

    """Instances of this class represent a Nabaztag device.
    """

    # Identification
    id = models.CharField(max_length=17, primary_key=True)
    name = models.CharField(max_length=255, blank=True)

    #Ear Positions
    left_ear_pos = models.PositiveIntegerField(
        default=0,
        validators=[
            # Ear position is between 0 and 17.
            MinValueValidator(0),
            MaxValueValidator(17),
        ],
        blank=True,
        null=True
    )
    right_ear_pos = models.PositiveIntegerField(
        default=0,
        validators=[
            # Ear position is between 0 and 17.
            MinValueValidator(0),
            MaxValueValidator(17),
        ],
        blank=True,
        null=True
    )

    # LED Colours
    top_led_color = RGBColorField(blank=True, null=True)
    bottom_led_color = RGBColorField(blank=True, null=True)

    # Location
    latitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)

    def get_pairings(self):

        """Returns a Dict of all Nabaztags which this Nabaztag is paired to.
        """

        pairing_list = {}

        for pairing in PairedNabaztags.objects.all().filter(nabaztag=self.id):
            pairing_list.update({pairing.paired_nabaztag.id: pairing.paired_nabaztag.name})

        return pairing_list

    def move_ear(self, ear, position):

        """Places an ear message in the redis pub-sub message queue identified by this Nabaztag's identifier.

        :param ear: The ear to move.
        :param position: The position to move it to.
        """

        connection = RedisPublisher(facility=self.id, broadcast=True)
        message = {"ear": ear, "pos": position}
        connection.publish_message(json.dumps(message))

    def change_led(self, led, color):

        """Places an LED message in the redis pub-sub message queue identified by this Nabaztag's identifier.

        :param led: The led to change.
        :param color: A tuple containing RGB values for the colour to set, e.g. (255, 255, 255)
        """

        connection = RedisPublisher(facility=self.id, broadcast=True)
        message = {'led': led, 'red': color[0], 'green': color[1], 'blue': color[2]}
        connection.publish_message(json.dumps(message))

    def speak_message(self, text):

        """Places a speech in the redis pub-sub message queue identified by this Nabaztag's identifier.

        :param text: The text to send to the text-to-speech service.
        """

        connection = RedisPublisher(facility=self.id, broadcast=True)
        message = {'speak': 1, 'text': text}
        connection.publish_message(json.dumps(message))


class PairedNabaztags(models.Model):

    """This class represents a pairing between two Nabaztags.

    The first Nabaztag ('nabaztag') in the pairing will receive updates from the second ('paired_nabaztag').
    However this doesn't work in the reverse direction (you can't send notifications to another Nabaztag unless
    it pairs with you, to avoid spamming).
    """

    nabaztag = models.ForeignKey(Nabaztag, related_name='+')
    paired_nabaztag = models.ForeignKey(Nabaztag, related_name='+')

    class Meta:
        """Ensure that a particular pairing between from one Nabaztag to another is unique.
        """
        unique_together = (("nabaztag", "paired_nabaztag"),)