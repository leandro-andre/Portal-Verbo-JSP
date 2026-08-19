from django.contrib import admin

from .models import Person


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("full_name", "preferred_name", "birth_date", "status", "email", "phone")
    list_filter = ("status",)
    search_fields = ("full_name", "preferred_name", "email", "phone")
    ordering = ("full_name", "birth_date")
