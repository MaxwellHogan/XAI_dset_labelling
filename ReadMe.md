We will use this project to create a hostable webserver that can be used to label a dataset.

To configure the software edit the software_config.yaml file:
* img_path : path to the images to be labelled
* shapmap_path : optional path to pre-compiled shap maps that can be used to assist in labelling
* lbl_path : path to where the labels are currently stored/will be stored

future plan wil be to add the descritive labels in the config file so it can be used with other datasets, for now we will hard code these. 

To prepare the sqlite database (that will store the info like the image filenames), set the parameters in the yaml file that was described above anf then run:
python manage.py runscript load_instances

if the database needs to be reset, call the following:
python manage.py flush