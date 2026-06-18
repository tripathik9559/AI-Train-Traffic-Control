from django.contrib import admin
from .models import Station, Platform, Route, TrackSection

@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'city', 'zone', 'station_type', 'total_platforms', 'is_active']
    list_filter = ['zone', 'station_type', 'is_junction']
    search_fields = ['name', 'code', 'city']
    ordering = ['name']

@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ['station', 'platform_number', 'platform_type', 'status', 'length']
    list_filter = ['status', 'platform_type']

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ['name', 'source_station', 'destination_station', 'distance', 'estimated_duration']
    ordering = ['name']

@admin.register(TrackSection)
class TrackSectionAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'from_station', 'to_station', 'status', 'length', 'number_of_lines']
    list_filter = ['status', 'number_of_lines', 'is_electrified']
    search_fields = ['code', 'name']
