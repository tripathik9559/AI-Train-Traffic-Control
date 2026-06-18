from django.contrib import admin
from .models import Report

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'report_type', 'from_date', 'to_date', 'generated_by', 'generated_at']
    list_filter = ['report_type']
    ordering = ['-generated_at']
