from django.contrib import admin
from .models import Schedule, TrackOccupancy

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ['train', 'station', 'scheduled_date', 'status', 'current_delay', 'platform']
    list_filter = ['status', 'scheduled_date']
    search_fields = ['train__train_number', 'station__code']
    ordering = ['scheduled_date', 'scheduled_arrival']

@admin.register(TrackOccupancy)
class TrackOccupancyAdmin(admin.ModelAdmin):
    list_display = ['train', 'track_section', 'entry_time', 'expected_exit_time', 'is_active']
    list_filter = ['is_active']
    ordering = ['-entry_time']
