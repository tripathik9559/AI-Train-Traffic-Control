from django.urls import path
from . import views

urlpatterns = [
    path('', views.api_trains_list, name='api_trains_list'),
    path('<int:train_id>/status/', views.update_train_status, name='api_update_status'),
]
