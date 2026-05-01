from django.urls import path

from . import views


app_name = "ministros"

urlpatterns = [
    path("ministros/formulario/<uuid:token>/", views.MinistroVisitanteFormView.as_view(), name="formulario_externo"),
    path("ministros/formulario/sucesso/", views.MinistroVisitanteSuccessView.as_view(), name="formulario_sucesso"),
]
