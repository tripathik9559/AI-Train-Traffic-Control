from django.urls import path
from . import views

app_name = 'simulation'

urlpatterns = [
    path('', views.simulation_index, name='index'),
    path('realtime/', views.realtime_simulator, name='realtime'),
    path('run/', views.run_simulation, name='run'),
    path('<int:sim_id>/', views.simulation_detail, name='detail'),
]
