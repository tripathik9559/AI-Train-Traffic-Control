"""
Train Management Views — List, Create, Update, Delete, Detail.
"""

import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count
from django.utils import timezone

from apps.stations.models import Station, TrackSection
from .models import Train
from .forms import TrainForm

logger = logging.getLogger(__name__)


@login_required
def train_list(request):
    """Train Fleet Management Command Center — list with full KPI metrics."""
    all_trains = Train.objects.filter(is_active=True).select_related(
        'source_station', 'destination_station'
    )

    # ── Fleet KPI metrics ──────────────────────────────────────────────────
    total_trains     = all_trains.count()
    active_trains    = all_trains.filter(current_status__in=['RUNNING', 'SCHEDULED']).count()
    delayed_trains   = all_trains.filter(current_status='DELAYED').count()
    on_time_trains   = all_trains.filter(current_delay__lte=5).count()
    cancelled_trains = all_trains.filter(current_status='CANCELLED').count()
    maintenance_trains = all_trains.filter(current_status='MAINTENANCE').count()

    avg_speed_val = all_trains.aggregate(avg=Avg('speed'))['avg'] or 0
    avg_speed = round(avg_speed_val, 1)

    fleet_efficiency = round((on_time_trains / max(total_trains, 1)) * 100, 1)

    # ── Zone / search summary data ─────────────────────────────────────────
    live_positions   = all_trains.filter(current_status='RUNNING').count()
    total_sections   = TrackSection.objects.filter(is_active=True).count()
    clear_sections   = TrackSection.objects.filter(status='CLEAR', is_active=True).count()
    route_utilization = round((1 - clear_sections / max(total_sections, 1)) * 100, 1)
    zones = Station.objects.filter(is_active=True).values_list('zone', flat=True).distinct()
    zone_list = [z for z in zones if z]

    # ── AI Insights data ──────────────────────────────────────────────────
    try:
        from apps.ai_engine.models import AIRecommendation
        ai_recs = AIRecommendation.objects.filter(is_active=True).order_by('-generated_at')[:5]
        high_priority_trains = all_trains.filter(priority_level__gte=4).order_by('-priority_level')[:5]
        attention_trains = all_trains.filter(
            Q(current_status='DELAYED') | Q(current_delay__gt=15)
        ).order_by('-current_delay')[:5]
    except Exception:
        ai_recs = []
        high_priority_trains = all_trains.filter(priority_level__gte=4)[:5]
        attention_trains = all_trains.filter(current_delay__gt=15)[:5]

    # ── Station heatmap data ──────────────────────────────────────────────
    stations_for_heatmap = Station.objects.filter(is_active=True).prefetch_related('platforms')[:8]

    # ── Filtered table queryset ────────────────────────────────────────────
    trains = all_trains
    search = request.GET.get('search', '').strip()
    status_filter   = request.GET.get('status', '')
    type_filter     = request.GET.get('type', '')
    priority_filter = request.GET.get('priority', '')
    zone_filter     = request.GET.get('zone', '')
    delay_filter    = request.GET.get('delay_status', '')
    quick_filter    = request.GET.get('quick_filter', '')

    if search:
        trains = trains.filter(
            Q(train_number__icontains=search) |
            Q(train_name__icontains=search) |
            Q(source_station__code__icontains=search) |
            Q(destination_station__code__icontains=search)
        )
    if status_filter:
        trains = trains.filter(current_status=status_filter)
    if type_filter:
        trains = trains.filter(train_type=type_filter)
    if priority_filter:
        trains = trains.filter(priority_level=priority_filter)
    if zone_filter:
        trains = trains.filter(
            Q(source_station__zone__icontains=zone_filter) |
            Q(destination_station__zone__icontains=zone_filter)
        )
    if delay_filter == 'delayed':
        trains = trains.filter(current_delay__gt=5)
    elif delay_filter == 'ontime':
        trains = trains.filter(current_delay__lte=5)
    if quick_filter == 'critical':
        trains = trains.filter(priority_level=5)
    elif quick_filter == 'delayed':
        trains = trains.filter(current_status='DELAYED')
    elif quick_filter == 'high_priority':
        trains = trains.filter(priority_level__gte=4)
    elif quick_filter == 'freight':
        trains = trains.filter(train_type='FREIGHT')
    elif quick_filter == 'passenger':
        trains = trains.filter(train_type__in=['PASSENGER', 'EXPRESS', 'MAIL'])
    elif quick_filter == 'superfast':
        trains = trains.filter(train_type__in=['RAJDHANI', 'SHATABDI', 'DURONTO', 'VANDE_BHARAT'])

    sort_by = request.GET.get('sort', 'train_number')
    allowed_sorts = ['train_number', '-train_number', 'train_name', 'current_delay',
                     '-current_delay', 'priority_level', '-priority_level',
                     'current_status', 'train_type']
    if sort_by not in allowed_sorts:
        sort_by = 'train_number'
    trains = trains.order_by(sort_by)

    paginator = Paginator(trains, 15)
    page_obj  = paginator.get_page(request.GET.get('page'))

    context = {
        # Table
        'page_obj': page_obj,
        'search': search,
        'status_filter':   status_filter,
        'type_filter':     type_filter,
        'priority_filter': priority_filter,
        'zone_filter':     zone_filter,
        'delay_filter':    delay_filter,
        'quick_filter':    quick_filter,
        'sort_by':         sort_by,
        'status_choices':   Train.Status.choices,
        'type_choices':     Train.TrainType.choices,
        'priority_choices': Train.Priority.choices,
        'zone_list': zone_list,
        'total_count': trains.count(),

        # Fleet KPIs
        'total_trains':      total_trains,
        'active_trains':     active_trains,
        'delayed_trains':    delayed_trains,
        'on_time_trains':    on_time_trains,
        'cancelled_trains':  cancelled_trains,
        'maintenance_trains': maintenance_trains,
        'avg_speed':         avg_speed,
        'fleet_efficiency':  fleet_efficiency,

        # Search summary
        'live_positions':    live_positions,
        'route_utilization': route_utilization,

        # AI / Smart Ops
        'ai_recs':            ai_recs,
        'high_priority_trains': high_priority_trains,
        'attention_trains':     attention_trains,

        # Heatmap
        'stations_for_heatmap': stations_for_heatmap,

        # Meta
        'page_title': 'Train Fleet Management',
        'active_nav': 'trains',
        'current_time': timezone.now(),
    }
    return render(request, 'trains/list.html', context)


