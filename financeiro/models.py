from django.conf import settings
from django.db import models


class ConfiguracaoFinanceira(models.Model):
    class Ambiente(models.TextChoices):
        TESTE = "teste", "Teste"
        PRODUCAO = "producao", "Producao"

    ambiente = models.CharField(
        "ambiente",
        max_length=20,
        choices=Ambiente.choices,
        default=Ambiente.TESTE,
    )
    mercado_pago_access_token = models.CharField(
        "access token do Mercado Pago",
        max_length=255,
        blank=True,
    )
    mercado_pago_public_key = models.CharField(
        "public key do Mercado Pago",
        max_length=255,
        blank=True,
    )
    mercado_pago_webhook_secret = models.CharField(
        "segredo do webhook Mercado Pago",
        max_length=255,
        blank=True,
        help_text="Chave secreta usada para validar o header x-signature do webhook.",
    )
    webhook_url = models.URLField("URL do webhook", blank=True)
    conectado = models.BooleanField("conectado", default=False)
    ultima_verificacao = models.DateTimeField("ultima verificacao", null=True, blank=True)
    mensagem_status = models.TextField("mensagem de status", blank=True)
    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        verbose_name = "configuracao financeira"
        verbose_name_plural = "configuracoes financeiras"

    def __str__(self):
        return f"Mercado Pago ({self.get_ambiente_display()})"

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Contribuicao(models.Model):
    class Tipo(models.TextChoices):
        DIZIMO = "dizimo", "Dizimo"
        OFERTA = "oferta", "Oferta"
        MISSOES = "missoes", "Missoes"
        CAMPANHA = "campanha", "Campanha"

    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        APROVADO = "aprovado", "Aprovado"
        RECUSADO = "recusado", "Recusado"
        CANCELADO = "cancelado", "Cancelado"
        ERRO = "erro", "Erro"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="usuario",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="contribuicoes",
    )
    tipo = models.CharField("tipo", max_length=20, choices=Tipo.choices)
    valor = models.DecimalField("valor", max_digits=10, decimal_places=2)
    descricao = models.TextField("descricao", blank=True)
    status = models.CharField(
        "status",
        max_length=20,
        choices=Status.choices,
        default=Status.PENDENTE,
    )
    mercado_pago_preference_id = models.CharField(
        "preference id Mercado Pago",
        max_length=120,
        blank=True,
        db_index=True,
    )
    mercado_pago_payment_id = models.CharField(
        "payment id Mercado Pago",
        max_length=120,
        blank=True,
        db_index=True,
    )
    link_pagamento = models.URLField("link de pagamento", blank=True, max_length=500)
    criado_em = models.DateTimeField("criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        verbose_name = "contribuicao"
        verbose_name_plural = "contribuicoes"
        ordering = ["-criado_em", "-id"]

    def __str__(self):
        return f"{self.get_tipo_display()} - R$ {self.valor}"
