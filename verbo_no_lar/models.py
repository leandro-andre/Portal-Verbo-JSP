from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models

from ministros.models import Ministro


class CasaVerboNoLar(models.Model):
    class DiaSemana(models.TextChoices):
        SEGUNDA = "segunda", "Segunda-feira"
        TERCA = "terca", "Terca-feira"
        QUARTA = "quarta", "Quarta-feira"
        QUINTA = "quinta", "Quinta-feira"
        SEXTA = "sexta", "Sexta-feira"
        SABADO = "sabado", "Sabado"
        DOMINGO = "domingo", "Domingo"

    nome = models.CharField("Nome da casa", max_length=160)
    casal_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Casal responsavel",
        on_delete=models.PROTECT,
        related_name="casas_verbo_no_lar_responsavel",
    )
    anfitriao = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Anfitriao",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="casas_verbo_no_lar_anfitriao",
    )
    telefone_whatsapp = models.CharField("Telefone/WhatsApp", max_length=30, blank=True)

    endereco = models.CharField("Endereco completo", max_length=220, blank=True)
    bairro = models.CharField("Bairro", max_length=120, blank=True)
    ponto_referencia = models.CharField("Ponto de referencia", max_length=180, blank=True)
    link_google_maps = models.URLField("Link do Google Maps", blank=True)
    latitude = models.DecimalField("Latitude", max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField("Longitude", max_digits=9, decimal_places=6, blank=True, null=True)

    dia_padrao = models.CharField(
        "Dia padrao do encontro",
        max_length=20,
        choices=DiaSemana.choices,
        blank=True,
    )
    horario_padrao = models.TimeField("Horario padrao", blank=True, null=True)
    capacidade_aproximada = models.PositiveIntegerField("Capacidade aproximada", blank=True, null=True)

    ativo = models.BooleanField("Ativo", default=True)
    observacoes = models.TextField("Observacoes", blank=True)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        ordering = ["-ativo", "nome"]
        verbose_name = "Casa do Verbo no Lar"
        verbose_name_plural = "Casas do Verbo no Lar"

    def __str__(self):
        return self.nome

    @property
    def dia_horario_padrao(self):
        partes = []
        if self.dia_padrao:
            partes.append(self.get_dia_padrao_display())
        if self.horario_padrao:
            partes.append(self.horario_padrao.strftime("%H:%M"))
        return " | ".join(partes) if partes else "-"


class ParticipanteVerboNoLar(models.Model):
    class Tipo(models.TextChoices):
        MEMBRO = "membro", "Membro"
        VISITANTE = "visitante", "Visitante"

    casa = models.ForeignKey(
        CasaVerboNoLar,
        verbose_name="Casa",
        on_delete=models.CASCADE,
        related_name="participantes",
    )
    membro = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Membro",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="participacoes_verbo_no_lar",
    )
    nome_visitante = models.CharField("Nome do visitante", max_length=160, blank=True)
    telefone = models.CharField("Telefone", max_length=30, blank=True)
    tipo = models.CharField("Tipo", max_length=20, choices=Tipo.choices)
    ativo = models.BooleanField("Ativo", default=True)
    observacoes = models.TextField("Observacoes", blank=True)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        ordering = ["-ativo", "tipo", "nome_visitante"]
        verbose_name = "Participante do Verbo no Lar"
        verbose_name_plural = "Participantes do Verbo no Lar"
        constraints = [
            models.UniqueConstraint(
                fields=["casa", "membro"],
                condition=models.Q(membro__isnull=False),
                name="uniq_participante_por_membro_e_casa",
            )
        ]

    def __str__(self):
        return self.nome_exibicao

    @property
    def nome_exibicao(self):
        if self.membro_id:
            return self.membro.get_full_name() or getattr(self.membro, "username", "Membro")
        return self.nome_visitante or "Visitante"

    def clean(self):
        super().clean()
        if self.tipo == self.Tipo.MEMBRO and not self.membro_id:
            raise ValidationError({"membro": "Informe o membro quando o tipo for membro."})
        if self.tipo == self.Tipo.VISITANTE and not self.nome_visitante:
            raise ValidationError({"nome_visitante": "Informe o nome do visitante."})
        if self.tipo == self.Tipo.MEMBRO and self.nome_visitante:
            raise ValidationError({"nome_visitante": "Nao preencha nome do visitante para membro."})
        if self.tipo == self.Tipo.VISITANTE and self.membro_id:
            raise ValidationError({"membro": "Nao selecione membro para visitante."})


