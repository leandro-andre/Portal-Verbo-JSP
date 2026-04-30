from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    telefone = models.CharField("Telefone", max_length=20, blank=True)
    foto = models.ImageField("Foto de Perfil", upload_to="perfil/", blank=True, null=True)
    data_nascimento = models.DateField("Data de Nascimento", blank=True, null=True)
    is_membro = models.BooleanField("\u00c9 Membro?", default=True)

    class Meta:
        verbose_name = "Usu\u00e1rio"
        verbose_name_plural = "Usu\u00e1rios"
