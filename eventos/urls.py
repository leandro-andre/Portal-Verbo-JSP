from django.urls import path

from . import views

app_name = "eventos"

urlpatterns = [
    path("agenda/", views.agenda, name="agenda"),
    path("eventos/checkin/<uuid:codigo_checkin>/", views.CheckinPorTokenView.as_view(), name="checkin_token"),
]

