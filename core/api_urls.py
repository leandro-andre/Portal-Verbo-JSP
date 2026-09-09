from django.urls import path

from .api_views import GlobalSearchView, SecretaryDashboardView


urlpatterns = [
    path("search/", GlobalSearchView.as_view(), name="global-search"),
    path("secretaria/dashboard/", SecretaryDashboardView.as_view(), name="secretary-dashboard"),
]
