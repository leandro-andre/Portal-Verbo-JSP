import uuid
from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import models

from .validators import validate_brazilian_mobile


def person_photo_upload_to(instance, filename):
    suffix = Path(filename).suffix.lower()
    return f"people/photos/{instance.pk or 'pending'}/{uuid.uuid4().hex}{suffix}"


class PersonQuerySet(models.QuerySet):
    def possible_duplicates(self, *, full_name, birth_date):
        full_name = (full_name or "").strip()
        if not full_name or not birth_date:
            return self.none()
        return self.filter(full_name__iexact=full_name, birth_date=birth_date)


class Person(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Ativa"
        INACTIVE = "INACTIVE", "Inativa"

    full_name = models.CharField("Nome completo", max_length=150)
    preferred_name = models.CharField("Nome preferido", max_length=150, blank=True)
    birth_date = models.DateField("Data de nascimento")
    email = models.EmailField("E-mail", blank=True)
    phone = models.CharField("Telefone", max_length=30, blank=True)
    photo = models.ImageField("Foto", upload_to=person_photo_upload_to, blank=True, null=True)
    status = models.CharField(
        "Status",
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    objects = PersonQuerySet.as_manager()

    class Meta:
        ordering = ["full_name", "birth_date", "id"]
        verbose_name = "Pessoa"
        verbose_name_plural = "Pessoas"
        indexes = [
            models.Index(fields=["full_name", "birth_date"], name="person_name_birth_idx"),
        ]

    def __str__(self):
        return self.display_name

    @property
    def display_name(self):
        return self.preferred_name or self.full_name

    def clean(self):
        super().clean()
        self.full_name = (self.full_name or "").strip()
        self.preferred_name = (self.preferred_name or "").strip()
        self.email = (self.email or "").strip()
        try:
            self.phone = validate_brazilian_mobile(self.phone)
        except ValidationError as exc:
            raise ValidationError({"phone": exc.messages}) from exc

        if not self.full_name:
            raise ValidationError({"full_name": "Informe o nome completo."})
        if not self.birth_date:
            raise ValidationError({"birth_date": "Informe a data de nascimento."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class PersonUnavailability(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Ativa"
        INACTIVE = "INACTIVE", "Inativa"

    person = models.ForeignKey(
        Person,
        verbose_name="Pessoa",
        on_delete=models.CASCADE,
        related_name="unavailabilities",
    )
    start_date = models.DateField("Data inicial")
    end_date = models.DateField("Data final")
    start_time = models.TimeField("Hora inicial", blank=True, null=True)
    end_time = models.TimeField("Hora final", blank=True, null=True)
    reason = models.TextField("Motivo", blank=True)
    status = models.CharField(
        "Status",
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        ordering = ["-start_date", "-id"]
        verbose_name = "Indisponibilidade da pessoa"
        verbose_name_plural = "Indisponibilidades das pessoas"
        permissions = [
            ("deactivate_personunavailability", "Can deactivate person unavailability"),
            ("reactivate_personunavailability", "Can reactivate person unavailability"),
        ]

    def __str__(self):
        return f"{self.person} indisponivel de {self.start_date} a {self.end_date}"

    @property
    def is_full_day(self):
        return self.start_time is None and self.end_time is None
