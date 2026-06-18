"""
Analytics Models — KPI snapshots and aggregated metrics.
"""

from django.db import models


class AnalyticsSnapshot(models.Model):
    """Daily analytics snapshot for dashboard charts."""

    date = models.DateField(unique=True)

    # Train metrics
    total_trains = models.IntegerField(default=0)
    trains_running = models.IntegerField(default=0)
    trains_delayed = models.IntegerField(default=0)
    trains_cancelled = models.IntegerField(default=0)
    trains_on_time = models.IntegerField(default=0)

    # Delay metrics
    avg_delay_minutes = models.FloatField(default=0.0)
    max_delay_minutes = models.FloatField(default=0.0)
    total_delay_minutes = models.FloatField(default=0.0)

    # Throughput
    section_throughput = models.FloatField(default=0.0, help_text='Trains/hour')
    punctuality_rate = models.FloatField(default=0.0, help_text='% on time')

    # Conflicts
    conflicts_detected = models.IntegerField(default=0)
    conflicts_resolved = models.IntegerField(default=0)

    # Platform & track utilization
    platform_utilization = models.FloatField(default=0.0, help_text='% utilization')
    track_utilization = models.FloatField(default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analytics_snapshots'
        ordering = ['-date']

    def __str__(self):
        return f"Analytics {self.date}: {self.punctuality_rate:.1f}% punctual"
