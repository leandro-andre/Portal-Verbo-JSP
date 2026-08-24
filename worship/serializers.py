from rest_framework import serializers

from .models import Weekday, WorshipService, WorshipServiceTemplate


class WorshipServiceTemplateSerializer(serializers.ModelSerializer):
    weekday_label = serializers.CharField(source="get_weekday_display", read_only=True)

    class Meta:
        model = WorshipServiceTemplate
        fields = ["id", "name", "weekday", "weekday_label", "time", "active", "created_at", "updated_at"]
        read_only_fields = ["id", "weekday_label", "active", "created_at", "updated_at"]

    def validate_weekday(self, value):
        if value not in Weekday.values:
            raise serializers.ValidationError("Dia da semana invalido.")
        return value


class WorshipServiceTemplateSummarySerializer(serializers.ModelSerializer):
    weekday_label = serializers.CharField(source="get_weekday_display", read_only=True)

    class Meta:
        model = WorshipServiceTemplate
        fields = ["id", "name", "weekday", "weekday_label", "time", "active"]


class WorshipServiceSerializer(serializers.ModelSerializer):
    template = WorshipServiceTemplateSummarySerializer(read_only=True)
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = WorshipService
        fields = [
            "id",
            "template",
            "name",
            "date",
            "source_date",
            "time",
            "status",
            "status_label",
            "kind",
            "kind_label",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "template",
            "source_date",
            "status",
            "status_label",
            "kind",
            "kind_label",
            "created_at",
            "updated_at",
        ]


class GenerateWorshipServicesSerializer(serializers.Serializer):
    year = serializers.IntegerField(min_value=2000, max_value=2100)
    month = serializers.IntegerField(min_value=1, max_value=12)


class ExtraordinaryWorshipServiceSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    date = serializers.DateField()
    time = serializers.TimeField()
    notes = serializers.CharField(required=False, allow_blank=True)
