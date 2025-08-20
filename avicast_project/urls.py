"""
URL configuration for avicast_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

def custom_login_redirect(request):
    """Custom login view that redirects based on user role"""
    if request.user.is_authenticated:
        if request.user.role == 'SUPERADMIN':
            return redirect('admin:index')
        else:
            # Redirect ADMIN and FIELD_WORKER to home page
            return redirect('home')
    return auth_views.LoginView.as_view(template_name='registration/login.html')(request)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('login/', custom_login_redirect, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('fauna/', include('apps.fauna.urls', namespace='fauna')),
    path('locations/', include('apps.locations.urls', namespace='locations')),
    path('analytics/', include('apps.analytics.urls', namespace='analytics')),
]
