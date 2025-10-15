from django.contrib.auth import get_user_model
from django.shortcuts import redirect

User = get_user_model()


class RoleRestrictionMiddleware:
    """
    Middleware to enforce role-based access control:
    - SUPERADMIN: Only admin system access
    - ADMIN: Only main system access (no admin system)
    - FIELD_WORKER: Only main system access (no admin system)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and hasattr(request.user, "role"):
            current_path = request.path
            
            # SUPERADMIN restrictions: redirect to admin system from main system
            if request.user.role == User.Role.SUPERADMIN:
                restricted_urls = [
                    "/fauna/",
                    "/sites/",
                    "/census/",
                    "/reports/",
                    "/analytics/",
                    "/image-processing/",
                    "/weather/",
                ]

                if any(current_path.startswith(url) for url in restricted_urls):
                    return redirect("admin_system:admin_dashboard")

                if current_path == "/" and request.method == "GET":
                    return redirect("admin_system:admin_dashboard")
            
            # ADMIN and FIELD_WORKER restrictions: deny access to admin system
            elif request.user.role in [User.Role.ADMIN, User.Role.FIELD_WORKER]:
                if current_path.startswith("/admin-system/"):
                    from django.contrib import messages
                    messages.error(request, "Access denied. Admin system access requires SUPERADMIN privileges.")
                    return redirect("home")

        response = self.get_response(request)
        return response
