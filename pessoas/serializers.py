from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from usuarios.services import get_access_status

from .models import Person


class PersonPortalUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    access_status = serializers.SerializerMethodField()

    def get_access_status(self, obj):
        return get_access_status(obj)


class PersonSerializer(serializers.ModelSerializer):
    allow_possible_duplicate = serializers.BooleanField(
        default=False,
        required=False,
        write_only=True,
    )
    display_name = serializers.CharField(read_only=True)
    portal_user = PersonPortalUserSerializer(source="user_account", read_only=True)

    class Meta:
        model = Person
        fields = [
            "id",
            "full_name",
            "preferred_name",
            "display_name",
            "birth_date",
            "email",
            "phone",
            "status",
            "portal_user",
            "allow_possible_duplicate",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "display_name", "created_at", "updated_at")

    def validate(self, attrs):
        allow_possible_duplicate = attrs.pop("allow_possible_duplicate", False)
        values = {}
        if self.instance is not None:
            values = {
                "full_name": self.instance.full_name,
                "preferred_name": self.instance.preferred_name,
                "birth_date": self.instance.birth_date,
                "email": self.instance.email,
                "phone": self.instance.phone,
                "status": self.instance.status,
            }
        values.update(attrs)

        person = Person(**values)
        try:
            person.full_clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict) from exc

        attrs.update(
            {
                "full_name": person.full_name,
                "preferred_name": person.preferred_name,
                "email": person.email,
                "phone": person.phone,
                "allow_possible_duplicate": allow_possible_duplicate,
            }
        )
        return attrs

    def create(self, validated_data):
        validated_data.pop("allow_possible_duplicate", None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop("allow_possible_duplicate", None)
        return super().update(instance, validated_data)
