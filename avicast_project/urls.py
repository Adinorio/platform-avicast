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

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.urls import include, path
from django.views.generic import TemplateView, RedirectView
# from apps.users.admin_index import custom_admin_index  # REMOVED - No longer using Django admin




def custom_login_redirect(request):
    """Custom login view that redirects based on user role"""
    if request.user.is_authenticated:
        if request.user.role == "SUPERADMIN":
            return redirect("admin_system:admin_dashboard")
        else:
            # Redirect ADMIN and FIELD_WORKER to main system home page
            return redirect("home")
    return auth_views.LoginView.as_view(template_name="registration/login.html")(request)


urlpatterns = [
    # path("admin/", admin.site.urls),  # REMOVED - Using custom admin system instead
    path("admin/", RedirectView.as_view(url='/admin-system/', permanent=False)),  # Redirect old admin to custom admin
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("login/", custom_login_redirect, name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="home"), name="logout"),
    path("users/", include("apps.users.urls", namespace="users")),
    path("fauna/", include("apps.fauna.urls", namespace="fauna")),
    path("admin-system/", include("apps.admin_system.urls", namespace="admin_system")),
    path("locations/", include("apps.locations.urls", namespace="locations")),
    path("analytics/", include("apps.analytics_new.urls", namespace="analytics_new")),
    path("image-processing/", include("apps.image_processing.urls", namespace="image_processing")),
    path("weather/", include("apps.weather.urls", namespace="weather")),
    path("system-logs/", include("apps.users.urls", namespace="system_logs")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
