from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # User Management Dashboard
    path('dashboard/', views.user_management_dashboard, name='user_management_dashboard'),
    path('list/', views.user_management_list, name='user_management_list'),
    path('create/', views.create_user, name='create_user'),
    path('update/<int:user_id>/', views.update_user, name='update_user'),
    path('logs/', views.system_logs, name='system_logs'),

    # Password Management
    path('change-password/', views.change_password, name='change_password'),
]
