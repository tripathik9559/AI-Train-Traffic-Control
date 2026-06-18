"""
AI Engine Views — Priority Analysis & Recommendations
"""

import json
import logging
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from apps.trains.models import Train
from apps.stations.models import TrackSection, Station
from apps.conflicts.models import Conflict, Recommendation
from .services import PriorityEngine
from .models import AIRecommendation

logger = logging.getLogger(__name__)
engine = PriorityEngine()


@login_required
def priority_dashboard(request):
    """Main AI Priority Engine dashboard."""
    trains = Train.objects.filter(
        is_active=True,
        current_status__in=['RUNNING', 'DELAYED', 'SCHEDULED']
    ).select_related('source_station', 'destination_station').order_by('priority_level')

    active_conflicts = Conflict.objects.filter(
        status='ACTIVE'
    ).select_related('train_a', 'train_b', 'station').order_by('-severity')[:10]

    recent_recommendations = Recommendation.objects.filter(
        status='PENDING'
    ).select_related('primary_train', 'secondary_train').order_by('-generated_at')[:10]

    context = {
        'trains': trains,
        'active_conflicts': active_conflicts,
        'recent_recommendations': recent_recommendations,
        'page_title': 'AI Priority Engine',
        'active_nav': 'ai_engine',
        'total_trains': trains.count(),
        'active_conflict_count': active_conflicts.count(),
        'pending_recs': recent_recommendations.count(),
    }
    return render(request, 'ai_engine/priority_dashboard.html', context)


@login_required
def analyze_train_priority(request, train_id):
    """Detailed priority analysis for a single train."""
    train = get_object_or_404(Train, id=train_id, is_active=True)

    from apps.scheduling.models import Schedule
    schedule = Schedule.objects.filter(
        train=train,
        scheduled_date=timezone.now().date()
    ).first()

    result = engine.calculate_priority(train, schedule)

    context = {
        'train': train,
        'result': result,
        'weights': engine.WEIGHTS,
        'page_title': f'Priority Analysis — {train.train_number}',
        'active_nav': 'ai_engine',
    }
    return render(request, 'ai_engine/train_analysis.html', context)


@login_required
def conflict_analysis(request, conflict_id):
    """AI analysis and recommendations for a specific conflict."""
    conflict = get_object_or_404(Conflict, id=conflict_id)

    recommendations = engine.generate_recommendations_for_conflict(conflict)

    trains = [conflict.train_a]
    if conflict.train_b:
        trains.append(conflict.train_b)

    ranked = engine.rank_at_conflict(trains)

    context = {
        'conflict': conflict,
        'recommendations': recommendations,
        'ranked_trains': ranked,
        'page_title': f'Conflict Analysis #{conflict.id}',
        'active_nav': 'ai_engine',
    }
    return render(request, 'ai_engine/conflict_analysis.html', context)


@login_required
@require_http_methods(["POST"])
def api_rank_trains(request):
    """API: Rank multiple trains by priority score."""
    try:
        data = json.loads(request.body)
        train_ids = data.get('train_ids', [])

        if not train_ids or len(train_ids) < 2:
            return JsonResponse({'error': 'Provide at least 2 train IDs'}, status=400)

        trains = list(Train.objects.filter(id__in=train_ids, is_active=True))
        if len(trains) < 2:
            return JsonResponse({'error': 'Could not find requested trains'}, status=404)

        ranked = engine.rank_at_conflict(trains)

        return JsonResponse({
            'success': True,
            'ranked': [
                {
                    'rank': r['rank'],
                    'rank_label': r['rank_label'],
                    'train_number': r['train'].train_number,
                    'train_name': r['train'].train_name,
                    'total_score': r['total_score'],
                    'action': r['action'],
                    'action_detail': r['action_detail'],
                    'action_color': r['action_color'],
                    'scores': {k: round(v, 2) for k, v in r['scores'].items()},
                }
                for r in ranked
            ]
        })
    except Exception as e:
        logger.error(f"AI rank error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_priority_score(request, train_id):
    """API: Get priority score for a single train."""
    train = get_object_or_404(Train, id=train_id)

    from apps.scheduling.models import Schedule
    schedule = Schedule.objects.filter(
        train=train, scheduled_date=timezone.now().date()
    ).first()

    result = engine.calculate_priority(train, schedule)

    return JsonResponse({
        'train_id': train.id,
        'train_number': train.train_number,
        'total_score': result['total_score'],
        'score_percentage': result['score_percentage'],
        'action': result['action'],
        'action_detail': result['action_detail'],
        'action_color': result['action_color'],
        'scores': {k: round(v, 2) for k, v in result['scores'].items()},
        'delay_minutes': result['delay_minutes'],
    })


@login_required
@require_http_methods(["POST"])
def accept_recommendation(request, rec_id):
    """Accept a pending recommendation."""
    rec = get_object_or_404(Recommendation, id=rec_id)
    rec.status = 'ACCEPTED'
    rec.accepted_by = request.user
    rec.accepted_at = timezone.now()
    rec.save()
    return JsonResponse({'success': True, 'message': 'Recommendation accepted.'})


@login_required
@require_http_methods(["POST"])
def reject_recommendation(request, rec_id):
    """Reject a recommendation."""
    rec = get_object_or_404(Recommendation, id=rec_id)
    rec.status = 'REJECTED'
    rec.save()
    return JsonResponse({'success': True, 'message': 'Recommendation rejected.'})


@login_required
def throughput_optimizer(request):
    """Section throughput optimization view."""
    sections = TrackSection.objects.filter(is_active=True).select_related(
        'from_station', 'to_station'
    )

    section_data = []
    for section in sections:
        recs = engine.get_section_throughput_recommendations(section)
        from apps.scheduling.models import Schedule
        today_count = Schedule.objects.filter(
            track_section=section,
            scheduled_date=timezone.now().date()
        ).count()

        utilization = min(100, (today_count / max(section.capacity, 1)) * 50)
        section_data.append({
            'section': section,
            'train_count': today_count,
            'utilization': round(utilization, 1),
            'recommendations': recs,
        })

    context = {
        'section_data': section_data,
        'page_title': 'Throughput Optimizer',
        'active_nav': 'ai_engine',
    }
    return render(request, 'ai_engine/throughput.html', context)
