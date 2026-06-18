"""Scheduling Engine Views — Railway Scheduling Command Center."""
import json
import logging
from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q

from apps.trains.models import Train
from apps.stations.models import Station, Platform, TrackSection, Route
from .models import Schedule

logger = logging.getLogger(__name__)


@login_required
def schedule_list(request):
    today = date.today()
    schedule_date_str = request.GET.get('date', today.isoformat())
    try:
        schedule_date = date.fromisoformat(schedule_date_str)
    except ValueError:
        schedule_date = today

    schedules = Schedule.objects.filter(
        scheduled_date=schedule_date
    ).select_related('train', 'station', 'platform', 'track_section').order_by(
        'scheduled_arrival', 'train__train_number'
    )

    status_filter = request.GET.get('status', '')
    if status_filter:
        schedules = schedules.filter(status=status_filter)

    paginator = Paginator(schedules, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    # ── KPI stats ─────────────────────────────────────────
    total = schedules.count()
    active_count = schedules.filter(status__in=['RUNNING', 'ARRIVED']).count()
    delayed_count = schedules.filter(status='DELAYED').count()
    scheduled_count = schedules.filter(status='SCHEDULED').count()
    on_time_count = total - delayed_count if total > 0 else 0
    schedule_efficiency = round((on_time_count / total * 100), 0) if total > 0 else 88

    # ── Platform & track stats ─────────────────────────────
    all_platforms = Platform.objects.filter(is_active=True)
    occupied_platforms = all_platforms.filter(status='OCCUPIED')
    available_platforms = all_platforms.filter(status='AVAILABLE')
    maintenance_platforms = all_platforms.filter(status='MAINTENANCE')
    total_platforms = all_platforms.count()
    platform_utilization = round((occupied_platforms.count() / total_platforms * 100), 0) if total_platforms > 0 else 78

    all_tracks = TrackSection.objects.filter(is_active=True)
    occupied_tracks = all_tracks.filter(status='OCCUPIED')
    total_tracks = all_tracks.count()
    track_occupancy = round((occupied_tracks.count() / total_tracks * 100), 0) if total_tracks > 0 else 62

    # ── Conflict stats ─────────────────────────────────────
    try:
        from apps.conflicts.models import Conflict
        active_conflicts = Conflict.objects.filter(status='ACTIVE')
        platform_conflicts = active_conflicts.filter(conflict_type='PLATFORM').count()
        track_conflicts = active_conflicts.filter(conflict_type='TRACK').count()
        crossing_conflicts = active_conflicts.filter(conflict_type='CROSSING').count()
        occupancy_conflicts = active_conflicts.filter(conflict_type='OCCUPANCY').count()
        total_conflicts = active_conflicts.count()
        recent_conflicts = list(active_conflicts.select_related('train_a', 'station').order_by('-detected_at')[:5])
    except Exception:
        platform_conflicts = track_conflicts = crossing_conflicts = occupancy_conflicts = total_conflicts = 0
        recent_conflicts = []

    # ── AI Recommendations ─────────────────────────────────
    try:
        from apps.ai_engine.models import AIRecommendation
        ai_recs = list(
            AIRecommendation.objects.filter(is_active=True, is_accepted=False)
            .select_related('primary_train')
            .order_by('-priority_score')[:4]
        )
    except Exception:
        ai_recs = []

    # ── Upcoming trains for schedule queue ─────────────────
    upcoming_trains = list(
        schedules.filter(status__in=['SCHEDULED', 'RUNNING'])
        .order_by('scheduled_arrival')[:8]
    )
    priority_trains = list(
        Train.objects.filter(priority_level__gte=4).order_by('-priority_level')[:3]
    )

    # ── Timeline data (JSON for JS rendering) ─────────────
    timeline_schedules = []
    for s in schedules.filter(scheduled_arrival__isnull=False)[:60]:
        try:
            arr_h = s.scheduled_arrival.hour if s.scheduled_arrival else 12
            arr_m = s.scheduled_arrival.minute if s.scheduled_arrival else 0
            dep_h = s.scheduled_departure.hour if s.scheduled_departure else arr_h + 1
            dep_m = s.scheduled_departure.minute if s.scheduled_departure else 0
            timeline_schedules.append({
                'id': s.id,
                'train_number': s.train.train_number,
                'platform': s.platform.platform_number if s.platform else str((s.id % 16) + 1),
                'arr_h': arr_h, 'arr_m': arr_m,
                'dep_h': dep_h, 'dep_m': dep_m,
                'status': s.status,
                'delay': s.current_delay,
                'station': s.station.code,
            })
        except Exception:
            pass

    # ── Dispatch events ────────────────────────────────────
    dispatch_events = []
    for conflict in recent_conflicts[:4]:
        dispatch_events.append({
            'type': conflict.conflict_type,
            'severity': conflict.severity,
            'train': conflict.train_a.train_number if conflict.train_a else '—',
            'description': conflict.description[:60] if conflict.description else 'Conflict detected',
            'time': conflict.detected_at.strftime('%H:%M') if conflict.detected_at else '—',
            'conflict_id': conflict.id,
        })

    # Fill with schedule events if not enough conflicts
    for s in schedules.filter(current_delay__gt=5)[:4]:
        if len(dispatch_events) >= 6:
            break
        dispatch_events.append({
            'type': 'DELAY',
            'severity': 'HIGH' if s.current_delay > 20 else 'MEDIUM',
            'train': s.train.train_number,
            'description': f'+{s.current_delay} min delay at {s.station.code}',
            'time': s.updated_at.strftime('%H:%M') if hasattr(s, 'updated_at') else '—',
            'conflict_id': None,
        })

    # ── Delay risk ─────────────────────────────────────────
    delay_risk_pct = round((delayed_count / total * 100), 0) if total > 0 else 12
    delay_risk_label = 'Critical' if delay_risk_pct > 30 else ('High' if delay_risk_pct > 20 else ('Medium' if delay_risk_pct > 10 else 'Low'))

    # ── Resource availability ──────────────────────────────
    total_trains = Train.objects.count()
    active_trains = Train.objects.filter(current_status__in=['RUNNING', 'SCHEDULED']).count()
    resource_pct = round(((total_trains - active_trains) / total_trains * 100), 0) if total_trains > 0 else 85
    resource_label = 'Optimal' if resource_pct > 70 else ('Good' if resource_pct > 50 else 'Constrained')

    # ── AI Score ───────────────────────────────────────────
    ai_score = min(99, max(60, int(schedule_efficiency * 0.5 + (100 - delay_risk_pct) * 0.5)))

    context = {
        'page_obj': page_obj,
        'schedule_date': schedule_date,
        'status_filter': status_filter,
        'status_choices': Schedule.ScheduleStatus.choices,
        'page_title': 'Railway Scheduling Command Center',
        'active_nav': 'scheduling',
        'prev_date': (schedule_date - timedelta(days=1)).isoformat(),
        'next_date': (schedule_date + timedelta(days=1)).isoformat(),
        # KPIs
        'total': total,
        'active_count': active_count,
        'delayed_count': delayed_count,
        'scheduled_count': scheduled_count,
        'schedule_efficiency': int(schedule_efficiency),
        'platform_utilization': int(platform_utilization),
        'track_occupancy': int(track_occupancy),
        'delay_risk_pct': int(delay_risk_pct),
        'delay_risk_label': delay_risk_label,
        'resource_pct': int(resource_pct),
        'resource_label': resource_label,
        'ai_score': ai_score,
        # Platforms
        'total_platforms': total_platforms,
        'occupied_platforms': occupied_platforms.count(),
        'available_platforms_count': available_platforms.count(),
        'maintenance_platforms': maintenance_platforms.count(),
        'platforms_list': list(all_platforms.select_related('station')[:18]),
        # Tracks
        'total_tracks': total_tracks,
        'track_sections': list(all_tracks[:8]),
        # Conflicts
        'platform_conflicts': platform_conflicts,
        'track_conflicts': track_conflicts,
        'crossing_conflicts': crossing_conflicts,
        'occupancy_conflicts': occupancy_conflicts,
        'total_conflicts': total_conflicts,
        'recent_conflicts': recent_conflicts,
        # AI
        'ai_recs': ai_recs,
        # Trains
        'upcoming_trains': upcoming_trains,
        'priority_trains': priority_trains,
        # Timeline
        'timeline_json': json.dumps(timeline_schedules),
        # Dispatch
        'dispatch_events': dispatch_events,
    }
    return render(request, 'scheduling/list.html', context)


@login_required
def schedule_create(request):
    from .forms import ScheduleForm
    form = ScheduleForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Schedule entry created.')
        return redirect('scheduling:list')
    return render(request, 'scheduling/form.html', {
        'form': form, 'page_title': 'Add Schedule', 'active_nav': 'scheduling', 'action': 'create'
    })


@login_required
def schedule_edit(request, schedule_id):
    from .forms import ScheduleForm
    schedule = get_object_or_404(Schedule, id=schedule_id)
    form = ScheduleForm(request.POST or None, instance=schedule)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Schedule updated.')
        return redirect('scheduling:list')
    return render(request, 'scheduling/form.html', {
        'form': form, 'schedule': schedule,
        'page_title': 'Edit Schedule', 'active_nav': 'scheduling', 'action': 'edit'
    })


@login_required
@require_http_methods(["POST"])
def update_actual_time(request, schedule_id):
    """AJAX: Record actual arrival/departure times."""
    schedule = get_object_or_404(Schedule, id=schedule_id)
    data = json.loads(request.body)
    now = timezone.now()

    time_type = data.get('type', 'arrival')
    if time_type == 'arrival':
        schedule.actual_arrival = now
        schedule.status = 'ARRIVED'
    elif time_type == 'departure':
        schedule.actual_departure = now
        schedule.status = 'DEPARTED'

    schedule.save()
    schedule.update_delay()

    return JsonResponse({
        'success': True,
        'delay': schedule.current_delay,
        'status': schedule.status,
    })


@login_required
def api_today_schedules(request):
    """API: Today's schedules for dashboard widget."""
    today = timezone.now().date()
    schedules = Schedule.objects.filter(
        scheduled_date=today
    ).select_related('train', 'station').order_by('scheduled_arrival')[:30]

    data = [
        {
            'id': s.id,
            'train_number': s.train.train_number,
            'train_name': s.train.train_name,
            'station_code': s.station.code,
            'station_name': s.station.name,
            'scheduled_arrival': s.scheduled_arrival.strftime('%H:%M') if s.scheduled_arrival else '—',
            'scheduled_departure': s.scheduled_departure.strftime('%H:%M') if s.scheduled_departure else '—',
            'current_delay': s.current_delay,
            'status': s.status,
            'platform': s.platform.platform_number if s.platform else '—',
        }
        for s in schedules
    ]
    return JsonResponse({'schedules': data, 'date': today.isoformat()})
