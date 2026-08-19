from rest_framework import serializers

from .enums import ChurchStatus
from .models import ChurchJourney


class ChurchJourneySerializer(serializers.ModelSerializer):
    person_id = serializers.IntegerField(read_only=True)
    church_status = serializers.SerializerMethodField()

    class Meta:
        model = ChurchJourney
        fields = [
            "id",
            "person_id",
            "started_at",
            "church_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = (
            "id",
            "person_id",
            "church_status",
            "created_at",
            "updated_at",
        )

    def get_church_status(self, obj):
        return ChurchStatus.VISITOR.value
