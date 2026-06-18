from django.urls import path
from . import views

app_name = 'ai_engine'

urlpatterns = [
    path('', views.priority_dashboard, name='dashboard'),
    path('train/<int:train_id>/', views.analyze_train_priority, name='train_analysis'),
    path('conflict/<int:conflict_id>/', views.conflict_analysis, name='conflict_analysis'),
    path('throughput/', views.throughput_optimizer, name='throughput'),
    path('recommendation/<int:rec_id>/accept/', views.accept_recommendation, name='accept_rec'),
    path('recommendation/<int:rec_id>/reject/', views.reject_recommendation, name='reject_rec'),
]
