from django.urls import path

from .views import PersonChurchJourneyView


urlpatterns = [
    path(
        "people/<int:person_id>/church-journey/",
        PersonChurchJourneyView.as_view(),
        name="person-church-journey",
    ),
]
