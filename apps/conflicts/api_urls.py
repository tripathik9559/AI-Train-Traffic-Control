from django.urls import path
from . import views

urlpatterns = [
    path('detect/', views.run_detection, name='api_detect'),
    path('report/', views.conflict_report_api, name='api_report'),
    path('<int:conflict_id>/resolve/', views.resolve_conflict, name='api_resolve'),
    path('<int:conflict_id>/acknowledge/', views.acknowledge_conflict, name='api_acknowledge'),
]
