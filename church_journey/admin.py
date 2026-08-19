from django.contrib import admin

from .models import ChurchJourney


@admin.register(ChurchJourney)
class ChurchJourneyAdmin(admin.ModelAdmin):
    list_display = ("person", "started_at", "created_at", "updated_at")
    list_select_related = ("person",)
    search_fields = ("person__full_name", "person__preferred_name", "person__email")
