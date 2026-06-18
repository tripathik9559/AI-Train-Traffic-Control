from django.urls import path
from . import views

app_name = 'scheduling'

urlpatterns = [
    path('', views.schedule_list, name='list'),
    path('add/', views.schedule_create, name='create'),
    path('<int:schedule_id>/edit/', views.schedule_edit, name='edit'),
    path('<int:schedule_id>/time/', views.update_actual_time, name='update_time'),
]
