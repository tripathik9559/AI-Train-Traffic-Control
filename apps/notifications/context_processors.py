from .models import Notification


def notifications_processor(request):
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            is_read=False
        ).filter(
            user=request.user
        ).count() + Notification.objects.filter(
            is_read=False, is_broadcast=True, user__isnull=True
        ).count()

        recent = Notification.objects.filter(
            is_read=False
        ).filter(
            user=request.user
        ).order_by('-created_at')[:5]

        broadcast = Notification.objects.filter(
            is_read=False, is_broadcast=True, user__isnull=True
        ).order_by('-created_at')[:3]

        notifications = list(recent) + list(broadcast)
        notifications.sort(key=lambda n: n.created_at, reverse=True)

        return {
            'unread_notification_count': unread_count,
            'recent_notifications': notifications[:5],
        }
    return {'unread_notification_count': 0, 'recent_notifications': []}
