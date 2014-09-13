# Django imports
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

# Django REST Framework imports
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

# Nabaztag imports
from nabaztag.forms import *
from nabaztag.models import Nabaztag, PairedNabaztags

# Other imports
import json


# Global constants
LEFT = 'L'
RIGHT = 'R'
TOP = 'T'
BOTTOM = 'B'
ZERO_EAR_POS = 0
ZERO_COLOR_VALUE = "#000000"
PRESSED = 1


################## VIEW CLASSES ##################

class IndexView(ListView):

    """Instances of this class are created with requests to /

    A response is returned containing a list of all Nabaztags ordered by name.
    """

    template_name = 'index.html'
    queryset = Nabaztag.objects.all().order_by('name')


class ControlView(DetailView):

    """Instances of this class are created with requests to /control/<pk>

    The response contains the Nabaztag object identified by the pk value in the URL.
    """

    context_object_name = "nabaztag"
    template_name = 'control.html'

    def get_object(self, queryset=None):

        """Returns the Nabaztag object identified by the pk value in the url.
        """

        return get_object_or_404(Nabaztag, pk=self.kwargs.get('pk', None))

    def get_context_data(self, **kwargs):

        """Returns a dictionary containing the context for the control.html template.

        The context contains the requested Nabaztag object, plus forms initialised to the state of the object.
        """

        context = super(ControlView, self).get_context_data(**kwargs)

        context['left_ear_form'] = LeftEarForm({'left_ear_pos': context['nabaztag'].left_ear_pos})
        context['right_ear_form'] = RightEarForm({'right_ear_pos': context['nabaztag'].right_ear_pos})
        context['reset_ears_form'] = ResetEarsForm()

        context['top_led_form'] = TopLedForm({'top_led_color': context['nabaztag'].top_led_color})
        context['bottom_led_form'] = BottomLEDForm({'bottom_led_color': context['nabaztag'].bottom_led_color})
        context['reset_leds_form'] = ResetLedsForm()

        context['create_pairing_form'] = CreatePairingForm(nabaztag=context['nabaztag'])
        context['delete_pairing_form'] = DeletePairingForm(nabaztag=context['nabaztag'])
        context['paired_list'] = context['nabaztag'].get_pairings()

        context['text_to_speech_form'] = TextToSpeechForm(auto_id=False)

        return context

    def post(self, request, **kwargs):

        """Called when POST requests are made to /control/<pk>

        Looks through the POST data of the request to determine which form was submitted,
        confirms the form is valid and sets the relevant value in the Nabaztag object, then
        calls the relevant function in the Nabaztag object to send the new value over the
        websocket connection.
        """

        self.object = self.get_object()
        context = self.get_context_data(**kwargs)
        nabaztag = self.object

        if 'left_ear_pos' in request.POST:
            context['left_ear_form'] = LeftEarForm(request.POST)
            if context['left_ear_form'].is_valid():
                position = context['left_ear_form'].cleaned_data['left_ear_pos']
                nabaztag.left_ear_pos = position
                nabaztag.save()
                nabaztag.move_ear(LEFT, position)

        elif 'right_ear_pos' in request.POST:
            context['right_ear_form'] = RightEarForm(request.POST)
            if context['right_ear_form'].is_valid():
                position = context['right_ear_form'].cleaned_data['right_ear_pos']
                nabaztag.right_ear_pos = position
                nabaztag.save()
                nabaztag.move_ear(RIGHT, position)

        elif 'reset_ears' in request.POST:
            context['reset_ears_form'] = ResetEarsForm(request.POST)
            if context['reset_ears_form'].is_valid():
                nabaztag.left_ear_pos = ZERO_EAR_POS
                nabaztag.right_ear_pos = ZERO_EAR_POS
                nabaztag.save()
                context['left_ear_form'] = LeftEarForm({'left_ear_pos': context['nabaztag'].left_ear_pos})
                context['right_ear_form'] = RightEarForm({'right_ear_pos': context['nabaztag'].right_ear_pos})
                nabaztag.move_ear(LEFT, ZERO_EAR_POS)
                nabaztag.move_ear(RIGHT, ZERO_EAR_POS)

        elif 'top_led_color' in request.POST:
            context['top_led_form'] = TopLedForm(request.POST)
            if context['top_led_form'].is_valid():
                color = context['top_led_form'].cleaned_data['top_led_color']
                nabaztag.top_led_color = color
                nabaztag.save()
                nabaztag.change_led(TOP, hex_to_rgb(color))

        elif 'bottom_led_color' in request.POST:
            context['bottom_led_form'] = BottomLEDForm(request.POST)
            if context['bottom_led_form'].is_valid():
                color = context['bottom_led_form'].cleaned_data['bottom_led_color']
                nabaztag.bottom_led_color = color
                nabaztag.save()
                nabaztag.change_led(BOTTOM, hex_to_rgb(color))

        elif 'reset_leds' in request.POST:
            context['reset_leds_form'] = ResetLedsForm(request.POST)
            if context['reset_leds_form'].is_valid():
                nabaztag.top_led_color = ZERO_COLOR_VALUE
                nabaztag.bottom_led_color = ZERO_COLOR_VALUE
                nabaztag.save()
                context['top_led_form'] = TopLedForm({'top_led_color': context['nabaztag'].top_led_color})
                context['bottom_led_form'] = BottomLEDForm({'bottom_led_color': context['nabaztag'].bottom_led_color})
                nabaztag.change_led(TOP, hex_to_rgb(ZERO_COLOR_VALUE))
                nabaztag.change_led(BOTTOM, hex_to_rgb(ZERO_COLOR_VALUE))

        elif 'create_pairing_identifier' in request.POST:
            context['create_pairing_form'] = CreatePairingForm(request.POST, nabaztag=nabaztag)
            if context['create_pairing_form'].is_valid():
                nabaztag_to_pair = Nabaztag.objects.get(id=context['create_pairing_form'].
                                                        cleaned_data['create_pairing_identifier'])
                pairing = PairedNabaztags(nabaztag=nabaztag, paired_nabaztag=nabaztag_to_pair)
                pairing.save()
                context['paired_list'] = nabaztag.get_pairings()

        elif 'delete_pairing_identifier' in request.POST:
            context['delete_pairing_form'] = DeletePairingForm(request.POST, nabaztag=nabaztag)
            if context['delete_pairing_form'].is_valid():
                nabaztag_to_unpair = context['delete_pairing_form']. \
                    cleaned_data['delete_pairing_identifier'].paired_nabaztag
                PairedNabaztags.objects.filter(nabaztag=nabaztag, paired_nabaztag=nabaztag_to_unpair).delete()
                context['paired_list'] = nabaztag.get_pairings()

        elif 'text_to_speech' in request.POST:
            ttsform = TextToSpeechForm(request.POST, auto_id=False)
            if ttsform.is_valid():
                text = ttsform.cleaned_data['text_to_speech']
                nabaztag.speak_message(text)

        return self.render_to_response(context)


