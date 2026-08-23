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


class Membership(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Ativa"
        INACTIVE = "INACTIVE", "Inativa"

    person = models.OneToOneField(
        "pessoas.Person",
        verbose_name="Pessoa",
        on_delete=models.CASCADE,
        related_name="membership",
    )
    status = models.CharField(
        "Status",
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    member_since = models.DateField("Membro desde")
    approved_by = models.ForeignKey(
        "usuarios.Usuario",
        verbose_name="Aprovado por",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="memberships_approved",
    )
    approved_at = models.DateTimeField("Aprovado em", blank=True, null=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        ordering = ["person__full_name", "person_id"]
        verbose_name = "Membresia"
        verbose_name_plural = "Membresias"
        permissions = [
            ("approve_membership", "Can approve membership"),
        ]

    def __str__(self):
        return f"Membresia de {self.person}"

    def clean(self):
        super().clean()
        errors = {}

        if not self.person_id:
            errors["person"] = "Informe a pessoa."
        elif not hasattr(self.person, "church_journey"):
            errors["person"] = "Membership exige jornada eclesiastica."
        else:
            from .selectors import get_completed_discipleship

            if not get_completed_discipleship(self.person):
                errors["person"] = "Membership exige discipulado concluido."

        if not self.member_since:
            errors["member_since"] = "Informe a data oficial de membresia."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


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
        COMPLETED = "COMPLETED", "Concluido"

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
    completed_at = models.DateField("Data de conclusao", blank=True, null=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        ordering = ["person__full_name", "id"]
        verbose_name = "Matricula de discipulado"
        verbose_name_plural = "Matriculas de discipulado"
        permissions = [
            ("withdraw_discipleshipenrollment", "Can withdraw discipleship enrollment"),
            ("complete_discipleshipenrollment", "Can complete discipleship enrollment"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["person", "discipleship_class"],
                name="unique_person_discipleship_class_enrollment",
            ),
        ]

    def __str__(self):
        return f"{self.person} - {self.discipleship_class}"


class DiscipleshipLesson(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Agendada"
        CANCELLED = "CANCELLED", "Cancelada"

    discipleship_class = models.ForeignKey(
        DiscipleshipClass,
        verbose_name="Turma de discipulado",
        on_delete=models.PROTECT,
        related_name="lessons",
    )
    title = models.CharField("Titulo", max_length=150)
    lesson_date = models.DateField("Data da aula")
    status = models.CharField(
        "Status",
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
    )
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        ordering = ["lesson_date", "id"]
        verbose_name = "Aula de discipulado"
        verbose_name_plural = "Aulas de discipulado"
        permissions = [
            ("cancel_discipleshiplesson", "Can cancel discipleship lesson"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["discipleship_class", "lesson_date"],
                name="unique_discipleship_class_lesson_date",
            ),
        ]

    def __str__(self):
        return f"{self.discipleship_class} - {self.title}"

    def clean(self):
        super().clean()
        self.title = (self.title or "").strip()
        if not self.title:
            raise ValidationError({"title": "Informe o titulo da aula."})


class DiscipleshipClassAssistant(models.Model):
    discipleship_class = models.ForeignKey(
        DiscipleshipClass,
        verbose_name="Turma de discipulado",
        on_delete=models.CASCADE,
        related_name="assistants",
    )
    person = models.ForeignKey(
        "pessoas.Person",
        verbose_name="Auxiliar",
        on_delete=models.PROTECT,
        related_name="discipleship_classes_assisted",
    )
    created_at = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        ordering = ["person__full_name", "id"]
        verbose_name = "Auxiliar de turma de discipulado"
        verbose_name_plural = "Auxiliares de turmas de discipulado"
        constraints = [
            models.UniqueConstraint(
                fields=["discipleship_class", "person"],
                name="unique_discipleship_class_assistant",
            ),
        ]

    def __str__(self):
        return f"{self.person} - {self.discipleship_class}"


class DiscipleshipAttendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Presente"
        ABSENT = "ABSENT", "Ausente"
        JUSTIFIED = "JUSTIFIED", "Justificada"

    enrollment = models.ForeignKey(
        DiscipleshipEnrollment,
        verbose_name="Matricula",
        on_delete=models.PROTECT,
        related_name="attendance_records",
    )
    lesson = models.ForeignKey(
        DiscipleshipLesson,
        verbose_name="Aula",
        on_delete=models.PROTECT,
        related_name="attendance_records",
    )
    status = models.CharField("Status", max_length=20, choices=Status.choices)
    recorded_by = models.ForeignKey(
        "usuarios.Usuario",
        verbose_name="Registrado por",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="discipleship_attendance_records",
    )
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        ordering = ["lesson__lesson_date", "enrollment__person__full_name", "id"]
        verbose_name = "Presenca de discipulado"
        verbose_name_plural = "Presencas de discipulado"
        constraints = [
            models.UniqueConstraint(
                fields=["enrollment", "lesson"],
                name="unique_discipleship_attendance_enrollment_lesson",
            ),
        ]

    def __str__(self):
        return f"{self.enrollment} - {self.lesson} ({self.status})"
