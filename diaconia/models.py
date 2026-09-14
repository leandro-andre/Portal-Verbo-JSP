from django.conf import settings
from django.db import models
from django.db.models.functions import Lower


class DiaconiaModule(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ("view_diaconia_module", "Can view Diaconia module"),
            ("manage_diaconia_stock", "Can manage Diaconia stock"),
        )
        verbose_name = "Modulo Diaconia"
        verbose_name_plural = "Modulo Diaconia"


class StockCategory(models.Model):
    name = models.CharField("Nome", max_length=120)
    description = models.TextField("Descricao", blank=True)
    is_active = models.BooleanField("Ativa", default=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        ordering = ["name", "id"]
        verbose_name = "Categoria de estoque"
        verbose_name_plural = "Categorias de estoque"
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="uniq_diaconia_stock_category_name_ci",
            )
        ]
        permissions = [
            ("deactivate_stockcategory", "Can deactivate stock category"),
            ("reactivate_stockcategory", "Can reactivate stock category"),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = (self.name or "").strip()
        return super().save(*args, **kwargs)


class StockItem(models.Model):
    class Unit(models.TextChoices):
        UN = "UN", "Unidade"
        PACOTE = "PACOTE", "Pacote"
        CAIXA = "CAIXA", "Caixa"
        FARDO = "FARDO", "Fardo"
        GARRAFAO = "GARRAFAO", "Garrafao"
        LITRO = "LITRO", "Litro"
        KG = "KG", "Quilograma"

    name = models.CharField("Nome", max_length=160)
    category = models.ForeignKey(
        StockCategory,
        verbose_name="Categoria",
        on_delete=models.PROTECT,
        related_name="items",
    )
    unit = models.CharField("Unidade", max_length=20, choices=Unit.choices)
    minimum_stock = models.PositiveIntegerField("Estoque minimo", default=0)
    notes = models.TextField("Observacao", blank=True)
    is_active = models.BooleanField("Ativo", default=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        ordering = ["name", "id"]
        verbose_name = "Item de estoque"
        verbose_name_plural = "Itens de estoque"
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="uniq_diaconia_stock_item_name_ci",
            )
        ]
        permissions = [
            ("deactivate_stockitem", "Can deactivate stock item"),
            ("reactivate_stockitem", "Can reactivate stock item"),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = (self.name or "").strip()
        return super().save(*args, **kwargs)


class StockMovement(models.Model):
    class Type(models.TextChoices):
        ENTRADA = "ENTRADA", "Entrada"
        SAIDA = "SAIDA", "Saida"

    item = models.ForeignKey(
        StockItem,
        verbose_name="Item",
        on_delete=models.PROTECT,
        related_name="movements",
    )
    movement_type = models.CharField("Tipo", max_length=20, choices=Type.choices)
    quantity = models.PositiveIntegerField("Quantidade")
    notes = models.TextField("Observacao", blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Criado por",
        on_delete=models.PROTECT,
        related_name="diaconia_stock_movements",
    )
    created_at = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "Movimentacao de estoque"
        verbose_name_plural = "Movimentacoes de estoque"
        indexes = [
            models.Index(fields=["item", "-created_at"], name="diaconia_mov_item_created_idx"),
            models.Index(fields=["-created_at"], name="diaconia_mov_created_idx"),
        ]

    def __str__(self):
        return f"{self.item} - {self.get_movement_type_display()} {self.quantity}"
