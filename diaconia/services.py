from django.db import IntegrityError, transaction
from django.db.models import Case, CharField, Count, F, IntegerField, Sum, Value, When
from django.db.models.functions import Coalesce

from .models import (
    AttendanceCount,
    AttendanceCountEntry,
    CountingEnvironment,
    InventoryCategory,
    InventoryCount,
    InventoryCountEntry,
    InventoryItem,
    InventoryLocation,
    StockCategory,
    StockItem,
    StockMovement,
)


INVALID_STOCK_CATEGORY_TRANSITION = "INVALID_STOCK_CATEGORY_TRANSITION"
INVALID_STOCK_ITEM_TRANSITION = "INVALID_STOCK_ITEM_TRANSITION"
STOCK_CATEGORY_INACTIVE = "STOCK_CATEGORY_INACTIVE"
STOCK_ITEM_INACTIVE = "STOCK_ITEM_INACTIVE"
INVALID_STOCK_MOVEMENT_QUANTITY = "INVALID_STOCK_MOVEMENT_QUANTITY"
INSUFFICIENT_STOCK = "INSUFFICIENT_STOCK"
INVALID_COUNTING_ENVIRONMENT_TRANSITION = "INVALID_COUNTING_ENVIRONMENT_TRANSITION"
INVALID_INVENTORY_CATEGORY_TRANSITION = "INVALID_INVENTORY_CATEGORY_TRANSITION"
INVENTORY_CATEGORY_INACTIVE = "INVENTORY_CATEGORY_INACTIVE"
INVALID_INVENTORY_ITEM_TRANSITION = "INVALID_INVENTORY_ITEM_TRANSITION"
INVALID_INVENTORY_LOCATION_TRANSITION = "INVALID_INVENTORY_LOCATION_TRANSITION"
INVENTORY_COUNT_DUPLICATE = "INVENTORY_COUNT_DUPLICATE"
INVENTORY_COUNT_MATRIX_MISMATCH = "INVENTORY_COUNT_MATRIX_MISMATCH"
INVENTORY_COUNT_WITHOUT_ITEMS = "INVENTORY_COUNT_WITHOUT_ITEMS"
INVENTORY_COUNT_WITHOUT_LOCATIONS = "INVENTORY_COUNT_WITHOUT_LOCATIONS"
INVALID_INVENTORY_COUNT_QUANTITY = "INVALID_INVENTORY_COUNT_QUANTITY"
INVENTORY_COUNT_WITHOUT_PREVIOUS = "INVENTORY_COUNT_WITHOUT_PREVIOUS"
ATTENDANCE_COUNT_DUPLICATE = "ATTENDANCE_COUNT_DUPLICATE"
ATTENDANCE_COUNT_ENVIRONMENT_MISMATCH = "ATTENDANCE_COUNT_ENVIRONMENT_MISMATCH"
ATTENDANCE_COUNT_WITHOUT_ENVIRONMENTS = "ATTENDANCE_COUNT_WITHOUT_ENVIRONMENTS"
INVALID_ATTENDANCE_COUNT_QUANTITY = "INVALID_ATTENDANCE_COUNT_QUANTITY"


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


class InventoryComparisonStatus:
    INCREASE = "INCREASE"
    DECREASE = "DECREASE"
    UNCHANGED = "UNCHANGED"
    NEW = "NEW"
    NOT_COUNTED = "NOT_COUNTED"


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


def create_counting_environment(*, name, description=""):
    return CountingEnvironment.objects.create(name=name, description=description, is_active=True)


def update_counting_environment(environment, *, name=None, description=None):
    if name is not None:
        environment.name = name
    if description is not None:
        environment.description = description
    environment.save()
    return environment


def deactivate_counting_environment(environment):
    if not environment.is_active:
        raise DiaconiaError(
            INVALID_COUNTING_ENVIRONMENT_TRANSITION,
            "Somente ambientes ativos podem ser inativados.",
        )
    environment.is_active = False
    environment.save(update_fields=["is_active", "updated_at"])
    return environment


