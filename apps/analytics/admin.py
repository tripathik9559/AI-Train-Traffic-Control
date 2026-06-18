from django.contrib import admin
from .models import AnalyticsSnapshot

@admin.register(AnalyticsSnapshot)
class AnalyticsSnapshotAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_trains', 'punctuality_rate', 'avg_delay_minutes', 'conflicts_detected']
    ordering = ['-date']
