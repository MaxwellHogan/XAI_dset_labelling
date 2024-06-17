# https://www.youtube.com/watch?v=TcnWEQMT3_A
from base.models import Dset_Instance, DSet_object, Discriminative_Features
from django.contrib.auth.models import User

import os
from pathlib import Path
import shutil ## used for copying images
import json
import xml.etree.ElementTree as ET

import numpy as np
import matplotlib.pyplot as plt
import cv2
import base64


from tqdm import tqdm 

BASE_DIR = Path(__file__).resolve().parent.parent

## look up tables for the Discriminative features 
class_name_lut = dict(Discriminative_Features.CLASS_NAME)
static_obstacle_class_lut = dict(Discriminative_Features.STATIC_OBS_CLASS_NAME)
traffic_light_state_lut = dict(Discriminative_Features.TRAFFIC_LIGHT_STATE)
colour_lut = dict(Discriminative_Features.CAR_COLORS)
body_shape_lut = dict(Discriminative_Features.BODY_SHAPES)
viewing_angle_lut = dict(Discriminative_Features.VIEWING_ANGLES)
current_state_lut = dict(Discriminative_Features.CURRENT_STATE)
occlusion_state_lut = dict(Discriminative_Features.OCCLUSION)


'''
    Convert hsv code to rgb code
        I use it when generating evenly spaced colour palettes for plotting
'''
def random_color():
    h = np.random.uniform(0, 1, 1)[0]
    s = np.random.uniform(0, 1, 1)[0]
    v = 1

    if h == 1.0: h = 0.0
    i = int(h*6.0); f = h*6.0 - i
    
    w = int(255*( v * (1.0 - s) ))
    q = int(255*( v * (1.0 - s * f) ))
    t = int(255*( v * (1.0 - s * (1.0 - f)) ))
    v = int(255*v)
    
    if i==0: return (v, t, w)
    if i==1: return (q, v, w)
    if i==2: return (w, v, t)
    if i==3: return (w, q, v)
    if i==4: return (t, w, v)
    if i==5: return (v, w, q)


# define a function to 
# convert a simple dictionary 
# of key/value pairs into XML
def dict_to_xml(tag, d):
    elem = ET.Element(tag)
    for key, val in d.items():
        key=key.lower()
        if type(val) is dict:
            ## 
            elem.append(dict_to_xml(key, val))
        else:
            # create an Element
            # class object
            child = ET.Element(key)
            child.text = str(val)
            elem.append(child)
    return elem

def parse_dset_Instances(dset_Instance: Dset_Instance) -> ET.Element:

    folder_path = None 
    ## get the objects and belonging to this instance
    img_objects = DSet_object.objects.filter(parent__id = dset_Instance.id)

    root = dict_to_xml("annotation", {
        "dset" : dset_Instance.set_name,
        "folder" : "None" if folder_path is None else folder_path,
        "filename" : dset_Instance.img_name,
        "source" : "EVD_dataset", 
        "size" : {"width" : 640, "height" : 480, "depth":3},
        "segmented" : True
    })

    yolo_labels = []

    for img_obj in img_objects.iterator():
        ## get obj description 
        obj_features = Discriminative_Features.objects.filter(parent__id=img_obj.id).last()

        if obj_features is None: continue

        ## bndbox 
        bndbox = np.frombuffer(base64.b64decode(img_obj.bounding_box), dtype=np.float64).astype(int)
        ## points
        try:
            points = np.frombuffer(base64.b64decode(img_obj.semantic_points), dtype=np.float64).astype(int)
            points = points.reshape(-1, 2)
        except:
            continue
        
        ## calculate normalised bbox dims for yolo labels 
        x_centre = ((bndbox[0] + bndbox[2])/2)/640
        y_centre = ((bndbox[1] + bndbox[3])/2)/480
        width_norm  = (bndbox[2] - bndbox[0])/640
        height_norm = (bndbox[3] - bndbox[1])/480

        obj_dict = {
            "name": class_name_lut[obj_features.class_name],
            "bndbox" :{
                "xmin": bndbox[0],
                "ymin": bndbox[1],
                "xmax": bndbox[2],
                "ymax": bndbox[3]
            },
            "points" : np.array2string(points, separator = ",").replace(",\n", ","),
        }

        if obj_dict["name"] == "Car":
            obj_dict["car_colour"] = colour_lut[obj_features.colour]
            obj_dict["body_shape"] = body_shape_lut[obj_features.body_shape]
            obj_dict["persective"] = viewing_angle_lut[obj_features.viewing_angle]
            obj_dict["current_state"] = current_state_lut[obj_features.current_state]
            obj_dict["occlusion"] = occlusion_state_lut[obj_features.occlusion_state]

            ## add car to yolo labels 
            yolo_labels.append([0, x_centre, y_centre, width_norm, height_norm])

        elif obj_dict["name"] in ["Pedestrian", "MotorBike", "Cyclist (on road only)"]:
            obj_dict["occlusion"] = occlusion_state_lut[obj_features.occlusion_state]

            ## add these classes to yolo labels 
            class_no = ["Pedestrian", "MotorBike", "Cyclist (on road only)"].index(obj_dict["name"]) + 1
            yolo_labels.append([class_no, x_centre, y_centre, width_norm, height_norm])

        elif obj_dict["name"] == "Static obstacle":
            obj_dict["static_obstacle_name"] = static_obstacle_class_lut[obj_features.static_obstacle_class]
            # print(obj_dict["name"], obj_dict["static_obstacle_name"])
            if obj_dict["static_obstacle_name"] == "traffic light":
                # print("here")
                obj_dict["traffic_light_state"] = traffic_light_state_lut[obj_features.traffic_light_state]
                yolo_labels.append([4, x_centre, y_centre, width_norm, height_norm])
                # kill
            obj_dict["occlusion"] = occlusion_state_lut[obj_features.occlusion_state]
        else:
            pass

        root.append(dict_to_xml("object", obj_dict))

    return root, yolo_labels


