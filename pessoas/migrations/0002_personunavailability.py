from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("pessoas", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PersonUnavailability",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("start_date", models.DateField(verbose_name="Data inicial")),
                ("end_date", models.DateField(verbose_name="Data final")),
                ("start_time", models.TimeField(blank=True, null=True, verbose_name="Hora inicial")),
                ("end_time", models.TimeField(blank=True, null=True, verbose_name="Hora final")),
                ("reason", models.TextField(blank=True, verbose_name="Motivo")),
                (
                    "status",
                    models.CharField(
                        choices=[("ACTIVE", "Ativa"), ("INACTIVE", "Inativa")],
                        default="ACTIVE",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Atualizado em")),
                (
                    "person",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="unavailabilities",
                        to="pessoas.person",
                        verbose_name="Pessoa",
                    ),
                ),
            ],
            options={
                "verbose_name": "Indisponibilidade da pessoa",
                "verbose_name_plural": "Indisponibilidades das pessoas",
                "ordering": ["-start_date", "-id"],
                "permissions": [
                    ("deactivate_personunavailability", "Can deactivate person unavailability"),
                    ("reactivate_personunavailability", "Can reactivate person unavailability"),
                ],
            },
        ),
    ]
