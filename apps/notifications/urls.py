from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('',                              views.notification_list,   name='list'),
    path('<int:notif_id>/read/',          views.mark_read,           name='mark_read'),
    path('<int:notif_id>/delete/',        views.delete_notification, name='delete'),
    path('mark-all-read/',               views.mark_all_read,       name='mark_all_read'),
    path('delete-all-read/',             views.delete_all_read,     name='delete_all_read'),
]
