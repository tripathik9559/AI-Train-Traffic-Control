from django.urls import path
from . import views

urlpatterns = [
    path('', views.api_stations_json, name='api_stations'),
    path('sections/', views.api_sections_json, name='api_sections'),
    path('sections/<int:section_id>/status/', views.update_section_status, name='api_section_status'),
]