def reactivate_counting_environment(environment):
    if environment.is_active:
        raise DiaconiaError(
            INVALID_COUNTING_ENVIRONMENT_TRANSITION,
            "Somente ambientes inativos podem ser reativados.",
        )
    environment.is_active = True
    environment.save(update_fields=["is_active", "updated_at"])
    return environment


def get_attendance_count_queryset():
    return (
        AttendanceCount.objects.select_related("created_by")
        .prefetch_related("entries__environment")
    )


def attendance_count_total_expression():
    return Coalesce(Sum("entries__quantity"), Value(0), output_field=IntegerField())


def attendance_count_shift_order_expression():
    return Case(
        When(shift=AttendanceCount.Shift.EVENING, then=Value(3)),
        When(shift=AttendanceCount.Shift.AFTERNOON, then=Value(2)),
        When(shift=AttendanceCount.Shift.MORNING, then=Value(1)),
        default=Value(0),
        output_field=IntegerField(),
    )


def get_attendance_count_list_queryset():
    return (
        AttendanceCount.objects.select_related("created_by")
        .annotate(total_people=attendance_count_total_expression(), shift_order=attendance_count_shift_order_expression())
        .order_by("-date", "-shift_order", "-created_at", "-id")
    )


def get_attendance_count_total(attendance_count):
    annotated_total = getattr(attendance_count, "total_people", None)
    if annotated_total is not None:
        return annotated_total
    entries = getattr(attendance_count, "_prefetched_objects_cache", {}).get("entries")
    if entries is not None:
        return sum(entry.quantity for entry in entries)
    result = attendance_count.entries.aggregate(total=Coalesce(Sum("quantity"), Value(0), output_field=IntegerField()))
    return result["total"] or 0


def validate_attendance_count_environments(entries):
    active_environment_ids = list(
        CountingEnvironment.objects.filter(is_active=True)
        .order_by("id")
        .values_list("id", flat=True)
    )
    if not active_environment_ids:
        raise DiaconiaError(
            ATTENDANCE_COUNT_WITHOUT_ENVIRONMENTS,
            "Nenhum ambiente ativo foi cadastrado.",
        )

    sent_environment_ids = [entry["environment"].id for entry in entries]
    if len(sent_environment_ids) != len(set(sent_environment_ids)):
        raise DiaconiaError(
            ATTENDANCE_COUNT_ENVIRONMENT_MISMATCH,
            "Cada ambiente deve aparecer apenas uma vez na contagem.",
        )

    if set(sent_environment_ids) != set(active_environment_ids):
        raise DiaconiaError(
            ATTENDANCE_COUNT_ENVIRONMENT_MISMATCH,
            "Os ambientes ativos mudaram. Atualize a tela e tente novamente.",
        )

    for entry in entries:
        environment = entry["environment"]
        if not environment.is_active:
            raise DiaconiaError(
                ATTENDANCE_COUNT_ENVIRONMENT_MISMATCH,
                "A contagem deve usar apenas ambientes ativos.",
            )
        if entry["quantity"] < 0:
            raise DiaconiaError(
                INVALID_ATTENDANCE_COUNT_QUANTITY,
                "A quantidade nao pode ser negativa.",
            )


def create_attendance_count(*, date, shift, notes="", entries, created_by):
    if AttendanceCount.objects.filter(date=date, shift=shift).exists():
        raise DiaconiaError(
            ATTENDANCE_COUNT_DUPLICATE,
            "Ja existe uma contagem registrada para esta data e turno.",
        )

    with transaction.atomic():
        validate_attendance_count_environments(entries)
        try:
            attendance_count = AttendanceCount.objects.create(
                date=date,
                shift=shift,
                notes=notes,
                created_by=created_by,
            )
            AttendanceCountEntry.objects.bulk_create(
                [
                    AttendanceCountEntry(
                        attendance_count=attendance_count,
                        environment=entry["environment"],
                        quantity=entry["quantity"],
                    )
                    for entry in entries
                ]
            )
        except IntegrityError as exc:
            raise DiaconiaError(
                ATTENDANCE_COUNT_DUPLICATE,
                "Ja existe uma contagem registrada para esta data e turno.",
            ) from exc

    return get_attendance_count_queryset().get(pk=attendance_count.pk)


