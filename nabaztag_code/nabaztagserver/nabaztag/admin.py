from django.contrib import admin

from nabaztag.models import Nabaztag


class NabaztagAdmin(admin.ModelAdmin):

    """This class defines sections of settings for the admin page.
    """

    fieldsets = [
        ('Identification', {'fields': ['id', 'name']}),
        ('Ears', {'fields': ['left_ear_pos', 'right_ear_pos']}),
        ('Lights', {'fields': ['bottom_led_color', 'top_led_color']}),
        ('Location', {'fields': ['latitude', 'longitude']}),
    ]


admin.site.register(Nabaztag, NabaztagAdmin)
