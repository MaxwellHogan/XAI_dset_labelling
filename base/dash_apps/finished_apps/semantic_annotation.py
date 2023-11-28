import plotly.express as px
from dash import no_update, html, dcc
from dash.dependencies import Input, Output
from django_plotly_dash import DjangoDash
from skimage import data
import json
import cv2
import numpy as np
import pickle 
import base64

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
fig.update_layout(dragmode="drawclosedpath")
config = {
    "modeBarButtonsToAdd": [
        "drawline",
        "drawopenpath",
        "drawclosedpath",
        "drawcircle",
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

def parse_shape(shapes : list, session_state):

    img_id = session_state["img_id"] 

    ## delete old instances 
    DSet_object.objects.filter(parent__id = img_id).delete()

    for idx, shape in enumerate(shapes):
        ## set up dataset onject - connect it to it's parent (the file)
        dSet_object = DSet_object(
            parent = Dset_Instance.objects.get(id = img_id)
        )

        if shape["type"] == "path":

            points = shape["path"]
            points = [p.split(",") for p in points.replace("M", "").replace("Z","").split("L")]
            points = np.array([(float(p0),float(p1)) for p0,p1 in points], dtype=np.float64)
            print(points.shape)
            dSet_object.semantic_points = base64.b64encode(points)

            box = np.array((points.min(axis=0), points.max(axis =0 ))).flatten()
            dSet_object.bounding_box = base64.b64encode(box)

        elif shape["type"] == "rect":
            box = np.array([(float(shape['x0']), float(shape['y0'])),(float(shape['x1']), float(shape['y1']))], dtype=np.float64)
            dSet_object.bounding_box = base64.b64encode(box)
        else: 
            pass ## object not supported 

        dSet_object.save()


@app.callback(
    Output("annotations-data-pre", "children"),
    Input("graph-pic", "relayoutData"),
    prevent_initial_call=True,
)
def on_new_annotation(relayout_data, session_state = None):

    if "shapes" in relayout_data:
        parse_shape(relayout_data["shapes"], session_state)
        return json.dumps(relayout_data["shapes"], indent=2)
    else:
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

    fig = px.imshow(img, height=800, width=1200)
    fig.update_layout(dragmode="drawclosedpath")

    return fig