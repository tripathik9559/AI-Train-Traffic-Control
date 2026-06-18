from django.urls import path
from . import views

urlpatterns = [
    path('delay-trend/', views.api_delay_trend, name='api_delay_trend'),
    path('throughput/', views.api_throughput_chart, name='api_throughput'),
    path('train-types/', views.api_train_type_distribution, name='api_train_types'),
    path('conflicts/', views.api_conflict_stats, name='api_conflict_stats'),
    path('platforms/', views.api_platform_utilization, name='api_platforms'),
    path('kpis/', views.api_kpi_summary, name='api_kpis'),
    path('sections/', views.api_section_status, name='api_sections'),
]
