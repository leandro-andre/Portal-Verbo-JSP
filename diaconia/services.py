from django.db import transaction
from django.db.models import Case, CharField, F, IntegerField, Sum, Value, When
from django.db.models.functions import Coalesce

from .models import StockCategory, StockItem, StockMovement


INVALID_STOCK_CATEGORY_TRANSITION = "INVALID_STOCK_CATEGORY_TRANSITION"
INVALID_STOCK_ITEM_TRANSITION = "INVALID_STOCK_ITEM_TRANSITION"
STOCK_CATEGORY_INACTIVE = "STOCK_CATEGORY_INACTIVE"
STOCK_ITEM_INACTIVE = "STOCK_ITEM_INACTIVE"
INVALID_STOCK_MOVEMENT_QUANTITY = "INVALID_STOCK_MOVEMENT_QUANTITY"
INSUFFICIENT_STOCK = "INSUFFICIENT_STOCK"


class StockStatus:
    NORMAL = "NORMAL"
    LOW_STOCK = "LOW_STOCK"
    WITHOUT_MINIMUM = "WITHOUT_MINIMUM"
    INACTIVE = "INACTIVE"

    LABELS = {
        NORMAL: "Normal",
        LOW_STOCK: "Estoque baixo",
        WITHOUT_MINIMUM: "Sem controle",
        INACTIVE: "Inativo",
    }


class DiaconiaError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(message)


def deactivate_stock_category(category):
    if not category.is_active:
        raise DiaconiaError(
            INVALID_STOCK_CATEGORY_TRANSITION,
            "Somente categorias ativas podem ser inativadas.",
        )
    category.is_active = False
    category.save(update_fields=["is_active", "updated_at"])
    return category


def reactivate_stock_category(category):
    if category.is_active:
        raise DiaconiaError(
            INVALID_STOCK_CATEGORY_TRANSITION,
            "Somente categorias inativas podem ser reativadas.",
        )
    category.is_active = True
    category.save(update_fields=["is_active", "updated_at"])
    return category


def deactivate_stock_item(item):
    if not item.is_active:
        raise DiaconiaError(
            INVALID_STOCK_ITEM_TRANSITION,
            "Somente itens ativos podem ser inativados.",
        )
    item.is_active = False
    item.save(update_fields=["is_active", "updated_at"])
    return item


def reactivate_stock_item(item):
    if item.is_active:
        raise DiaconiaError(
            INVALID_STOCK_ITEM_TRANSITION,
            "Somente itens inativos podem ser reativados.",
        )
    item.is_active = True
    item.save(update_fields=["is_active", "updated_at"])
    return item


def ensure_stock_category_active(category):
    if not category.is_active:
        raise DiaconiaError(
            STOCK_CATEGORY_INACTIVE,
            "A categoria precisa estar ativa.",
        )


def create_stock_category(*, name, description=""):
    return StockCategory.objects.create(name=name, description=description, is_active=True)


def update_stock_category(category, *, name=None, description=None):
    if name is not None:
        category.name = name
    if description is not None:
        category.description = description
    category.save()
    return category


def create_stock_item(*, name, category, unit, minimum_stock=0, notes=""):
    ensure_stock_category_active(category)
    return StockItem.objects.create(
        name=name,
        category=category,
        unit=unit,
        minimum_stock=minimum_stock,
        notes=notes,
        is_active=True,
    )


def update_stock_item(item, *, name=None, category=None, unit=None, minimum_stock=None, notes=None):
    if category is not None:
        ensure_stock_category_active(category)
        item.category = category
    if name is not None:
        item.name = name
    if unit is not None:
        item.unit = unit
    if minimum_stock is not None:
        item.minimum_stock = minimum_stock
    if notes is not None:
        item.notes = notes
    item.save()
    return item


def stock_balance_expression():
    return Coalesce(
        Sum(
            Case(
                When(movements__movement_type=StockMovement.Type.ENTRADA, then=F("movements__quantity")),
                When(movements__movement_type=StockMovement.Type.SAIDA, then=-F("movements__quantity")),
                default=Value(0),
                output_field=IntegerField(),
            )
        ),
        Value(0),
        output_field=IntegerField(),
    )


def get_stock_items_with_balance():
    return StockItem.objects.select_related("category").annotate(current_stock=stock_balance_expression())


def stock_status_annotation():
    return Case(
        When(is_active=False, then=Value(StockStatus.INACTIVE)),
        When(minimum_stock=0, then=Value(StockStatus.WITHOUT_MINIMUM)),
        When(minimum_stock__gt=0, minimum_stock__gte=stock_balance_expression(), then=Value(StockStatus.LOW_STOCK)),
        default=Value(StockStatus.NORMAL),
        output_field=CharField(),
    )


def get_stock_items_with_status():
    return get_stock_items_with_balance().annotate(stock_status=stock_status_annotation())


def classify_stock_status(*, current_stock, minimum_stock, is_active=True):
    if not is_active:
        return StockStatus.INACTIVE
    if minimum_stock == 0:
        return StockStatus.WITHOUT_MINIMUM
    if current_stock <= minimum_stock:
        return StockStatus.LOW_STOCK
    return StockStatus.NORMAL


def stock_status_label(status):
    return StockStatus.LABELS.get(status, status)


def get_stock_summary(*, replenishment_limit=6):
    queryset = get_stock_items_with_status().filter(is_active=True)
    active_items = queryset.count()
    low_stock_items = queryset.filter(stock_status=StockStatus.LOW_STOCK).count()
    without_minimum_control = queryset.filter(stock_status=StockStatus.WITHOUT_MINIMUM).count()
    replenishment_items = queryset.filter(stock_status=StockStatus.LOW_STOCK).order_by(
        "current_stock",
        "minimum_stock",
        "name",
        "id",
    )[:replenishment_limit]
    return {
        "active_items": active_items,
        "low_stock_items": low_stock_items,
        "without_minimum_control": without_minimum_control,
        "replenishment_items": list(replenishment_items),
    }


def get_current_stock(item):
    result = item.movements.aggregate(
        current_stock=Coalesce(
            Sum(
                Case(
                    When(movement_type=StockMovement.Type.ENTRADA, then=F("quantity")),
                    When(movement_type=StockMovement.Type.SAIDA, then=-F("quantity")),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            ),
            Value(0),
            output_field=IntegerField(),
        )
    )
    return result["current_stock"] or 0


def create_stock_movement(*, item, movement_type, quantity, notes="", created_by):
    if quantity <= 0:
        raise DiaconiaError(
            INVALID_STOCK_MOVEMENT_QUANTITY,
            "Informe uma quantidade maior que zero.",
        )

    with transaction.atomic():
        locked_item = StockItem.objects.select_for_update().get(pk=item.pk)
        if not locked_item.is_active:
            raise DiaconiaError(
                STOCK_ITEM_INACTIVE,
                "Este item esta inativo e nao pode receber movimentacoes.",
            )

        current_stock = get_current_stock(locked_item)
        if movement_type == StockMovement.Type.SAIDA and quantity > current_stock:
            if current_stock == 0:
                raise DiaconiaError(
                    INSUFFICIENT_STOCK,
                    "Nao ha saldo disponivel para este item.",
                )
            raise DiaconiaError(
                INSUFFICIENT_STOCK,
                f"O saldo disponivel e de {current_stock} {locked_item.unit}.",
            )

        return StockMovement.objects.create(
            item=locked_item,
            movement_type=movement_type,
            quantity=quantity,
            notes=notes,
            created_by=created_by,
        )
