from django.contrib.auth.models import AbstractUser
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