def validate_attendance_count_historical_entries(attendance_count, entries):
    current_environment_ids = list(attendance_count.entries.order_by("environment_id").values_list("environment_id", flat=True))
    sent_environment_ids = [entry["environment"].id for entry in entries]

    if len(sent_environment_ids) != len(set(sent_environment_ids)):
        raise DiaconiaError(
            ATTENDANCE_COUNT_ENVIRONMENT_MISMATCH,
            "Cada ambiente deve aparecer apenas uma vez na contagem.",
        )

    if set(sent_environment_ids) != set(current_environment_ids):
        raise DiaconiaError(
            ATTENDANCE_COUNT_ENVIRONMENT_MISMATCH,
            "A correcao deve manter exatamente os ambientes originais da contagem.",
        )

    for entry in entries:
        if entry["quantity"] < 0:
            raise DiaconiaError(
                INVALID_ATTENDANCE_COUNT_QUANTITY,
                "A quantidade nao pode ser negativa.",
            )


def update_attendance_count(attendance_count, *, date, shift, notes="", entries):
    if AttendanceCount.objects.filter(date=date, shift=shift).exclude(pk=attendance_count.pk).exists():
        raise DiaconiaError(
            ATTENDANCE_COUNT_DUPLICATE,
            "Ja existe uma contagem registrada para esta data e turno.",
        )

    with transaction.atomic():
        locked_count = AttendanceCount.objects.select_for_update().get(pk=attendance_count.pk)
        validate_attendance_count_historical_entries(locked_count, entries)
        locked_count.date = date
        locked_count.shift = shift
        locked_count.notes = notes
        try:
            locked_count.save(update_fields=["date", "shift", "notes", "updated_at"])
            entries_by_environment_id = {entry["environment"].id: entry["quantity"] for entry in entries}
            count_entries = list(locked_count.entries.select_for_update())
            for count_entry in count_entries:
                count_entry.quantity = entries_by_environment_id[count_entry.environment_id]
            AttendanceCountEntry.objects.bulk_update(count_entries, ["quantity"])
        except IntegrityError as exc:
            raise DiaconiaError(
                ATTENDANCE_COUNT_DUPLICATE,
                "Ja existe uma contagem registrada para esta data e turno.",
            ) from exc

    return get_attendance_count_queryset().get(pk=attendance_count.pk)


def create_inventory_category(*, name, description=""):
    return InventoryCategory.objects.create(name=name, description=description, is_active=True)


def update_inventory_category(category, *, name=None, description=None):
    if name is not None:
        category.name = name
    if description is not None:
        category.description = description
    category.save()
    return category


def deactivate_inventory_category(category):
    if not category.is_active:
        raise DiaconiaError(
            INVALID_INVENTORY_CATEGORY_TRANSITION,
            "Somente categorias ativas podem ser inativadas.",
        )
    category.is_active = False
    category.save(update_fields=["is_active", "updated_at"])
    return category


def reactivate_inventory_category(category):
    if category.is_active:
        raise DiaconiaError(
            INVALID_INVENTORY_CATEGORY_TRANSITION,
            "Somente categorias inativas podem ser reativadas.",
        )
    category.is_active = True
    category.save(update_fields=["is_active", "updated_at"])
    return category


def create_inventory_location(*, name, description=""):
    return InventoryLocation.objects.create(name=name, description=description, is_active=True)


def update_inventory_location(location, *, name=None, description=None):
    if name is not None:
        location.name = name
    if description is not None:
        location.description = description
    location.save()
    return location


def deactivate_inventory_location(location):
    if not location.is_active:
        raise DiaconiaError(
            INVALID_INVENTORY_LOCATION_TRANSITION,
            "Somente locais ativos podem ser inativados.",
        )
    location.is_active = False
    location.save(update_fields=["is_active", "updated_at"])
    return location


def reactivate_inventory_location(location):
    if location.is_active:
        raise DiaconiaError(
            INVALID_INVENTORY_LOCATION_TRANSITION,
            "Somente locais inativos podem ser reativados.",
        )
    location.is_active = True
    location.save(update_fields=["is_active", "updated_at"])
    return location


