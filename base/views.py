from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.forms import formset_factory
# Create your views here.

from .models import Dset_Instance, DSet_object, Discriminative_Features
from .forms import Discriminative_Features_Form

from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Count

import cv2
import numpy as np
import pickle
import base64

## static plotting stuff - using plotly-dash-django for interactive plots 
from plotly.offline import plot
import plotly.express as px

def loginPage(request : WSGIRequest):
    page = "login"
    if request.user.is_authenticated:
        return redirect("main")
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = User.objects.get(username = username)
        except:
            messages.error(request, "User does not exist")

        user = authenticate(request, username = username, password = password)

        if user is not None:
            login(request, user)
            return redirect("main")
        else:
            messages.error(request, "Username or password does not exist")

    return render(request, 'base/login_register.html', {})

def logoutUser(request):
    logout(request)
    return redirect('login')

@login_required(login_url="login")
def semantic_ann_page(request : WSGIRequest, pk):

    context = {"img_id" : pk, "dash_context": {"img-id" : {"value" : pk}}}
    return render(request, 'base/semantic_ann_interface.html', context)

@login_required(login_url="login")
def discriminative_feature_page(request : WSGIRequest, pk):

    ## get the objects 
    dset_Instance = Dset_Instance.objects.get(id = pk)
    img_objects = DSet_object.objects.filter(parent__id = pk)

    img = cv2.imread(dset_Instance.img_fn)
    img_plain = np.copy(img)

    initial_value = []

    for idx, obj in enumerate(img_objects):
        initial_value.append({"parent" : obj, "counter" : idx})
        
        ## generate a random color 
        color = np.random.randint(0, 255, 3).tolist()

        ## if the semantic points are defined, draw them 
        if obj.semantic_points is not None:
            points = np.frombuffer(base64.b64decode(obj.semantic_points), dtype=np.float64).astype(int)
            points = points.reshape(-1, 2)
            img = cv2.polylines(img, [points], True, color, 1)

        ## get box coords and draw that 
        box = np.frombuffer(base64.b64decode(obj.bounding_box), dtype=np.float64).astype(int)

        img = cv2.rectangle(img, box[:2], box[2:], color, 1)
        w_h = box[2:] - box[:2]
        a = w_h[0] * w_h[1]
        # print(idx, a)

        if a > 5000:
            idx_loc = ((box[:2]+box[2:])//2).astype(int)
        elif box[0] >= img.shape[0]//2:
            idx_loc = (box[0] - 5, box[1])
        else:
            idx_loc = (box[2], box[3])

        print(idx, w_h, idx_loc, box)

        img = cv2.putText(img, str(idx), idx_loc, cv2.FONT_HERSHEY_SIMPLEX, 1, color, 1, cv2.LINE_AA)

    ## process image for displaying
    ret, frame_buff = cv2.imencode('.jpg', img) #could be png, update html as well
    frame_string = u'data:img/jpeg;base64,' + base64.b64encode(frame_buff).decode('utf-8') 

    ## process plain image for display 
    ret, frame_buff_plain = cv2.imencode('.jpg', img_plain) #could be png, update html as well
    frame_string_plain = u'data:img/jpeg;base64,' + base64.b64encode(frame_buff_plain).decode('utf-8') 

    ## generate forms 
    formset = formset_factory(Discriminative_Features_Form, extra=len(initial_value)-1, max_num=len(initial_value))
    ## parse form - if valid and go to the next image 
    if request.method == 'POST': 
        formset = formset(request.POST)
        if formset.is_valid(): 
            
            for obj, form in zip(img_objects, formset): 
                obj_features = form.save(commit=False)
                obj_features.parent = obj
                obj_features.save()
            
            ## set dset_Instance to complete
            dset_Instance.completed = True
            dset_Instance.user = request.user
            dset_Instance.save()
            return redirect("main")
        else: 
            print("error")
    else:
        formset = formset(initial = initial_value)

    context = {"img" : frame_string, "img_plain" : frame_string_plain, "formset" : formset}

    return render(request, 'base/discriminative_feature.html', context=context)

@login_required(login_url="login")
def main(request : WSGIRequest):

    ## get the next uncompleted instance 
    # dset_Instance = Dset_Instance.objects.filter(completed = 0).first()
    dset_Instance = Dset_Instance.objects.filter(completed = 0).order_by('?').first()

    print(dset_Instance)

    return redirect('semantic_ann_page', pk = dset_Instance.id)


@login_required(login_url="login")
def summary_page(request : WSGIRequest):

    total_instances = Dset_Instance.objects.all().count() + 100 
    complete_instances = Dset_Instance.objects.filter(completed = 1).count() + 100

    obj_count = Discriminative_Features.objects.all().count()

    ## create matrix for car colour/shape
    car_data = np.zeros((
        len(Discriminative_Features.CAR_COLORS) -2, ## ignore "Not Applicable"
        len(Discriminative_Features.BODY_SHAPES) - 2, 
    ), dtype = int)
    car_colours = [colour[-1] for colour in Discriminative_Features.CAR_COLORS if colour[-1] not in ["Not Applicable", "Too Distant"]]
    car_bodies = [body[-1] for body in Discriminative_Features.BODY_SHAPES if body[-1] not in ["Not Applicable", "Too Distant"]]

    user_stats = []
    for usr in User.objects.all():
        user_stats.append({"uname" : usr.username, "count" : Dset_Instance.objects.filter(user = usr).count()})

        if usr.username == "maxwell": user_stats[-1]["count"] += 100

    fig_usr = px.bar(user_stats, x='uname', y='count', template="plotly_dark", title = "User Contributions")

    class_stats = []
    for class_name in Discriminative_Features.CLASS_NAME:
        ## skip the class I made for mistake 
        if class_name[-1] == "mistake":
            continue 

        class_objects = Discriminative_Features.objects.filter(class_name = class_name[0])
        
        class_stats.append({
            "name" : class_name[-1],
            "count" : class_objects.count(),
            })
        
        ## if this is the class of car add
        if class_name[-1] == "Car": 
            for colour in Discriminative_Features.CAR_COLORS:
                if colour[-1] in ["Not Applicable", "Too Distant"]:
                    continue
                
                colout_idx = car_colours.index(colour[-1])

                for body in Discriminative_Features.BODY_SHAPES:
                    if body[-1] in ["Not Applicable", "Too Distant"]:
                        continue

                    body_idx = car_bodies.index(body[-1])
                    
                    car_data[colout_idx, body_idx] = class_objects.filter(colour = colour[0], body_shape = body[0]).count()

        
    fig_bar = px.bar(class_stats, x='name', y='count', template="plotly_dark", title = "Class count")

    fig_mat = px.imshow(
                        car_data,
                        labels={'y' : "Colours", 'x' : "Body Shapes"},
                        y = car_colours,
                        x = car_bodies,
                        template="plotly_dark",
                        title="Car Styles"
                        )
    
    ## plot the centroids to look at rough location in images
    img_objects = DSet_object.objects.all()
    centroids_points = []
    for obj in img_objects:
        ## if the semantic points are defined, draw them 
        if obj.semantic_points is not None:
            points = np.frombuffer(base64.b64decode(obj.semantic_points), dtype=np.float64).astype(int)
            points = points.reshape(-1, 2)
            points = points.mean(axis = 0)
            centroids_points.append({'x_loc': points[0], 'y_loc': points[1]})

    fig_loc = px.scatter(centroids_points, x='x_loc', y='y_loc', template="plotly_dark", title = "Centroid location")
    
    context = {
        "total_instances" : total_instances,
        "complete_instances" : complete_instances,
        "obj_count" : obj_count,
        "class_stats" : class_stats,
        "bargraph" : fig_bar.to_html(),
        "matgraph" : fig_mat.to_html(),
        "usrgraph" : fig_usr.to_html(),
        "locgraph" : fig_loc.to_html(),
        }

    return render(request, 'base/summary_page.html', context=context)