def run():
    yaml_path = BASE_DIR / "software_config.json"
    
    with open(yaml_path, 'r') as file:
        software_config = json.load(file)

    for dset_name in software_config["sets"]:
        dset_info = software_config[dset_name]

    output_path = Path(software_config["output_path"])
    
    ## print users 

    ## define new stuff we want to edit 
    # username = "maxwell"
    # set_name = "winter"

    # usr = User.objects.filter(username=username).first()
    dset_Instances = Dset_Instance.objects.all()
    # dset_Instances = dset_Instances.filter(set_name=set_name)
    dset_Instances = dset_Instances.filter(completed=1)
    # dset_Instances = dset_Instances.filter(user=usr)
    
    # dset_Instance = dset_Instances.first()
    # print(dset_Instance.img_name, dset_Instance.user)

    for dset_Instance in tqdm(dset_Instances.iterator(), total=dset_Instances.count()):

        set_name = dset_Instance.set_name

        ## define img objects
        img = cv2.imread(dset_Instance.img_fn)
        mask_vis = np.zeros_like(img)
        mask_lbl = np.zeros_like(img)

        ## define img output filename
        img_fn_out = str(output_path / set_name /"images" / (dset_Instance.img_name + ".bmp"))

        shutil.copyfile(dset_Instance.img_fn, img_fn_out)

        ## get the objects belonging to this instance 
        img_objects = DSet_object.objects.filter(parent__id = dset_Instance.id)

        root, yolo_labels = parse_dset_Instances(dset_Instance)

        xml_out = img_fn_out.replace("images", "xml_lbl").replace(".bmp", "_{}.xml".format(set_name))
        ET.ElementTree(root).write(xml_out)

        # yolo_out = dset_Instance.img_fn.replace("rgb", "yolo_lbl").replace(".bmp", "_{}.txt".format(set_name))
        yolo_out = img_fn_out.replace("images", "labels").replace(".bmp", ".txt")
        yolo_labels_np = np.array(yolo_labels, dtype=np.float16)
        # print(yolo_labels_np)
        np.savetxt(yolo_out, yolo_labels_np, delimiter=" ", fmt='%.16f')

        ## generate the mask 
        for idx, obj in enumerate(img_objects.iterator()):
            r_color = random_color()

            try:
                points = np.frombuffer(base64.b64decode(obj.semantic_points), dtype=np.float64).astype(int)
                points = points.reshape(-1, 2)
            except Exception as error: 
                print(dset_Instance.set_name, dset_Instance.img_name, idx, error)
                continue

            mask_vis = cv2.fillPoly(mask_vis, [points], color=r_color)
            mask_lbl = cv2.fillPoly(mask_lbl, [points], color=(idx, idx, idx))

            box = np.frombuffer(base64.b64decode(obj.bounding_box), dtype=np.float64).astype(int)
            img = cv2.rectangle(img, box[:2], box[2:], r_color, 1)

        ## create image for visual inspection
        vis = np.concatenate((img, mask_vis), axis=1)
        username_idx = dset_Instance.user.username
        vis = cv2.putText(vis, username_idx, (640, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 1, cv2.LINE_AA)

        out_filename = img_fn_out.replace("images", "visual_label").replace(".bmp", '_{}.jpg'.format(set_name))
        cv2.imwrite(out_filename, vis)
        out_filename = img_fn_out.replace("images", "masks").replace(".bmp", '_{}.bmp'.format(set_name))
        cv2.imwrite(out_filename, mask_lbl)

        # break
