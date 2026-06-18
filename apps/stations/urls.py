from django.urls import path
from . import views

app_name = 'stations'

urlpatterns = [
    path('', views.station_list, name='list'),
    path('add/', views.station_create, name='create'),
    path('<int:station_id>/', views.station_detail, name='detail'),
    path('<int:station_id>/edit/', views.station_edit, name='edit'),
    path('routes/', views.route_list, name='routes'),
    path('routes/add/', views.route_create, name='route_create'),
    path('sections/', views.track_section_list, name='sections'),
    path('sections/add/', views.track_section_create, name='section_create'),
    path('sections/<int:section_id>/status/', views.update_section_status, name='section_status'),
]
