from django.contrib import admin

from .models import DepartmentScheduleRequirement, Schedule, ScheduleAssignment


class ScheduleAssignmentInline(admin.TabularInline):
    model = ScheduleAssignment
    extra = 0


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ("department", "worship_service", "status", "created_by")
    list_filter = ("status", "department")
    inlines = [ScheduleAssignmentInline]


@admin.register(ScheduleAssignment)
class ScheduleAssignmentAdmin(admin.ModelAdmin):
    list_display = ("schedule", "department_membership", "created_by", "created_at")
    list_filter = ("schedule__status", "schedule__department")


@admin.register(DepartmentScheduleRequirement)
class DepartmentScheduleRequirementAdmin(admin.ModelAdmin):
    list_display = ("department", "role", "minimum_quantity", "recommended_quantity", "active")
    list_filter = ("active", "department")
