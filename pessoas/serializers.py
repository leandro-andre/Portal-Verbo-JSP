from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Person


class PersonSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(read_only=True)

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
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "display_name", "created_at", "updated_at")

    def validate(self, attrs):
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
            }
        )
        return attrs
