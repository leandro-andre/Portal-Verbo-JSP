from django.urls import include, path

from . import views

app_name = "departamentos"

urlpatterns = [
    path("", views.DepartamentoListView.as_view(), name="lista"),
    path("novo/", views.DepartamentoCreateView.as_view(), name="novo"),
    path("<int:pk>/editar/", views.DepartamentoUpdateView.as_view(), name="editar"),
    path("<int:pk>/membros/", views.DepartamentoMembrosView.as_view(), name="membros"),
    path(
        "<int:pk>/membros/<int:participacao_id>/status/",
        views.DepartamentoMembroStatusView.as_view(),
        name="membro_status",
    ),
    path("", include("escalas.urls")),
]
