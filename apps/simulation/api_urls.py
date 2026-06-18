from django.urls import path
from . import views

urlpatterns = [
    path('run/', views.run_simulation, name='api_run'),
    path('state/', views.realtime_state_api, name='api_state'),
]
