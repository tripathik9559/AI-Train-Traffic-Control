from django.urls import path
from . import views

app_name = 'network'

urlpatterns = [
    path('', views.network_visualizer, name='visualizer'),
]
