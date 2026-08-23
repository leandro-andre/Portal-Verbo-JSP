from rest_framework import serializers

from .models import Departamento


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
