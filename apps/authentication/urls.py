from django.urls import path
from . import views

app_name = 'auth'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('password-change/', views.password_change_view, name='password_change'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('password-reset/<str:token>/', views.password_reset_confirm_view, name='password_reset_confirm'),
    path('users/', views.user_list_view, name='user_list'),
    path('users/<int:user_id>/toggle/', views.toggle_user_status, name='toggle_user_status'),
]