################## NABAZTAG API FUNCTIONS ##################

class EarMoved(APIView):

    """Instances of this class are created when a request is made to /update/<pk>/ear

    Only POST requests are acted upon.
    """

    def get_object(self, pk):

        """Returns the Nabaztag object identified by pk, or a 404 if it does not exist.

        :param pk: The primary key of the Nabaztag object.
        """

        try:
            return Nabaztag.objects.get(pk=pk)
        except Nabaztag.DoesNotExist:
            raise Http404

    def post(self, request, pk):

        """Called when a POST request is made to /update/<pk>/ear

        :param request: The Django request object.
        :param pk: The primary key of the Nabaztag object.

        The Nabaztag object identified by pk is obtained, and we check whether any other
        Nabaztag objects are paired to it. If so, their state is updated and we send them
        a message telling them to reset the relevant ear, returning a HTTP_200_OK

        If the body of the request is not valid JSON, or doesn't contain the information we
        expect, return a HTTP_400_BAD_REQUEST.
        """

        paired_nabaztag = self.get_object(pk)
        pairings = PairedNabaztags.objects.all().filter(paired_nabaztag=paired_nabaztag)

        try:
            message = json.loads(request.body)

            for pair in pairings:
                nabaztag = pair.nabaztag

                if message['ear'] == LEFT:
                    nabaztag.move_ear(LEFT, ZERO_EAR_POS)
                    paired_nabaztag.left_ear_pos = ZERO_EAR_POS
                    nabaztag.left_ear_pos = ZERO_EAR_POS
                elif message['ear'] == RIGHT:
                    nabaztag.move_ear(RIGHT, ZERO_EAR_POS)
                    paired_nabaztag.right_ear_pos = ZERO_EAR_POS
                    nabaztag.right_ear_pos = ZERO_EAR_POS

                nabaztag.save()
                paired_nabaztag.save()
                return Response({"status": 200, "message": "OK"}, content_type="application/json")
        except ValueError:
            return Response(
                {"status": 400, "message": "Request was not valid JSON"},
                status=status.HTTP_400_BAD_REQUEST,
                content_type="application/json"
            )
        except KeyError:
            return Response(
                {"status": 400, "message": "Invalid request"},
                status=status.HTTP_400_BAD_REQUEST,
                content_type="application/json"
            )


