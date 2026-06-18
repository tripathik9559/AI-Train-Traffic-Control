"""
Scenario Simulation Models
Stores simulation configurations and results.
"""

from django.db import models
from apps.authentication.models import User


class Simulation(models.Model):
    """A simulation scenario configured by a controller."""

    class ScenarioType(models.TextChoices):
        TRAIN_DELAY = 'TRAIN_DELAY', 'Train Delay Simulation'
        PLATFORM_FAILURE = 'PLATFORM_FAILURE', 'Platform Failure'
        MAINTENANCE_BLOCK = 'MAINTENANCE_BLOCK', 'Maintenance Block'
        SIGNAL_FAILURE = 'SIGNAL_FAILURE', 'Signal Failure'
        HEAVY_RAIN = 'HEAVY_RAIN', 'Heavy Rain / Flooding'
        ROUTE_CONGESTION = 'ROUTE_CONGESTION', 'Route Congestion'
        MASS_DELAY = 'MASS_DELAY', 'Mass Delay Cascade'
        CUSTOM = 'CUSTOM', 'Custom Scenario'

    class SimulationStatus(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        RUNNING = 'RUNNING', 'Running'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    name = models.CharField(max_length=200)
    scenario_type = models.CharField(max_length=30, choices=ScenarioType.choices)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=SimulationStatus.choices, default=SimulationStatus.DRAFT)

    # Configuration
    affected_trains = models.ManyToManyField('trains.Train', blank=True, related_name='simulations')
    affected_sections = models.ManyToManyField('stations.TrackSection', blank=True)
    affected_stations = models.ManyToManyField('stations.Station', blank=True)
    delay_minutes = models.IntegerField(default=30, help_text='Simulated delay in minutes')
    duration_hours = models.FloatField(default=2.0, help_text='Scenario duration in hours')
    simulation_speed = models.FloatField(default=1.0, help_text='1x = real time, 10x = 10x speed')

    # Parameters
    parameters = models.JSONField(default=dict, blank=True)

    # Results
    result_summary = models.TextField(blank=True)
    throughput_impact = models.FloatField(null=True, blank=True, help_text='% throughput reduction')
    trains_affected_count = models.IntegerField(null=True, blank=True)
    estimated_recovery_time = models.IntegerField(null=True, blank=True, help_text='Minutes to recover')
    recommendations = models.TextField(blank=True)

    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='simulations')
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'simulations'
        verbose_name = 'Simulation'
        verbose_name_plural = 'Simulations'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_scenario_type_display()})"

    @property
    def duration_display(self):
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return f"{int(delta.total_seconds())}s"
        return '—'


class SimulationResult(models.Model):
    """Individual train result within a simulation."""

    simulation = models.ForeignKey(Simulation, on_delete=models.CASCADE, related_name='results')
    train = models.ForeignKey('trains.Train', on_delete=models.CASCADE, related_name='simulation_results')
    station = models.ForeignKey('stations.Station', on_delete=models.SET_NULL, null=True, blank=True)

    simulated_delay = models.IntegerField(default=0)
    cascaded_delay = models.IntegerField(default=0)
    status_change = models.CharField(max_length=50, blank=True)
    platform_conflict = models.BooleanField(default=False)
    track_conflict = models.BooleanField(default=False)
    recommended_action = models.TextField(blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'simulation_results'
        ordering = ['-simulated_delay']

    def __str__(self):
        return f"Sim#{self.simulation_id} — {self.train.train_number}: +{self.simulated_delay} min"
