"""
Railway Control System - Main URL Configuration
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect


def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    return redirect('auth:login')


urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # Home redirect
    path('', home_redirect, name='home'),

    # Authentication Module
    path('auth/', include('apps.authentication.urls', namespace='auth')),

    # Dashboard
    path('dashboard/', include('apps.analytics.urls', namespace='dashboard')),

    # Train Management
    path('trains/', include('apps.trains.urls', namespace='trains')),

    # Station & Route Management
    path('stations/', include('apps.stations.urls', namespace='stations')),

    # Scheduling Engine
    path('scheduling/', include('apps.scheduling.urls', namespace='scheduling')),

    # Conflict Detection
    path('conflicts/', include('apps.conflicts.urls', namespace='conflicts')),

    # AI Engine
    path('ai-engine/', include('apps.ai_engine.urls', namespace='ai_engine')),

    # ML Prediction
    path('ml-prediction/', include('apps.ml_prediction.urls', namespace='ml_prediction')),

    # Simulation
    path('simulation/', include('apps.simulation.urls', namespace='simulation')),

    # Notifications
    path('notifications/', include('apps.notifications.urls', namespace='notifications')),

    # Reporting
    path('reports/', include('apps.reporting.urls', namespace='reporting')),

    # Network Visualizer (served via trains urls)
    path('network/', include('apps.trains.urls_network', namespace='network')),

    # REST API
    path('api/trains/', include('apps.trains.api_urls')),
    path('api/stations/', include('apps.stations.api_urls')),
    path('api/scheduling/', include('apps.scheduling.api_urls')),
    path('api/conflicts/', include('apps.conflicts.api_urls')),
    path('api/ai-engine/', include('apps.ai_engine.api_urls')),
    path('api/ml/', include('apps.ml_prediction.api_urls')),
    path('api/simulation/', include('apps.simulation.api_urls')),
    path('api/analytics/', include('apps.analytics.api_urls')),
    path('api/notifications/', include('apps.notifications.api_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin customization
admin.site.site_header = "Railway Control System — Admin"
admin.site.site_title = "Railway Control Admin"
admin.site.index_title = "Railway Control Management"