class ButtonPressed(APIView):

    """Instances of this class are created when a request is made to /update/<pk>/button

    Only POST requests are acted upon.
    """

    def get_object(self, pk):

        """Returns the Nabaztag object identified by pk, or a 404 if it does not exist.

        :param pk: The primary key of the Nabaztag object.
        """

        try:
            return Nabaztag.objects.get(pk=pk)
        except Nabaztag.DoesNotExist:
            raise Http404

    def post(self, request, pk):

        """Called when a POST request is made to /update/<pk>/button

        :param request: The Django request object.
        :param pk: The primary key of the Nabaztag object.

        The Nabaztag object identified by pk is obtained, and we check whether any other
        Nabaztag objects are paired to it. If so, their state is updated and we send them
        a message telling them to reset both ears, returning a HTTP_200_OK

        If the body of the request is not valid JSON, or doesn't contain the information we
        expect, return a HTTP_400_BAD_REQUEST.
        """

        paired_nabaztag = self.get_object(pk)
        pairings = PairedNabaztags.objects.all().filter(paired_nabaztag=paired_nabaztag)

        try:
            message = json.loads(request.body)

            for pair in pairings:
                nabaztag = pair.nabaztag

                if message['button'] == PRESSED:
                    nabaztag.move_ear(LEFT, ZERO_EAR_POS)
                    nabaztag.move_ear(RIGHT, ZERO_EAR_POS)
                    paired_nabaztag.left_ear_pos = ZERO_EAR_POS
                    paired_nabaztag.right_ear_pos = ZERO_EAR_POS
                    nabaztag.left_ear_pos = ZERO_EAR_POS
                    nabaztag.right_ear_pos = ZERO_EAR_POS

                nabaztag.save()

            paired_nabaztag.save()
            return Response({"status": 200, "message": "OK"}, content_type="application/json")
        except ValueError:
            return Response(
                {"status": 400, "message": "Request was not valid JSON"},
                status=status.HTTP_400_BAD_REQUEST,
                content_type="application/json"
            )
        except KeyError:
            return Response(
                {"status": 400, "message": "Invalid request"},
                status=status.HTTP_400_BAD_REQUEST,
                content_type="application/json"
            )


class SetLocation(APIView):

    """Instances of this class are created when a request is made to /update/<pk>/location

    Only POST requests are acted upon.
    """

    def get_object(self, pk):

        """Returns the Nabaztag object identified by pk, or a 404 if it does not exist.

        :param pk: The primary key of the Nabaztag object.
        """

        try:
            return Nabaztag.objects.get(pk=pk)
        except Nabaztag.DoesNotExist:
            raise Http404

    def post(self, request, pk):

        """Called when a POST request is made to /update/<pk>/location

        :param request: The Django request object.
        :param pk: The primary key of the Nabaztag object.

        The Nabaztag object identified by pk is obtained, and we update its location from
        the request body.

        If the body of the request is not valid JSON, or doesn't contain the information we
        expect, return a HTTP_400_BAD_REQUEST.
        """

        try:
            nabaztag = self.get_object(pk)
            location = json.loads(request.body)

            # If the location service on the Nabaztag was unavilable, the body will contain {"unavailable": 1},
            # in which case we don't update the location.
            if not 'unavailable' in location:
                nabaztag.latitude = location['lat']
                nabaztag.longitude = location['lon']
                nabaztag.save()

            return Response({"status": 200, "message": "OK"}, content_type="application/json")
        except ValueError:
            return Response(
                {"status": 400, "message": "Request was not valid JSON"},
                status=status.HTTP_400_BAD_REQUEST,
                content_type="application/json"
            )
        except KeyError:
            return Response(
                {"status": 400, "message": "Invalid request"},
                status=status.HTTP_400_BAD_REQUEST,
                content_type="application/json"
            )



################## HELPER FUNCTIONS ##################

def hex_to_rgb(value):

    """Converts a hex colour string, e.g. #ffffff, to a rgb tuple, e.g. (255, 255, 255)
    """

    value = value.strip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv / 3], 16) for i in range(0, lv, lv / 3))