from django.urls import path
from . import views

urlpatterns = [
    path('rank/', views.api_rank_trains, name='api_rank_trains'),
    path('priority/<int:train_id>/', views.api_priority_score, name='api_priority_score'),
]
