from django.urls import path

from .api_views import SecretaryDashboardView


urlpatterns = [
    path("secretaria/dashboard/", SecretaryDashboardView.as_view(), name="secretary-dashboard"),
]
