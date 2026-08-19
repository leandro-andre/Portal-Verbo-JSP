from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .services import get_access_status
from .models import AccessRequest


class PublicAccessRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessRequest
        fields = [
            "id",
            "full_name",
            "birth_date",
            "email",
            "phone",
            "status",
            "created_at",
        ]
        read_only_fields = ("id", "status", "created_at")

    def validate(self, attrs):
        access_request = AccessRequest(**attrs)
        try:
            access_request.full_clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict) from exc

        attrs.update(
            {
                "full_name": access_request.full_name,
                "email": access_request.email,
                "phone": access_request.phone,
            }
        )
        return attrs


class AccessRequestPersonSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    display_name = serializers.CharField()
    full_name = serializers.CharField()
    birth_date = serializers.DateField()
    email = serializers.EmailField(allow_blank=True)
    phone = serializers.CharField(allow_blank=True)
    status = serializers.CharField()


class AccessRequestUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    display_name = serializers.CharField()


class AdminAccessRequestSerializer(serializers.ModelSerializer):
    person = AccessRequestPersonSerializer(read_only=True)
    reviewed_by = AccessRequestUserSerializer(read_only=True)
    candidates = serializers.SerializerMethodField()

    class Meta:
        model = AccessRequest
        fields = [
            "id",
            "full_name",
            "birth_date",
            "email",
            "phone",
            "status",
            "created_at",
            "updated_at",
            "reviewed_at",
            "rejection_reason",
            "person",
            "reviewed_by",
            "candidates",
        ]
        read_only_fields = fields

    def get_candidates(self, obj):
        if obj.status != AccessRequest.Status.PENDING:
            return []
        candidates = obj.candidate_people if hasattr(obj, "candidate_people") else []
        return AccessRequestPersonSerializer(candidates, many=True).data


class ApproveAccessRequestSerializer(serializers.Serializer):
    person_id = serializers.IntegerField(required=False)
    create_new_person = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        person_id = attrs.get("person_id")
        create_new_person = attrs.get("create_new_person", False)
        if bool(person_id) == bool(create_new_person):
            raise serializers.ValidationError(
                {
                    "identity": (
                        "Escolha uma pessoa existente ou solicite a criacao de uma nova pessoa."
                    )
                }
            )
        return attrs


class RejectAccessRequestSerializer(serializers.Serializer):
    rejection_reason = serializers.CharField(required=False, allow_blank=True)


class PortalUserPersonSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    display_name = serializers.CharField()
    status = serializers.CharField()


class PortalUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    is_active = serializers.BooleanField()
    access_status = serializers.SerializerMethodField()
    last_login = serializers.DateTimeField(allow_null=True)
    date_joined = serializers.DateTimeField()
    person = PortalUserPersonSerializer(allow_null=True)
    is_superuser = serializers.BooleanField()

    def get_access_status(self, obj):
        return get_access_status(obj)
