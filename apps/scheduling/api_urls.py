from django.urls import path
from . import views

urlpatterns = [
    path('today/', views.api_today_schedules, name='api_today_schedules'),
    path('<int:schedule_id>/time/', views.update_actual_time, name='api_update_time'),
]
