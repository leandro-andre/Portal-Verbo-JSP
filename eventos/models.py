from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
import uuid
from django.utils import timezone


class Evento(models.Model):
    class TipoEvento(models.TextChoices):
        CONFERENCIA = "conferencia", "Conferencia"
        SEMINARIO = "seminario", "Seminario"
        ENCONTRO = "encontro", "Encontro"
        TREINAMENTO = "treinamento", "Treinamento"
        CONGRESSO = "congresso", "Congresso"
        RETIRO = "retiro", "Retiro"
        ESPECIAL = "especial", "Evento especial"

    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)

    data_inicio = models.DateField()
    data_fim = models.DateField(blank=True, null=True)
    horario = models.TimeField()

    local = models.CharField(max_length=200, blank=True)

    tipo = models.CharField(
        max_length=20,
        choices=TipoEvento.choices,
        blank=True,
    )

    imagem = models.ImageField(upload_to="eventos/", blank=True, null=True)
    capacidade_maxima = models.PositiveIntegerField(blank=True, null=True)

    publicado = models.BooleanField(default=True)
    inscricoes_abertas = models.BooleanField(default=False)
    destaque_home = models.BooleanField(default=False)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["data_inicio", "horario"]
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"

    def __str__(self) -> str:
        data_str = self.data_inicio.strftime("%d/%m/%Y") if self.data_inicio else "Sem data"
        return f"{self.titulo} ({data_str})"

    @property
    def data(self):
        return self.data_inicio

    @property
    def total_inscritos(self):
        return self.inscricoes.exclude(status=InscricaoEvento.Status.CANCELADO).count()

    @property
    def total_presentes(self):
        return self.inscricoes.filter(status=InscricaoEvento.Status.PRESENTE).count()

    @property
    def vagas_disponiveis(self):
        if self.capacidade_maxima is None:
            return None
        return max(self.capacidade_maxima - self.total_inscritos, 0)

    @property
    def lotado(self):
        return self.capacidade_maxima is not None and self.total_inscritos >= self.capacidade_maxima

    def clean(self):
        super().clean()
        if self.data_fim and self.data_inicio and self.data_fim < self.data_inicio:
            raise ValidationError({"data_fim": "A data fim nao pode ser anterior a data inicio."})

    def inscricoes_permitidas(self):
        return bool(self.publicado and self.inscricoes_abertas and not self.lotado)


class InscricaoEvento(models.Model):
    class Status(models.TextChoices):
        INSCRITO = "inscrito", "Inscrito"
        CANCELADO = "cancelado", "Cancelado"
        PRESENTE = "presente", "Presente"

    evento = models.ForeignKey(
        Evento,
        verbose_name="Evento",
        on_delete=models.CASCADE,
        related_name="inscricoes",
    )
    nome = models.CharField("Nome", max_length=150)
    telefone = models.CharField("Telefone/WhatsApp", max_length=30, blank=True)
    email = models.EmailField("E-mail")
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Usuario vinculado",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="inscricoes_eventos",
    )
    status = models.CharField(
        "Status",
        max_length=20,
        choices=Status.choices,
        default=Status.INSCRITO,
    )
    pagamento_status = models.CharField(
        "Status de pagamento futuro",
        max_length=30,
        blank=True,
        help_text="Reservado para integracao futura. Nao usado agora.",
    )

    codigo_checkin = models.UUIDField(
        "Codigo de check-in",
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
    )
    checkin_realizado = models.BooleanField("Check-in realizado", default=False)
    checkin_em = models.DateTimeField("Check-in em", blank=True, null=True)
    presente_em = models.DateTimeField("Presente em", blank=True, null=True)
    checkin_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Check-in por",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="checkins_eventos",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Inscricao de evento"
        verbose_name_plural = "Inscricoes de eventos"
        constraints = [
            models.UniqueConstraint(
                fields=["evento", "usuario"],
                condition=Q(usuario__isnull=False),
                name="uniq_inscricao_evento_por_usuario",
            ),
            models.UniqueConstraint(
                fields=["evento", "email"],
                name="uniq_inscricao_evento_por_email",
            ),
        ]

    def __str__(self):
        return f"{self.nome} - {self.evento}"

    def registrar_checkin(self, *, por_usuario, quando=None):
        if self.status == InscricaoEvento.Status.PRESENTE or self.checkin_realizado:
            return False
        if self.status == InscricaoEvento.Status.CANCELADO:
            raise ValidationError("Nao e possivel fazer check-in de uma inscricao cancelada.")
        quando = quando or timezone.now()
        self.status = InscricaoEvento.Status.PRESENTE
        self.checkin_realizado = True
        self.checkin_em = quando
        self.presente_em = quando
        self.checkin_por = por_usuario
        self.save(
            update_fields=[
                "status",
                "checkin_realizado",
                "checkin_em",
                "presente_em",
                "checkin_por",
                "atualizado_em",
            ]
        )
        return True
