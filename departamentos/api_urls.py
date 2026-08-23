from django.urls import path

from . import api_views


urlpatterns = [
    path("departments/", api_views.DepartmentListCreateView.as_view(), name="department-list"),
    path("departments/<int:pk>/", api_views.DepartmentDetailView.as_view(), name="department-detail"),
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
