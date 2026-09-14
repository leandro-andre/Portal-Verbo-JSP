from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CountingEnvironment, StockCategory, StockItem, StockMovement
from .serializers import (
    AttendanceCountCreateSerializer,
    AttendanceCountFilterSerializer,
    AttendanceCountListSerializer,
    AttendanceCountSerializer,
    AttendanceCountUpdateSerializer,
    CountingEnvironmentSerializer,
    CountingEnvironmentUpdateSerializer,
    StockCategorySerializer,
    StockCategoryUpdateSerializer,
    StockItemSerializer,
    StockItemUpdateSerializer,
    StockMovementCreateSerializer,
    StockMovementSerializer,
)
from .services import (
    DiaconiaError,
    create_attendance_count,
    create_stock_category,
    create_stock_item,
    create_stock_movement,
    create_counting_environment,
    deactivate_counting_environment,
    deactivate_stock_category,
    deactivate_stock_item,
    get_attendance_count_list_queryset,
    get_attendance_count_queryset,
    get_stock_items_with_status,
    get_stock_summary,
    reactivate_stock_category,
    reactivate_stock_item,
    reactivate_counting_environment,
    update_stock_category,
    update_stock_item,
    update_counting_environment,
    update_attendance_count,
)


DIACONIA_VIEW = "diaconia.view_diaconia_module"
DIACONIA_STOCK_MANAGE = "diaconia.manage_diaconia_stock"
DIACONIA_COUNTING_MANAGE = "diaconia.manage_diaconia_counting"


class HasDiaconiaPermission(BasePermission):
    method_permissions = {
        "GET": DIACONIA_VIEW,
        "POST": DIACONIA_STOCK_MANAGE,
        "PATCH": DIACONIA_STOCK_MANAGE,
    }

    def has_permission(self, request, view):
        view_method_permissions = getattr(view, "method_permission_required", {})
        permission = (
            view_method_permissions.get(request.method)
            or getattr(view, "permission_required", None)
            or self.method_permissions.get(request.method)
        )
        return bool(
            request.user.is_authenticated
            and request.user.is_active
            and permission
            and request.user.has_perm(permission)
        )


def ensure_or_403(condition):
    if not condition:
        raise PermissionDenied("Sua sessao atual nao possui permissao para acessar esta area.")


def business_error_response(exc):
    return Response({"code": exc.code, "message": exc.message}, status=status.HTTP_409_CONFLICT)


class StockUnitListView(APIView):
    permission_classes = [HasDiaconiaPermission]
    permission_required = DIACONIA_VIEW

    def get(self, request):
        return Response([{"value": value, "label": label} for value, label in StockItem.Unit.choices])


class StockCategoryListCreateView(APIView):
    permission_classes = [HasDiaconiaPermission]

    def get(self, request):
        queryset = StockCategory.objects.order_by("name", "id")
        status_filter = (request.query_params.get("status") or "").upper()
        if status_filter == "ACTIVE":
            queryset = queryset.filter(is_active=True)
        elif status_filter == "INACTIVE":
            queryset = queryset.filter(is_active=False)
        return Response(StockCategorySerializer(queryset, many=True).data)

    def post(self, request):
        serializer = StockCategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = create_stock_category(**serializer.validated_data)
        return Response(StockCategorySerializer(category).data, status=status.HTTP_201_CREATED)


