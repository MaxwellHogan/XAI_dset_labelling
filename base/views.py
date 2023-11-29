from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.forms import formset_factory
# Create your views here.

from .models import Dset_Instance, DSet_object
from .forms import Discriminative_Features_Form

from django.core.handlers.wsgi import WSGIRequest

import cv2
import numpy as np
import pickle
import base64

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
    dset_Instance = Dset_Instance.objects.filter(completed = 0).first()

    print(dset_Instance)

    return redirect('semantic_ann_page', pk = dset_Instance.id)

