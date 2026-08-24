from django.urls import path

from .api_views import (
    AdminAccessRequestApproveView,
    AdminAccessRequestDetailView,
    AdminAccessRequestListView,
    AdminAccessRequestRejectView,
    AdminUserDetailView,
    AdminUserDisableView,
    AdminUserEnableView,
    AdminUserPersonLinkView,
    AdminUserListView,
    MyProfilePhotoView,
    MyProfileView,
    PublicAccessRequestCreateView,
    activate_account_view,
    csrf_view,
    current_user_view,
    login_view,
    logout_view,
)
from scheduling.views import MySchedulesView


urlpatterns = [
    path("auth/csrf/", csrf_view, name="auth-csrf"),
    path("auth/current-user/", current_user_view, name="auth-current-user"),
    path("auth/login/", login_view, name="auth-login"),
    path("auth/logout/", logout_view, name="auth-logout"),
    path("auth/activate/", activate_account_view, name="auth-activate"),
    path("me/profile/", MyProfileView.as_view(), name="my-profile"),
    path("me/profile/photo/", MyProfilePhotoView.as_view(), name="my-profile-photo"),
    path("me/schedules/", MySchedulesView.as_view(), name="my-schedules"),
    path("users/", AdminUserListView.as_view(), name="admin-user-list"),
    path("users/<int:pk>/", AdminUserDetailView.as_view(), name="admin-user-detail"),
    path("users/<int:pk>/disable/", AdminUserDisableView.as_view(), name="admin-user-disable"),
    path("users/<int:pk>/enable/", AdminUserEnableView.as_view(), name="admin-user-enable"),
    path("users/<int:pk>/person/", AdminUserPersonLinkView.as_view(), name="admin-user-person"),
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
