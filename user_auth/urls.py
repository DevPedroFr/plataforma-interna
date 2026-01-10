"""
URLs de autenticação
"""

from django.urls import path
from . import views

app_name = 'auth'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('delete_user/', views.delete_user_view, name='delete_user'),
    path('create_user/', views.create_user_view, name='create_user'),
    path('update_user/', views.update_user_view, name='update_user'),
    path('user_password/', views.user_password_view, name='user_password'),
]
