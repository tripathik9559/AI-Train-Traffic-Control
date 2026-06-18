from django.contrib import admin
from .models import DelayPrediction, MLModelMetadata

@admin.register(DelayPrediction)
class DelayPredictionAdmin(admin.ModelAdmin):
    list_display = ['train', 'predicted_delay_minutes', 'risk_level', 'confidence_score', 'predicted_at']
    list_filter = ['risk_level', 'weather_code']
    ordering = ['-predicted_at']

@admin.register(MLModelMetadata)
class MLModelMetadataAdmin(admin.ModelAdmin):
    list_display = ['version', 'algorithm', 'r2_score', 'mean_absolute_error', 'is_active', 'training_date']
    list_filter = ['is_active']
    ordering = ['-training_date']
