from rest_framework import serializers

from .models import StockCategory, StockItem
from .services import DiaconiaError, ensure_stock_category_active


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

    class Meta:
        model = StockItem
        fields = [
            "id",
            "name",
            "category",
            "category_id",
            "unit",
            "unit_label",
            "minimum_stock",
            "notes",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "category", "unit_label", "is_active", "created_at", "updated_at"]

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
