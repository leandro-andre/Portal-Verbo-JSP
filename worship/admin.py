from django.contrib import admin

from .models import WorshipService, WorshipServiceTemplate


@admin.register(WorshipServiceTemplate)
class WorshipServiceTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "weekday", "time", "active")
    list_filter = ("weekday", "active")
    search_fields = ("name",)


@admin.register(WorshipService)
class WorshipServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "date", "time", "kind", "status", "template", "source_date")
    list_filter = ("kind", "status", "date")
    search_fields = ("name", "notes")
