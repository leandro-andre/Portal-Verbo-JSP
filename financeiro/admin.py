from django.contrib import admin

from .forms import ConfiguracaoFinanceiraForm
from .models import ConfiguracaoFinanceira, Contribuicao


@admin.register(ConfiguracaoFinanceira)
class ConfiguracaoFinanceiraAdmin(admin.ModelAdmin):
    form = ConfiguracaoFinanceiraForm
    list_display = ("ambiente", "conectado", "ultima_verificacao", "atualizado_em")
    readonly_fields = ("conectado", "ultima_verificacao", "mensagem_status", "atualizado_em")
    fieldsets = (
        (
            "Mercado Pago",
            {
                "fields": (
                    "ambiente",
                    "mercado_pago_access_token",
                    "mercado_pago_public_key",
                    "mercado_pago_webhook_secret",
                    "webhook_url",
                )
            },
        ),
        (
            "Status",
            {
                "fields": (
                    "conectado",
                    "ultima_verificacao",
                    "mensagem_status",
                    "atualizado_em",
                )
            },
        ),
    )

    def has_add_permission(self, request):
        return not ConfiguracaoFinanceira.objects.exists()


@admin.register(Contribuicao)
class ContribuicaoAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "tipo", "valor", "status", "criado_em")
    list_filter = ("tipo", "status", "criado_em")
    search_fields = (
        "usuario__username",
        "usuario__first_name",
        "usuario__last_name",
        "usuario__email",
        "mercado_pago_preference_id",
        "mercado_pago_payment_id",
    )
    readonly_fields = (
        "mercado_pago_preference_id",
        "mercado_pago_payment_id",
        "link_pagamento",
        "criado_em",
        "atualizado_em",
    )
