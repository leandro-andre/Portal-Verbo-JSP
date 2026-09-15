from django.conf import settings
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower


class DiaconiaModule(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ("view_diaconia_module", "Can view Diaconia module"),
            ("manage_diaconia_stock", "Can manage Diaconia stock"),
            ("manage_diaconia_counting", "Can manage Diaconia counting"),
            ("manage_diaconia_inventory", "Can manage Diaconia inventory"),
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


class CountingEnvironment(models.Model):
    name = models.CharField("Nome", max_length=120)
    description = models.TextField("Descricao", blank=True)
    is_active = models.BooleanField("Ativo", default=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        ordering = ["name", "id"]
        verbose_name = "Ambiente de contagem"
        verbose_name_plural = "Ambientes de contagem"
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="uniq_diaconia_counting_environment_name_ci",
            )
        ]
        permissions = [
            ("deactivate_countingenvironment", "Can deactivate counting environment"),
            ("reactivate_countingenvironment", "Can reactivate counting environment"),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = (self.name or "").strip()
        return super().save(*args, **kwargs)


class AttendanceCount(models.Model):
    class Shift(models.TextChoices):
        MORNING = "MORNING", "Manha"
        AFTERNOON = "AFTERNOON", "Tarde"
        EVENING = "EVENING", "Noite"

    date = models.DateField("Data")
    shift = models.CharField("Turno", max_length=20, choices=Shift.choices)
    notes = models.TextField("Observacao", blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Criado por",
        on_delete=models.PROTECT,
        related_name="diaconia_attendance_counts",
    )
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at", "-id"]
        verbose_name = "Contagem de publico"
        verbose_name_plural = "Contagens de publico"
        constraints = [
            models.UniqueConstraint(fields=["date", "shift"], name="uniq_diaconia_attendance_count_date_shift"),
        ]
        indexes = [
            models.Index(fields=["date", "shift"], name="diaconia_count_date_shift_idx"),
        ]

    def __str__(self):
        return f"{self.date} - {self.get_shift_display()}"


class AttendanceCountEntry(models.Model):
    attendance_count = models.ForeignKey(
        AttendanceCount,
        verbose_name="Contagem",
        on_delete=models.CASCADE,
        related_name="entries",
    )
    environment = models.ForeignKey(
        CountingEnvironment,
        verbose_name="Ambiente",
        on_delete=models.PROTECT,
        related_name="attendance_entries",
    )
    quantity = models.IntegerField("Quantidade")

    class Meta:
        ordering = ["environment__name", "id"]
        verbose_name = "Item da contagem de publico"
        verbose_name_plural = "Itens da contagem de publico"
        constraints = [
            models.UniqueConstraint(
                fields=["attendance_count", "environment"],
                name="uniq_diaconia_attendance_count_environment",
            ),
            models.CheckConstraint(
                condition=Q(quantity__gte=0),
                name="chk_diaconia_attendance_entry_quantity_gte_0",
            ),
        ]

    def __str__(self):
        return f"{self.environment} - {self.quantity}"


class InventoryCategory(models.Model):
    name = models.CharField("Nome", max_length=120)
    description = models.TextField("Descricao", blank=True)
    is_active = models.BooleanField("Ativa", default=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        ordering = ["name", "id"]
        verbose_name = "Categoria de inventario"
        verbose_name_plural = "Categorias de inventario"
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="uniq_diaconia_inventory_category_name_ci",
            )
        ]
        permissions = [
            ("deactivate_inventorycategory", "Can deactivate inventory category"),
            ("reactivate_inventorycategory", "Can reactivate inventory category"),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = (self.name or "").strip()
        return super().save(*args, **kwargs)


class InventoryLocation(models.Model):
    name = models.CharField("Nome", max_length=120)
    description = models.TextField("Descricao", blank=True)
    is_active = models.BooleanField("Ativo", default=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        ordering = ["name", "id"]
        verbose_name = "Local de inventario"
        verbose_name_plural = "Locais de inventario"
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="uniq_diaconia_inventory_location_name_ci",
            )
        ]
        permissions = [
            ("deactivate_inventorylocation", "Can deactivate inventory location"),
            ("reactivate_inventorylocation", "Can reactivate inventory location"),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = (self.name or "").strip()
        return super().save(*args, **kwargs)


class InventoryItem(models.Model):
    category = models.ForeignKey(
        InventoryCategory,
        verbose_name="Categoria",
        on_delete=models.PROTECT,
        related_name="items",
    )
    name = models.CharField("Nome", max_length=160)
    description = models.TextField("Descricao", blank=True)
    is_active = models.BooleanField("Ativo", default=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        ordering = ["name", "id"]
        verbose_name = "Item de inventario"
        verbose_name_plural = "Itens de inventario"
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="uniq_diaconia_inventory_item_name_ci",
            )
        ]
        permissions = [
            ("deactivate_inventoryitem", "Can deactivate inventory item"),
            ("reactivate_inventoryitem", "Can reactivate inventory item"),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = (self.name or "").strip()
        return super().save(*args, **kwargs)
