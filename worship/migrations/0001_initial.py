# Generated manually for PVV-031.

import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="WorshipServiceTemplate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150, verbose_name="Nome")),
                (
                    "weekday",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (0, "Segunda-feira"),
                            (1, "Terca-feira"),
                            (2, "Quarta-feira"),
                            (3, "Quinta-feira"),
                            (4, "Sexta-feira"),
                            (5, "Sabado"),
                            (6, "Domingo"),
                        ],
                        verbose_name="Dia da semana",
                    ),
                ),
                ("time", models.TimeField(verbose_name="Horario")),
                ("active", models.BooleanField(default=True, verbose_name="Ativo")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Atualizado em")),
            ],
            options={
                "verbose_name": "Culto padrao",
                "verbose_name_plural": "Cultos padrao",
                "ordering": ["weekday", "time", "name"],
                "permissions": [
                    ("deactivate_worship_service_template", "Can deactivate worship service template"),
                    ("reactivate_worship_service_template", "Can reactivate worship service template"),
                ],
            },
        ),
        migrations.CreateModel(
            name="WorshipService",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150, verbose_name="Nome")),
                ("date", models.DateField(verbose_name="Data")),
                ("source_date", models.DateField(blank=True, null=True, verbose_name="Data original do padrao")),
                ("time", models.TimeField(verbose_name="Horario")),
                (
                    "status",
                    models.CharField(
                        choices=[("SCHEDULED", "Agendado"), ("CANCELLED", "Cancelado")],
                        default="SCHEDULED",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                (
                    "kind",
                    models.CharField(
                        choices=[("REGULAR", "Regular"), ("EXTRAORDINARY", "Extraordinario")],
                        max_length=20,
                        verbose_name="Tipo",
                    ),
                ),
                ("notes", models.TextField(blank=True, verbose_name="Observacoes")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Atualizado em")),
                (
                    "template",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="services",
                        to="worship.worshipservicetemplate",
                        verbose_name="Culto padrao",
                    ),
                ),
            ],
            options={
                "verbose_name": "Culto da agenda",
                "verbose_name_plural": "Cultos da agenda",
                "ordering": ["date", "time", "name"],
                "permissions": [
                    ("generate_worship_services", "Can generate worship services"),
                    ("cancel_worship_service", "Can cancel worship service"),
                    ("reactivate_worship_service", "Can reactivate worship service"),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="worshipservice",
            constraint=models.UniqueConstraint(
                condition=Q(("template__isnull", False)),
                fields=("template", "source_date"),
                name="uniq_worship_service_template_source_date",
            ),
        ),
    ]
