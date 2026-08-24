from django.urls import path

from . import views


urlpatterns = [
    path("departments/", views.ScheduleDepartmentListView.as_view(), name="schedule-department-list"),
    path("monthly/", views.MonthlyScheduleView.as_view(), name="schedule-monthly"),
    path("schedules/", views.ScheduleListCreateView.as_view(), name="schedule-list"),
    path("schedules/<int:pk>/", views.ScheduleDetailView.as_view(), name="schedule-detail"),
    path("schedules/<int:pk>/validation/", views.ScheduleValidationView.as_view(), name="schedule-validation"),
    path("schedules/<int:pk>/publish/", views.SchedulePublishView.as_view(), name="schedule-publish"),
    path("schedules/<int:pk>/reopen/", views.ScheduleReopenView.as_view(), name="schedule-reopen"),
    path("schedules/<int:pk>/cancel/", views.ScheduleCancelView.as_view(), name="schedule-cancel"),
    path("schedules/<int:pk>/reactivate/", views.ScheduleReactivateView.as_view(), name="schedule-reactivate"),
    path("schedules/<int:schedule_id>/assignments/", views.ScheduleAssignmentListCreateView.as_view(), name="schedule-assignment-list"),
    path("schedules/<int:schedule_id>/assignments/<int:assignment_id>/", views.ScheduleAssignmentDeleteView.as_view(), name="schedule-assignment-delete"),
    path("schedules/<int:schedule_id>/eligible-members/", views.ScheduleEligibleMembersView.as_view(), name="schedule-eligible-members"),
]
