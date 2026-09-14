from django.db import migrations, models
import django.db.models.deletion
import django.db.models.functions.text


class Migration(migrations.Migration):

    dependencies = [
        ("diaconia", "0001_initial"),
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
                ),
                "verbose_name": "Modulo Diaconia",
                "verbose_name_plural": "Modulo Diaconia",
            },
        ),
        migrations.CreateModel(
            name="StockCategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, verbose_name="Nome")),
                ("description", models.TextField(blank=True, verbose_name="Descricao")),
                ("is_active", models.BooleanField(default=True, verbose_name="Ativa")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Atualizado em")),
            ],
            options={
                "verbose_name": "Categoria de estoque",
                "verbose_name_plural": "Categorias de estoque",
                "ordering": ["name", "id"],
                "permissions": [
                    ("deactivate_stockcategory", "Can deactivate stock category"),
                    ("reactivate_stockcategory", "Can reactivate stock category"),
                ],
            },
        ),
        migrations.CreateModel(
            name="StockItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160, verbose_name="Nome")),
                (
                    "unit",
                    models.CharField(
                        choices=[
                            ("UN", "Unidade"),
                            ("PACOTE", "Pacote"),
                            ("CAIXA", "Caixa"),
                            ("FARDO", "Fardo"),
                            ("GARRAFAO", "Garrafao"),
                            ("LITRO", "Litro"),
                            ("KG", "Quilograma"),
                        ],
                        max_length=20,
                        verbose_name="Unidade",
                    ),
                ),
                ("minimum_stock", models.PositiveIntegerField(default=0, verbose_name="Estoque minimo")),
                ("notes", models.TextField(blank=True, verbose_name="Observacao")),
                ("is_active", models.BooleanField(default=True, verbose_name="Ativo")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Atualizado em")),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="items",
                        to="diaconia.stockcategory",
                        verbose_name="Categoria",
                    ),
                ),
            ],
            options={
                "verbose_name": "Item de estoque",
                "verbose_name_plural": "Itens de estoque",
                "ordering": ["name", "id"],
                "permissions": [
                    ("deactivate_stockitem", "Can deactivate stock item"),
                    ("reactivate_stockitem", "Can reactivate stock item"),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="stockcategory",
            constraint=models.UniqueConstraint(
                django.db.models.functions.text.Lower("name"),
                name="uniq_diaconia_stock_category_name_ci",
            ),
        ),
        migrations.AddConstraint(
            model_name="stockitem",
            constraint=models.UniqueConstraint(
                django.db.models.functions.text.Lower("name"),
                name="uniq_diaconia_stock_item_name_ci",
            ),
        ),
    ]
