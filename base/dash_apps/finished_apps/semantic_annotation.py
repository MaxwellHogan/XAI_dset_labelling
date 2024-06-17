import plotly.express as px
from dash import no_update, html, dcc
from dash.dependencies import Input, Output
from django_plotly_dash import DjangoDash
from skimage import data
import re
import json
import cv2
import numpy as np
import pandas as pd
import pickle 
import base64
from pathlib import Path

## link to the django_plotly_dash project documentation
# https://django-plotly-dash.readthedocs.io/en/latest/introduction.html
## annotation examples
# https://dash.plotly.com/annotations#extracting-an-image-subregion-defined-by-an-annotation

# import sys
# from pathlib import Path
# BASE_DIR = Path(__file__).resolve().parent.parent.parent
# sys.path.append(BASE_DIR)
from base.models import DSet_object, Dset_Instance


img_fn = ""
fig = px.imshow(np.zeros((512,512,3),dtype=np.uint8), width=800)
fig.update_layout(
    dragmode="drawclosedpath",
    newshape=dict(fillcolor="rgba(0,0,125,0)", line=dict(color="darkblue", width=2))
)
config = {
    "modeBarButtonsToAdd": [
        # "drawline",
        # "drawopenpath",
        "drawclosedpath",
        # "drawcircle",
        "drawrect",
        "eraseshape",
    ]

}

app = DjangoDash('semantic_annotation')
app.layout = html.Div(
    [
        dcc.Input(id="img-id",style={"display": "none"}, value=img_fn),
        dcc.Graph(id="graph-pic", figure=fig, config=config),
        html.Pre(id="annotations-data-pre"),
    ]
)

