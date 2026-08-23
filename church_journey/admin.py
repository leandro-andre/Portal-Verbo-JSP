from django.contrib import admin

from .models import (
    ChurchJourney,
    DiscipleshipAttendance,
    DiscipleshipClass,
    DiscipleshipClassAssistant,
    DiscipleshipEnrollment,
    DiscipleshipLesson,
    Membership,
    MembershipStatusHistory,
)


@admin.register(ChurchJourney)
class ChurchJourneyAdmin(admin.ModelAdmin):
    list_display = ("person", "started_at", "created_at", "updated_at")
    list_select_related = ("person",)
    search_fields = ("person__full_name", "person__preferred_name", "person__email")


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("person", "status", "member_since", "approved_by", "approved_at")
    list_filter = ("status", "member_since", "approved_at")
    list_select_related = ("person", "approved_by")
    search_fields = ("person__full_name", "person__preferred_name", "person__email")


@admin.register(MembershipStatusHistory)
class MembershipStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("membership", "from_status", "to_status", "changed_by", "changed_at")
    list_filter = ("from_status", "to_status", "changed_at")
    list_select_related = ("membership__person", "changed_by")
    readonly_fields = ("membership", "from_status", "to_status", "changed_by", "changed_at", "reason")
    search_fields = ("membership__person__full_name", "membership__person__preferred_name", "changed_by__username")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


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


@admin.register(DiscipleshipEnrollment)
class DiscipleshipEnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        "person",
        "discipleship_class",
        "status",
        "enrolled_at",
        "withdrawn_at",
        "completed_at",
    )
    list_filter = ("status", "enrolled_at", "completed_at")
    list_select_related = ("person", "discipleship_class")
    search_fields = ("person__full_name", "person__preferred_name", "discipleship_class__name")


@admin.register(DiscipleshipLesson)
class DiscipleshipLessonAdmin(admin.ModelAdmin):
    list_display = ("title", "discipleship_class", "lesson_date", "status")
    list_filter = ("status", "lesson_date")
    list_select_related = ("discipleship_class",)
    search_fields = ("title", "discipleship_class__name")


@admin.register(DiscipleshipClassAssistant)
class DiscipleshipClassAssistantAdmin(admin.ModelAdmin):
    list_display = ("person", "discipleship_class", "created_at")
    list_select_related = ("person", "discipleship_class")
    search_fields = ("person__full_name", "person__preferred_name", "discipleship_class__name")


@admin.register(DiscipleshipAttendance)
class DiscipleshipAttendanceAdmin(admin.ModelAdmin):
    list_display = ("enrollment", "lesson", "status", "recorded_by", "updated_at")
    list_filter = ("status", "lesson__lesson_date")
    list_select_related = ("enrollment__person", "lesson", "recorded_by")
    search_fields = ("enrollment__person__full_name", "lesson__title", "recorded_by__username")