def get_inventory_items_queryset():
    return InventoryItem.objects.select_related("category")


def get_inventory_count_queryset():
    return InventoryCount.objects.select_related("created_by").prefetch_related(
        "entries__item__category",
        "entries__location",
    )


def get_inventory_count_list_queryset():
    return (
        InventoryCount.objects.select_related("created_by")
        .annotate(
            items_count=Count("entries__item", distinct=True),
            locations_count=Count("entries__location", distinct=True),
        )
        .order_by("-date", "-created_at", "-id")
    )


def validate_inventory_count_matrix(entries):
    active_item_ids = list(
        InventoryItem.objects.filter(is_active=True)
        .order_by("id")
        .values_list("id", flat=True)
    )
    active_location_ids = list(
        InventoryLocation.objects.filter(is_active=True)
        .order_by("id")
        .values_list("id", flat=True)
    )

    if not active_item_ids:
        raise DiaconiaError(
            INVENTORY_COUNT_WITHOUT_ITEMS,
            "Nenhum item ativo disponivel para contagem.",
        )
    if not active_location_ids:
        raise DiaconiaError(
            INVENTORY_COUNT_WITHOUT_LOCATIONS,
            "Nenhum local ativo disponivel para contagem.",
        )

    expected_pairs = {(item_id, location_id) for item_id in active_item_ids for location_id in active_location_ids}
    sent_pairs = []
    for entry in entries:
        item = entry["item"]
        location = entry["location"]
        if not item.is_active or not location.is_active:
            raise DiaconiaError(
                INVENTORY_COUNT_MATRIX_MISMATCH,
                "Os itens ou locais ativos mudaram. Atualize a tela e tente novamente.",
            )
        if entry["quantity"] < 0:
            raise DiaconiaError(
                INVALID_INVENTORY_COUNT_QUANTITY,
                "A quantidade nao pode ser negativa.",
            )
        sent_pairs.append((item.id, location.id))

    if len(sent_pairs) != len(set(sent_pairs)):
        raise DiaconiaError(
            INVENTORY_COUNT_MATRIX_MISMATCH,
            "Cada combinacao de item e local deve aparecer apenas uma vez.",
        )

    if set(sent_pairs) != expected_pairs:
        raise DiaconiaError(
            INVENTORY_COUNT_MATRIX_MISMATCH,
            "Os itens ou locais ativos mudaram. Atualize a tela e tente novamente.",
        )


def create_inventory_count(*, date, notes="", entries, created_by):
    if InventoryCount.objects.filter(date=date).exists():
        raise DiaconiaError(
            INVENTORY_COUNT_DUPLICATE,
            "Ja existe uma contagem de inventario registrada para esta data.",
        )

    with transaction.atomic():
        validate_inventory_count_matrix(entries)
        try:
            inventory_count = InventoryCount.objects.create(
                date=date,
                notes=notes,
                created_by=created_by,
            )
            InventoryCountEntry.objects.bulk_create(
                [
                    InventoryCountEntry(
                        inventory_count=inventory_count,
                        item=entry["item"],
                        location=entry["location"],
                        quantity=entry["quantity"],
                    )
                    for entry in entries
                ]
            )
        except IntegrityError as exc:
            raise DiaconiaError(
                INVENTORY_COUNT_DUPLICATE,
                "Ja existe uma contagem de inventario registrada para esta data.",
            ) from exc

    return get_inventory_count_queryset().get(pk=inventory_count.pk)


def validate_inventory_count_historical_entries(inventory_count, entries):
    current_pairs = set(
        inventory_count.entries.order_by("item_id", "location_id").values_list("item_id", "location_id")
    )
    sent_pairs = []
    for entry in entries:
        if entry["quantity"] < 0:
            raise DiaconiaError(
                INVALID_INVENTORY_COUNT_QUANTITY,
                "A quantidade nao pode ser negativa.",
            )
        sent_pairs.append((entry["item"].id, entry["location"].id))

    if len(sent_pairs) != len(set(sent_pairs)):
        raise DiaconiaError(
            INVENTORY_COUNT_MATRIX_MISMATCH,
            "Cada combinacao de item e local deve aparecer apenas uma vez.",
        )

    if set(sent_pairs) != current_pairs:
        raise DiaconiaError(
            INVENTORY_COUNT_MATRIX_MISMATCH,
            "A correcao deve manter exatamente os itens e locais originais da contagem.",
        )


