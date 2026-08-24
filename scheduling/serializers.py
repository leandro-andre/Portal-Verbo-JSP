from rest_framework import serializers

from departamentos.models import Departamento, DepartmentMembership
from departamentos.serializers import DepartmentRoleSerializer
from worship.models import WorshipService

from .models import Schedule, ScheduleAssignment
from .selectors import get_assignment_candidates, get_schedule_assignments


class ScheduleDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departamento
        fields = ["id", "nome", "codigo", "ativo"]


class ScheduleWorshipServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorshipService
        fields = ["id", "name", "date", "time", "kind", "status"]


class ScheduleUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    display_name = serializers.CharField()


class AssignmentPersonSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(source="display_name")


class AssignmentDepartmentMembershipSerializer(serializers.ModelSerializer):
    person = AssignmentPersonSerializer(read_only=True)
    role = DepartmentRoleSerializer(read_only=True)

    class Meta:
        model = DepartmentMembership
        fields = ["id", "person", "role", "status"]


class ScheduleAssignmentSerializer(serializers.ModelSerializer):
    department_membership = AssignmentDepartmentMembershipSerializer(read_only=True)
    created_by = ScheduleUserSerializer(read_only=True)

    class Meta:
        model = ScheduleAssignment
        fields = ["id", "department_membership", "created_by", "created_at"]


class ScheduleSerializer(serializers.ModelSerializer):
    department = ScheduleDepartmentSerializer(read_only=True)
    worship_service = ScheduleWorshipServiceSerializer(read_only=True)
    created_by = ScheduleUserSerializer(read_only=True)
    assignments_count = serializers.IntegerField(read_only=True)
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = Schedule
        fields = [
            "id",
            "department",
            "worship_service",
            "status",
            "created_by",
            "created_at",
            "updated_at",
            "permissions",
            "assignments_count",
        ]

    def get_permissions(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        from .views import can_manage_schedule

        can_manage = can_manage_schedule(user, obj.department)
        return {
            "can_manage": can_manage,
            "can_edit_assignments": can_manage and obj.status == Schedule.Status.DRAFT,
        }


class ScheduleDetailSerializer(ScheduleSerializer):
    assignments = serializers.SerializerMethodField()

    class Meta(ScheduleSerializer.Meta):
        fields = ScheduleSerializer.Meta.fields + ["assignments"]

    def get_assignments(self, obj):
        return ScheduleAssignmentSerializer(get_schedule_assignments(obj), many=True).data


class ScheduleCreateSerializer(serializers.Serializer):
    department_id = serializers.PrimaryKeyRelatedField(queryset=Departamento.objects.all(), source="department")
    worship_service_id = serializers.PrimaryKeyRelatedField(queryset=WorshipService.objects.all(), source="worship_service")


class ScheduleAssignmentCreateSerializer(serializers.Serializer):
    department_membership_id = serializers.PrimaryKeyRelatedField(
        queryset=DepartmentMembership.objects.select_related("person", "department", "role"),
        source="department_membership",
    )


class ScheduleCandidateSerializer(serializers.Serializer):
    def to_representation(self, instance):
        return {
            "department_membership": AssignmentDepartmentMembershipSerializer(instance["department_membership"]).data,
            "eligible": instance["eligibility"].eligible,
            "reasons": [reason.as_dict() for reason in instance["eligibility"].reasons],
        }


def serialize_assignment_candidates(schedule):
    return ScheduleCandidateSerializer(get_assignment_candidates(schedule), many=True).data
