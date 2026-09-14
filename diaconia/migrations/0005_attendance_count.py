from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("diaconia", "0004_counting_environment"),
    ]

    operations = [
        migrations.CreateModel(
            name="AttendanceCount",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField(verbose_name="Data")),
                (
                    "shift",
                    models.CharField(
                        choices=[("MORNING", "Manha"), ("AFTERNOON", "Tarde"), ("EVENING", "Noite")],
                        max_length=20,
                        verbose_name="Turno",
                    ),
                ),
                ("notes", models.TextField(blank=True, verbose_name="Observacao")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Atualizado em")),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="diaconia_attendance_counts",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Criado por",
                    ),
                ),
            ],
            options={
                "verbose_name": "Contagem de publico",
                "verbose_name_plural": "Contagens de publico",
                "ordering": ["-date", "-created_at", "-id"],
            },
        ),
        migrations.CreateModel(
            name="AttendanceCountEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.IntegerField(verbose_name="Quantidade")),
                (
                    "attendance_count",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="entries",
                        to="diaconia.attendancecount",
                        verbose_name="Contagem",
                    ),
                ),
                (
                    "environment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="attendance_entries",
                        to="diaconia.countingenvironment",
                        verbose_name="Ambiente",
                    ),
                ),
            ],
            options={
                "verbose_name": "Item da contagem de publico",
                "verbose_name_plural": "Itens da contagem de publico",
                "ordering": ["environment__name", "id"],
            },
        ),
        migrations.AddIndex(
            model_name="attendancecount",
            index=models.Index(fields=["date", "shift"], name="diaconia_count_date_shift_idx"),
        ),
        migrations.AddConstraint(
            model_name="attendancecount",
            constraint=models.UniqueConstraint(fields=("date", "shift"), name="uniq_diaconia_attendance_count_date_shift"),
        ),
        migrations.AddConstraint(
            model_name="attendancecountentry",
            constraint=models.UniqueConstraint(
                fields=("attendance_count", "environment"),
                name="uniq_diaconia_attendance_count_environment",
            ),
        ),
        migrations.AddConstraint(
            model_name="attendancecountentry",
            constraint=models.CheckConstraint(
                condition=models.Q(("quantity__gte", 0)),
                name="chk_diaconia_attendance_entry_quantity_gte_0",
            ),
        ),
    ]
