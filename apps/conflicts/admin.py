from django.contrib import admin
from .models import Conflict, Recommendation

@admin.register(Conflict)
class ConflictAdmin(admin.ModelAdmin):
    list_display = ['conflict_type','severity','status','train_a','train_b','station','detected_at']
    list_filter = ['conflict_type','severity','status']
    search_fields = ['train_a__train_number','train_b__train_number']
    ordering = ['-detected_at']
    readonly_fields = ['detected_at']

@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ['recommendation_type','primary_train','status','confidence','generated_at']
    list_filter = ['recommendation_type','status']
    ordering = ['-generated_at']
