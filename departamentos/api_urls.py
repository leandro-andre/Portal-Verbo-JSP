from django.urls import path

from . import api_views


urlpatterns = [
    path("departments/", api_views.DepartmentListCreateView.as_view(), name="department-list"),
    path("departments/<int:pk>/", api_views.DepartmentDetailView.as_view(), name="department-detail"),
    path(
        "departments/<int:department_id>/roles/",
        api_views.DepartmentRoleListCreateView.as_view(),
        name="department-role-list",
    ),
    path(
        "departments/<int:department_id>/roles/<int:role_id>/",
        api_views.DepartmentRoleDetailView.as_view(),
        name="department-role-detail",
    ),
    path(
        "departments/<int:department_id>/roles/<int:role_id>/deactivate/",
        api_views.DepartmentRoleDeactivateView.as_view(),
        name="department-role-deactivate",
    ),
    path(
        "departments/<int:department_id>/roles/<int:role_id>/reactivate/",
        api_views.DepartmentRoleReactivateView.as_view(),
        name="department-role-reactivate",
    ),
    path(
        "departments/<int:department_id>/members/",
        api_views.DepartmentMembershipListCreateView.as_view(),
        name="department-membership-list",
    ),
    path(
        "departments/<int:department_id>/schedule-requirements/",
        api_views.DepartmentScheduleRequirementListCreateView.as_view(),
        name="department-schedule-requirement-list",
    ),
    path(
        "departments/<int:department_id>/schedule-requirements/<int:requirement_id>/",
        api_views.DepartmentScheduleRequirementDetailView.as_view(),
        name="department-schedule-requirement-detail",
    ),
    path(
        "departments/<int:department_id>/schedule-requirements/<int:requirement_id>/deactivate/",
        api_views.DepartmentScheduleRequirementDeactivateView.as_view(),
        name="department-schedule-requirement-deactivate",
    ),
    path(
        "departments/<int:department_id>/schedule-requirements/<int:requirement_id>/reactivate/",
        api_views.DepartmentScheduleRequirementReactivateView.as_view(),
        name="department-schedule-requirement-reactivate",
    ),
    path(
        "departments/<int:department_id>/eligible-people/",
        api_views.DepartmentEligiblePeopleView.as_view(),
        name="department-eligible-people",
    ),
    path(
        "departments/<int:department_id>/members/<int:membership_id>/",
        api_views.DepartmentMembershipDetailView.as_view(),
        name="department-membership-detail",
    ),
    path(
        "departments/<int:department_id>/members/<int:membership_id>/deactivate/",
        api_views.DepartmentMembershipDeactivateView.as_view(),
        name="department-membership-deactivate",
    ),
    path(
        "departments/<int:department_id>/members/<int:membership_id>/reactivate/",
        api_views.DepartmentMembershipReactivateView.as_view(),
        name="department-membership-reactivate",
    ),
    path(
        "departments/<int:pk>/deactivate/",
        api_views.DepartmentDeactivateView.as_view(),
        name="department-deactivate",
    ),
    path(
        "departments/<int:pk>/reactivate/",
        api_views.DepartmentReactivateView.as_view(),
        name="department-reactivate",
    ),
]
