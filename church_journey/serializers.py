from rest_framework import serializers

from pessoas.models import Person

from .enums import ChurchStatus
from .models import (
    ChurchJourney,
    DiscipleshipAttendance,
    DiscipleshipClass,
    DiscipleshipEnrollment,
    DiscipleshipLesson,
)


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


class DiscipleshipClassTeacherSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    display_name = serializers.CharField()
    full_name = serializers.CharField(required=False)


class DiscipleshipClassSerializer(serializers.ModelSerializer):
    teacher = DiscipleshipClassTeacherSerializer(read_only=True)
    teacher_id = serializers.PrimaryKeyRelatedField(
        queryset=Person.objects.all(),
        source="teacher",
        write_only=True,
    )

    class Meta:
        model = DiscipleshipClass
        fields = [
            "id",
            "name",
            "teacher",
            "teacher_id",
            "start_date",
            "expected_end_date",
            "planned_sessions",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "teacher", "status", "created_at", "updated_at")

    def validate_name(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Informe o nome da turma.")
        return value

    def validate_planned_sessions(self, value):
        if value <= 0:
            raise serializers.ValidationError("Informe uma quantidade positiva de aulas.")
        return value

    def validate(self, attrs):
        start_date = attrs.get("start_date", getattr(self.instance, "start_date", None))
        expected_end_date = attrs.get(
            "expected_end_date",
            getattr(self.instance, "expected_end_date", None),
        )
        if start_date and expected_end_date and expected_end_date < start_date:
            raise serializers.ValidationError(
                {"expected_end_date": "O termino previsto nao pode ser anterior ao inicio."}
            )
        return attrs


class DiscipleshipEnrollmentClassSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class DiscipleshipEnrollmentPersonSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    display_name = serializers.CharField()
    full_name = serializers.CharField()


class DiscipleshipEnrollmentSerializer(serializers.ModelSerializer):
    person = DiscipleshipEnrollmentPersonSerializer(read_only=True)
    person_id = serializers.PrimaryKeyRelatedField(
        queryset=Person.objects.all(),
        source="person",
        write_only=True,
    )
    discipleship_class = DiscipleshipEnrollmentClassSerializer(read_only=True)

    class Meta:
        model = DiscipleshipEnrollment
        fields = [
            "id",
            "person",
            "person_id",
            "discipleship_class",
            "status",
            "enrolled_at",
            "withdrawn_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = (
            "id",
            "person",
            "discipleship_class",
            "status",
            "enrolled_at",
            "withdrawn_at",
            "created_at",
            "updated_at",
        )


class DiscipleshipLessonSerializer(serializers.ModelSerializer):
    discipleship_class_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = DiscipleshipLesson
        fields = [
            "id",
            "discipleship_class_id",
            "title",
            "lesson_date",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = (
            "id",
            "discipleship_class_id",
            "status",
            "created_at",
            "updated_at",
        )

    def validate_title(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Informe o titulo da aula.")
        return value


class DiscipleshipAttendanceLessonSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    lesson_date = serializers.DateField()
    status = serializers.CharField()


class DiscipleshipAttendancePersonSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    display_name = serializers.CharField()


class DiscipleshipAttendanceRecordSerializer(serializers.ModelSerializer):
    recorded_by = serializers.SerializerMethodField()

    class Meta:
        model = DiscipleshipAttendance
        fields = ["id", "status", "recorded_by", "created_at", "updated_at"]

    def get_recorded_by(self, obj):
        if obj.recorded_by_id is None:
            return None
        return {
            "id": obj.recorded_by_id,
            "display_name": obj.recorded_by.get_full_name() or obj.recorded_by.username,
        }


class DiscipleshipAttendanceRecordInputSerializer(serializers.Serializer):
    enrollment_id = serializers.PrimaryKeyRelatedField(
        queryset=DiscipleshipEnrollment.objects.select_related("person", "discipleship_class"),
        source="enrollment",
    )
    status = serializers.CharField()


class DiscipleshipAttendanceBatchSerializer(serializers.Serializer):
    records = DiscipleshipAttendanceRecordInputSerializer(many=True)
