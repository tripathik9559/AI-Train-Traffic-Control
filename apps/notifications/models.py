"""
Notification Models
System notifications for conflicts, delays, and alerts.
"""

from django.db import models
from apps.authentication.models import User


class Notification(models.Model):
    """System notification for a user."""

    class NotificationType(models.TextChoices):
        CONFLICT = 'CONFLICT', 'Conflict Alert'
        DELAY = 'DELAY', 'Delay Alert'
        RECOMMENDATION = 'RECOMMENDATION', 'AI Recommendation'
        SYSTEM = 'SYSTEM', 'System Notice'
        INFO = 'INFO', 'Information'
        SUCCESS = 'SUCCESS', 'Success'

    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        NORMAL = 'NORMAL', 'Normal'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical'

    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='notifications', null=True, blank=True,
        help_text='null = broadcast to all'
    )
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.NORMAL)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    is_broadcast = models.BooleanField(default=False)

    related_conflict_id = models.IntegerField(null=True, blank=True)
    related_train_id = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        user_str = self.user.username if self.user else 'ALL'
        return f"[{self.notification_type}] {self.title} → {user_str}"

    @property
    def type_icon(self):
        icons = {
            'CONFLICT': '⚠️',
            'DELAY': '🕐',
            'RECOMMENDATION': '🤖',
            'SYSTEM': '🔧',
            'INFO': 'ℹ️',
            'SUCCESS': '✅',
        }
        return icons.get(self.notification_type, '📢')

    @property
    def type_color(self):
        colors = {
            'CONFLICT': '#e74c3c',
            'DELAY': '#f39c12',
            'RECOMMENDATION': '#3498db',
            'SYSTEM': '#9b59b6',
            'INFO': '#17a2b8',
            'SUCCESS': '#2ecc71',
        }
        return colors.get(self.notification_type, '#6c757d')

    def mark_read(self):
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
