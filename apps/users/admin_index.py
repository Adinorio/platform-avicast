"""
Custom Admin Index View for AVICAST Dashboard
Provides statistics and enhanced dashboard functionality
"""

from django.contrib.admin import AdminSite
from django.contrib.admin.views.main import ChangeList
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Count
from django.contrib.auth import get_user_model

from apps.fauna.models import Species
# from apps.locations.models import Site  # Temporarily disabled during revamp

User = get_user_model()


@staff_member_required
def custom_admin_index(request):
    """
    Custom admin index view with statistics
    """
    from django.contrib.admin.sites import site
    from django.contrib.admin.views.main import ChangeList
    
    # Get app list from admin site
    app_list = site.get_app_list(request)
    
    # Get statistics
    try:
        total_users = User.objects.count()
    except:
        total_users = 0
    
    try:
        total_species = Species.objects.count()
    except:
        total_species = 0
    
    try:
        # total_observations = Site.objects.count()  # Temporarily disabled during revamp
        total_observations = 0
    except:
        total_observations = 0
    
    # Image processing temporarily removed for remake
    
    # Get recent actions
    from django.contrib.admin.models import LogEntry
    recent_actions = LogEntry.objects.select_related('content_type', 'user').order_by('-action_time')[:10]
    
    context = {
        'title': 'AVICAST System Administration',
        'app_list': app_list,
        'total_users': total_users,
        'total_species': total_species,
        'total_sites': total_observations,
        'recent_actions': recent_actions,
    }
    # Include admin site context so base.html conditions (e.g., is_nav_sidebar_enabled)
    # and header/usertools variables are present
    context.update(site.each_context(request))
    
    return render(request, 'admin/index.html', context)
