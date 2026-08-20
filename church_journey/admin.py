from django.contrib import admin

from .models import ChurchJourney, DiscipleshipClass


@admin.register(ChurchJourney)
class ChurchJourneyAdmin(admin.ModelAdmin):
    list_display = ("person", "started_at", "created_at", "updated_at")
    list_select_related = ("person",)
    search_fields = ("person__full_name", "person__preferred_name", "person__email")


@admin.register(DiscipleshipClass)
class DiscipleshipClassAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "teacher",
        "start_date",
        "expected_end_date",
        "planned_sessions",
        "status",
    )
    list_filter = ("status", "start_date")
    list_select_related = ("teacher",)
    search_fields = ("name", "teacher__full_name", "teacher__preferred_name")
