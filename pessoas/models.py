from django.core.exceptions import ValidationError
from django.db import models


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
        self.phone = (self.phone or "").strip()

        if not self.full_name:
            raise ValidationError({"full_name": "Informe o nome completo."})
        if not self.birth_date:
            raise ValidationError({"birth_date": "Informe a data de nascimento."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
