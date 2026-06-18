"""
AI Engine Models
Stores AI recommendations and priority analysis results.
"""

from django.db import models


class AIRecommendation(models.Model):
    """Standalone AI-generated recommendation (not tied to a conflict)."""

    class RecommendationType(models.TextChoices):
        THROUGHPUT = 'THROUGHPUT', 'Throughput Optimization'
        PRIORITY = 'PRIORITY', 'Train Priority'
        HOLDING = 'HOLDING', 'Holding Strategy'
        CROSSING = 'CROSSING', 'Crossing Order'
        REROUTING = 'REROUTING', 'Rerouting'

    recommendation_type = models.CharField(max_length=30, choices=RecommendationType.choices)
    title = models.CharField(max_length=200)
    description = models.TextField()
    reasoning = models.TextField()
    priority_score = models.FloatField(default=5.0)
    confidence = models.FloatField(default=0.85)
    is_active = models.BooleanField(default=True)
    is_accepted = models.BooleanField(default=False)
    generated_at = models.DateTimeField(auto_now_add=True)

    primary_train = models.ForeignKey(
        'trains.Train', on_delete=models.CASCADE,
        related_name='ai_recommendations', null=True, blank=True
    )
    affected_section = models.ForeignKey(
        'stations.TrackSection', on_delete=models.SET_NULL,
        null=True, blank=True
    )

    class Meta:
        db_table = 'ai_recommendations'
        ordering = ['-generated_at']

    def __str__(self):
        return f"{self.get_recommendation_type_display()} — {self.title[:60]}"

    @property
    def confidence_pct(self):
        return round(self.confidence * 100, 1)
