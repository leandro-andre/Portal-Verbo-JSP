from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("diaconia", "0002_stock_category_item"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="StockMovement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "movement_type",
                    models.CharField(
                        choices=[("ENTRADA", "Entrada"), ("SAIDA", "Saida")],
                        max_length=20,
                        verbose_name="Tipo",
                    ),
                ),
                ("quantity", models.PositiveIntegerField(verbose_name="Quantidade")),
                ("notes", models.TextField(blank=True, verbose_name="Observacao")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="diaconia_stock_movements",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Criado por",
                    ),
                ),
                (
                    "item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="movements",
                        to="diaconia.stockitem",
                        verbose_name="Item",
                    ),
                ),
            ],
            options={
                "verbose_name": "Movimentacao de estoque",
                "verbose_name_plural": "Movimentacoes de estoque",
                "ordering": ["-created_at", "-id"],
                "indexes": [
                    models.Index(fields=["item", "-created_at"], name="diaconia_mov_item_created_idx"),
                    models.Index(fields=["-created_at"], name="diaconia_mov_created_idx"),
                ],
            },
        ),
    ]
