from django.urls import path

from . import views


app_name = "financeiro"

urlpatterns = [
    path("configuracao/", views.ConfiguracaoFinanceiraUpdateView.as_view(), name="configuracao"),
    path("contribuicoes/", views.ContribuicaoAdminListView.as_view(), name="contribuicoes"),
]
