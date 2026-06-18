"""
Station & Route Management Models
Covers stations, platforms, routes, and track sections.
"""

from django.db import models
from django.utils import timezone


class Station(models.Model):
    """Railway station model."""

    class StationType(models.TextChoices):
        JUNCTION = 'JUNCTION', 'Junction'
        TERMINAL = 'TERMINAL', 'Terminal'
        HALT = 'HALT', 'Halt'
        CROSSING = 'CROSSING', 'Crossing Station'
        MAJOR = 'MAJOR', 'Major Station'

    name = models.CharField(max_length=150)
    code = models.CharField(max_length=10, unique=True, db_index=True)
    station_type = models.CharField(max_length=20, choices=StationType.choices, default=StationType.JUNCTION)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zone = models.CharField(max_length=50, blank=True, help_text='Railway zone e.g. NR, NCR')
    division = models.CharField(max_length=50, blank=True)

    # Geographic coordinates for visualization
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)

    # Operational details
    total_platforms = models.IntegerField(default=1)
    is_junction = models.BooleanField(default=False)
    has_goods_shed = models.BooleanField(default=False)
    has_fuel_point = models.BooleanField(default=False)
    elevation = models.FloatField(default=0.0, help_text='Elevation in meters')

    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'stations'
        verbose_name = 'Station'
        verbose_name_plural = 'Stations'
        ordering = ['name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['zone']),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def coordinates(self):
        return {'lat': self.latitude, 'lng': self.longitude}

    @property
    def active_platforms(self):
        return self.platforms.filter(is_active=True)

    @property
    def available_platforms(self):
        return self.platforms.filter(is_active=True, status='AVAILABLE')


class Platform(models.Model):
    """Station platform model."""

    class PlatformType(models.TextChoices):
        ARRIVAL = 'ARRIVAL', 'Arrival'
        DEPARTURE = 'DEPARTURE', 'Departure'
        BOTH = 'BOTH', 'Arrival & Departure'
        GOODS = 'GOODS', 'Goods'

    class PlatformStatus(models.TextChoices):
        AVAILABLE = 'AVAILABLE', 'Available'
        OCCUPIED = 'OCCUPIED', 'Occupied'
        MAINTENANCE = 'MAINTENANCE', 'Under Maintenance'
        CLOSED = 'CLOSED', 'Closed'

    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='platforms')
    platform_number = models.CharField(max_length=10)
    platform_type = models.CharField(max_length=20, choices=PlatformType.choices, default=PlatformType.BOTH)
    length = models.FloatField(default=500.0, help_text='Platform length in meters')
    status = models.CharField(max_length=20, choices=PlatformStatus.choices, default=PlatformStatus.AVAILABLE)
    has_shelter = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'platforms'
        verbose_name = 'Platform'
        verbose_name_plural = 'Platforms'
        unique_together = ('station', 'platform_number')
        ordering = ['station', 'platform_number']

    def __str__(self):
        return f"Platform {self.platform_number} — {self.station.name}"

    @property
    def is_available(self):
        return self.status == self.PlatformStatus.AVAILABLE and self.is_active


class Route(models.Model):
    """Train route between two stations."""

    name = models.CharField(max_length=200)
    source_station = models.ForeignKey(
        Station, on_delete=models.CASCADE,
        related_name='routes_from'
    )
    destination_station = models.ForeignKey(
        Station, on_delete=models.CASCADE,
        related_name='routes_to'
    )
    distance = models.FloatField(help_text='Distance in kilometers')
    estimated_duration = models.IntegerField(help_text='Estimated travel time in minutes')
    via_stations = models.JSONField(default=list, blank=True, help_text='List of intermediate station codes')
    max_speed = models.FloatField(default=130.0, help_text='Maximum permitted speed on route')
    is_electrified = models.BooleanField(default=True)
    is_double_line = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'routes'
        verbose_name = 'Route'
        verbose_name_plural = 'Routes'
        ordering = ['name']

    def __str__(self):
        return f"{self.source_station.code} → {self.destination_station.code} ({self.distance} km)"

    @property
    def average_speed(self):
        if self.estimated_duration > 0:
            return round((self.distance / self.estimated_duration) * 60, 1)
        return 0


class TrackSection(models.Model):
    """Individual track section between two stations."""

    class TrackStatus(models.TextChoices):
        CLEAR = 'CLEAR', 'Clear'
        OCCUPIED = 'OCCUPIED', 'Occupied'
        BLOCKED = 'BLOCKED', 'Blocked'
        MAINTENANCE = 'MAINTENANCE', 'Under Maintenance'
        SIGNAL_FAILURE = 'SIGNAL_FAILURE', 'Signal Failure'

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    from_station = models.ForeignKey(
        Station, on_delete=models.CASCADE,
        related_name='sections_from'
    )
    to_station = models.ForeignKey(
        Station, on_delete=models.CASCADE,
        related_name='sections_to'
    )
    length = models.FloatField(help_text='Section length in kilometers')
    number_of_lines = models.IntegerField(default=2, help_text='Number of parallel tracks')
    max_speed = models.FloatField(default=130.0)
    capacity = models.IntegerField(default=1, help_text='Max simultaneous trains')
    status = models.CharField(max_length=20, choices=TrackStatus.choices, default=TrackStatus.CLEAR)
    is_electrified = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    last_maintenance = models.DateField(null=True, blank=True)
    next_maintenance = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'track_sections'
        verbose_name = 'Track Section'
        verbose_name_plural = 'Track Sections'
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.name} ({self.from_station.code}—{self.to_station.code})"

    @property
    def is_clear(self):
        return self.status == self.TrackStatus.CLEAR

    @property
    def status_color(self):
        colors = {
            'CLEAR': '#2ecc71',
            'OCCUPIED': '#f39c12',
            'BLOCKED': '#e74c3c',
            'MAINTENANCE': '#3498db',
            'SIGNAL_FAILURE': '#9b59b6',
        }
        return colors.get(self.status, '#95a5a6')
