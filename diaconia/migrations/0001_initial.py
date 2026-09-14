from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DiaconiaModule",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
            ],
            options={
                "verbose_name": "Modulo Diaconia",
                "verbose_name_plural": "Modulo Diaconia",
                "permissions": (("view_diaconia_module", "Can view Diaconia module"),),
                "default_permissions": (),
                "managed": False,
            },
        ),
    ]
