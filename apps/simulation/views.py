"""
Simulation Views — Scenario Simulation Engine
"""

import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.trains.models import Train
from apps.stations.models import TrackSection, Station
from .models import Simulation, SimulationResult
from .services import ScenarioSimulator

logger = logging.getLogger(__name__)


@login_required
def simulation_index(request):
    """Simulation dashboard — list past simulations and run new ones."""
    simulations = Simulation.objects.filter(
        created_by=request.user
    ).prefetch_related('affected_trains').order_by('-created_at')

    trains = Train.objects.filter(is_active=True).order_by('train_number')
    sections = TrackSection.objects.filter(is_active=True).select_related('from_station', 'to_station')
    stations = Station.objects.filter(is_active=True).order_by('name')

    context = {
        'simulations': simulations[:20],
        'trains': trains,
        'sections': sections,
        'stations': stations,
        'scenario_types': Simulation.ScenarioType.choices,
        'page_title': 'Scenario Simulation Engine',
        'active_nav': 'simulation',
        'total_simulations': simulations.count(),
        'completed_count': simulations.filter(status='COMPLETED').count(),
    }
    return render(request, 'simulation/index.html', context)


@login_required
def realtime_simulator(request):
    """Real-time operations simulator view."""
    trains = Train.objects.filter(
        is_active=True,
        current_status__in=['RUNNING', 'SCHEDULED', 'DELAYED']
    ).select_related('source_station', 'destination_station')[:20]

    stations = Station.objects.filter(is_active=True).order_by('name')[:15]

    context = {
        'trains': trains,
        'stations': stations,
        'page_title': 'Real-Time Operations Simulator',
        'active_nav': 'simulation',
    }
    return render(request, 'simulation/realtime.html', context)


@login_required
@require_http_methods(["POST"])
def run_simulation(request):
    """Create and run a simulation scenario."""
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        data = request.POST.dict()

    name = data.get('name', f"Simulation {timezone.now().strftime('%d/%m %H:%M')}")
    scenario_type = data.get('scenario_type', 'TRAIN_DELAY')
    delay_minutes = int(data.get('delay_minutes', 30))
    duration_hours = float(data.get('duration_hours', 2.0))
    train_ids = data.get('train_ids', [])

    simulation = Simulation.objects.create(
        name=name,
        scenario_type=scenario_type,
        description=data.get('description', ''),
        delay_minutes=delay_minutes,
        duration_hours=duration_hours,
        parameters=data.get('parameters', {}),
        created_by=request.user,
    )

    if train_ids:
        trains = Train.objects.filter(id__in=train_ids)
        simulation.affected_trains.set(trains)

    simulator = ScenarioSimulator()
    try:
        sim, results = simulator.run(simulation)

        results_data = [
            {
                'train_number': r.train.train_number,
                'train_name': r.train.train_name,
                'simulated_delay': r.simulated_delay,
                'cascaded_delay': r.cascaded_delay,
                'status_change': r.status_change,
                'platform_conflict': r.platform_conflict,
                'track_conflict': r.track_conflict,
                'recommended_action': r.recommended_action,
            }
            for r in results
        ]

        return JsonResponse({
            'success': True,
            'simulation_id': sim.id,
            'status': sim.status,
            'throughput_impact': sim.throughput_impact,
            'trains_affected': sim.trains_affected_count,
            'recovery_time': sim.estimated_recovery_time,
            'summary': sim.result_summary,
            'recommendations': sim.recommendations,
            'results': results_data,
        })

    except Exception as e:
        simulation.status = 'FAILED'
        simulation.save(update_fields=['status'])
        logger.error(f"Simulation failed: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def simulation_detail(request, sim_id):
    """Detailed simulation result view."""
    simulation = get_object_or_404(Simulation, id=sim_id, created_by=request.user)
    results = SimulationResult.objects.filter(simulation=simulation).select_related('train', 'station')

    context = {
        'simulation': simulation,
        'results': results,
        'page_title': f'Simulation: {simulation.name}',
        'active_nav': 'simulation',
    }
    return render(request, 'simulation/detail.html', context)


@login_required
def realtime_state_api(request):
    """API: Return real-time train states for the simulator."""
    import random

    trains = Train.objects.filter(
        is_active=True
    ).select_related('source_station', 'destination_station')[:20]

    train_states = []
    for i, train in enumerate(trains):
        # Simulate position along a route (0–100%)
        progress = random.uniform(0, 100)
        speed = random.uniform(60, train.speed) if train.current_status == 'RUNNING' else 0
        delay = train.current_delay + random.randint(-2, 5)

        train_states.append({
            'id': train.id,
            'number': train.train_number,
            'name': train.train_name,
            'type': train.train_type,
            'status': train.current_status,
            'delay': max(0, delay),
            'speed': round(speed, 1),
            'progress': round(progress, 1),
            'priority': train.priority_level,
            'type_color': train.type_color,
            'source': train.source_station.code if train.source_station else 'SRC',
            'destination': train.destination_station.code if train.destination_station else 'DST',
        })

    from apps.stations.models import TrackSection
    sections = TrackSection.objects.filter(is_active=True).select_related('from_station', 'to_station')
    section_states = [
        {
            'code': s.code,
            'name': s.name,
            'status': s.status,
            'color': s.status_color,
            'from': s.from_station.code,
            'to': s.to_station.code,
        }
        for s in sections[:20]
    ]

    return JsonResponse({
        'timestamp': timezone.now().isoformat(),
        'trains': train_states,
        'sections': section_states,
    })
