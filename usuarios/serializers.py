import re

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from PIL import Image, UnidentifiedImageError

from church_journey.selectors import get_discipleship_completed_at, has_completed_discipleship
from departamentos.models import DepartmentMembership
from pessoas.models import Person, validate_brazilian_mobile
from pessoas.serializers import get_photo_url
from .services import get_access_status
from .models import AccessRequest


USERNAME_ALREADY_EXISTS_CODE = "USERNAME_ALREADY_EXISTS"


def normalize_phone(value):
    digits = re.sub(r"\D+", "", value or "")
    return digits or (value or "").strip()


class PublicAccessRequestCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, required=True, trim_whitespace=False)
    password_confirm = serializers.CharField(write_only=True, required=True, trim_whitespace=False)

    class Meta:
        model = AccessRequest
        fields = [
            "id",
            "full_name",
            "birth_date",
            "email",
            "phone",
            "username",
            "password",
            "password_confirm",
            "status",
            "created_at",
        ]
        read_only_fields = ("id", "status", "created_at")

    def validate(self, attrs):
        user_model = get_user_model()
        username = user_model.normalize_username((attrs.get("username") or "").strip())
        password = attrs.get("password") or ""
        password_confirm = attrs.get("password_confirm") or ""
        attrs["phone"] = normalize_phone(attrs.get("phone"))

        errors = {}
        username_field = user_model._meta.get_field(user_model.USERNAME_FIELD)
        if not username:
            errors["username"] = ["Informe o usuario."]
        elif len(username) > username_field.max_length:
            errors["username"] = [f"Certifique-se de que o valor tenha no maximo {username_field.max_length} caracteres."]
        else:
            for validator in username_field.validators:
                try:
                    validator(username)
                except DjangoValidationError as exc:
                    errors.setdefault("username", []).extend(exc.messages)

        if password != password_confirm:
            errors["password_confirm"] = ["As senhas nao conferem."]

        if password:
            candidate_user = user_model(username=username, email=attrs.get("email") or "")
            try:
                validate_password(password, candidate_user)
            except DjangoValidationError as exc:
                errors["password"] = list(exc.messages)
        else:
            errors["password"] = ["Informe a senha."]

        if errors:
            raise serializers.ValidationError(errors)

        access_request = AccessRequest(
            full_name=attrs.get("full_name"),
            birth_date=attrs.get("birth_date"),
            email=attrs.get("email"),
            phone=attrs.get("phone"),
        )
        try:
            access_request.full_clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict) from exc

        attrs.update(
            {
                "full_name": access_request.full_name,
                "email": access_request.email,
                "phone": access_request.phone,
                "username": username,
            }
        )
        return attrs

    def create(self, validated_data):
        username = validated_data.pop("username")
        password = validated_data.pop("password")
        validated_data.pop("password_confirm", None)
        user_model = get_user_model()
        usuario = user_model(
            username=username,
            email=validated_data["email"],
            telefone=validated_data["phone"],
            is_active=False,
        )
        usuario.set_password(password)
        usuario.save()
        return AccessRequest.objects.create(usuario=usuario, **validated_data)


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


class AccessRequestPendingUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    is_active = serializers.BooleanField()
    access_status = serializers.SerializerMethodField()

    def get_access_status(self, obj):
        return get_access_status(obj)


class AdminAccessRequestSerializer(serializers.ModelSerializer):
    person = AccessRequestPersonSerializer(read_only=True)
    reviewed_by = AccessRequestUserSerializer(read_only=True)
    usuario = AccessRequestPendingUserSerializer(read_only=True)
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
            "usuario",
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
    full_name = serializers.CharField()
    email = serializers.EmailField(allow_blank=True)
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


class LinkUserPersonSerializer(serializers.Serializer):
    person_id = serializers.IntegerField(required=True)


SELF_PROFILE_MESSAGE = (
    "Seu acesso ainda nao esta vinculado a uma pessoa. Procure a Secretaria para revisar seu cadastro."
)


class MyProfileUpdateSerializer(serializers.Serializer):
    phone = serializers.CharField(required=False, allow_blank=True)

    allowed_fields = {"phone"}

    def validate(self, attrs):
        extra_fields = set(self.initial_data).difference(self.allowed_fields)
        if extra_fields:
            raise serializers.ValidationError(
                {field: "Este campo nao pode ser alterado neste endpoint." for field in sorted(extra_fields)}
            )
        if "phone" in self.initial_data:
            try:
                attrs["phone"] = validate_brazilian_mobile(attrs.get("phone", ""))
            except DjangoValidationError as exc:
                raise serializers.ValidationError({"phone": exc.messages}) from exc
        return attrs


class MyProfilePhotoUploadSerializer(serializers.Serializer):
    photo = serializers.FileField(required=True)

    allowed_content_types = {"image/jpeg", "image/png", "image/webp"}
    max_size = 5 * 1024 * 1024

    def validate_photo(self, photo):
        content_type = getattr(photo, "content_type", "")
        if content_type not in self.allowed_content_types:
            raise serializers.ValidationError("Envie uma imagem JPEG, PNG ou WEBP.")
        if photo.size > self.max_size:
            raise serializers.ValidationError("A foto deve ter no maximo 5MB.")
        try:
            Image.open(photo).verify()
        except (UnidentifiedImageError, OSError) as exc:
            raise serializers.ValidationError("Envie um arquivo de imagem valido.") from exc
        finally:
            photo.seek(0)
        return photo


def _account_payload(user):
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "email": user.email,
        "is_active": user.is_active,
    }


def _person_payload(person, request):
    return {
        "id": person.id,
        "full_name": person.full_name,
        "preferred_name": person.preferred_name,
        "display_name": person.display_name,
        "birth_date": person.birth_date.isoformat(),
        "email": person.email,
        "phone": person.phone,
        "status": person.status,
        "photo_url": get_photo_url(person, request),
    }


def _church_payload(person):
    membership = getattr(person, "membership", None)
    if membership is not None:
        membership_status = membership.status
        member_since = membership.member_since.isoformat()
    else:
        membership_status = None
        member_since = None

    completed_at = get_discipleship_completed_at(person)
    return {
        "person_status": person.status,
        "has_church_journey": hasattr(person, "church_journey"),
        "membership_status": membership_status,
        "member_since": member_since,
        "discipleship_completed": has_completed_discipleship(person),
        "discipleship_completed_at": completed_at.isoformat() if completed_at else None,
    }


def _departments_payload(person):
    memberships = (
        DepartmentMembership.objects.filter(person=person, status=DepartmentMembership.Status.ACTIVE)
        .select_related("department", "role")
        .order_by("department__nome", "role__name", "id")
    )
    return [
        {
            "id": membership.id,
            "status": membership.status,
            "joined_at": membership.joined_at.isoformat(),
            "department": {
                "id": membership.department_id,
                "name": membership.department.nome,
                "code": membership.department.codigo,
            },
            "role": {
                "id": membership.role_id,
                "name": membership.role.name,
                "code": membership.role.code,
            },
        }
        for membership in memberships
    ]


def my_profile_payload(user, request):
    person = getattr(user, "person", None)
    if person is None:
        return {
            "person_linked": False,
            "message": SELF_PROFILE_MESSAGE,
            "account": _account_payload(user),
            "person": None,
            "church": None,
            "departments": [],
        }

    person = (
        Person.objects.select_related("membership", "church_journey")
        .filter(pk=person.pk)
        .first()
    ) or person
    return {
        "person_linked": True,
        "message": "",
        "account": _account_payload(user),
        "person": _person_payload(person, request),
        "church": _church_payload(person),
        "departments": _departments_payload(person),
    }
