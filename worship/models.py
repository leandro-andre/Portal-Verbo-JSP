from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Weekday(models.IntegerChoices):
    MONDAY = 0, "Segunda-feira"
    TUESDAY = 1, "Terca-feira"
    WEDNESDAY = 2, "Quarta-feira"
    THURSDAY = 3, "Quinta-feira"
    FRIDAY = 4, "Sexta-feira"
    SATURDAY = 5, "Sabado"
    SUNDAY = 6, "Domingo"


class WorshipServiceTemplate(models.Model):
    class QuerySet(models.QuerySet):
        def active(self):
            return self.filter(active=True)

        def ordered(self):
            return self.order_by("weekday", "time", "name")

    objects = QuerySet.as_manager()

    name = models.CharField("Nome", max_length=150)
    weekday = models.PositiveSmallIntegerField("Dia da semana", choices=Weekday.choices)
    time = models.TimeField("Horario")
    active = models.BooleanField("Ativo", default=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        ordering = ["weekday", "time", "name"]
        verbose_name = "Culto padrao"
        verbose_name_plural = "Cultos padrao"
        permissions = [
            ("deactivate_worship_service_template", "Can deactivate worship service template"),
            ("reactivate_worship_service_template", "Can reactivate worship service template"),
        ]

    def __str__(self):
        return f"{self.name} - {self.get_weekday_display()} ({self.time.strftime('%H:%M')})"

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class WorshipService(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Agendado"
        CANCELLED = "CANCELLED", "Cancelado"

    class Kind(models.TextChoices):
        REGULAR = "REGULAR", "Regular"
        EXTRAORDINARY = "EXTRAORDINARY", "Extraordinario"

    class QuerySet(models.QuerySet):
        def for_month(self, year, month):
            return self.filter(date__year=year, date__month=month)

        def ordered(self):
            return self.order_by("date", "time", "name")

    objects = QuerySet.as_manager()

    template = models.ForeignKey(
        WorshipServiceTemplate,
        verbose_name="Culto padrao",
        on_delete=models.SET_NULL,
        related_name="services",
        blank=True,
        null=True,
    )
    name = models.CharField("Nome", max_length=150)
    date = models.DateField("Data")
    source_date = models.DateField("Data original do padrao", blank=True, null=True)
    time = models.TimeField("Horario")
    status = models.CharField("Status", max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    kind = models.CharField("Tipo", max_length=20, choices=Kind.choices)
    notes = models.TextField("Observacoes", blank=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        ordering = ["date", "time", "name"]
        verbose_name = "Culto da agenda"
        verbose_name_plural = "Cultos da agenda"
        constraints = [
            models.UniqueConstraint(
                fields=["template", "source_date"],
                condition=Q(template__isnull=False),
                name="uniq_worship_service_template_source_date",
            )
        ]
        permissions = [
            ("generate_worship_services", "Can generate worship services"),
            ("cancel_worship_service", "Can cancel worship service"),
            ("reactivate_worship_service", "Can reactivate worship service"),
        ]

    def __str__(self):
        return f"{self.name} - {self.date:%d/%m/%Y} {self.time:%H:%M}"

    def clean(self):
        super().clean()
        errors = {}

        if self.kind == self.Kind.REGULAR:
            if not self.template_id:
                errors["template"] = "Culto regular precisa estar vinculado a um culto padrao."
            if not self.source_date:
                errors["source_date"] = "Culto regular precisa preservar a data original do padrao."

        if self.kind == self.Kind.EXTRAORDINARY:
            if self.template_id:
                errors["template"] = "Culto extraordinario nao deve estar vinculado a um culto padrao."
            if self.source_date:
                errors["source_date"] = "Culto extraordinario nao deve possuir data original de padrao."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
