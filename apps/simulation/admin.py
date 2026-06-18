from django.contrib import admin
from .models import Simulation, SimulationResult

@admin.register(Simulation)
class SimulationAdmin(admin.ModelAdmin):
    list_display = ['name', 'scenario_type', 'status', 'throughput_impact', 'created_by', 'created_at']
    list_filter = ['scenario_type', 'status']
    ordering = ['-created_at']

@admin.register(SimulationResult)
class SimulationResultAdmin(admin.ModelAdmin):
    list_display = ['simulation', 'train', 'simulated_delay', 'cascaded_delay', 'platform_conflict']
    ordering = ['-simulated_delay']
