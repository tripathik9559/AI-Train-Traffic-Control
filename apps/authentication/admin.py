from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserActivity


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_on_duty', 'created_at']
    list_filter = ['role', 'is_active', 'is_on_duty', 'department']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'employee_id']
    ordering = ['-created_at']
    fieldsets = UserAdmin.fieldsets + (
        ('Railway Info', {'fields': ('role', 'employee_id', 'department', 'phone', 'section_assigned', 'is_on_duty', 'avatar')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Railway Info', {'fields': ('role', 'employee_id', 'department', 'phone', 'section_assigned')}),
    )


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'ip_address', 'timestamp']
    list_filter = ['action']
    search_fields = ['user__username', 'action']
    readonly_fields = ['timestamp']
    ordering = ['-timestamp']