@login_required
def train_create(request):
    """Create a new train."""
    form = TrainForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            train = form.save(commit=False)
            train.created_by = request.user
            train.save()
            messages.success(request, f'Train {train.train_number} — {train.train_name} created.')
            return redirect('trains:detail', train_id=train.id)
        else:
            messages.error(request, 'Please correct the errors below.')

    context = {
        'form': form,
        'stations': Station.objects.filter(is_active=True).order_by('name'),
        'page_title': 'Add New Train',
        'active_nav': 'trains',
        'action': 'create',
    }
    return render(request, 'trains/form.html', context)


@login_required
def train_edit(request, train_id):
    """Edit an existing train."""
    train = get_object_or_404(Train, id=train_id, is_active=True)
    form = TrainForm(request.POST or None, instance=train)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, f'Train {train.train_number} updated successfully.')
            return redirect('trains:detail', train_id=train.id)
        else:
            messages.error(request, 'Please correct the errors below.')

    context = {
        'form': form,
        'train': train,
        'stations': Station.objects.filter(is_active=True).order_by('name'),
        'page_title': f'Edit Train — {train.train_number}',
        'active_nav': 'trains',
        'action': 'edit',
    }
    return render(request, 'trains/form.html', context)


@login_required
def train_detail(request, train_id):
    """Train detail view with schedules, delays, history."""
    train = get_object_or_404(Train, id=train_id)

    today = timezone.now().date()
    from apps.scheduling.models import Schedule
    today_schedules = Schedule.objects.filter(
        train=train, scheduled_date=today
    ).select_related('station', 'platform', 'track_section').order_by('stop_sequence')

    from apps.conflicts.models import Conflict
    recent_conflicts = Conflict.objects.filter(
        Q(train_a=train) | Q(train_b=train)
    ).order_by('-detected_at')[:5]

    from apps.ml_prediction.models import DelayPrediction
    recent_predictions = DelayPrediction.objects.filter(
        train=train
    ).order_by('-predicted_at')[:3]

    context = {
        'train': train,
        'today_schedules': today_schedules,
        'recent_conflicts': recent_conflicts,
        'recent_predictions': recent_predictions,
        'page_title': f'{train.train_number} — {train.train_name}',
        'active_nav': 'trains',
    }
    return render(request, 'trains/detail.html', context)


