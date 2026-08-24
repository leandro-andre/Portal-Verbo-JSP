from django.conf import settings
from django.db import models
from django.db.models import F, Q


class Schedule(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Rascunho"
        PUBLISHED = "PUBLISHED", "Publicada"
        CANCELLED = "CANCELLED", "Cancelada"

    department = models.ForeignKey(
        "departamentos.Departamento",
        verbose_name="Departamento",
        on_delete=models.PROTECT,
        related_name="schedules",
    )
    worship_service = models.ForeignKey(
        "worship.WorshipService",
        verbose_name="Culto",
        on_delete=models.PROTECT,
        related_name="schedules",
    )
    status = models.CharField("Status", max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Criada por",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="created_schedules",
    )
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        ordering = ["worship_service__date", "worship_service__time", "department__nome", "id"]
        verbose_name = "Escala"
        verbose_name_plural = "Escalas"
        constraints = [
            models.UniqueConstraint(
                fields=["department", "worship_service"],
                name="uniq_schedule_department_worship_service",
            )
        ]
        permissions = [
            ("publish_schedule", "Can publish schedule"),
            ("reopen_schedule", "Can reopen schedule"),
            ("cancel_schedule", "Can cancel schedule"),
            ("reactivate_schedule", "Can reactivate schedule"),
        ]

    def __str__(self):
        return f"{self.department} - {self.worship_service}"


class ScheduleAssignment(models.Model):
    schedule = models.ForeignKey(
        Schedule,
        verbose_name="Escala",
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    department_membership = models.ForeignKey(
        "departamentos.DepartmentMembership",
        verbose_name="Vinculo departamental",
        on_delete=models.PROTECT,
        related_name="schedule_assignments",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Criado por",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="created_schedule_assignments",
    )
    created_at = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        ordering = ["department_membership__person__full_name", "id"]
        verbose_name = "Pessoa escalada"
        verbose_name_plural = "Pessoas escaladas"
        constraints = [
            models.UniqueConstraint(
                fields=["schedule", "department_membership"],
                name="uniq_schedule_assignment_membership",
            )
        ]

    def __str__(self):
        return f"{self.department_membership} em {self.schedule}"


class DepartmentScheduleRequirement(models.Model):
    department = models.ForeignKey(
        "departamentos.Departamento",
        verbose_name="Departamento",
        on_delete=models.PROTECT,
        related_name="schedule_requirements",
    )
    role = models.ForeignKey(
        "departamentos.DepartmentRole",
        verbose_name="Cargo",
        on_delete=models.PROTECT,
        related_name="schedule_requirements",
    )
    minimum_quantity = models.PositiveIntegerField("Quantidade minima", default=0)
    recommended_quantity = models.PositiveIntegerField("Quantidade recomendada", default=0)
    active = models.BooleanField("Ativo", default=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        ordering = ["department__nome", "role__name", "id"]
        verbose_name = "Requisito de composicao de escala"
        verbose_name_plural = "Requisitos de composicao de escala"
        constraints = [
            models.UniqueConstraint(
                fields=["department", "role"],
                name="uniq_schedule_requirement_department_role",
            ),
            models.CheckConstraint(
                condition=Q(minimum_quantity__gte=0),
                name="schedule_requirement_minimum_non_negative",
            ),
            models.CheckConstraint(
                condition=Q(recommended_quantity__gte=0),
                name="schedule_requirement_recommended_non_negative",
            ),
            models.CheckConstraint(
                condition=Q(recommended_quantity__gte=F("minimum_quantity")),
                name="schedule_requirement_recommended_gte_minimum",
            ),
        ]

    def __str__(self):
        return f"{self.department} - {self.role}"
