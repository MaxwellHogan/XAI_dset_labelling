## this file is not create automatically - had to create it
## the purpose of this file is store the urls for the 'base' app

from django.urls import path
from . import views
from base.dash_apps.finished_apps import semantic_annotation ## add plotly app 

urlpatterns = [
    path('', views.loginPage, name="login"), ## default to the login page 
    path('logout/', views.logoutUser, name="logout"),
    path('main/', views.main, name ="main"),
    path('semantic_ann_page/<slug:pk>/', views.semantic_ann_page, name ="semantic_ann_page"),
    path('discriminative_feature_page/<slug:pk>/', views.discriminative_feature_page, name ="discriminative_feature_page")
]