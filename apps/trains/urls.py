from django.urls import path
from . import views

app_name = 'trains'

urlpatterns = [
    path('', views.train_list, name='list'),
    path('add/', views.train_create, name='create'),
    path('<int:train_id>/', views.train_detail, name='detail'),
    path('<int:train_id>/edit/', views.train_edit, name='edit'),
    path('<int:train_id>/delete/', views.train_delete, name='delete'),
    path('<int:train_id>/status/', views.update_train_status, name='update_status'),
]
