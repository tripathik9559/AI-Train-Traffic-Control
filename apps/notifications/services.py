"""
Notification Service — complete implementation.
Handles creation, bulk dispatch, cleanup and stats for all notification types.
"""
import logging
from django.utils import timezone
from django.db.models import Count, Q
from .models import Notification

logger = logging.getLogger(__name__)

_TYPE = Notification.NotificationType
_PRI  = Notification.Priority


class NotificationService:
    """Central service for creating and managing system notifications."""

    # ── Conflict ────────────────────────────────────────────────────────────
    def create_conflict_notification(self, conflict):
        priority_map = {
            'CRITICAL': _PRI.CRITICAL,
            'HIGH':     _PRI.HIGH,
            'MEDIUM':   _PRI.NORMAL,
            'LOW':      _PRI.LOW,
        }
        icons = {'CRITICAL': '🚨', 'HIGH': '⚠️', 'MEDIUM': '⚡', 'LOW': 'ℹ️'}
        icon  = icons.get(conflict.severity, '⚠️')
        pri   = priority_map.get(conflict.severity, _PRI.NORMAL)

        return self._create(
            notification_type=_TYPE.CONFLICT,
            priority=pri,
            title=f"{icon} {conflict.get_conflict_type_display()} — {conflict.severity} Severity",
            message=(
                f"{conflict.description[:400]}\n"
                f"Detected at {conflict.detected_at.strftime('%H:%M') if hasattr(conflict,'detected_at') else 'N/A'}. "
                f"Immediate controller review required."
            ),
            link=f"/conflicts/{conflict.id}/",
            is_broadcast=True,
            related_conflict_id=conflict.id,
            related_train_id=conflict.train_a_id,
        )

    # ── Delay ────────────────────────────────────────────────────────────────
    def create_delay_notification(self, train, delay_minutes, reason=""):
        if delay_minutes >= 60:
            severity_label = "🔴 SEVERE"
            pri = _PRI.CRITICAL
        elif delay_minutes >= 30:
            severity_label = "🟠 MAJOR"
            pri = _PRI.HIGH
        else:
            severity_label = "🟡 MINOR"
            pri = _PRI.NORMAL

        reason_text = f" Reason: {reason}." if reason else ""
        return self._create(
            notification_type=_TYPE.DELAY,
            priority=pri,
            title=f"{severity_label} Delay — {train.train_number} (+{delay_minutes} min)",
            message=(
                f"{train.train_name} ({train.train_number}) is running "
                f"{delay_minutes} minutes behind schedule.{reason_text}"
            ),
            link=f"/trains/{train.id}/",
            is_broadcast=True,
            related_train_id=train.id,
        )

    # ── AI Recommendation ────────────────────────────────────────────────────
    def create_recommendation_notification(self, train, recommendation_text, user=None):
        return self._create(
            notification_type=_TYPE.RECOMMENDATION,
            priority=_PRI.NORMAL,
            title=f"🤖 AI Recommendation — {train.train_number}",
            message=recommendation_text[:500],
            link=f"/ai-engine/priority/",
            user=user,
            is_broadcast=(user is None),
            related_train_id=train.id,
        )

    # ── System ───────────────────────────────────────────────────────────────
    def create_system_notification(self, title, message, priority='NORMAL', user=None, link=""):
        return self._create(
            notification_type=_TYPE.SYSTEM,
            priority=priority,
            title=title,
            message=message,
            link=link,
            user=user,
            is_broadcast=(user is None),
        )

    # ── Success ──────────────────────────────────────────────────────────────
    def create_success_notification(self, title, message, user=None, link=""):
        return self._create(
            notification_type=_TYPE.SUCCESS,
            priority=_PRI.LOW,
            title=f"✅ {title}",
            message=message,
            link=link,
            user=user,
            is_broadcast=(user is None),
        )

    # ── Bulk broadcast ───────────────────────────────────────────────────────
    def broadcast(self, notification_type, title, message, priority=_PRI.NORMAL, link=""):
        """Create one broadcast notification visible to all users."""
        return self._create(
            notification_type=notification_type,
            priority=priority,
            title=title,
            message=message,
            link=link,
            user=None,
            is_broadcast=True,
        )

    # ── Maintenance / cleanup ────────────────────────────────────────────────
    def purge_old_notifications(self, days=30):
        """Remove read notifications older than `days` days. Returns count deleted."""
        cutoff = timezone.now() - timezone.timedelta(days=days)
        qs = Notification.objects.filter(is_read=True, created_at__lt=cutoff)
        count, _ = qs.delete()
        logger.info("Purged %d old notifications (older than %d days)", count, days)
        return count

    # ── Stats ────────────────────────────────────────────────────────────────
    @staticmethod
    def get_stats():
        """Return aggregate notification statistics for analytics."""
        qs = Notification.objects.all()
        total = qs.count()
        unread = qs.filter(is_read=False).count()
        by_type = list(
            qs.values('notification_type')
              .annotate(count=Count('id'))
              .order_by('-count')
        )
        by_priority = list(
            qs.values('priority')
              .annotate(count=Count('id'))
              .order_by('-count')
        )
        critical_unread = qs.filter(priority=_PRI.CRITICAL, is_read=False).count()
        return {
            'total':           total,
            'unread':          unread,
            'read':            total - unread,
            'critical_unread': critical_unread,
            'by_type':         by_type,
            'by_priority':     by_priority,
        }

    # ── Internal helper ──────────────────────────────────────────────────────
    @staticmethod
    def _create(**kwargs):
        try:
            n = Notification.objects.create(**kwargs)
            logger.debug("Notification created: [%s] %s", kwargs.get('notification_type'), kwargs.get('title'))
            return n
        except Exception as exc:
            logger.error("Failed to create notification: %s | kwargs=%s", exc, kwargs)
            return None


# Module-level singleton
notification_service = NotificationService()
