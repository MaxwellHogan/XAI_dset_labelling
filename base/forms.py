from django.forms import ModelForm
from .models import Discriminative_Features

class Discriminative_Features_Form(ModelForm):
    class Meta:
        model = Discriminative_Features
        fields = ['colour', "body_shape", "viewing_angle"]