class EscalaVerboNoLar(models.Model):
    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        CONFIRMADO = "confirmado", "Confirmado"
        REALIZADO = "realizado", "Realizado"
        CANCELADO = "cancelado", "Cancelado"

    casa = models.ForeignKey(
        CasaVerboNoLar,
        verbose_name="Casa",
        on_delete=models.CASCADE,
        related_name="escalas",
    )
    ministro = models.ForeignKey(
        Ministro,
        verbose_name="Ministro",
        on_delete=models.PROTECT,
        related_name="escalas_verbo_no_lar",
    )
    data = models.DateField("Data")
    horario = models.TimeField("Horario", blank=True, null=True)
    tema = models.CharField("Tema", max_length=180, blank=True)
    status = models.CharField("Status", max_length=20, choices=Status.choices, default=Status.PENDENTE)
    observacoes = models.TextField("Observacoes", blank=True)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        ordering = ["-data", "-criado_em"]
        verbose_name = "Escala do Verbo no Lar"
        verbose_name_plural = "Escalas do Verbo no Lar"

    def __str__(self):
        return f"{self.casa} - {self.data.strftime('%d/%m/%Y')}"


MATERIAL_EXTENSIONS = ["pdf", "doc", "docx", "ppt", "pptx", "txt"]
material_validators = [FileExtensionValidator(allowed_extensions=MATERIAL_EXTENSIONS)]


class MaterialApoioVerboNoLar(models.Model):
    titulo = models.CharField("Titulo/Tema", max_length=180)
    data = models.DateField("Data", blank=True, null=True)
    texto_base = models.CharField("Texto base", max_length=200, blank=True)
    conteudo = models.TextField("Conteudo", blank=True)
    anexo = models.FileField(
        "Anexo",
        upload_to="verbo_no_lar/materiais/",
        blank=True,
        null=True,
        validators=material_validators,
    )
    casa = models.ForeignKey(
        CasaVerboNoLar,
        verbose_name="Casa (opcional)",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="materiais",
    )
    observacoes = models.TextField("Observacoes", blank=True)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        ordering = ["-data", "-criado_em"]
        verbose_name = "Material de apoio (Verbo no Lar)"
        verbose_name_plural = "Materiais de apoio (Verbo no Lar)"

    def __str__(self):
        return self.titulo


class RelatorioEncontroVerboNoLar(models.Model):
    casa = models.ForeignKey(
        CasaVerboNoLar,
        verbose_name="Casa",
        on_delete=models.CASCADE,
        related_name="relatorios",
    )
    data = models.DateField("Data")
    ministro = models.ForeignKey(
        Ministro,
        verbose_name="Ministro",
        on_delete=models.PROTECT,
        related_name="relatorios_verbo_no_lar",
    )
    tema = models.CharField("Tema", max_length=180, blank=True)
    quantidade_presentes = models.PositiveIntegerField("Quantidade de presentes", default=0)
    quantidade_visitantes = models.PositiveIntegerField("Quantidade de visitantes", default=0)
    pedidos_oracao = models.TextField("Pedidos de oracao", blank=True)
    observacoes = models.TextField("Observacoes", blank=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Criado por",
        on_delete=models.PROTECT,
        related_name="relatorios_verbo_no_lar",
    )
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        ordering = ["-data", "-criado_em"]
        verbose_name = "Relatorio de encontro (Verbo no Lar)"
        verbose_name_plural = "Relatorios de encontros (Verbo no Lar)"

    def __str__(self):
        return f"{self.casa} - {self.data.strftime('%d/%m/%Y')}"
