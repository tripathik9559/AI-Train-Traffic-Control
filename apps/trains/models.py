"""
Train Management Models
Represents railway trains with all operational attributes.
"""

from django.db import models
from django.utils import timezone
from apps.authentication.models import User


class Train(models.Model):
    """Core Train model with full operational attributes."""

    class TrainType(models.TextChoices):
        RAJDHANI = 'RAJDHANI', 'Rajdhani Express'
        SHATABDI = 'SHATABDI', 'Shatabdi Express'
        DURONTO = 'DURONTO', 'Duronto Express'
        VANDE_BHARAT = 'VANDE_BHARAT', 'Vande Bharat Express'
        EXPRESS = 'EXPRESS', 'Express'
        MAIL = 'MAIL', 'Mail'
        PASSENGER = 'PASSENGER', 'Passenger'
        FREIGHT = 'FREIGHT', 'Freight'
        SPECIAL = 'SPECIAL', 'Special'

    class Status(models.TextChoices):
        SCHEDULED = 'SCHEDULED', 'Scheduled'
        RUNNING = 'RUNNING', 'Running'
        DELAYED = 'DELAYED', 'Delayed'
        ARRIVED = 'ARRIVED', 'Arrived'
        CANCELLED = 'CANCELLED', 'Cancelled'
        HELD = 'HELD', 'Held'
        MAINTENANCE = 'MAINTENANCE', 'Under Maintenance'

    class Priority(models.IntegerChoices):
        LOWEST = 1, 'Lowest'
        LOW = 2, 'Low'
        NORMAL = 3, 'Normal'
        HIGH = 4, 'High'
        CRITICAL = 5, 'Critical'

    # Basic Information
    train_number = models.CharField(max_length=10, unique=True, db_index=True)
    train_name = models.CharField(max_length=100)
    train_type = models.CharField(max_length=20, choices=TrainType.choices, default=TrainType.EXPRESS)

    # Operational Parameters
    speed = models.FloatField(default=100.0, help_text='Maximum speed in km/h')
    priority_level = models.IntegerField(choices=Priority.choices, default=Priority.NORMAL)
    rake_composition = models.CharField(max_length=200, blank=True, help_text='Coaches/wagons info')
    total_coaches = models.IntegerField(default=12)

    # Route Information
    source_station = models.ForeignKey(
        'stations.Station',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='originating_trains'
    )
    destination_station = models.ForeignKey(
        'stations.Station',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='terminating_trains'
    )
    via_route = models.CharField(max_length=500, blank=True, help_text='Intermediate stations')

    # Timing
    scheduled_departure = models.TimeField(null=True, blank=True)
    scheduled_arrival = models.TimeField(null=True, blank=True)
    days_of_operation = models.CharField(
        max_length=50,
        default='Daily',
        help_text='e.g., Mon,Wed,Fri or Daily'
    )

    # Status
    current_status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED
    )
    current_delay = models.IntegerField(default=0, help_text='Delay in minutes')
    last_known_location = models.CharField(max_length=100, blank=True)

    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_trains'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'trains'
        verbose_name = 'Train'
        verbose_name_plural = 'Trains'
        ordering = ['train_number']
        indexes = [
            models.Index(fields=['train_number']),
            models.Index(fields=['train_type']),
            models.Index(fields=['current_status']),
            models.Index(fields=['priority_level']),
        ]

    def __str__(self):
        return f"{self.train_number} - {self.train_name}"

    @property
    def status_badge_class(self):
        mapping = {
            'SCHEDULED': 'badge-info',
            'RUNNING': 'badge-success',
            'DELAYED': 'badge-warning',
            'ARRIVED': 'badge-primary',
            'CANCELLED': 'badge-danger',
            'HELD': 'badge-secondary',
            'MAINTENANCE': 'badge-dark',
        }
        return mapping.get(self.current_status, 'badge-secondary')

    @property
    def type_color(self):
        mapping = {
            'RAJDHANI': '#e74c3c',
            'SHATABDI': '#3498db',
            'DURONTO': '#9b59b6',
            'VANDE_BHARAT': '#2ecc71',
            'EXPRESS': '#f39c12',
            'MAIL': '#1abc9c',
            'PASSENGER': '#95a5a6',
            'FREIGHT': '#7f8c8d',
            'SPECIAL': '#e91e63',
        }
        return mapping.get(self.train_type, '#95a5a6')

    @property
    def is_delayed(self):
        return self.current_delay > 0 or self.current_status == self.Status.DELAYED

    def get_delay_display(self):
        if self.current_delay == 0:
            return 'On time'
        elif self.current_delay > 0:
            return f'+{self.current_delay} min late'
        else:
            return f'{abs(self.current_delay)} min early'