def update_inventory_count(inventory_count, *, date, notes="", entries):
    if InventoryCount.objects.filter(date=date).exclude(pk=inventory_count.pk).exists():
        raise DiaconiaError(
            INVENTORY_COUNT_DUPLICATE,
            "Ja existe uma contagem de inventario registrada para esta data.",
        )

    with transaction.atomic():
        locked_count = InventoryCount.objects.select_for_update().get(pk=inventory_count.pk)
        validate_inventory_count_historical_entries(locked_count, entries)
        locked_count.date = date
        locked_count.notes = notes
        try:
            locked_count.save(update_fields=["date", "notes", "updated_at"])
            quantities_by_pair = {
                (entry["item"].id, entry["location"].id): entry["quantity"]
                for entry in entries
            }
            count_entries = list(locked_count.entries.select_for_update())
            for count_entry in count_entries:
                count_entry.quantity = quantities_by_pair[(count_entry.item_id, count_entry.location_id)]
            InventoryCountEntry.objects.bulk_update(count_entries, ["quantity"])
        except IntegrityError as exc:
            raise DiaconiaError(
                INVENTORY_COUNT_DUPLICATE,
                "Ja existe uma contagem de inventario registrada para esta data.",
            ) from exc

    return get_inventory_count_queryset().get(pk=inventory_count.pk)


def get_previous_inventory_count(inventory_count):
    return (
        get_inventory_count_queryset()
        .filter(date__lt=inventory_count.date)
        .order_by("-date", "-created_at", "-id")
        .first()
    )


def _prefetched_entries(inventory_count):
    return list(
        getattr(inventory_count, "_prefetched_objects_cache", {}).get("entries")
        or inventory_count.entries.select_related("item__category", "location")
    )


def _inventory_count_maps(inventory_count):
    items = {}
    totals = {}
    location_quantities = {}
    locations_by_item = {}
    for entry in _prefetched_entries(inventory_count):
        item = entry.item
        location = entry.location
        items[item.id] = item
        totals[item.id] = totals.get(item.id, 0) + entry.quantity
        location_quantities[(item.id, location.id)] = entry.quantity
        locations_by_item.setdefault(item.id, {})[location.id] = location
    return {
        "items": items,
        "totals": totals,
        "location_quantities": location_quantities,
        "locations_by_item": locations_by_item,
    }


def _status_from_values(previous_value, current_value):
    if current_value > previous_value:
        return InventoryComparisonStatus.INCREASE
    if current_value < previous_value:
        return InventoryComparisonStatus.DECREASE
    return InventoryComparisonStatus.UNCHANGED


def _variation_percent(previous_value, variation):
    if previous_value == 0:
        return None
    return round((variation / previous_value) * 100, 2)


