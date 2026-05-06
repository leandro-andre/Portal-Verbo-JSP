from django.urls import path

from . import views


app_name = "financeiro"

urlpatterns = [
    path("contribuir/", views.ContribuicaoCreateView.as_view(), name="contribuir"),
    path("retorno/", views.RetornoPagamentoView.as_view(), name="retorno"),
    path("webhook/", views.MercadoPagoWebhookView.as_view(), name="webhook"),
]