class StockCategoryDetailView(APIView):
    permission_classes = [HasDiaconiaPermission]

    def get_object(self, pk):
        return get_object_or_404(StockCategory, pk=pk)

    def get(self, request, pk):
        ensure_or_403(request.user.has_perm(DIACONIA_VIEW))
        return Response(StockCategorySerializer(self.get_object(pk)).data)

    def patch(self, request, pk):
        ensure_or_403(request.user.has_perm(DIACONIA_STOCK_MANAGE))
        serializer = StockCategoryUpdateSerializer(self.get_object(pk), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        category = update_stock_category(serializer.instance, **serializer.validated_data)
        return Response(StockCategorySerializer(category).data)


class StockCategoryDeactivateView(APIView):
    permission_classes = [HasDiaconiaPermission]
    permission_required = DIACONIA_STOCK_MANAGE

    def post(self, request, pk):
        try:
            category = deactivate_stock_category(get_object_or_404(StockCategory, pk=pk))
        except DiaconiaError as exc:
            return business_error_response(exc)
        return Response(StockCategorySerializer(category).data)


class StockCategoryReactivateView(APIView):
    permission_classes = [HasDiaconiaPermission]
    permission_required = DIACONIA_STOCK_MANAGE

    def post(self, request, pk):
        try:
            category = reactivate_stock_category(get_object_or_404(StockCategory, pk=pk))
        except DiaconiaError as exc:
            return business_error_response(exc)
        return Response(StockCategorySerializer(category).data)


class StockItemListCreateView(APIView):
    permission_classes = [HasDiaconiaPermission]

    def get(self, request):
        queryset = get_stock_items_with_status().order_by("name", "id")
        status_filter = (request.query_params.get("status") or "").upper()
        if status_filter == "ACTIVE":
            queryset = queryset.filter(is_active=True)
        elif status_filter == "INACTIVE":
            queryset = queryset.filter(is_active=False)
        stock_status = (request.query_params.get("stock_status") or "").upper()
        if stock_status:
            queryset = queryset.filter(stock_status=stock_status)
        category_id = request.query_params.get("category")
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        search = (request.query_params.get("search") or "").strip()
        if search:
            queryset = queryset.filter(name__icontains=search)
        return Response(StockItemSerializer(queryset, many=True).data)

    def post(self, request):
        serializer = StockItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            item = create_stock_item(**serializer.validated_data)
        except DiaconiaError as exc:
            return business_error_response(exc)
        return Response(StockItemSerializer(item).data, status=status.HTTP_201_CREATED)


class StockItemDetailView(APIView):
    permission_classes = [HasDiaconiaPermission]

    def get_object(self, pk):
        return get_object_or_404(get_stock_items_with_status(), pk=pk)

    def get(self, request, pk):
        ensure_or_403(request.user.has_perm(DIACONIA_VIEW))
        return Response(StockItemSerializer(self.get_object(pk)).data)

    def patch(self, request, pk):
        ensure_or_403(request.user.has_perm(DIACONIA_STOCK_MANAGE))
        serializer = StockItemUpdateSerializer(self.get_object(pk), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            item = update_stock_item(serializer.instance, **serializer.validated_data)
        except DiaconiaError as exc:
            return business_error_response(exc)
        return Response(StockItemSerializer(item).data)


class StockSummaryView(APIView):
    permission_classes = [HasDiaconiaPermission]
    permission_required = DIACONIA_VIEW

    def get(self, request):
        summary = get_stock_summary()
        return Response(
            {
                "active_items": summary["active_items"],
                "low_stock_items": summary["low_stock_items"],
                "without_minimum_control": summary["without_minimum_control"],
                "replenishment_items": StockItemSerializer(summary["replenishment_items"], many=True).data,
            }
        )


class StockItemDeactivateView(APIView):
    permission_classes = [HasDiaconiaPermission]
    permission_required = DIACONIA_STOCK_MANAGE

    def post(self, request, pk):
        try:
            item = deactivate_stock_item(get_object_or_404(StockItem.objects.select_related("category"), pk=pk))
        except DiaconiaError as exc:
            return business_error_response(exc)
        return Response(StockItemSerializer(item).data)


class StockItemReactivateView(APIView):
    permission_classes = [HasDiaconiaPermission]
    permission_required = DIACONIA_STOCK_MANAGE

    def post(self, request, pk):
        try:
            item = reactivate_stock_item(get_object_or_404(StockItem.objects.select_related("category"), pk=pk))
        except DiaconiaError as exc:
            return business_error_response(exc)
        return Response(StockItemSerializer(item).data)


class StockMovementListCreateView(APIView):
    permission_classes = [HasDiaconiaPermission]

    def get(self, request):
        queryset = (
            StockMovement.objects.select_related("item", "created_by")
            .order_by("-created_at", "-id")
        )
        item_id = request.query_params.get("item")
        if item_id:
            queryset = queryset.filter(item_id=item_id)
        movement_type = (request.query_params.get("type") or "").upper()
        if movement_type in StockMovement.Type.values:
            queryset = queryset.filter(movement_type=movement_type)
        search = (request.query_params.get("search") or "").strip()
        if search:
            queryset = queryset.filter(item__name__icontains=search)
        return Response(StockMovementSerializer(queryset, many=True).data)

    def post(self, request):
        ensure_or_403(request.user.has_perm(DIACONIA_STOCK_MANAGE))
        serializer = StockMovementCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            movement = create_stock_movement(
                item=serializer.validated_data["item"],
                movement_type=serializer.validated_data["movement_type"],
                quantity=serializer.validated_data["quantity"],
                notes=serializer.validated_data.get("notes", ""),
                created_by=request.user,
            )
        except DiaconiaError as exc:
            return business_error_response(exc)
        return Response(StockMovementSerializer(movement).data, status=status.HTTP_201_CREATED)


class StockMovementDetailView(APIView):
    permission_classes = [HasDiaconiaPermission]
    permission_required = DIACONIA_VIEW

    def get(self, request, pk):
        movement = get_object_or_404(
            StockMovement.objects.select_related("item", "created_by"),
            pk=pk,
        )
        return Response(StockMovementSerializer(movement).data)


class CountingEnvironmentListCreateView(APIView):
    permission_classes = [HasDiaconiaPermission]
    method_permission_required = {"GET": DIACONIA_VIEW, "POST": DIACONIA_COUNTING_MANAGE}

    def get(self, request):
        queryset = CountingEnvironment.objects.order_by("name", "id")
        status_filter = (request.query_params.get("status") or "").upper()
        if status_filter == "ACTIVE":
            queryset = queryset.filter(is_active=True)
        elif status_filter == "INACTIVE":
            queryset = queryset.filter(is_active=False)
        search = (request.query_params.get("search") or "").strip()
        if search:
            queryset = queryset.filter(name__icontains=search)
        return Response(CountingEnvironmentSerializer(queryset, many=True).data)

    def post(self, request):
        ensure_or_403(request.user.has_perm(DIACONIA_COUNTING_MANAGE))
        serializer = CountingEnvironmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        environment = create_counting_environment(**serializer.validated_data)
        return Response(CountingEnvironmentSerializer(environment).data, status=status.HTTP_201_CREATED)


class CountingEnvironmentDetailView(APIView):
    permission_classes = [HasDiaconiaPermission]
    method_permission_required = {"GET": DIACONIA_VIEW, "PATCH": DIACONIA_COUNTING_MANAGE}

    def get_object(self, pk):
        return get_object_or_404(CountingEnvironment, pk=pk)

    def get(self, request, pk):
        ensure_or_403(request.user.has_perm(DIACONIA_VIEW))
        return Response(CountingEnvironmentSerializer(self.get_object(pk)).data)

    def patch(self, request, pk):
        ensure_or_403(request.user.has_perm(DIACONIA_COUNTING_MANAGE))
        serializer = CountingEnvironmentUpdateSerializer(self.get_object(pk), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        environment = update_counting_environment(serializer.instance, **serializer.validated_data)
        return Response(CountingEnvironmentSerializer(environment).data)


class CountingEnvironmentDeactivateView(APIView):
    permission_classes = [HasDiaconiaPermission]
    permission_required = DIACONIA_COUNTING_MANAGE

    def post(self, request, pk):
        try:
            environment = deactivate_counting_environment(get_object_or_404(CountingEnvironment, pk=pk))
        except DiaconiaError as exc:
            return business_error_response(exc)
        return Response(CountingEnvironmentSerializer(environment).data)


class CountingEnvironmentReactivateView(APIView):
    permission_classes = [HasDiaconiaPermission]
    permission_required = DIACONIA_COUNTING_MANAGE

    def post(self, request, pk):
        try:
            environment = reactivate_counting_environment(get_object_or_404(CountingEnvironment, pk=pk))
        except DiaconiaError as exc:
            return business_error_response(exc)
        return Response(CountingEnvironmentSerializer(environment).data)


class AttendanceCountListCreateView(APIView):
    permission_classes = [HasDiaconiaPermission]
    method_permission_required = {"GET": DIACONIA_VIEW, "POST": DIACONIA_COUNTING_MANAGE}

    def get(self, request):
        filter_serializer = AttendanceCountFilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        queryset = get_attendance_count_list_queryset()
        date_from = filter_serializer.validated_data.get("date_from")
        date_to = filter_serializer.validated_data.get("date_to")
        shift = filter_serializer.validated_data.get("shift")
        created_by = filter_serializer.validated_data.get("created_by")
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        if shift:
            queryset = queryset.filter(shift=shift)
        if created_by:
            queryset = queryset.filter(created_by_id=created_by)
        return Response(AttendanceCountListSerializer(queryset, many=True).data)

    def post(self, request):
        ensure_or_403(request.user.has_perm(DIACONIA_COUNTING_MANAGE))
        serializer = AttendanceCountCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            attendance_count = create_attendance_count(
                date=serializer.validated_data["date"],
                shift=serializer.validated_data["shift"],
                notes=serializer.validated_data.get("notes", ""),
                entries=serializer.validated_data["entries"],
                created_by=request.user,
            )
        except DiaconiaError as exc:
            return business_error_response(exc)
        return Response(AttendanceCountSerializer(attendance_count).data, status=status.HTTP_201_CREATED)


class AttendanceCountDetailView(APIView):
    permission_classes = [HasDiaconiaPermission]
    method_permission_required = {"GET": DIACONIA_VIEW, "PATCH": DIACONIA_COUNTING_MANAGE}

    def get(self, request, pk):
        attendance_count = get_object_or_404(get_attendance_count_queryset(), pk=pk)
        return Response(AttendanceCountSerializer(attendance_count).data)

    def patch(self, request, pk):
        ensure_or_403(request.user.has_perm(DIACONIA_COUNTING_MANAGE))
        attendance_count = get_object_or_404(get_attendance_count_queryset(), pk=pk)
        serializer = AttendanceCountUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            attendance_count = update_attendance_count(
                attendance_count,
                date=serializer.validated_data["date"],
                shift=serializer.validated_data["shift"],
                notes=serializer.validated_data.get("notes", ""),
                entries=serializer.validated_data["entries"],
            )
        except DiaconiaError as exc:
            return business_error_response(exc)
        return Response(AttendanceCountSerializer(attendance_count).data)
