from django.urls import path

from .api_views import (
    GlobalSearchView,
    NotificationListView,
    NotificationReadAllView,
    NotificationReadView,
    NotificationRecentView,
    SecretaryDashboardView,
)


urlpatterns = [
    path("notifications/", NotificationListView.as_view(), name="notification-list"),
    path("notifications/recent/", NotificationRecentView.as_view(), name="notification-recent"),
    path("notifications/read-all/", NotificationReadAllView.as_view(), name="notification-read-all"),
    path("notifications/<int:pk>/read/", NotificationReadView.as_view(), name="notification-read"),
    path("search/", GlobalSearchView.as_view(), name="global-search"),
    path("secretaria/dashboard/", SecretaryDashboardView.as_view(), name="secretary-dashboard"),
]
