from rest_framework import serializers

from pessoas.models import Person

from .models import Departamento, DepartmentMembership, DepartmentRole
from .selectors import (
    get_department_context_permissions,
    is_department_membership_operationally_eligible,
)


class DepartmentSerializer(serializers.ModelSerializer):
    codigo = serializers.CharField()

    class Meta:
        model = Departamento
        fields = ["id", "nome", "codigo", "descricao", "ativo", "criado_em"]
        read_only_fields = ["id", "ativo", "criado_em"]

    def validate(self, attrs):
        extra_fields = set(self.initial_data).difference({"nome", "codigo", "descricao"})
        if extra_fields:
            raise serializers.ValidationError(
                {field: "Este campo nao pode ser enviado neste endpoint." for field in sorted(extra_fields)}
            )
        return attrs

    def validate_nome(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Informe o nome do departamento.")
        return value

    def validate_codigo(self, value):
        codigo = Departamento.normalizar_codigo(value)
        if not codigo:
            raise serializers.ValidationError("Informe o codigo do departamento.")
        if Departamento.objects.filter(codigo__iexact=codigo).exists():
            raise serializers.ValidationError("Este codigo ja esta em uso.")
        return codigo

    def create(self, validated_data):
        validated_data["ativo"] = True
        return super().create(validated_data)


class DepartmentDetailSerializer(DepartmentSerializer):
    permissions = serializers.SerializerMethodField()

    class Meta(DepartmentSerializer.Meta):
        fields = DepartmentSerializer.Meta.fields + ["permissions"]

    def get_permissions(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        return get_department_context_permissions(user, obj)


class DepartmentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departamento
        fields = ["nome", "descricao"]

    def validate(self, attrs):
        extra_fields = set(self.initial_data).difference({"nome", "descricao", "codigo"})
        if extra_fields:
            raise serializers.ValidationError(
                {field: "Este campo nao pode ser enviado neste endpoint." for field in sorted(extra_fields)}
            )
        codigo = self.initial_data.get("codigo") if hasattr(self, "initial_data") else None
        if codigo is not None and Departamento.normalizar_codigo(codigo) != self.instance.codigo:
            raise serializers.ValidationError(
                {"codigo": "O codigo do departamento nao pode ser alterado."}
            )
        return attrs

    def validate_nome(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Informe o nome do departamento.")
        return value


class DepartmentRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepartmentRole
        fields = [
            "id",
            "department",
            "name",
            "code",
            "active",
            "can_manage_department",
            "can_manage_members",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "department", "active", "created_at", "updated_at"]


class DepartmentRoleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepartmentRole
        fields = ["name", "code", "can_manage_department", "can_manage_members"]

    def validate(self, attrs):
        extra_fields = set(self.initial_data).difference(
            {"name", "code", "can_manage_department", "can_manage_members"}
        )
        if extra_fields:
            raise serializers.ValidationError(
                {field: "Este campo nao pode ser enviado neste endpoint." for field in sorted(extra_fields)}
            )
        return attrs

    def validate_name(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Informe o nome do cargo.")
        return value

    def validate_code(self, value):
        code = Departamento.normalizar_codigo(value)
        if not code:
            raise serializers.ValidationError("Informe o codigo do cargo.")
        department = self.context["department"]
        if DepartmentRole.objects.filter(department=department, code__iexact=code).exists():
            raise serializers.ValidationError("Este codigo ja esta em uso neste departamento.")
        return code


class DepartmentRoleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepartmentRole
        fields = ["name", "can_manage_department", "can_manage_members"]

    def validate(self, attrs):
        extra_fields = set(self.initial_data).difference(
            {"name", "code", "can_manage_department", "can_manage_members"}
        )
        if extra_fields:
            raise serializers.ValidationError(
                {field: "Este campo nao pode ser enviado neste endpoint." for field in sorted(extra_fields)}
            )
        code = self.initial_data.get("code") if hasattr(self, "initial_data") else None
        if code is not None and Departamento.normalizar_codigo(code) != self.instance.code:
            raise serializers.ValidationError({"code": "O codigo do cargo nao pode ser alterado."})
        return attrs

    def validate_name(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Informe o nome do cargo.")
        return value


class DepartmentPersonSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(read_only=True)

    class Meta:
        model = Person
        fields = ["id", "full_name", "display_name", "email", "phone"]


class DepartmentMembershipSerializer(serializers.ModelSerializer):
    person = DepartmentPersonSerializer(read_only=True)
    role = DepartmentRoleSerializer(read_only=True)
    operationally_eligible = serializers.SerializerMethodField()

    class Meta:
        model = DepartmentMembership
        fields = [
            "id",
            "department",
            "person",
            "role",
            "status",
            "joined_at",
            "left_at",
            "operationally_eligible",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_operationally_eligible(self, obj):
        return is_department_membership_operationally_eligible(obj)


class DepartmentMembershipCreateSerializer(serializers.ModelSerializer):
    person_id = serializers.PrimaryKeyRelatedField(
        queryset=Person.objects.all(),
        source="person",
    )
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=DepartmentRole.objects.all(),
        source="role",
    )

    class Meta:
        model = DepartmentMembership
        fields = ["person_id", "role_id", "joined_at"]

    def validate(self, attrs):
        extra_fields = set(self.initial_data).difference({"person_id", "role_id", "joined_at"})
        if extra_fields:
            raise serializers.ValidationError(
                {field: "Este campo nao pode ser enviado neste endpoint." for field in sorted(extra_fields)}
            )
        return attrs


class DepartmentMembershipUpdateSerializer(serializers.ModelSerializer):
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=DepartmentRole.objects.all(),
        source="role",
    )

    class Meta:
        model = DepartmentMembership
        fields = ["role_id"]

    def validate(self, attrs):
        extra_fields = set(self.initial_data).difference({"role_id"})
        if extra_fields:
            raise serializers.ValidationError(
                {field: "Este campo nao pode ser enviado neste endpoint." for field in sorted(extra_fields)}
            )
        return attrs
