"""Conflict Detection Engine Views."""
import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import Q

from apps.trains.models import Train
from .models import Conflict, Recommendation
from .services import ConflictDetectionEngine

logger = logging.getLogger(__name__)
engine = ConflictDetectionEngine()


@ensure_csrf_cookie
@login_required
def conflict_list(request):
    conflicts = Conflict.objects.select_related(
        'train_a', 'train_b', 'station', 'track_section'
    ).order_by('-detected_at')

    status_filter = request.GET.get('status', '')
    severity_filter = request.GET.get('severity', '')
    type_filter = request.GET.get('type', '')

    if status_filter:
        conflicts = conflicts.filter(status=status_filter)
    if severity_filter:
        conflicts = conflicts.filter(severity=severity_filter)
    if type_filter:
        conflicts = conflicts.filter(conflict_type=type_filter)

    paginator = Paginator(conflicts, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    active_count = Conflict.objects.filter(status='ACTIVE').count()
    critical_count = Conflict.objects.filter(status='ACTIVE', severity='CRITICAL').count()
    high_count = Conflict.objects.filter(status='ACTIVE', severity='HIGH').count()
    medium_count = Conflict.objects.filter(status='ACTIVE', severity='MEDIUM').count()
    low_count = Conflict.objects.filter(status='ACTIVE', severity='LOW').count()

    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'severity_filter': severity_filter,
        'type_filter': type_filter,
        'status_choices': Conflict.ConflictStatus.choices,
        'severity_choices': Conflict.Severity.choices,
        'type_choices': Conflict.ConflictType.choices,
        'page_title': 'Conflict Management',
        'active_nav': 'conflicts',
        'active_count': active_count,
        'critical_count': critical_count,
        'high_count': high_count,
        'medium_count': medium_count,
        'low_count': low_count,
        'total_count': conflicts.count(),
        'impact_delay': active_count * 18,
        'impact_thru': (active_count * 3 + critical_count * 5),
        'impact_pax': active_count * 240,
        'impact_rev': round(active_count * 1.5, 1),
    }
    return render(request, 'conflicts/list.html', context)


@login_required
def conflict_detail(request, conflict_id):
    conflict = get_object_or_404(Conflict, id=conflict_id)
    recommendations = Recommendation.objects.filter(conflict=conflict).order_by('-generated_at')

    context = {
        'conflict': conflict,
        'recommendations': recommendations,
        'page_title': f'Conflict #{conflict.id}',
        'active_nav': 'conflicts',
    }
    return render(request, 'conflicts/detail.html', context)


@login_required
@require_http_methods(["POST"])
def run_detection(request):
    """Trigger conflict detection engine for today."""
    from django.utils import timezone
    today = timezone.now().date()
    detected = engine.detect_all(scheduled_date=today)
    return JsonResponse({
        'success': True,
        'detected': len(detected),
        'message': f'{len(detected)} conflict(s) detected for {today}.',
    })


@login_required
@require_http_methods(["POST"])
def resolve_conflict(request, conflict_id):
    conflict = get_object_or_404(Conflict, id=conflict_id)
    if conflict.status == 'RESOLVED':
        return JsonResponse({'error': 'Already resolved'}, status=400)
    data = json.loads(request.body) if request.body else {}
    conflict.resolve(user=request.user, notes=data.get('notes', ''))
    return JsonResponse({'success': True, 'message': f'Conflict #{conflict_id} resolved.'})


@login_required
@require_http_methods(["POST"])
def acknowledge_conflict(request, conflict_id):
    conflict = get_object_or_404(Conflict, id=conflict_id)
    conflict.status = 'ACKNOWLEDGED'
    conflict.save(update_fields=['status'])
    return JsonResponse({'success': True})


@login_required
def conflict_report_api(request):
    from_date = request.GET.get('from', (timezone.now().date() - timezone.timedelta(days=7)).isoformat())
    to_date = request.GET.get('to', timezone.now().date().isoformat())
    try:
        from datetime import date
        from_date = date.fromisoformat(from_date)
        to_date = date.fromisoformat(to_date)
    except ValueError:
        from_date = timezone.now().date() - timezone.timedelta(days=7)
        to_date = timezone.now().date()
    report = engine.generate_conflict_report(from_date, to_date)
    return JsonResponse(report)
