from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Usuario(AbstractUser):
    class StatusEclesiastico(models.TextChoices):
        VISITANTE = "visitante", "Visitante"
        MEMBRO = "membro", "Membro"

    telefone = models.CharField("Telefone", max_length=20, blank=True)
    foto = models.ImageField("Foto de Perfil", upload_to="perfil/", blank=True, null=True)
    data_nascimento = models.DateField("Data de Nascimento", blank=True, null=True)
    person = models.OneToOneField(
        "pessoas.Person",
        verbose_name="Pessoa vinculada",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="user_account",
    )
    status_eclesiastico = models.CharField(
        "Status eclesiastico",
        max_length=20,
        choices=StatusEclesiastico.choices,
        default=StatusEclesiastico.VISITANTE,
    )
    discipulado_concluido = models.BooleanField("Discipulado concluido?", default=False)
    discipulado_concluido_em = models.DateField(
        "Data de conclusao do discipulado",
        blank=True,
        null=True,
    )
    qualificado_por = models.ForeignKey(
        "self",
        verbose_name="Qualificado por",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="usuarios_qualificados",
    )
    qualificado_em = models.DateTimeField("Qualificado em", blank=True, null=True)
    eh_pastor = models.BooleanField("Pastor?", default=False)

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    @property
    def is_membro(self):
        return self.status_eclesiastico == self.StatusEclesiastico.MEMBRO

    @property
    def is_visitante(self):
        return self.status_eclesiastico == self.StatusEclesiastico.VISITANTE

    @property
    def display_name(self):
        if self.person_id:
            return self.person.display_name
        return self.get_full_name() or self.username

    def qualificar_como_membro(self, qualificado_por, discipulado_concluido_em=None):
        self.status_eclesiastico = self.StatusEclesiastico.MEMBRO
        self.discipulado_concluido = True
        if discipulado_concluido_em:
            self.discipulado_concluido_em = discipulado_concluido_em
        elif not self.discipulado_concluido_em:
            self.discipulado_concluido_em = timezone.localdate()
        self.qualificado_por = qualificado_por
        self.qualificado_em = timezone.now()


class AccessRequestQuerySet(models.QuerySet):
    def pending(self):
        return self.filter(status=AccessRequest.Status.PENDING)

    def pending_for_contact(self, *, email, phone):
        email = (email or "").strip()
        phone = (phone or "").strip()
        if not email and not phone:
            return self.none()

        query = models.Q()
        if email:
            query |= models.Q(email__iexact=email)
        if phone:
            query |= models.Q(phone=phone)

        return self.pending().filter(query)


class AccessRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendente"
        APPROVED = "APPROVED", "Aprovada"
        REJECTED = "REJECTED", "Rejeitada"

    full_name = models.CharField("Nome completo", max_length=150)
    birth_date = models.DateField("Data de nascimento")
    email = models.EmailField("E-mail")
    phone = models.CharField("Telefone", max_length=30)
    status = models.CharField(
        "Status",
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    person = models.ForeignKey(
        "pessoas.Person",
        verbose_name="Pessoa vinculada",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="access_requests",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Revisada por",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="access_requests_reviewed",
    )
    reviewed_at = models.DateTimeField("Revisada em", blank=True, null=True)
    rejection_reason = models.TextField("Motivo da rejeicao", blank=True)
    created_at = models.DateTimeField("Criada em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizada em", auto_now=True)

    objects = AccessRequestQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "Solicitacao de acesso"
        verbose_name_plural = "Solicitacoes de acesso"
        indexes = [
            models.Index(fields=["status", "email"], name="access_req_status_email_idx"),
            models.Index(fields=["status", "phone"], name="access_req_status_phone_idx"),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.get_status_display()})"

    def clean(self):
        super().clean()
        self.full_name = (self.full_name or "").strip()
        self.email = (self.email or "").strip().lower()
        self.phone = (self.phone or "").strip()

        errors = {}
        if not self.full_name:
            errors["full_name"] = "Informe o nome completo."
        if not self.birth_date:
            errors["birth_date"] = "Informe a data de nascimento."
        elif self.birth_date > timezone.localdate():
            errors["birth_date"] = "A data de nascimento nao pode ser futura."
        if not self.email:
            errors["email"] = "Informe o e-mail."
        if not self.phone:
            errors["phone"] = "Informe o telefone."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
