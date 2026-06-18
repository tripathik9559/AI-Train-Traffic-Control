"""
Authentication Views
Login, Register, Profile, Password Reset, Logout.
"""

import logging
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator

from .models import User, UserActivity
from .forms import (
    CustomLoginForm, CustomRegisterForm, ProfileUpdateForm,
    PasswordChangeForm, AdminUserForm,
    ForgotPasswordForm, PasswordResetConfirmForm,
)

logger = logging.getLogger(__name__)


def login_view(request):
    """Handle user login with role-based redirection."""
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    form = CustomLoginForm(data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)
                    user.update_last_active()

                    # Log activity
                    UserActivity.objects.create(
                        user=user,
                        action='LOGIN',
                        description=f'User logged in from {request.META.get("REMOTE_ADDR")}',
                        ip_address=request.META.get('REMOTE_ADDR'),
                    )

                    messages.success(request, f'Welcome back, {user.display_name}!')
                    next_url = request.GET.get('next', 'dashboard:index')
                    return redirect(next_url)
                else:
                    messages.error(request, 'Your account is deactivated. Contact administrator.')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please correct the errors below.')

    context = {
        'form': form,
        'page_title': 'Login — Railway Control System',
    }
    return render(request, 'auth/login.html', context)


def register_view(request):
    """Handle user registration."""
    if request.user.is_authenticated and not request.user.is_admin:
        return redirect('dashboard:index')

    form = CustomRegisterForm(request.POST or None, request.FILES or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            user.save()

            UserActivity.objects.create(
                user=user,
                action='REGISTER',
                description='New user account created',
                ip_address=request.META.get('REMOTE_ADDR'),
            )

            messages.success(request, f'Account created for {user.username}. Please login.')
            return redirect('auth:login')
        else:
            messages.error(request, 'Please correct the errors below.')

    context = {
        'form': form,
        'page_title': 'Register — Railway Control System',
    }
    return render(request, 'auth/register.html', context)


@login_required
def logout_view(request):
    """Handle user logout."""
    UserActivity.objects.create(
        user=request.user,
        action='LOGOUT',
        description='User logged out',
        ip_address=request.META.get('REMOTE_ADDR'),
    )
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('auth:login')


@login_required
def profile_view(request):
    """Display and update user profile."""
    form = ProfileUpdateForm(
        request.POST or None,
        request.FILES or None,
        instance=request.user
    )

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('auth:profile')
        else:
            messages.error(request, 'Please correct the errors below.')

    # Recent activities
    activities = UserActivity.objects.filter(user=request.user).order_by('-timestamp')[:10]

    context = {
        'form': form,
        'activities': activities,
        'page_title': 'My Profile',
        'active_nav': 'profile',
    }
    return render(request, 'auth/profile.html', context)


@login_required
def password_change_view(request):
    """Handle password change."""
    form = PasswordChangeForm(request.user, request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)

            UserActivity.objects.create(
                user=request.user,
                action='PASSWORD_CHANGE',
                description='User changed password',
                ip_address=request.META.get('REMOTE_ADDR'),
            )

            messages.success(request, 'Password changed successfully.')
            return redirect('auth:profile')
        else:
            messages.error(request, 'Please correct the errors below.')

    context = {
        'form': form,
        'page_title': 'Change Password',
        'active_nav': 'profile',
    }
    return render(request, 'auth/password_change.html', context)


@login_required
def user_list_view(request):
    """Admin-only: List all users."""
    if not request.user.is_admin:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard:index')

    users = User.objects.all().order_by('-created_at')
    search = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')

    if search:
        users = users.filter(
            username__icontains=search
        ) | users.filter(
            first_name__icontains=search
        ) | users.filter(
            last_name__icontains=search
        ) | users.filter(
            email__icontains=search
        )

    if role_filter:
        users = users.filter(role=role_filter)

    paginator = Paginator(users, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'role_filter': role_filter,
        'roles': User.Role.choices,
        'page_title': 'User Management',
        'active_nav': 'users',
        'total_users': users.count(),
        'admin_count': User.objects.filter(role=User.Role.ADMIN).count(),
        'controller_count': User.objects.filter(role=User.Role.SECTION_CONTROLLER).count(),
    }
    return render(request, 'auth/user_list.html', context)


@login_required
def toggle_user_status(request, user_id):
    """Admin: Toggle user active status."""
    if not request.user.is_admin:
        return JsonResponse({'error': 'Access denied'}, status=403)

    target_user = get_object_or_404(User, id=user_id)
    if target_user == request.user:
        return JsonResponse({'error': 'Cannot deactivate yourself'}, status=400)

    target_user.is_active = not target_user.is_active
    target_user.save()

    status = 'activated' if target_user.is_active else 'deactivated'
    return JsonResponse({
        'success': True,
        'is_active': target_user.is_active,
        'message': f'User {target_user.username} {status} successfully.'
    })


# ─────────────────────────────────────────────────────────────────────────────
# PASSWORD RESET — FORGOT PASSWORD FLOW
# ─────────────────────────────────────────────────────────────────────────────

def forgot_password_view(request):
    """Step 1: User enters email → token generated → link shown (console email in dev)."""
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    form = ForgotPasswordForm(request.POST or None)
    token_sent = False

    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        try:
            user = User.objects.get(email__iexact=email, is_active=True)
            from .models import PasswordResetToken
            reset_token = PasswordResetToken.generate_for(user)

            # Build reset URL
            reset_url = request.build_absolute_uri(
                f"/auth/password-reset/{reset_token.token}/"
            )

            # Send via Django email backend (console in dev, SMTP in prod)
            from django.core.mail import send_mail
            from django.conf import settings as dj_settings
            send_mail(
                subject="Password Reset — RailControl AI",
                message=(
                    f"Hello {user.display_name},\n\n"
                    f"You requested a password reset for your RailControl AI account.\n"
                    f"Click the link below to set a new password (valid for 1 hour):\n\n"
                    f"{reset_url}\n\n"
                    f"If you did not request this, please ignore this email.\n\n"
                    f"— RailControl AI System"
                ),
                from_email=getattr(dj_settings, 'DEFAULT_FROM_EMAIL', 'noreply@railcontrol.ai'),
                recipient_list=[user.email],
                fail_silently=False,
            )

            UserActivity.objects.create(
                user=user,
                action='PASSWORD_RESET_REQUESTED',
                description=f'Password reset requested from {request.META.get("REMOTE_ADDR")}',
                ip_address=request.META.get('REMOTE_ADDR'),
            )

            logger.info("Password reset token created for user: %s", user.username)
            token_sent = True

        except User.DoesNotExist:
            pass  # Form already validated — this path shouldn't be hit
        except Exception as exc:
            logger.error("Password reset email failed: %s", exc)
            messages.error(request, "Could not send reset email. Please try again later.")

    context = {
        'form': form,
        'token_sent': token_sent,
        'page_title': 'Forgot Password — Railway Control System',
    }
    return render(request, 'auth/forgot_password.html', context)


def password_reset_confirm_view(request, token):
    """Step 2: User clicks link → sets new password."""
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    from .models import PasswordResetToken
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError as DjValidationError

    try:
        reset_obj = PasswordResetToken.objects.select_related('user').get(token=token)
    except PasswordResetToken.DoesNotExist:
        reset_obj = None

    token_valid = reset_obj is not None and reset_obj.is_valid
    form = PasswordResetConfirmForm(request.POST or None)
    reset_done = False

    if request.method == 'POST' and token_valid:
        if form.is_valid():
            new_password = form.cleaned_data['new_password1']
            user = reset_obj.user
            try:
                validate_password(new_password, user)
            except DjValidationError as exc:
                form.add_error('new_password1', exc)
            else:
                user.set_password(new_password)
                user.save(update_fields=['password'])
                reset_obj.used = True
                reset_obj.save(update_fields=['used'])

                UserActivity.objects.create(
                    user=user,
                    action='PASSWORD_RESET_COMPLETED',
                    description='Password reset via forgot-password link',
                    ip_address=request.META.get('REMOTE_ADDR'),
                )
                logger.info("Password reset completed for user: %s", user.username)
                reset_done = True

    context = {
        'form': form,
        'token_valid': token_valid,
        'reset_done': reset_done,
        'page_title': 'Reset Password — Railway Control System',
    }
    return render(request, 'auth/password_reset_confirm.html', context)
