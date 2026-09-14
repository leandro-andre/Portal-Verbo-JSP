from django.db import migrations, models
import django.db.models.functions.text


class Migration(migrations.Migration):

    dependencies = [
        ("diaconia", "0003_stock_movement"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="diaconiamodule",
            options={
                "default_permissions": (),
                "managed": False,
                "permissions": (
                    ("view_diaconia_module", "Can view Diaconia module"),
                    ("manage_diaconia_stock", "Can manage Diaconia stock"),
                    ("manage_diaconia_counting", "Can manage Diaconia counting"),
                ),
                "verbose_name": "Modulo Diaconia",
                "verbose_name_plural": "Modulo Diaconia",
            },
        ),
        migrations.CreateModel(
            name="CountingEnvironment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, verbose_name="Nome")),
                ("description", models.TextField(blank=True, verbose_name="Descricao")),
                ("is_active", models.BooleanField(default=True, verbose_name="Ativo")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Atualizado em")),
            ],
            options={
                "verbose_name": "Ambiente de contagem",
                "verbose_name_plural": "Ambientes de contagem",
                "ordering": ["name", "id"],
                "permissions": [
                    ("deactivate_countingenvironment", "Can deactivate counting environment"),
                    ("reactivate_countingenvironment", "Can reactivate counting environment"),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="countingenvironment",
            constraint=models.UniqueConstraint(
                django.db.models.functions.text.Lower("name"),
                name="uniq_diaconia_counting_environment_name_ci",
            ),
        ),
    ]