def build_inventory_count_comparison(inventory_count):
    current_count = get_inventory_count_queryset().get(pk=inventory_count.pk)
    previous_count = get_previous_inventory_count(current_count)
    if previous_count is None:
        return {
            "current": current_count,
            "previous": None,
            "items": [],
            "summary": {
                "increase": 0,
                "decrease": 0,
                "unchanged": 0,
                "new": 0,
                "not_counted": 0,
            },
        }

    current_maps = _inventory_count_maps(current_count)
    previous_maps = _inventory_count_maps(previous_count)
    item_ids = sorted(
        set(current_maps["items"]).union(previous_maps["items"]),
        key=lambda item_id: (
            (current_maps["items"].get(item_id) or previous_maps["items"][item_id]).category.name,
            (current_maps["items"].get(item_id) or previous_maps["items"][item_id]).name,
            item_id,
        ),
    )

    summary = {"increase": 0, "decrease": 0, "unchanged": 0, "new": 0, "not_counted": 0}
    compared_items = []
    for item_id in item_ids:
        item = current_maps["items"].get(item_id) or previous_maps["items"][item_id]
        has_previous = item_id in previous_maps["totals"]
        has_current = item_id in current_maps["totals"]
        previous_total = previous_maps["totals"].get(item_id)
        current_total = current_maps["totals"].get(item_id)

        if has_previous and has_current:
            variation = current_total - previous_total
            status = _status_from_values(previous_total, current_total)
            variation_percent = _variation_percent(previous_total, variation)
            location_ids = sorted(
                set(previous_maps["locations_by_item"].get(item_id, {})).union(
                    current_maps["locations_by_item"].get(item_id, {})
                ),
                key=lambda location_id: (
                    (
                        current_maps["locations_by_item"].get(item_id, {}).get(location_id)
                        or previous_maps["locations_by_item"].get(item_id, {})[location_id]
                    ).name,
                    location_id,
                ),
            )
            locations = []
            for location_id in location_ids:
                location = (
                    current_maps["locations_by_item"].get(item_id, {}).get(location_id)
                    or previous_maps["locations_by_item"].get(item_id, {})[location_id]
                )
                previous_location_quantity = previous_maps["location_quantities"].get((item_id, location_id))
                current_location_quantity = current_maps["location_quantities"].get((item_id, location_id))
                if previous_location_quantity is None:
                    location_status = InventoryComparisonStatus.NEW
                    location_variation = None
                elif current_location_quantity is None:
                    location_status = InventoryComparisonStatus.NOT_COUNTED
                    location_variation = None
                else:
                    location_variation = current_location_quantity - previous_location_quantity
                    location_status = _status_from_values(previous_location_quantity, current_location_quantity)
                locations.append(
                    {
                        "location_id": location_id,
                        "location_name": location.name,
                        "previous_quantity": previous_location_quantity,
                        "current_quantity": current_location_quantity,
                        "variation": location_variation,
                        "status": location_status,
                    }
                )
        elif has_current:
            variation = None
            variation_percent = None
            status = InventoryComparisonStatus.NEW
            locations = []
        else:
            variation = None
            variation_percent = None
            status = InventoryComparisonStatus.NOT_COUNTED
            locations = []

        summary[status.lower()] += 1
        compared_items.append(
            {
                "item_id": item_id,
                "item_name": item.name,
                "category_id": item.category_id,
                "category_name": item.category.name,
                "previous_total": previous_total,
                "current_total": current_total,
                "variation": variation,
                "variation_percent": variation_percent,
                "status": status,
                "locations": locations,
            }
        )

    return {
        "current": current_count,
        "previous": previous_count,
        "items": compared_items,
        "summary": summary,
    }


def ensure_inventory_category_active(category):
    if not category.is_active:
        raise DiaconiaError(
            INVENTORY_CATEGORY_INACTIVE,
            "A categoria selecionada esta inativa.",
        )


def create_inventory_item(*, name, category, description=""):
    ensure_inventory_category_active(category)
    return InventoryItem.objects.create(
        name=name,
        category=category,
        description=description,
        is_active=True,
    )


def update_inventory_item(item, *, name=None, category=None, description=None):
    if category is not None and category.pk != item.category_id:
        ensure_inventory_category_active(category)
        item.category = category
    if name is not None:
        item.name = name
    if description is not None:
        item.description = description
    item.save()
    return item


def deactivate_inventory_item(item):
    if not item.is_active:
        raise DiaconiaError(
            INVALID_INVENTORY_ITEM_TRANSITION,
            "Somente itens ativos podem ser inativados.",
        )
    item.is_active = False
    item.save(update_fields=["is_active", "updated_at"])
    return item


def reactivate_inventory_item(item):
    if item.is_active:
        raise DiaconiaError(
            INVALID_INVENTORY_ITEM_TRANSITION,
            "Somente itens inativos podem ser reativados.",
        )
    item.is_active = True
    item.save(update_fields=["is_active", "updated_at"])
    return item
