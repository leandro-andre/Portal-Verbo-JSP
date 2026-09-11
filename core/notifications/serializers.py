from rest_framework import serializers

from core.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "type",
            "title",
            "message",
            "target_url",
            "source_app",
            "source_type",
            "source_id",
            "created_at",
            "read_at",
            "is_read",
        ]

    def get_is_read(self, obj):
        return obj.read_at is not None
