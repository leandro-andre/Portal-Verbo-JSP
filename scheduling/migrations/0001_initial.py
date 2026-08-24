# Generated manually for PVV-032.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("departamentos", "0009_departmentrole_can_manage_schedules"),
        ("worship", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Schedule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("DRAFT", "Rascunho"), ("PUBLISHED", "Publicada"), ("CANCELLED", "Cancelada")], default="DRAFT", max_length=20, verbose_name="Status")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Atualizado em")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_schedules", to=settings.AUTH_USER_MODEL, verbose_name="Criada por")),
                ("department", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="schedules", to="departamentos.departamento", verbose_name="Departamento")),
                ("worship_service", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="schedules", to="worship.worshipservice", verbose_name="Culto")),
            ],
            options={
                "verbose_name": "Escala",
                "verbose_name_plural": "Escalas",
                "ordering": ["worship_service__date", "worship_service__time", "department__nome", "id"],
                "permissions": [
                    ("publish_schedule", "Can publish schedule"),
                    ("reopen_schedule", "Can reopen schedule"),
                    ("cancel_schedule", "Can cancel schedule"),
                    ("reactivate_schedule", "Can reactivate schedule"),
                ],
            },
        ),
        migrations.CreateModel(
            name="ScheduleAssignment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_schedule_assignments", to=settings.AUTH_USER_MODEL, verbose_name="Criado por")),
                ("department_membership", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="schedule_assignments", to="departamentos.departmentmembership", verbose_name="Vinculo departamental")),
                ("schedule", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assignments", to="scheduling.schedule", verbose_name="Escala")),
            ],
            options={
                "verbose_name": "Pessoa escalada",
                "verbose_name_plural": "Pessoas escaladas",
                "ordering": ["department_membership__person__full_name", "id"],
            },
        ),
        migrations.AddConstraint(
            model_name="schedule",
            constraint=models.UniqueConstraint(fields=("department", "worship_service"), name="uniq_schedule_department_worship_service"),
        ),
        migrations.AddConstraint(
            model_name="scheduleassignment",
            constraint=models.UniqueConstraint(fields=("schedule", "department_membership"), name="uniq_schedule_assignment_membership"),
        ),
    ]
