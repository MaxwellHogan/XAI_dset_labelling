We will use this project to create a hostable webserver that can be used to label a dataset.

In order to run the server and access it from outside my network I have installed Tailscale. Then running this commnad will start the server:
python manage.py runserver 0.0.0.0:8000

To configure the software edit the software_config.yaml file:
* img_path : path to the images to be labelled
* shapmap_path : optional path to pre-compiled shap maps that can be used to assist in labelling
* lbl_path : path to where the labels are currently stored/will be stored

future plan wil be to add the descritive labels in the config file so it can be used with other datasets, for now we will hard code these. 

To prepare the sqlite database (that will store the info like the image filenames), set the parameters in the yaml file that was described above anf then run:
python manage.py runscript load_instances

It is a good idea to backup the sqlite data before running any scripts:
sqlite3 db.sqlite3 ".backup db.sqlite3.back"



if the database needs to be reset, call the following:
python manage.py flush


