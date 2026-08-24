# Generated manually for PVV-032.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("departamentos", "0008_department_role_membership"),
    ]

    operations = [
        migrations.AddField(
            model_name="departmentrole",
            name="can_manage_schedules",
            field=models.BooleanField(default=False, verbose_name="Pode gerenciar escalas"),
        ),
    ]
