from django.urls import path
from . import views

app_name = 'reporting'

urlpatterns = [
    path('', views.report_index, name='index'),
    path('daily/', views.generate_daily_report, name='daily'),
    path('conflicts/', views.generate_conflict_report, name='conflicts'),
    path('trains/', views.generate_train_report, name='trains'),
]
