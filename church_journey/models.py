from django.db import models
from django.utils import timezone


class ChurchJourney(models.Model):
    person = models.OneToOneField(
        "pessoas.Person",
        verbose_name="Pessoa",
        on_delete=models.CASCADE,
        related_name="church_journey",
    )
    started_at = models.DateField("Data de entrada na jornada", default=timezone.localdate)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        ordering = ["person__full_name", "person_id"]
        verbose_name = "Jornada eclesiastica"
        verbose_name_plural = "Jornadas eclesiasticas"

    def __str__(self):
        return f"Jornada eclesiastica de {self.person}"
