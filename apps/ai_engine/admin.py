from django.contrib import admin
from .models import AIRecommendation

@admin.register(AIRecommendation)
class AIRecommendationAdmin(admin.ModelAdmin):
    list_display = ['recommendation_type', 'title', 'confidence', 'is_active', 'generated_at']
    list_filter = ['recommendation_type', 'is_active', 'is_accepted']
    ordering = ['-generated_at']
