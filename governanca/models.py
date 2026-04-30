from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models


class ConteudoAuditLog(models.Model):
    class Acao(models.TextChoices):
        CREATE = "create", "Criacao"
        UPDATE = "update", "Atualizacao"
        DELETE = "delete", "Exclusao"
        PUBLISH = "publish", "Publicacao"
        UNPUBLISH = "unpublish", "Despublicacao"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Usuario",
        on_delete=models.SET_NULL,
        related_name="auditorias_conteudo_publico",
        null=True,
        blank=True,
    )
    content_type = models.ForeignKey(
        ContentType,
        verbose_name="Tipo de conteudo",
        on_delete=models.CASCADE,
        related_name="auditorias_conteudo_publico",
    )
    object_id = models.CharField("ID do objeto", max_length=64)
    object_repr = models.CharField("Objeto", max_length=255, blank=True)
    acao = models.CharField("Acao", max_length=20, choices=Acao.choices)
    campo = models.CharField("Campo", max_length=100, blank=True)
    valor_anterior = models.TextField("Valor anterior", blank=True)
    valor_novo = models.TextField("Valor novo", blank=True)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        ordering = ["-criado_em", "-id"]
        verbose_name = "Log de auditoria"
        verbose_name_plural = "Logs de auditoria"

    def __str__(self):
        campo = f"::{self.campo}" if self.campo else ""
        return f"{self.content_type.app_label}.{self.content_type.model}:{self.object_id}{campo}"
