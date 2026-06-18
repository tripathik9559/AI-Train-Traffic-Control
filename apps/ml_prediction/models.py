"""
ML Prediction Models
Stores delay prediction inputs, outputs, and model metadata.
"""

from django.db import models


class DelayPrediction(models.Model):
    """Stores individual delay predictions made by the ML model."""

    class RiskLevel(models.TextChoices):
        LOW = 'LOW', 'Low Risk (< 10 min)'
        MEDIUM = 'MEDIUM', 'Medium Risk (10–30 min)'
        HIGH = 'HIGH', 'High Risk (30–60 min)'
        CRITICAL = 'CRITICAL', 'Critical Risk (> 60 min)'

    train = models.ForeignKey(
        'trains.Train', on_delete=models.CASCADE,
        related_name='delay_predictions', null=True, blank=True
    )

    # Input Features
    train_type_encoded = models.IntegerField(default=0)
    day_of_week = models.IntegerField(default=0, help_text='0=Mon … 6=Sun')
    hour_of_day = models.IntegerField(default=12)
    weather_code = models.IntegerField(default=0, help_text='0=Clear,1=Rain,2=Fog,3=Extreme')
    traffic_density = models.FloatField(default=0.5, help_text='0.0–1.0')
    historical_avg_delay = models.FloatField(default=0.0, help_text='Historical average delay (min)')
    section_congestion = models.FloatField(default=0.0, help_text='0.0–1.0')
    is_peak_hour = models.BooleanField(default=False)
    scheduled_distance = models.FloatField(default=100.0)

    # Output
    predicted_delay_minutes = models.FloatField()
    risk_level = models.CharField(max_length=20, choices=RiskLevel.choices)
    confidence_score = models.FloatField(default=0.0)
    model_version = models.CharField(max_length=20, default='v1.0')

    # Metadata
    scheduled_date = models.DateField(null=True, blank=True)
    predicted_at = models.DateTimeField(auto_now_add=True)
    actual_delay = models.FloatField(null=True, blank=True, help_text='Filled after actual travel')

    class Meta:
        db_table = 'delay_predictions'
        verbose_name = 'Delay Prediction'
        verbose_name_plural = 'Delay Predictions'
        ordering = ['-predicted_at']
        indexes = [
            models.Index(fields=['scheduled_date']),
            models.Index(fields=['risk_level']),
        ]

    def __str__(self):
        train_str = self.train.train_number if self.train else 'Unknown'
        return f"{train_str} — {self.predicted_delay_minutes:.1f} min delay ({self.risk_level})"

    @property
    def risk_color(self):
        colors = {
            'LOW': '#2ecc71',
            'MEDIUM': '#f39c12',
            'HIGH': '#e67e22',
            'CRITICAL': '#e74c3c',
        }
        return colors.get(self.risk_level, '#95a5a6')

    @property
    def risk_icon(self):
        icons = {
            'LOW': '✅',
            'MEDIUM': '⚠️',
            'HIGH': '🔶',
            'CRITICAL': '🚨',
        }
        return icons.get(self.risk_level, '❓')

    @property
    def accuracy(self):
        """Calculate prediction accuracy if actual delay is known."""
        if self.actual_delay is not None and self.predicted_delay_minutes != 0:
            error = abs(self.actual_delay - self.predicted_delay_minutes)
            accuracy = max(0, 100 - (error / max(abs(self.predicted_delay_minutes), 1)) * 100)
            return round(accuracy, 1)
        return None


class MLModelMetadata(models.Model):
    """Tracks ML model versions and performance metrics."""

    version = models.CharField(max_length=20, unique=True)
    algorithm = models.CharField(max_length=100, default='Random Forest Regressor')
    training_date = models.DateTimeField(auto_now_add=True)
    training_samples = models.IntegerField(default=0)
    features_count = models.IntegerField(default=9)

    # Performance metrics
    r2_score = models.FloatField(default=0.0)
    mean_absolute_error = models.FloatField(default=0.0)
    root_mean_squared_error = models.FloatField(default=0.0)
    cross_val_score = models.FloatField(default=0.0)

    is_active = models.BooleanField(default=False)
    model_file_path = models.CharField(max_length=500)
    hyperparameters = models.JSONField(default=dict)

    class Meta:
        db_table = 'ml_model_metadata'
        verbose_name = 'ML Model Metadata'
        ordering = ['-training_date']

    def __str__(self):
        return f"{self.algorithm} {self.version} (R²={self.r2_score:.3f})"
