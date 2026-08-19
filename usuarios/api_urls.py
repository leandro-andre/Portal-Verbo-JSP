from django.urls import path

from .api_views import (
    AdminAccessRequestApproveView,
    AdminAccessRequestDetailView,
    AdminAccessRequestListView,
    AdminAccessRequestRejectView,
    PublicAccessRequestCreateView,
)


urlpatterns = [
    path("access-requests/", PublicAccessRequestCreateView.as_view(), name="access-request-create"),
    path(
        "access-requests/admin/",
        AdminAccessRequestListView.as_view(),
        name="access-request-admin-list",
    ),
    path(
        "access-requests/admin/<int:pk>/",
        AdminAccessRequestDetailView.as_view(),
        name="access-request-admin-detail",
    ),
    path(
        "access-requests/admin/<int:pk>/approve/",
        AdminAccessRequestApproveView.as_view(),
        name="access-request-admin-approve",
    ),
    path(
        "access-requests/admin/<int:pk>/reject/",
        AdminAccessRequestRejectView.as_view(),
        name="access-request-admin-reject",
    ),
]
