from django.urls import path
from . import views

app_name = 'conflicts'

urlpatterns = [
    path('', views.conflict_list, name='list'),
    path('<int:conflict_id>/', views.conflict_detail, name='detail'),
    path('detect/', views.run_detection, name='detect'),
    path('<int:conflict_id>/resolve/', views.resolve_conflict, name='resolve'),
    path('<int:conflict_id>/acknowledge/', views.acknowledge_conflict, name='acknowledge'),
]
