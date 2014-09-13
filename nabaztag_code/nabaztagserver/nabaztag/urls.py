from django.conf.urls import patterns, url
from nabaztag.views import *

urlpatterns = patterns(
    # Site URLs
    '',
    url(r'^$', IndexView.as_view()),
    url(r'^control/(?P<pk>(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2})$', ControlView.as_view()),

    # API URLs
    url(r'^update/(?P<pk>(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2})/ear$', EarMoved.as_view()),
    url(r'^update/(?P<pk>(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2})/button$', ButtonPressed.as_view()),
    url(r'^update/(?P<pk>(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2})/location', SetLocation.as_view()),
)
