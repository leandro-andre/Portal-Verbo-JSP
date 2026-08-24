from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import WorshipService, WorshipServiceTemplate
from .serializers import (
    ExtraordinaryWorshipServiceSerializer,
    GenerateWorshipServicesSerializer,
    WorshipServiceSerializer,
    WorshipServiceTemplateSerializer,
)
from .services import (
    WorshipScheduleError,
    cancel_worship_service,
    create_extraordinary_worship_service,
    create_worship_service_template,
    deactivate_worship_service_template,
    generate_worship_services_for_month,
    reactivate_worship_service,
    reactivate_worship_service_template,
    update_worship_service,
    update_worship_service_template,
)


def ensure_authenticated(user):
    if not getattr(user, "is_authenticated", False):
        raise PermissionDenied("Autenticacao obrigatoria.")


def can_manage_schedule(user):
    return bool(
        user.has_perm("worship.add_worshipservicetemplate")
        and user.has_perm("worship.change_worshipservicetemplate")
        and user.has_perm("worship.add_worshipservice")
        and user.has_perm("worship.change_worshipservice")
    )


def can_view_schedule(user):
    return bool(
        user.has_perm("worship.view_worshipservicetemplate")
        or user.has_perm("worship.view_worshipservice")
    )


def business_error_response(error):
    return Response({"code": error.code, "message": error.message}, status=status.HTTP_409_CONFLICT)


def validation_error_response(error):
    return Response(error.message_dict if hasattr(error, "message_dict") else error.messages, status=status.HTTP_400_BAD_REQUEST)


class TemplateListCreateView(APIView):
    def get(self, request):
        ensure_authenticated(request.user)
        if not can_view_schedule(request.user):
            raise PermissionDenied("Sem permissao para visualizar a agenda de cultos.")
        queryset = WorshipServiceTemplate.objects.all().ordered()
        return Response(WorshipServiceTemplateSerializer(queryset, many=True).data)

    def post(self, request):
        ensure_authenticated(request.user)
        if not can_manage_schedule(request.user):
            raise PermissionDenied("Sem permissao para administrar a agenda de cultos.")
        serializer = WorshipServiceTemplateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            template = create_worship_service_template(**serializer.validated_data)
        except ValidationError as error:
            return validation_error_response(error)
        return Response(WorshipServiceTemplateSerializer(template).data, status=status.HTTP_201_CREATED)


class TemplateDetailView(APIView):
    def get_object(self, pk):
        return get_object_or_404(WorshipServiceTemplate, pk=pk)

    def get(self, request, pk):
        ensure_authenticated(request.user)
        if not can_view_schedule(request.user):
            raise PermissionDenied("Sem permissao para visualizar a agenda de cultos.")
        return Response(WorshipServiceTemplateSerializer(self.get_object(pk)).data)

    def patch(self, request, pk):
        ensure_authenticated(request.user)
        if not can_manage_schedule(request.user):
            raise PermissionDenied("Sem permissao para administrar a agenda de cultos.")
        template = self.get_object(pk)
        serializer = WorshipServiceTemplateSerializer(template, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            template = update_worship_service_template(template, **serializer.validated_data)
        except ValidationError as error:
            return validation_error_response(error)
        return Response(WorshipServiceTemplateSerializer(template).data)


class TemplateDeactivateView(APIView):
    def post(self, request, pk):
        ensure_authenticated(request.user)
        if not request.user.has_perm("worship.deactivate_worship_service_template"):
            raise PermissionDenied("Sem permissao para inativar culto padrao.")
        try:
            template = deactivate_worship_service_template(get_object_or_404(WorshipServiceTemplate, pk=pk))
        except WorshipScheduleError as error:
            return business_error_response(error)
        return Response(WorshipServiceTemplateSerializer(template).data)


class TemplateReactivateView(APIView):
    def post(self, request, pk):
        ensure_authenticated(request.user)
        if not request.user.has_perm("worship.reactivate_worship_service_template"):
            raise PermissionDenied("Sem permissao para reativar culto padrao.")
        try:
            template = reactivate_worship_service_template(get_object_or_404(WorshipServiceTemplate, pk=pk))
        except WorshipScheduleError as error:
            return business_error_response(error)
        return Response(WorshipServiceTemplateSerializer(template).data)


class ServiceListView(APIView):
    def get(self, request):
        ensure_authenticated(request.user)
        if not can_view_schedule(request.user):
            raise PermissionDenied("Sem permissao para visualizar a agenda de cultos.")
        queryset = WorshipService.objects.select_related("template").ordered()
        year = request.query_params.get("year")
        month = request.query_params.get("month")
        if year and month:
            queryset = queryset.for_month(int(year), int(month))
        return Response(WorshipServiceSerializer(queryset, many=True).data)


class GenerateServicesView(APIView):
    def post(self, request):
        ensure_authenticated(request.user)
        if not request.user.has_perm("worship.generate_worship_services"):
            raise PermissionDenied("Sem permissao para gerar agenda de cultos.")
        serializer = GenerateWorshipServicesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = generate_worship_services_for_month(**serializer.validated_data)
        return Response(
            {
                "created_count": result["created_count"],
                "existing_count": result["existing_count"],
            }
        )


class ExtraordinaryServiceCreateView(APIView):
    def post(self, request):
        ensure_authenticated(request.user)
        if not can_manage_schedule(request.user):
            raise PermissionDenied("Sem permissao para administrar a agenda de cultos.")
        serializer = ExtraordinaryWorshipServiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = create_extraordinary_worship_service(**serializer.validated_data)
        return Response(WorshipServiceSerializer(service).data, status=status.HTTP_201_CREATED)


class ServiceDetailView(APIView):
    def get_object(self, pk):
        return get_object_or_404(WorshipService.objects.select_related("template"), pk=pk)

    def get(self, request, pk):
        ensure_authenticated(request.user)
        if not can_view_schedule(request.user):
            raise PermissionDenied("Sem permissao para visualizar a agenda de cultos.")
        return Response(WorshipServiceSerializer(self.get_object(pk)).data)

    def patch(self, request, pk):
        ensure_authenticated(request.user)
        if not can_manage_schedule(request.user):
            raise PermissionDenied("Sem permissao para administrar a agenda de cultos.")
        service = self.get_object(pk)
        serializer = WorshipServiceSerializer(service, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            service = update_worship_service(service, **serializer.validated_data)
        except ValidationError as error:
            return validation_error_response(error)
        return Response(WorshipServiceSerializer(service).data)


class ServiceCancelView(APIView):
    def post(self, request, pk):
        ensure_authenticated(request.user)
        if not request.user.has_perm("worship.cancel_worship_service"):
            raise PermissionDenied("Sem permissao para cancelar culto.")
        try:
            service = cancel_worship_service(get_object_or_404(WorshipService, pk=pk))
        except WorshipScheduleError as error:
            return business_error_response(error)
        return Response(WorshipServiceSerializer(service).data)


class ServiceReactivateView(APIView):
    def post(self, request, pk):
        ensure_authenticated(request.user)
        if not request.user.has_perm("worship.reactivate_worship_service"):
            raise PermissionDenied("Sem permissao para reativar culto.")
        try:
            service = reactivate_worship_service(get_object_or_404(WorshipService, pk=pk))
        except WorshipScheduleError as error:
            return business_error_response(error)
        return Response(WorshipServiceSerializer(service).data)
