# https://www.youtube.com/watch?v=TcnWEQMT3_A
from base.models import Dset_Instance

import os
from pathlib import Path
import yaml

BASE_DIR = Path(__file__).resolve().parent.parent

def run():
    yaml_path = BASE_DIR / "software_config.yaml"
    
    with open(yaml_path, 'r') as file:
        software_config = yaml.safe_load(file)

    img_path = Path(software_config["img_path"])
    shapmap_path = software_config["shapmap_path"] if "shapmap_path" in software_config else None
    lbl_path = Path(software_config["lbl_path"])

    ## make sure the label path exists - create it if it does not
    lbl_path.mkdir(parents=True, exist_ok=True)

    ## create list of all the filenames 
    img_content = os.listdir(img_path)

    if len(img_content) == 0:
        raise Exception("Image path supplied is empty!")

    ## delete old instances 
    # Dset_Instance.objects.all().delete() 

    for idx, img_fn in enumerate(img_content):

        img_name, img_ext = img_fn.split(".")
        full_img_fn = img_path / img_fn
        full_lbl_fn = lbl_path / img_fn.replace(img_ext, "xml")

        set_index = int(img_name.split('_')[-1])

        if idx == 0:
            print(img_name, img_ext, "\n", full_lbl_fn) 

        ## create instance
        dset_instance = Dset_Instance(
            img_name = img_name,
            img_fn = str(full_img_fn),
            lbl_fn = str(full_lbl_fn),
            set_index = set_index,
            shapmap_path = shapmap_path
        )

        dset_instance.save()
        
