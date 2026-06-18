from django.urls import path
from . import views

urlpatterns = [
    path('unread-count/',          views.api_unread_count, name='api_unread_count'),
    path('stats/',                 views.api_stats,        name='api_stats'),
    path('<int:notif_id>/read/',   views.mark_read,        name='api_mark_read'),
    path('mark-all/',              views.mark_all_read,    name='api_mark_all'),
]
