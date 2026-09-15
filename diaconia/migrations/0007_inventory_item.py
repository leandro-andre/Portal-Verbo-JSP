from django.db import migrations, models
import django.db.models.deletion
import django.db.models.functions.text


class Migration(migrations.Migration):

    dependencies = [
        ("diaconia", "0006_inventory_category_location"),
    ]

    operations = [
        migrations.CreateModel(
            name="InventoryItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160, verbose_name="Nome")),
                ("description", models.TextField(blank=True, verbose_name="Descricao")),
                ("is_active", models.BooleanField(default=True, verbose_name="Ativo")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Atualizado em")),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="items",
                        to="diaconia.inventorycategory",
                        verbose_name="Categoria",
                    ),
                ),
            ],
            options={
                "verbose_name": "Item de inventario",
                "verbose_name_plural": "Itens de inventario",
                "ordering": ["name", "id"],
                "permissions": [
                    ("deactivate_inventoryitem", "Can deactivate inventory item"),
                    ("reactivate_inventoryitem", "Can reactivate inventory item"),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="inventoryitem",
            constraint=models.UniqueConstraint(
                django.db.models.functions.text.Lower("name"),
                name="uniq_diaconia_inventory_item_name_ci",
            ),
        ),
    ]
