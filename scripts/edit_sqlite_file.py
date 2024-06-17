# https://www.youtube.com/watch?v=TcnWEQMT3_A
from base.models import Dset_Instance, Discriminative_Features, DSet_object

import os
from pathlib import Path
import json

from tqdm import tqdm 

BASE_DIR = Path(__file__).resolve().parent.parent

def run():
    yaml_path = BASE_DIR / "software_config.json"
    
    # with open(yaml_path, 'r') as file:
    #     software_config = json.load(file)

    # for dset_name in software_config["sets"]:
    #     dset_info = software_config[dset_name]
    #     print(dset_name, dset_info["img_path"])

    obj_features = Discriminative_Features.objects.all()
    for obj_feature in obj_features.iterator():
        obj_feature.img_name = obj_feature.parent.parent.img_fn
        obj_feature.save()

    dset_objs = DSet_object.objects.all()
    for dset_obj in dset_objs.iterator():
        dset_obj.img_name = dset_obj.parent.img_fn
        dset_obj.save()

    ## define new stuff we want to edit 
    # set_name = "winter"
    # summer_count = Dset_Instance.objects.filter(img_fn__contains="/media/maxwell/Lucky_chicken/output_files_20221209_1/rgb").count()
    # summer_done = Dset_Instance.objects.filter(img_fn__contains="/media/maxwell/Lucky_chicken/output_files_20221209_1/rgb").filter(completed = 1).count()
    # print(summer_done, "/", summer_count)

    # dset_instances = Dset_Instance.objects.all()

    # for dset_instance in tqdm(dset_instances.iterator(),total=dset_instances.count()):
    #     # for dset_instance in dset_instances.iterator():
    #     # print(dset_instance.set_index, dset_instance.set_name, dset_instance.set_index)
    #     set_index = int(dset_instance.set_index) + summer_count

    #     dset_instance.set_index=str(set_index)
    #     dset_instance.set_name=set_name

    #     dset_instance.save()

    #     uuid = dset_instance.id

    # test_instance = Dset_Instance.objects.filter(id = uuid)
    # print(test_instance.count())
    # test_instance = test_instance.first()
    # print(test_instance.set_index, test_instance.set_name, test_instance.set_index)