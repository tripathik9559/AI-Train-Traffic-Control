"""
Scheduling Engine Models
Train schedules, platform/track occupancy tracking.
"""

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator


class Schedule(models.Model):
    """Train schedule at a specific station."""

    class ScheduleStatus(models.TextChoices):
        SCHEDULED = 'SCHEDULED', 'Scheduled'
        RUNNING = 'RUNNING', 'Running'
        ARRIVED = 'ARRIVED', 'Arrived'
        DEPARTED = 'DEPARTED', 'Departed'
        DELAYED = 'DELAYED', 'Delayed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        DIVERTED = 'DIVERTED', 'Diverted'

    train = models.ForeignKey(
        'trains.Train',
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    station = models.ForeignKey(
        'stations.Station',
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    platform = models.ForeignKey(
        'stations.Platform',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='schedules'
    )
    track_section = models.ForeignKey(
        'stations.TrackSection',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='schedules'
    )
    route = models.ForeignKey(
        'stations.Route',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='schedules'
    )

    # Scheduling date
    scheduled_date = models.DateField()
    stop_sequence = models.IntegerField(default=1, validators=[MinValueValidator(1)])

    # Scheduled times
    scheduled_arrival = models.DateTimeField(null=True, blank=True)
    scheduled_departure = models.DateTimeField(null=True, blank=True)

    # Actual times (updated during operations)
    actual_arrival = models.DateTimeField(null=True, blank=True)
    actual_departure = models.DateTimeField(null=True, blank=True)

    # Delay tracking
    arrival_delay = models.IntegerField(default=0, help_text='Delay in minutes (positive=late)')
    departure_delay = models.IntegerField(default=0, help_text='Delay in minutes')
    current_delay = models.IntegerField(default=0)

    # Status
    status = models.CharField(
        max_length=20,
        choices=ScheduleStatus.choices,
        default=ScheduleStatus.SCHEDULED
    )

    # Halt information
    halt_duration = models.IntegerField(default=2, help_text='Halt duration in minutes')
    is_originating = models.BooleanField(default=False)
    is_terminating = models.BooleanField(default=False)

    # Distance from origin
    distance_from_origin = models.FloatField(default=0.0)

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'schedules'
        verbose_name = 'Schedule'
        verbose_name_plural = 'Schedules'
        ordering = ['scheduled_date', 'scheduled_arrival']
        indexes = [
            models.Index(fields=['scheduled_date']),
            models.Index(fields=['status']),
            models.Index(fields=['train', 'scheduled_date']),
            models.Index(fields=['station', 'scheduled_date']),
        ]

    def __str__(self):
        return f"{self.train.train_number} at {self.station.code} on {self.scheduled_date}"

    @property
    def arrival_time(self):
        return self.actual_arrival or self.scheduled_arrival

    @property
    def departure_time(self):
        return self.actual_departure or self.scheduled_departure

    @property
    def is_on_time(self):
        return self.current_delay <= 5

    @property
    def delay_display(self):
        if self.current_delay == 0:
            return 'On time'
        elif self.current_delay > 0:
            return f'+{self.current_delay} min'
        else:
            return f'{self.current_delay} min'

    def update_delay(self):
        """Recalculate current delay."""
        if self.actual_arrival and self.scheduled_arrival:
            diff = self.actual_arrival - self.scheduled_arrival
            self.arrival_delay = int(diff.total_seconds() / 60)

        if self.actual_departure and self.scheduled_departure:
            diff = self.actual_departure - self.scheduled_departure
            self.departure_delay = int(diff.total_seconds() / 60)

        self.current_delay = max(self.arrival_delay, self.departure_delay)
        self.save(update_fields=['arrival_delay', 'departure_delay', 'current_delay'])

        # Update train delay
        self.train.current_delay = self.current_delay
        if self.current_delay > 5:
            self.train.current_status = 'DELAYED'
        self.train.save(update_fields=['current_delay', 'current_status'])


class TrackOccupancy(models.Model):
    """Real-time track section occupancy tracking."""

    track_section = models.ForeignKey(
        'stations.TrackSection',
        on_delete=models.CASCADE,
        related_name='occupancies'
    )
    train = models.ForeignKey(
        'trains.Train',
        on_delete=models.CASCADE,
        related_name='track_occupancies'
    )
    schedule = models.ForeignKey(
        Schedule,
        on_delete=models.CASCADE,
        related_name='track_occupancies',
        null=True, blank=True
    )
    entry_time = models.DateTimeField()
    expected_exit_time = models.DateTimeField()
    actual_exit_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'track_occupancies'
        verbose_name = 'Track Occupancy'
        verbose_name_plural = 'Track Occupancies'
        ordering = ['-entry_time']

    def __str__(self):
        return f"{self.train.train_number} on {self.track_section.code}"
