from rest_framework import serializers

from .models import (
    AttendanceCount,
    AttendanceCountEntry,
    CountingEnvironment,
    InventoryCategory,
    InventoryItem,
    InventoryLocation,
    StockCategory,
    StockItem,
    StockMovement,
)
from .services import (
    DiaconiaError,
    classify_stock_status,
    ensure_inventory_category_active,
    ensure_stock_category_active,
    get_attendance_count_total,
    stock_status_label,
)


def reject_extra_fields(initial_data, allowed_fields):
    extra_fields = set(initial_data).difference(allowed_fields)
    if extra_fields:
        raise serializers.ValidationError(
            {field: "Este campo nao pode ser enviado neste endpoint." for field in sorted(extra_fields)}
        )


class StockCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StockCategory
        fields = ["id", "name", "description", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "is_active", "created_at", "updated_at"]

    def validate(self, attrs):
        reject_extra_fields(self.initial_data, {"name", "description"})
        return attrs

    def validate_name(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Informe o nome da categoria.")
        queryset = StockCategory.objects.filter(name__iexact=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("Ja existe uma categoria com este nome.")
        return value


class StockCategoryUpdateSerializer(StockCategorySerializer):
    class Meta(StockCategorySerializer.Meta):
        fields = ["name", "description"]
        read_only_fields = []


class StockCategoryOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockCategory
        fields = ["id", "name", "is_active"]
        read_only_fields = fields


class StockItemSerializer(serializers.ModelSerializer):
    category = StockCategoryOptionSerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=StockCategory.objects.all(),
        source="category",
        write_only=True,
    )
    unit_label = serializers.CharField(source="get_unit_display", read_only=True)
    current_stock = serializers.SerializerMethodField()
    stock_status = serializers.SerializerMethodField()
    stock_status_label = serializers.SerializerMethodField()

    class Meta:
        model = StockItem
        fields = [
            "id",
            "name",
            "category",
            "category_id",
            "unit",
            "unit_label",
            "current_stock",
            "stock_status",
            "stock_status_label",
            "minimum_stock",
            "notes",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "category",
            "unit_label",
            "current_stock",
            "stock_status",
            "stock_status_label",
            "is_active",
            "created_at",
            "updated_at",
        ]

    def get_current_stock(self, obj):
        return getattr(obj, "current_stock", 0) or 0

    def get_stock_status(self, obj):
        return getattr(
            obj,
            "stock_status",
            classify_stock_status(
                current_stock=self.get_current_stock(obj),
                minimum_stock=obj.minimum_stock,
                is_active=obj.is_active,
            ),
        )

    def get_stock_status_label(self, obj):
        return stock_status_label(self.get_stock_status(obj))

    def validate(self, attrs):
        reject_extra_fields(
            self.initial_data,
            {"name", "category_id", "unit", "minimum_stock", "notes"},
        )
        category = attrs.get("category")
        if category is not None:
            try:
                ensure_stock_category_active(category)
            except DiaconiaError as exc:
                raise serializers.ValidationError({"category_id": exc.message}) from exc
        return attrs

    def validate_name(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Informe o nome do item.")
        queryset = StockItem.objects.filter(name__iexact=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("Ja existe um item com este nome.")
        return value

    def validate_minimum_stock(self, value):
        if value < 0:
            raise serializers.ValidationError("O estoque minimo nao pode ser negativo.")
        return value


class StockItemUpdateSerializer(StockItemSerializer):
    class Meta(StockItemSerializer.Meta):
        fields = ["name", "category_id", "unit", "minimum_stock", "notes"]
        read_only_fields = []


class StockUnitSerializer(serializers.Serializer):
    value = serializers.CharField()
    label = serializers.CharField()


class StockMovementItemSerializer(serializers.ModelSerializer):
    unit_label = serializers.CharField(source="get_unit_display", read_only=True)

    class Meta:
        model = StockItem
        fields = ["id", "name", "unit", "unit_label", "is_active"]
        read_only_fields = fields


class StockMovementUserSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    display_name = serializers.CharField(read_only=True)


def serialize_user(user):
    return {
        "id": user.id,
        "display_name": getattr(user, "display_name", None) or user.get_full_name() or user.username,
    }


class StockMovementSerializer(serializers.ModelSerializer):
    item = StockMovementItemSerializer(read_only=True)
    movement_type_label = serializers.CharField(source="get_movement_type_display", read_only=True)
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = StockMovement
        fields = [
            "id",
            "item",
            "movement_type",
            "movement_type_label",
            "quantity",
            "notes",
            "created_by",
            "created_at",
        ]
        read_only_fields = fields

    def get_created_by(self, obj):
        return serialize_user(obj.created_by)


class StockMovementCreateSerializer(serializers.ModelSerializer):
    item_id = serializers.PrimaryKeyRelatedField(
        queryset=StockItem.objects.all(),
        source="item",
    )

    class Meta:
        model = StockMovement
        fields = ["item_id", "movement_type", "quantity", "notes"]

    def validate(self, attrs):
        reject_extra_fields(self.initial_data, {"item_id", "movement_type", "quantity", "notes"})
        return attrs

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Informe uma quantidade maior que zero.")
        return value


class CountingEnvironmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CountingEnvironment
        fields = ["id", "name", "description", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "is_active", "created_at", "updated_at"]

    def validate(self, attrs):
        reject_extra_fields(self.initial_data, {"name", "description"})
        return attrs

    def validate_name(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Informe o nome do ambiente.")
        queryset = CountingEnvironment.objects.filter(name__iexact=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("Ja existe um ambiente com este nome.")
        return value


class CountingEnvironmentUpdateSerializer(CountingEnvironmentSerializer):
    class Meta(CountingEnvironmentSerializer.Meta):
        fields = ["name", "description"]
        read_only_fields = []


class InventoryCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryCategory
        fields = ["id", "name", "description", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "is_active", "created_at", "updated_at"]

    def validate(self, attrs):
        reject_extra_fields(self.initial_data, {"name", "description"})
        return attrs

    def validate_name(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Informe o nome da categoria.")
        queryset = InventoryCategory.objects.filter(name__iexact=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("Ja existe uma categoria com este nome.")
        return value


class InventoryCategoryUpdateSerializer(InventoryCategorySerializer):
    class Meta(InventoryCategorySerializer.Meta):
        fields = ["name", "description"]
        read_only_fields = []


class InventoryLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryLocation
        fields = ["id", "name", "description", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "is_active", "created_at", "updated_at"]

    def validate(self, attrs):
        reject_extra_fields(self.initial_data, {"name", "description"})
        return attrs

    def validate_name(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Informe o nome do local.")
        queryset = InventoryLocation.objects.filter(name__iexact=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("Ja existe um local com este nome.")
        return value


class InventoryLocationUpdateSerializer(InventoryLocationSerializer):
    class Meta(InventoryLocationSerializer.Meta):
        fields = ["name", "description"]
        read_only_fields = []


class InventoryCategoryOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryCategory
        fields = ["id", "name", "is_active"]
        read_only_fields = fields


class InventoryItemSerializer(serializers.ModelSerializer):
    category = InventoryCategoryOptionSerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=InventoryCategory.objects.all(),
        source="category",
        write_only=True,
    )

    class Meta:
        model = InventoryItem
        fields = [
            "id",
            "name",
            "description",
            "category",
            "category_id",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "category", "is_active", "created_at", "updated_at"]

    def validate(self, attrs):
        reject_extra_fields(self.initial_data, {"name", "description", "category_id"})
        category = attrs.get("category")
        if category is not None:
            instance_category_id = getattr(self.instance, "category_id", None)
            if category.pk != instance_category_id:
                try:
                    ensure_inventory_category_active(category)
                except DiaconiaError as exc:
                    raise serializers.ValidationError({"category_id": exc.message}) from exc
        return attrs

    def validate_name(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Informe o nome do item.")
        queryset = InventoryItem.objects.filter(name__iexact=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("Ja existe um item com este nome.")
        return value


class InventoryItemUpdateSerializer(InventoryItemSerializer):
    class Meta(InventoryItemSerializer.Meta):
        fields = ["name", "description", "category_id"]
        read_only_fields = []


class AttendanceCountEnvironmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CountingEnvironment
        fields = ["id", "name", "is_active"]
        read_only_fields = fields


class AttendanceCountEntrySerializer(serializers.ModelSerializer):
    environment = AttendanceCountEnvironmentSerializer(read_only=True)

    class Meta:
        model = AttendanceCountEntry
        fields = ["id", "environment", "quantity"]
        read_only_fields = fields


class AttendanceCountSerializer(serializers.ModelSerializer):
    entries = AttendanceCountEntrySerializer(many=True, read_only=True)
    shift_label = serializers.CharField(source="get_shift_display", read_only=True)
    total_people = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceCount
        fields = [
            "id",
            "date",
            "shift",
            "shift_label",
            "notes",
            "total_people",
            "created_by",
            "entries",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_total_people(self, obj):
        return get_attendance_count_total(obj)

    def get_created_by(self, obj):
        return serialize_user(obj.created_by)


class AttendanceCountListSerializer(serializers.ModelSerializer):
    shift_label = serializers.CharField(source="get_shift_display", read_only=True)
    total_people = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceCount
        fields = [
            "id",
            "date",
            "shift",
            "shift_label",
            "total_people",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_total_people(self, obj):
        return get_attendance_count_total(obj)

    def get_created_by(self, obj):
        return serialize_user(obj.created_by)


class AttendanceCountEntryCreateSerializer(serializers.Serializer):
    environment_id = serializers.PrimaryKeyRelatedField(
        queryset=CountingEnvironment.objects.all(),
        source="environment",
    )
    quantity = serializers.IntegerField(min_value=0)

    def to_internal_value(self, data):
        reject_extra_fields(data, {"environment_id", "quantity"})
        return super().to_internal_value(data)


class AttendanceCountCreateSerializer(serializers.Serializer):
    date = serializers.DateField()
    shift = serializers.ChoiceField(choices=AttendanceCount.Shift.choices)
    notes = serializers.CharField(required=False, allow_blank=True)
    entries = AttendanceCountEntryCreateSerializer(many=True, allow_empty=False)

    def validate(self, attrs):
        reject_extra_fields(self.initial_data, {"date", "shift", "notes", "entries"})
        return attrs


class AttendanceCountUpdateSerializer(AttendanceCountCreateSerializer):
    pass


class AttendanceCountFilterSerializer(serializers.Serializer):
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    shift = serializers.ChoiceField(choices=AttendanceCount.Shift.choices, required=False)
    created_by = serializers.IntegerField(required=False, min_value=1)

    def validate(self, attrs):
        reject_extra_fields(self.initial_data, {"date_from", "date_to", "shift", "created_by"})
        date_from = attrs.get("date_from")
        date_to = attrs.get("date_to")
        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError({"date_to": "A data final deve ser maior ou igual a data inicial."})
        return attrs
