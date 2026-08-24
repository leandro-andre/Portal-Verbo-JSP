from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from usuarios.services import get_access_status
from church_journey.selectors import (
    get_completed_discipleship,
    get_discipleship_completed_at,
    has_completed_discipleship,
    is_eligible_for_membership,
    can_create_membership,
)

from .models import Person, PersonUnavailability, validate_brazilian_mobile


def get_photo_url(obj, request=None):
    photo = getattr(obj, "photo", None)
    if not photo:
        return None
    try:
        url = photo.url
    except ValueError:
        return None
    return request.build_absolute_uri(url) if request is not None else url


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
    photo_url = serializers.SerializerMethodField()
    portal_user = PersonPortalUserSerializer(source="user_account", read_only=True)
    has_church_journey = serializers.SerializerMethodField()
    discipleship = serializers.SerializerMethodField()

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
            "photo_url",
            "status",
            "portal_user",
            "has_church_journey",
            "discipleship",
            "allow_possible_duplicate",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "display_name", "created_at", "updated_at")

    def get_has_church_journey(self, obj):
        return hasattr(obj, "church_journey")

    def get_photo_url(self, obj):
        return get_photo_url(obj, self.context.get("request"))

    def get_discipleship(self, obj):
        completed_enrollment = get_completed_discipleship(obj)
        return {
            "completed": has_completed_discipleship(obj),
            "completed_at": get_discipleship_completed_at(obj),
            "completed_class": (
                {
                    "id": completed_enrollment.discipleship_class_id,
                    "name": completed_enrollment.discipleship_class.name,
                }
                if completed_enrollment is not None
                else None
            ),
            "membership_eligible": is_eligible_for_membership(obj),
            "membership_can_create": can_create_membership(obj),
        }

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
                "phone": validate_brazilian_mobile(person.phone),
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


class PersonUnavailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonUnavailability
        fields = [
            "id",
            "person",
            "start_date",
            "end_date",
            "start_time",
            "end_time",
            "reason",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "person", "status", "created_at", "updated_at"]

    def validate(self, attrs):
        allowed_fields = {"start_date", "end_date", "start_time", "end_time", "reason"}
        extra_fields = set(self.initial_data).difference(allowed_fields)
        if extra_fields:
            raise serializers.ValidationError(
                {field: "Este campo nao pode ser enviado neste endpoint." for field in sorted(extra_fields)}
            )

        values = {}
        if self.instance is not None:
            values = {
                "start_date": self.instance.start_date,
                "end_date": self.instance.end_date,
                "start_time": self.instance.start_time,
                "end_time": self.instance.end_time,
                "reason": self.instance.reason,
            }
        values.update(attrs)
        attrs.update(values)
        return attrs


class OperationalUnavailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonUnavailability
        fields = ["id", "start_date", "end_date", "start_time", "end_time", "status"]