def mask_to_polygons(mask):
    """
        Extracts polygon points from "binary" mask 
    """
    # cv2.RETR_CCOMP flag retrieves all the contours and arranges them to a 2-level
    # hierarchy. External contours (boundary) of the object are placed in hierarchy-1.
    # Internal contours (holes) are placed in hierarchy-2.
    # cv2.CHAIN_APPROX_NONE flag gets vertices of polygons from contours.
    mask = np.ascontiguousarray(mask)  # some versions of cv2 does not support incontiguous arr
    contours, hierarchy = cv2.findContours(mask.astype("uint8"), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    # print(len(res))
    # hierarchy = res[-1]
    if hierarchy is None:  # empty mask
        return [], [], False
    has_holes = (hierarchy.reshape(-1, 4)[:, 3] >= 0).sum() > 0

    contours = [x.flatten() for x in contours]

    # # These coordinates from OpenCV are integers in range [0, W-1 or H-1].
    # # We add 0.5 to turn them into real-value coordinate space. A better solution
    # # would be to first +0.5 and then dilate the returned polygon by 0.5.
    # res = [x + 0.5 for x in res if len(x) >= 6]

    return contours, hierarchy, has_holes

## define paths to label and mask files - later I will add this to the model 
wanted_catagories = [0,1,2,3,5,7,9,11]

def parse_pred(filename, pred_path = None):

    if pred_path is None: pred_path = Path("/media/maxwell/Lucky_chicken/output_files_20221209_1/panoptic_fpn_R_101_3x/")
    elif type(pred_path) is str: pred_path = Path(pred_path)
    elif type(pred_path) is Path: pass ## do nothing if obj is already Path tpye
    else: print("Attempting to parse prediciton file object of type:", type(pred_path))

    mask_path = pred_path / "masks" / (filename + ".csv")
    lbl_path  = pred_path / "labels" / (filename + ".csv")

    ## load the data
    try:
        mask = np.genfromtxt(mask_path, delimiter=",")
        lbls = pd.read_csv(lbl_path)

        ## list to hold selection strings 
        selections = []

        for _, row in lbls.iterrows():

            ## check if we actually want this category 
            class_name = row["category_id"]
            if class_name not in wanted_catagories:
                continue
            
            mask_i = mask == row["id"]
            contours, hierarchy, has_holes = mask_to_polygons(mask_i)

            ## currently using top poly - will ignore holes and splits in body 
            selections.append("M" + "L".join([",".join(map(str, p)) for p in contours[0].reshape(-1, 2).tolist()]) +"Z")

        return selections
    except:
        return []

def parse_shape(shapes : list, session_state):

    ## we have started editing this image so need to mark it as incomplete
    img_id = session_state["img_id"] 
    parent_Dset_Instance = Dset_Instance.objects.get(id = img_id) 
    if parent_Dset_Instance.completed:
        parent_Dset_Instance.completed = 0
        parent_Dset_Instance.save()

    def parse_path(shape):
        points = shape["path"]
        # print("Points", points)
        points = [p.split(",") for p in points.replace("M", "").replace("Z","").split("L")]
        points = np.array([(float(p0),float(p1)) for p0,p1 in points], dtype=np.float64)
        # print("Points", points)

        box = np.array((points.min(axis=0), points.max(axis = 0))).flatten()

        return points, box
        
    ## delete old instances 
    DSet_object.objects.filter(parent__id = img_id).delete()

    for idx, shape in enumerate(shapes):
        ## set up dataset object - connect it to it's parent (the file)
        dSet_object = DSet_object(
            parent = parent_Dset_Instance,
            img_name = parent_Dset_Instance.img_name,
            counter = idx
        )
        if "type" in shape:
            if shape["type"] == "path":
                points, box = parse_path(shape)

                dSet_object.semantic_points = base64.b64encode(points)
                dSet_object.bounding_box = base64.b64encode(box)

            elif shape["type"] == "rect":
                box = np.array([(float(shape['x0']), float(shape['y0'])),(float(shape['x1']), float(shape['y1']))], dtype=np.float64)
                dSet_object.bounding_box = base64.b64encode(box)
            else: 
                pass ## object not supported 

        elif "path" in shape:
            points, box = parse_path(shape)

            dSet_object.semantic_points = base64.b64encode(points)
            dSet_object.bounding_box = base64.b64encode(box)

        else:
            pass ## object not supported 

        dSet_object.save()

    print(parent_Dset_Instance.img_name, "\n" , [i.counter for i in DSet_object.objects.filter(parent__id = img_id).iterator()])

def update_shape(key, shape, session_state):

    shape_idx, _ = key.split('.')
    shape_idx = int(re.search(r'\d+', shape_idx).group())

    img_id = session_state["img_id"] 
    parent_Dset_Instance = Dset_Instance.objects.get(id = img_id) 

    def parse_path(points):
        points = [p.split(",") for p in points.replace("M", "").replace("Z","").split("L")]
        points = np.array([(float(p0),float(p1)) for p0,p1 in points], dtype=np.float64)

        box = np.array((points.min(axis=0), points.max(axis = 0))).flatten()

        return points, box

    dSet_object = DSet_object.objects.filter(img_name = parent_Dset_Instance.img_name)
    dSet_object = dSet_object.get(counter = shape_idx)

    points, box = parse_path(shape)

    dSet_object.semantic_points = base64.b64encode(points)
    dSet_object.bounding_box = base64.b64encode(box)
    dSet_object.save()


def load_user_labels(dset_Instance):

    selections = []

    ## load previous user labels 
    dSet_objects = DSet_object.objects.filter(parent__id = dset_Instance.id)
    
    for dSet_object in dSet_objects.iterator():
        try:
            points = np.frombuffer(base64.b64decode(dSet_object.semantic_points), dtype=np.float64).astype(int)
            points = points.reshape(-1, 2)
            selections.append("M" + "L".join([",".join(map(str, p)) for p in points.tolist()]) +"Z")
        except Exception as error: 
            print(dSet_object.id)
            continue

    return selections


@app.callback(
    Output("annotations-data-pre", "children"),
    Input("graph-pic", "relayoutData"),
    prevent_initial_call=True,
)
def on_new_annotation(relayout_data, session_state = None):
    print("on_new_annotation called")

    if "shapes" in relayout_data:
        parse_shape(relayout_data["shapes"], session_state)
        return json.dumps(relayout_data["shapes"], indent=2)
    else:
        ## if we are updating a single shape we need to run the following
        for key in relayout_data:
            if "shapes" in key:
                update_shape(key, relayout_data[key], session_state)

        return no_update


@app.callback(Output('graph-pic', 'figure'),
            Input('img-id', 'value'))
def display_output(img_id, session_state = None):
    """
        I am intending this function to be able to load an image and create the figure 
    """
    session_state["img_id"] = img_id

    dset_Instance = Dset_Instance.objects.get(id = img_id)

    img = cv2.cvtColor(cv2.imread(dset_Instance.img_fn), cv2.COLOR_BGR2RGB)

    fig = px.imshow(img, height=800, width=1200, template="plotly_dark")
    fig.update_layout(
        dragmode="drawclosedpath",
        newshape=dict(fillcolor="rgba(125,0,125,.2)", line=dict(color="darkblue", width=2))
    )

    if dset_Instance.completed == 0:
        ## parse the predicted labels from AI 
        selections = parse_pred(dset_Instance.img_name, pred_path=dset_Instance.pred_path)
        ## fig.add_selection(path="M2,6.5L4,7.5L4,6Z") 
        for sel in selections:
            fig.add_shape(path=sel, editable=True)
    else:
        ## pares the user labels 
        selections = load_user_labels(dset_Instance)
        for sel in selections:
            fig.add_shape(path=sel, editable=True)

    return fig