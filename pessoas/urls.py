from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    MyUnavailabilityDeactivateView,
    MyUnavailabilityDetailView,
    MyUnavailabilityListCreateView,
    MyUnavailabilityReactivateView,
    PersonUnavailabilityDeactivateView,
    PersonUnavailabilityDetailView,
    PersonUnavailabilityListCreateView,
    PersonUnavailabilityReactivateView,
    PersonViewSet,
)


router = DefaultRouter()
router.register("", PersonViewSet, basename="person")

urlpatterns = [
    path("me/unavailability/", MyUnavailabilityListCreateView.as_view(), name="my-unavailability-list"),
    path("me/unavailability/<int:pk>/", MyUnavailabilityDetailView.as_view(), name="my-unavailability-detail"),
    path(
        "me/unavailability/<int:pk>/deactivate/",
        MyUnavailabilityDeactivateView.as_view(),
        name="my-unavailability-deactivate",
    ),
    path(
        "me/unavailability/<int:pk>/reactivate/",
        MyUnavailabilityReactivateView.as_view(),
        name="my-unavailability-reactivate",
    ),
    path(
        "<int:person_id>/unavailability/",
        PersonUnavailabilityListCreateView.as_view(),
        name="person-unavailability-list",
    ),
    path(
        "<int:person_id>/unavailability/<int:pk>/",
        PersonUnavailabilityDetailView.as_view(),
        name="person-unavailability-detail",
    ),
    path(
        "<int:person_id>/unavailability/<int:pk>/deactivate/",
        PersonUnavailabilityDeactivateView.as_view(),
        name="person-unavailability-deactivate",
    ),
    path(
        "<int:person_id>/unavailability/<int:pk>/reactivate/",
        PersonUnavailabilityReactivateView.as_view(),
        name="person-unavailability-reactivate",
    ),
    path("", include(router.urls)),
]
