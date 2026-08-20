from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
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


class DiscipleshipClass(models.Model):
    class Status(models.TextChoices):
        PLANNED = "PLANNED", "Planejada"
        IN_PROGRESS = "IN_PROGRESS", "Em andamento"
        COMPLETED = "COMPLETED", "Concluida"
        CANCELLED = "CANCELLED", "Cancelada"

    name = models.CharField("Nome da turma", max_length=150)
    teacher = models.ForeignKey(
        "pessoas.Person",
        verbose_name="Professor",
        on_delete=models.PROTECT,
        related_name="discipleship_classes_taught",
    )
    start_date = models.DateField("Data de inicio")
    expected_end_date = models.DateField("Termino previsto")
    planned_sessions = models.PositiveIntegerField("Quantidade prevista de aulas")
    status = models.CharField(
        "Status",
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNED,
    )
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        ordering = ["-start_date", "name", "id"]
        verbose_name = "Turma de discipulado"
        verbose_name_plural = "Turmas de discipulado"
        permissions = [
            ("start_discipleshipclass", "Can start discipleship class"),
            ("complete_discipleshipclass", "Can complete discipleship class"),
            ("cancel_discipleshipclass", "Can cancel discipleship class"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["status"],
                condition=Q(status="IN_PROGRESS"),
                name="unique_discipleship_class_in_progress",
            ),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        errors = {}

        self.name = (self.name or "").strip()
        if not self.name:
            errors["name"] = "Informe o nome da turma."

        if self.planned_sessions is not None and self.planned_sessions <= 0:
            errors["planned_sessions"] = "Informe uma quantidade positiva de aulas."

        if (
            self.start_date
            and self.expected_end_date
            and self.expected_end_date < self.start_date
        ):
            errors["expected_end_date"] = "O termino previsto nao pode ser anterior ao inicio."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class DiscipleshipEnrollment(models.Model):
    class Status(models.TextChoices):
        ENROLLED = "ENROLLED", "Matriculado"
        WITHDRAWN = "WITHDRAWN", "Desistente"

    person = models.ForeignKey(
        "pessoas.Person",
        verbose_name="Pessoa",
        on_delete=models.PROTECT,
        related_name="discipleship_enrollments",
    )
    discipleship_class = models.ForeignKey(
        DiscipleshipClass,
        verbose_name="Turma de discipulado",
        on_delete=models.PROTECT,
        related_name="enrollments",
    )
    status = models.CharField(
        "Status",
        max_length=20,
        choices=Status.choices,
        default=Status.ENROLLED,
    )
    enrolled_at = models.DateField("Data da matricula", default=timezone.localdate)
    withdrawn_at = models.DateField("Data da desistencia", blank=True, null=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        ordering = ["person__full_name", "id"]
        verbose_name = "Matricula de discipulado"
        verbose_name_plural = "Matriculas de discipulado"
        permissions = [
            ("withdraw_discipleshipenrollment", "Can withdraw discipleship enrollment"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["person", "discipleship_class"],
                name="unique_person_discipleship_class_enrollment",
            ),
        ]

    def __str__(self):
        return f"{self.person} - {self.discipleship_class}"
