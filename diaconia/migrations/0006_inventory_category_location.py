from django.db import migrations, models
import django.db.models.functions.text


class Migration(migrations.Migration):

    dependencies = [
        ("diaconia", "0005_attendance_count"),
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
                    ("manage_diaconia_inventory", "Can manage Diaconia inventory"),
                ),
                "verbose_name": "Modulo Diaconia",
                "verbose_name_plural": "Modulo Diaconia",
            },
        ),
        migrations.CreateModel(
            name="InventoryCategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, verbose_name="Nome")),
                ("description", models.TextField(blank=True, verbose_name="Descricao")),
                ("is_active", models.BooleanField(default=True, verbose_name="Ativa")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Atualizado em")),
            ],
            options={
                "verbose_name": "Categoria de inventario",
                "verbose_name_plural": "Categorias de inventario",
                "ordering": ["name", "id"],
                "permissions": [
                    ("deactivate_inventorycategory", "Can deactivate inventory category"),
                    ("reactivate_inventorycategory", "Can reactivate inventory category"),
                ],
            },
        ),
        migrations.CreateModel(
            name="InventoryLocation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, verbose_name="Nome")),
                ("description", models.TextField(blank=True, verbose_name="Descricao")),
                ("is_active", models.BooleanField(default=True, verbose_name="Ativo")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Atualizado em")),
            ],
            options={
                "verbose_name": "Local de inventario",
                "verbose_name_plural": "Locais de inventario",
                "ordering": ["name", "id"],
                "permissions": [
                    ("deactivate_inventorylocation", "Can deactivate inventory location"),
                    ("reactivate_inventorylocation", "Can reactivate inventory location"),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="inventorycategory",
            constraint=models.UniqueConstraint(
                django.db.models.functions.text.Lower("name"),
                name="uniq_diaconia_inventory_category_name_ci",
            ),
        ),
        migrations.AddConstraint(
            model_name="inventorylocation",
            constraint=models.UniqueConstraint(
                django.db.models.functions.text.Lower("name"),
                name="uniq_diaconia_inventory_location_name_ci",
            ),
        ),
    ]
