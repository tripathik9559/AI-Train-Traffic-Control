"""
Authentication Models
Custom User model with role-based access control.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """Extended User model with role-based access control."""

    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrator'
        SECTION_CONTROLLER = 'SECTION_CONTROLLER', 'Section Controller'
        SUPERVISOR = 'SUPERVISOR', 'Supervisor'

    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.SECTION_CONTROLLER,
    )
    employee_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    department = models.CharField(max_length=100, blank=True, default='Operations')
    phone = models.CharField(max_length=15, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    section_assigned = models.CharField(max_length=100, blank=True)
    is_on_duty = models.BooleanField(default=False)
    last_active = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'auth_users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['employee_id']),
        ]

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_section_controller(self):
        return self.role == self.Role.SECTION_CONTROLLER

    @property
    def is_supervisor(self):
        return self.role == self.Role.SUPERVISOR

    def update_last_active(self):
        self.last_active = timezone.now()
        self.save(update_fields=['last_active'])

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        initials = (self.first_name[0] if self.first_name else self.username[0]).upper()
        return None

    @property
    def display_name(self):
        return self.get_full_name() or self.username


class UserActivity(models.Model):
    """Track user activities for audit purposes."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'auth_user_activities'
        verbose_name = 'User Activity'
        verbose_name_plural = 'User Activities'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} - {self.action} at {self.timestamp}"


class PasswordResetToken(models.Model):
    """One-time token for self-service password reset."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    class Meta:
        db_table = 'auth_password_reset_tokens'
        verbose_name = 'Password Reset Token'
        ordering = ['-created_at']

    def __str__(self):
        return f"Reset token for {self.user.username}"

    @property
    def is_valid(self):
        from django.utils import timezone
        return not self.used and self.expires_at > timezone.now()

    @classmethod
    def generate_for(cls, user):
        """Invalidate old tokens and create a fresh one (valid 1 hour)."""
        import secrets
        from django.utils import timezone
        from datetime import timedelta
        cls.objects.filter(user=user, used=False).update(used=True)
        token = secrets.token_urlsafe(48)
        return cls.objects.create(
            user=user,
            token=token,
            expires_at=timezone.now() + timedelta(hours=1),
        )
