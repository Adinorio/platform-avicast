from django.contrib import admin
from django.utils.html import format_html

from apps.users.models import User

from .models import FieldWorkSchedule, WeatherAlert, WeatherForecast


@admin.register(WeatherForecast)
class WeatherForecastAdmin(admin.ModelAdmin):
    list_display = (
        "site",
        "forecast_date",
        "forecast_time",
        "temperature",
        "weather_condition",
        "field_work_score",
        "field_work_recommendation",
        "api_source",
    )
    list_filter = ("site", "weather_condition", "api_source", "forecast_date", "tide_condition")
    search_fields = ("site__name", "site__location", "api_source")
    readonly_fields = ("created_at", "updated_at", "field_work_score", "field_work_recommendation")
    ordering = ("-forecast_date", "-forecast_time")

    fieldsets = (
        ("Location & Timing", {"fields": ("site", "forecast_date", "forecast_time")}),
        (
            "Weather Data",
            {
                "fields": (
                    "temperature",
                    "humidity",
                    "wind_speed",
                    "wind_direction",
                    "precipitation",
                    "pressure",
                    "weather_condition",
                    "visibility",
                )
            },
        ),
        (
            "Tide Information",
            {"fields": ("tide_condition", "tide_height"), "classes": ("collapse",)},
        ),
        (
            "API Information",
            {"fields": ("api_source", "api_response_data"), "classes": ("collapse",)},
        ),
        (
            "Field Work Analysis",
            {"fields": ("field_work_score", "field_work_recommendation"), "classes": ("collapse",)},
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def field_work_score(self, obj):
        score = obj.field_work_score
        if score >= 80:
            color = "green"
        elif score >= 60:
            color = "orange"
        elif score >= 40:
            color = "yellow"
        else:
            color = "red"

        return format_html('<span style="color: {};">{}/100</span>', color, score)

    field_work_score.short_description = "Field Work Score"

    def field_work_recommendation(self, obj):
        recommendation = obj.field_work_recommendation
        if recommendation == "EXCELLENT":
            return format_html('<span style="color: green;">✅ {}</span>', recommendation)
        elif recommendation == "GOOD":
            return format_html('<span style="color: blue;">👍 {}</span>', recommendation)
        elif recommendation == "MODERATE":
            return format_html('<span style="color: orange;">⚠️ {}</span>', recommendation)
        elif recommendation == "POOR":
            return format_html('<span style="color: red;">❌ {}</span>', recommendation)
        else:
            return format_html('<span style="color: darkred;">🚫 {}</span>', recommendation)

    field_work_recommendation.short_description = "Recommendation"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == User.Role.SUPERADMIN:
            return qs
        elif request.user.role == User.Role.ADMIN:
            return qs
        else:
            return qs  # Field workers can view all weather data

    def has_add_permission(self, request):
        return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]

    def has_change_permission(self, request, obj=None):
        return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]

    def has_delete_permission(self, request, obj=None):
        return request.user.role == User.Role.SUPERADMIN


@admin.register(FieldWorkSchedule)
class FieldWorkScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "site",
        "planned_date",
        "planned_time_range",
        "status",
        "assigned_personnel_count",
        "weather_optimization",
        "created_by",
    )
    list_filter = ("status", "planned_date", "site", "created_by__role")
    search_fields = ("title", "description", "site__name", "created_by__employee_id")
    readonly_fields = (
        "created_by",
        "created_at",
        "updated_at",
        "weather_score",
        "weather_recommendation",
    )
    ordering = ("-planned_date", "-planned_start_time")

    fieldsets = (
        ("Schedule Information", {"fields": ("title", "description", "site", "status")}),
        (
            "Timing",
            {
                "fields": (
                    "planned_date",
                    "planned_start_time",
                    "planned_end_time",
                    "actual_start_time",
                    "actual_end_time",
                )
            },
        ),
        ("Personnel", {"fields": ("assigned_personnel", "supervisor")}),
        (
            "Weather Optimization",
            {"fields": ("weather_score", "weather_recommendation"), "classes": ("collapse",)},
        ),
        (
            "Notes & Results",
            {
                "fields": ("planning_notes", "execution_notes", "results_summary"),
                "classes": ("collapse",),
            },
        ),
        (
            "User Information",
            {"fields": ("created_by", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def planned_time_range(self, obj):
        if obj.planned_start_time and obj.planned_end_time:
            return f"{obj.planned_start_time.strftime('%H:%M')} - {obj.planned_end_time.strftime('%H:%M')}"
        return "N/A"

    planned_time_range.short_description = "Time Range"

    def assigned_personnel_count(self, obj):
        count = obj.assigned_personnel.count()
        return f"{count} person(s)"

    assigned_personnel_count.short_description = "Personnel"

    def weather_optimization(self, obj):
        if obj.weather_recommendation:
            if obj.weather_recommendation in ["EXCELLENT", "GOOD"]:
                return format_html('<span style="color: green;">✅ Optimized</span>')
            else:
                return format_html('<span style="color: orange;">⚠️ Not Optimized</span>')
        return format_html('<span style="color: gray;">⏳ Pending</span>')

    weather_optimization.short_description = "Weather Optimization"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == User.Role.SUPERADMIN:
            return qs
        elif request.user.role == User.Role.ADMIN:
            return qs
        else:
            return qs.filter(assigned_personnel=request.user)

    def has_add_permission(self, request):
        return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]

    def has_change_permission(self, request, obj=None):
        if obj is None:
            return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]
        if request.user in obj.assigned_personnel.all():
            return True
        return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]

    def has_delete_permission(self, request, obj=None):
        return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]


@admin.register(WeatherAlert)
class WeatherAlertAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "alert_type",
        "severity",
        "valid_period",
        "affected_sites_count",
        "is_active",
        "issued_at",
    )
    list_filter = ("alert_type", "severity", "issued_at", "valid_from", "valid_until")
    search_fields = ("title", "description", "source", "external_id")
    readonly_fields = ("issued_at", "is_active")
    ordering = ("-issued_at",)

    fieldsets = (
        ("Alert Information", {"fields": ("title", "description", "alert_type", "severity")}),
        ("Timing", {"fields": ("valid_from", "valid_until", "issued_at")}),
        ("Affected Areas", {"fields": ("sites",)}),
        (
            "Source Information",
            {"fields": ("source", "external_id", "metadata"), "classes": ("collapse",)},
        ),
        ("Status", {"fields": ("is_active",), "classes": ("collapse",)}),
    )

    def valid_period(self, obj):
        return f"{obj.valid_from.strftime('%Y-%m-%d %H:%M')} to {obj.valid_until.strftime('%Y-%m-%d %H:%M')}"

    valid_period.short_description = "Valid Period"

    def affected_sites_count(self, obj):
        count = obj.sites.count()
        return f"{count} site(s)"

    affected_sites_count.short_description = "Affected Sites"

    def is_active(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✅ Active</span>')
        else:
            return format_html('<span style="color: red;">❌ Expired</span>')

    is_active.short_description = "Status"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == User.Role.SUPERADMIN:
            return qs
        elif request.user.role == User.Role.ADMIN:
            return qs
        else:
            return qs  # Field workers can view all weather alerts

    def has_add_permission(self, request):
        return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]

    def has_change_permission(self, request, obj=None):
        return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]

    def has_delete_permission(self, request, obj=None):
        return request.user.role == User.Role.SUPERADMIN
