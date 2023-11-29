from django.db import models
from django.contrib.auth.models import User
import uuid ## Universal Unique Identifyier class 
# Create your models here.

class Dset_Instance(models.Model):
    """
        This class represents an instance in our dataset,
        It is a basic object, only really needing the path to the img file 
        and path to the label file on the server. 

        call the follwoing to update the database:
        python manage.py runscript load_instances 

        you can edit the script/load_instances.py to change what info is laoded
        or adjust it to suit different datasets.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    id = models.UUIDField(primary_key = True, default = uuid.uuid4, editable = False, auto_created=True) ## unique id of the image
    img_name = models.TextField() ## name of image 
    img_fn = models.TextField() ## path to img on server
    lbl_fn = models.TextField() ## path to lbl filename on server
    set_index = models.TextField() ## id used to sort the 
    shapmap_path = models.TextField(null=True, blank=True, default=None) ## path to shap map - if in use
    updated = models.DateTimeField(auto_now=True) ## update timestamp every time
    created = models.DateTimeField(auto_now_add=True) ## update timestamp only when created
    completed = models.BooleanField(null=True, blank=True, default=False)

    class Meta:
        ordering = ['set_index'] ## sort by their index in the set - this should be their order in the collection
    def __str__(self) -> str:
         return self.img_name


class DSet_object(models.Model):
    """
        The purpose of this class is to represent 
    """
    id = models.UUIDField(primary_key = True, default = uuid.uuid4, editable = False, auto_created=True)
    parent = models.ForeignKey(Dset_Instance, on_delete=models.CASCADE) ## belongs to image 
    bounding_box = models.BinaryField(null=True, blank=True, default=None)
    semantic_points = models.BinaryField(null=True, blank=True, default=None)

    def __str__(self) -> str:
        return "{} BELONGING TO {}".format(self.__class__.__name__, str(self.parent))

class Discriminative_Features(models.Model):
    """
        This class represents an instance of a car - does not need to be saved to SQL database
        This will store information on the car whilst it is being labeled by the user.
    """
    id = models.UUIDField(primary_key = True, default = uuid.uuid4, auto_created=True)
    parent = models.ForeignKey(DSet_object, on_delete=models.CASCADE) ## belongs to Dset_object 
    counter = models.IntegerField(null=True, blank=True, default=0)
    
    ## Choices for additional classes 
    CAR_COLORS = (
        ("1", "Black"),
        ("2", "Blue"),
        ("3", "Brown"),
        ("4", "Green"),
        ("5", "Grey"),
        ("6", "Yellow"),
        ("7", "Orange"),
        ("8", "Red"),
        ("9", "Silver"),
        ("9", "White"),
        ("10", "multicolour"),
        ("11", "other"),
        ("12", "Not Applicable"),
        ("13", "Too Distant"),
    )
    colour = models.CharField(max_length=2, choices=CAR_COLORS)

    BODY_SHAPES = (
        ("1", "Convertable"),
        ("2", "Coupe"),
        ("3", "Estate"),
        ("4", "Hatchback"),
        ("5", "Sports Car/Super car"),
        ("6", "Pickup"),
        ("7", "SUV"),
        ("8", "Van"),
        ("9", "Large Misc"),
        ("9", "Medium Misc"),
        ("10", "Small Misc"),
        ("11", "London Taxi"),
        ("12", "London Bus"),
        ("13", "Not Applicable"),
        ("13", "Too Distant"),

    )
    body_shape = models.CharField(max_length=2, choices=BODY_SHAPES)

    VIEWING_ANGLES = (
        ("1", "FRONT"),
        ("2", "FRONT LEFT"),
        ("3", "LEFT"),
        ("4", "REAR LEFT"),
        ("5", "REAR"),
        ("6", "REAR RIGHT"),
        ("7", "RIGHT"),
        ("8", "FRONT RIGHT"),
        ("9", "Not Applicable"),
    )
    viewing_angle = models.CharField(max_length=2, choices=VIEWING_ANGLES)

    CURRENT_STATE = (
        ("1", "In my lane, in front"),
        ("2", "Parked on left side of the street"),
        ("3", "Parked on right side of the street"),
        ("4", "In oncoming lane"),
        ("5", "Crossing my lane"),
        ("5", "Entering my lane from LEFT"),
        ("6", "Entering my lane from RIGHT"),
        ("7", "In left lane (MULTI-LANE)"),
        ("8", "In right lane (MULTI-LANE)"),
        ("9", "Not Applicable"),
    )
    current_state = models.CharField(max_length=2, choices=CURRENT_STATE)
    
    def __str__(self) -> str:
        return "{} BELONGING TO {}".format(self.__class__.__name__, str(self.parent))