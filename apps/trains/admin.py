from django.contrib import admin
from .models import Train

@admin.register(Train)
class TrainAdmin(admin.ModelAdmin):
    list_display = ['train_number', 'train_name', 'train_type', 'current_status', 'current_delay', 'priority_level']
    list_filter = ['train_type', 'current_status', 'priority_level']
    search_fields = ['train_number', 'train_name']
    ordering = ['train_number']
