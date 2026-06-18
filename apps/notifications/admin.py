from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['notification_type', 'priority', 'title', 'user', 'is_read', 'created_at']
    list_filter = ['notification_type', 'priority', 'is_read', 'is_broadcast']
    ordering = ['-created_at']
