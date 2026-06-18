"""
Conflict Detection Models
Tracks conflicts between trains and AI recommendations.
"""

from django.db import models
from django.utils import timezone


class Conflict(models.Model):
    """Detected conflict between trains."""

    class ConflictType(models.TextChoices):
        TRACK = 'TRACK', 'Track Conflict'
        PLATFORM = 'PLATFORM', 'Platform Conflict'
        CROSSING = 'CROSSING', 'Crossing Conflict'
        OCCUPANCY = 'OCCUPANCY', 'Section Occupancy'
        HEADWAY = 'HEADWAY', 'Headway Violation'

    class Severity(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical'

    class ConflictStatus(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        ACKNOWLEDGED = 'ACKNOWLEDGED', 'Acknowledged'
        RESOLVED = 'RESOLVED', 'Resolved'
        FALSE_ALARM = 'FALSE_ALARM', 'False Alarm'

    conflict_type = models.CharField(max_length=20, choices=ConflictType.choices)
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.MEDIUM)
    status = models.CharField(max_length=20, choices=ConflictStatus.choices, default=ConflictStatus.ACTIVE)

    # Involved trains
    train_a = models.ForeignKey(
        'trains.Train',
        on_delete=models.CASCADE,
        related_name='conflicts_as_a'
    )
    train_b = models.ForeignKey(
        'trains.Train',
        on_delete=models.CASCADE,
        related_name='conflicts_as_b',
        null=True, blank=True
    )

    # Location of conflict
    track_section = models.ForeignKey(
        'stations.TrackSection',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='conflicts'
    )
    platform = models.ForeignKey(
        'stations.Platform',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='conflicts'
    )
    station = models.ForeignKey(
        'stations.Station',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='conflicts'
    )

    # Timing
    conflict_time = models.DateTimeField(help_text='When the conflict occurs/occurred')
    detected_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    # Details
    description = models.TextField()
    resolution_notes = models.TextField(blank=True)
    resolved_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='resolved_conflicts'
    )

    class Meta:
        db_table = 'conflicts'
        verbose_name = 'Conflict'
        verbose_name_plural = 'Conflicts'
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['severity']),
            models.Index(fields=['conflict_type']),
            models.Index(fields=['detected_at']),
        ]

    def __str__(self):
        trains = f"{self.train_a.train_number}"
        if self.train_b:
            trains += f" vs {self.train_b.train_number}"
        return f"{self.get_conflict_type_display()} - {trains}"

    @property
    def severity_color(self):
        colors = {
            'LOW': '#2ecc71',
            'MEDIUM': '#f39c12',
            'HIGH': '#e67e22',
            'CRITICAL': '#e74c3c',
        }
        return colors.get(self.severity, '#95a5a6')

    @property
    def age_minutes(self):
        delta = timezone.now() - self.detected_at
        return int(delta.total_seconds() / 60)

    def resolve(self, user, notes=''):
        self.status = self.ConflictStatus.RESOLVED
        self.resolved_at = timezone.now()
        self.resolved_by = user
        self.resolution_notes = notes
        self.save()


class Recommendation(models.Model):
    """AI-generated recommendation for conflict resolution or train management."""

    class RecommendationType(models.TextChoices):
        PRIORITY = 'PRIORITY', 'Train Priority Order'
        HOLD = 'HOLD', 'Hold Train'
        CROSS = 'CROSS', 'Crossing Order'
        PLATFORM_CHANGE = 'PLATFORM_CHANGE', 'Platform Change'
        SPEED_ADJUST = 'SPEED_ADJUST', 'Speed Adjustment'
        ROUTE_DIVERT = 'ROUTE_DIVERT', 'Route Diversion'

    class RecommendationStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        REJECTED = 'REJECTED', 'Rejected'
        IMPLEMENTED = 'IMPLEMENTED', 'Implemented'

    conflict = models.ForeignKey(
        Conflict,
        on_delete=models.CASCADE,
        related_name='recommendations',
        null=True, blank=True
    )
    recommendation_type = models.CharField(max_length=30, choices=RecommendationType.choices)
    status = models.CharField(
        max_length=20,
        choices=RecommendationStatus.choices,
        default=RecommendationStatus.PENDING
    )

    # Trains involved
    primary_train = models.ForeignKey(
        'trains.Train',
        on_delete=models.CASCADE,
        related_name='primary_recommendations'
    )
    secondary_train = models.ForeignKey(
        'trains.Train',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='secondary_recommendations'
    )

    # Recommendation details
    title = models.CharField(max_length=200)
    description = models.TextField()
    reasoning = models.TextField(help_text='AI explanation for this recommendation')
    priority_score = models.FloatField(default=5.0)
    confidence = models.FloatField(default=0.85, help_text='Confidence 0-1')
    estimated_benefit = models.CharField(max_length=200, blank=True)

    # Metadata
    generated_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    accepted_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='accepted_recommendations'
    )
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'recommendations'
        verbose_name = 'Recommendation'
        verbose_name_plural = 'Recommendations'
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['generated_at']),
        ]

    def __str__(self):
        return f"{self.get_recommendation_type_display()} for {self.primary_train.train_number}"

    @property
    def confidence_percentage(self):
        return round(self.confidence * 100, 1)
