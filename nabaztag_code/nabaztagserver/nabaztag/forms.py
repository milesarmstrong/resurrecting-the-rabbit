from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.forms import ModelForm, Form
from nabaztag.models import Nabaztag, PairedNabaztags


class LeftEarForm(ModelForm):

    """This class represents a form for controlling the left ear of a Nabaztag.
    """

    def __init__(self, *args, **kwargs):
        super(LeftEarForm, self).__init__(*args, **kwargs)
        self.fields['left_ear_pos'].label = "Left Ear: "
        self.fields['left_ear_pos'].widget.attrs['max'] = 17

    class Meta:
        model = Nabaztag
        fields = ['left_ear_pos']


class RightEarForm(ModelForm):

    """This class represents a form for controlling the right ear of a Nabaztag.
    """

    def __init__(self, *args, **kwargs):
        super(RightEarForm, self).__init__(*args, **kwargs)
        self.fields['right_ear_pos'].label = "Right Ear: "
        self.fields['right_ear_pos'].widget.attrs['max'] = 17

    class Meta:
        model = Nabaztag
        fields = ['right_ear_pos']


class ResetEarsForm(Form):
    """This class represents a form for resetting both ears of a Nabaztag.
    """
    reset_ears = forms.CharField(widget=forms.HiddenInput(attrs={'value': "reset_ears"}))

class TopLedForm(ModelForm):
    """This class represents a form for controlling the top led of a Nabaztag.
    """
    def __init__(self, *args, **kwargs):
        super(TopLedForm, self).__init__(*args, **kwargs)
        self.fields['top_led_color'].label = "Top LED Color: "

    class Meta:
        model = Nabaztag
        fields = ['top_led_color']

class BottomLEDForm(ModelForm):
    """This class represents a form for controlling the bottom led of a Nabaztag.
    """
    def __init__(self, *args, **kwargs):
        super(BottomLEDForm, self).__init__(*args, **kwargs)
        self.fields['bottom_led_color'].label = "Bottom LED Color: "

    class Meta:
        model = Nabaztag
        fields = ['bottom_led_color']


class ResetLedsForm(Form):
    """This class represents a form for resetting both leds of a Nabaztag.
    """
    reset_leds = forms.CharField(widget=forms.HiddenInput(attrs={'value': "reset_leds"}))


class TextToSpeechForm(Form):
    """This class represents a form for sending text to a Nabaztag for text-to-speech.
    """
    text_to_speech = forms.CharField(
        widget=forms.Textarea(
            attrs={'placeholder': "Enter text and press 'speak' to have your Nabaztag speak the text."},

        )
    )

class CreatePairingForm(forms.Form):
    """This class represents a form for adding a pairing from one Nabaztag to another.

    (nabaztag1 -> nabaztag2) allows Nabaztag 1 to receive updates from Nabaztag 2
    (nabaztag2 -> nabaztag1) allows Nabaztag 2 to receive updates from Nabaztag 1

    These two pairings are distinct.
    """
    def __init__(self, *args, **kwargs):
        global nabaztag
        nabaztag = kwargs.pop('nabaztag')
        super(CreatePairingForm, self).__init__(*args, **kwargs)

    def pairingvalidator(value):
        """Several validations are required.

        1. A Nabaztag with the specified ID must exist.
        2. The id provided for pairing cannot be your own.
        3. The pairing cannot already exist.
        """
        if not Nabaztag.objects.filter(id=value).exists():
            raise ValidationError('That Nabaztag doesn\'t exist')
        elif nabaztag.id == value:
            raise ValidationError('You can\'t pair with yourself')
        else:
            nabaztag_to_pair = Nabaztag.objects.get(id=value)
            qs = PairedNabaztags.objects.filter(nabaztag=nabaztag, paired_nabaztag=nabaztag_to_pair)
            if qs.count() > 0:
                raise ValidationError('This pairing already exists')

    create_pairing_identifier = forms.CharField(
        max_length=17,
        validators=[
            RegexValidator(
                r'([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}',
                'Not a valid Identifier',
                'Invalid Identifier'
            ),
            pairingvalidator,
        ],
    )
    create_pairing_identifier.widget = forms.TextInput(attrs={'size': 17, 'maxlength': 17,
                                                              'placeholder': "00:00:00:00:00:00"})
    create_pairing_identifier.label = "Pair With: "


class UserModelChoiceField(forms.ModelChoiceField):
    """A custom dropdown form for choosing a Nabaztag pairing to delete.
    """
    def label_from_instance(self, obj):
        return obj.paired_nabaztag.name + " (" + obj.paired_nabaztag.id + ")"


class DeletePairingForm(forms.Form):
    """This class represents a form for deleting the pairing from one Nabaztag to another.
    """
    delete_pairing_identifier = UserModelChoiceField(queryset=PairedNabaztags.objects.all())
    delete_pairing_identifier.label = "Remove Pairing: "
    delete_pairing_identifier.empty_label = None

    def __init__(self, *args, **kwargs):
        nabaztag = kwargs.pop('nabaztag')
        super(DeletePairingForm, self).__init__(*args, **kwargs)

        self.fields['delete_pairing_identifier'].queryset = PairedNabaztags.objects.filter(nabaztag=nabaztag.id)