@login_required
@require_http_methods(["POST"])
def train_delete(request, train_id):
    """Soft-delete a train."""
    train = get_object_or_404(Train, id=train_id)
    train.is_active = False
    train.save(update_fields=['is_active'])
    messages.success(request, f'Train {train.train_number} removed from active list.')
    return redirect('trains:list')


@login_required
@require_http_methods(["POST"])
def update_train_status(request, train_id):
    """AJAX: Update train status and delay."""
    train = get_object_or_404(Train, id=train_id)

    data = json.loads(request.body)
    new_status = data.get('status')
    new_delay = data.get('delay')

    if new_status and new_status in dict(Train.Status.choices):
        train.current_status = new_status
    if new_delay is not None:
        train.current_delay = int(new_delay)

    train.save(update_fields=['current_status', 'current_delay', 'updated_at'])

    if new_delay and int(new_delay) > 10:
        from apps.notifications.services import NotificationService
        NotificationService().create_delay_notification(train, int(new_delay))

    return JsonResponse({
        'success': True,
        'status': train.current_status,
        'delay': train.current_delay,
    })


@login_required
def network_visualizer(request):
    """Railway network visualizer using D3.js / Cytoscape."""
    stations = Station.objects.filter(is_active=True).prefetch_related('platforms')
    from apps.stations.models import TrackSection
    sections = TrackSection.objects.filter(is_active=True).select_related(
        'from_station', 'to_station'
    )
    trains = Train.objects.filter(is_active=True, current_status__in=['RUNNING', 'SCHEDULED'])

    nodes = [
        {
            'id': str(s.id),
            'label': s.code,
            'full_name': s.name,
            'type': s.station_type,
            'lat': s.latitude,
            'lng': s.longitude,
            'platforms': s.total_platforms,
            'is_junction': s.is_junction,
        }
        for s in stations
    ]

    edges = [
        {
            'id': sec.code,
            'source': str(sec.from_station.id),
            'target': str(sec.to_station.id),
            'label': sec.name,
            'length': sec.length,
            'status': sec.status,
            'color': sec.status_color,
            'lines': sec.number_of_lines,
        }
        for sec in sections
    ]

    context = {
        'nodes_json': json.dumps(nodes),
        'edges_json': json.dumps(edges),
        'trains': trains,
        'stations': stations,
        'sections': sections,
        'page_title': 'Railway Network Visualizer',
        'active_nav': 'network',
    }
    return render(request, 'network/visualizer.html', context)


@login_required
def api_trains_list(request):
    """API: Trains list in JSON."""
    trains = Train.objects.filter(is_active=True).select_related(
        'source_station', 'destination_station'
    )
    data = [
        {
            'id': t.id,
            'number': t.train_number,
            'name': t.train_name,
            'type': t.train_type,
            'status': t.current_status,
            'delay': t.current_delay,
            'priority': t.priority_level,
            'source': t.source_station.code if t.source_station else '',
            'destination': t.destination_station.code if t.destination_station else '',
            'type_color': t.type_color,
        }
        for t in trains
    ]
    return JsonResponse({'trains': data, 'count': len(data)})
