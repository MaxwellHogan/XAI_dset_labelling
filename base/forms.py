from django.forms import ModelForm
from .models import Discriminative_Features

class Discriminative_Features_Form(ModelForm):
    class Meta:
        model = Discriminative_Features
        fields = [
            'class_name',
            'colour',
            "body_shape",
            "viewing_angle",
            "current_state",
            "occlusion_state",
            "static_obstacle_class",
            "traffic_light_state",
        ]