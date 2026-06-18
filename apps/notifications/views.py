"""
Notification views — list, filter, mark-read, delete, stats API.
"""
import logging
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Notification
from .services import NotificationService

logger = logging.getLogger(__name__)


def _user_qs(user):
    """Base queryset visible to `user`: own + broadcasts."""
    return Notification.objects.filter(
        Q(user=user) | Q(is_broadcast=True, user__isnull=True)
    )


@login_required
def notification_list(request):
    qs = _user_qs(request.user)

    # ── Filters ──────────────────────────────────────────────────────────────
    filter_type     = request.GET.get('type', '')
    filter_priority = request.GET.get('priority', '')
    filter_read     = request.GET.get('read', '')       # 'unread' | 'read' | ''

    if filter_type:
        qs = qs.filter(notification_type=filter_type)
    if filter_priority:
        qs = qs.filter(priority=filter_priority)
    if filter_read == 'unread':
        qs = qs.filter(is_read=False)
    elif filter_read == 'read':
        qs = qs.filter(is_read=True)

    notifications = qs.order_by('-created_at')[:100]
    unread_count  = _user_qs(request.user).filter(is_read=False).count()
    stats         = NotificationService.get_stats()

    context = {
        'notifications':      notifications,
        'unread_count':       unread_count,
        'stats':              stats,
        'filter_type':        filter_type,
        'filter_priority':    filter_priority,
        'filter_read':        filter_read,
        'type_choices':       Notification.NotificationType.choices,
        'priority_choices':   Notification.Priority.choices,
        'page_title':         'Notification Centre',
        'active_nav':         'notifications',
    }
    return render(request, 'notifications/list.html', context)


# ── Mark single read ──────────────────────────────────────────────────────────
@login_required
@require_POST
def mark_read(request, notif_id):
    try:
        n = _user_qs(request.user).get(id=notif_id)
        n.mark_read()
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)


# ── Mark all read ─────────────────────────────────────────────────────────────
@login_required
@require_POST
def mark_all_read(request):
    now = timezone.now()
    updated = _user_qs(request.user).filter(is_read=False).update(
        is_read=True, read_at=now
    )
    return JsonResponse({'success': True, 'updated': updated})


# ── Delete single notification ────────────────────────────────────────────────
@login_required
@require_POST
def delete_notification(request, notif_id):
    try:
        n = _user_qs(request.user).get(id=notif_id)
        n.delete()
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)


# ── Delete all read ───────────────────────────────────────────────────────────
@login_required
@require_POST
def delete_all_read(request):
    count, _ = _user_qs(request.user).filter(is_read=True).delete()
    return JsonResponse({'success': True, 'deleted': count})


# ── API: unread count (polled by topbar) ──────────────────────────────────────
@login_required
def api_unread_count(request):
    count = _user_qs(request.user).filter(is_read=False).count()
    recent = list(
        _user_qs(request.user)
        .filter(is_read=False)
        .order_by('-created_at')[:5]
        .values('id', 'title', 'notification_type', 'priority', 'created_at')
    )
    # Serialise datetimes
    for r in recent:
        r['created_at'] = r['created_at'].isoformat()
    return JsonResponse({'count': count, 'recent': recent})


# ── API: notification stats ───────────────────────────────────────────────────
@login_required
def api_stats(request):
    return JsonResponse(NotificationService.get_stats())
