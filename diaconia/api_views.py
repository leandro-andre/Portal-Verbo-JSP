from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import StockCategory, StockItem, StockMovement
from .serializers import (
    StockCategorySerializer,
    StockCategoryUpdateSerializer,
    StockItemSerializer,
    StockItemUpdateSerializer,
    StockMovementCreateSerializer,
    StockMovementSerializer,
)
from .services import (
    DiaconiaError,
    create_stock_category,
    create_stock_item,
    create_stock_movement,
    deactivate_stock_category,
    deactivate_stock_item,
    get_stock_items_with_balance,
    reactivate_stock_category,
    reactivate_stock_item,
    update_stock_category,
    update_stock_item,
)


DIACONIA_VIEW = "diaconia.view_diaconia_module"
DIACONIA_STOCK_MANAGE = "diaconia.manage_diaconia_stock"


class HasDiaconiaStockPermission(BasePermission):
    method_permissions = {
        "GET": DIACONIA_VIEW,
        "POST": DIACONIA_STOCK_MANAGE,
        "PATCH": DIACONIA_STOCK_MANAGE,
    }

    def has_permission(self, request, view):
        permission = getattr(view, "permission_required", None) or self.method_permissions.get(request.method)
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
    permission_classes = [HasDiaconiaStockPermission]
    permission_required = DIACONIA_VIEW

    def get(self, request):
        return Response([{"value": value, "label": label} for value, label in StockItem.Unit.choices])


class StockCategoryListCreateView(APIView):
    permission_classes = [HasDiaconiaStockPermission]

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
    permission_classes = [HasDiaconiaStockPermission]

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
    permission_classes = [HasDiaconiaStockPermission]
    permission_required = DIACONIA_STOCK_MANAGE

    def post(self, request, pk):
        try:
            category = deactivate_stock_category(get_object_or_404(StockCategory, pk=pk))
        except DiaconiaError as exc:
            return business_error_response(exc)
        return Response(StockCategorySerializer(category).data)


class StockCategoryReactivateView(APIView):
    permission_classes = [HasDiaconiaStockPermission]
    permission_required = DIACONIA_STOCK_MANAGE

    def post(self, request, pk):
        try:
            category = reactivate_stock_category(get_object_or_404(StockCategory, pk=pk))
        except DiaconiaError as exc:
            return business_error_response(exc)
        return Response(StockCategorySerializer(category).data)


class StockItemListCreateView(APIView):
    permission_classes = [HasDiaconiaStockPermission]

    def get(self, request):
        queryset = get_stock_items_with_balance().order_by("name", "id")
        status_filter = (request.query_params.get("status") or "").upper()
        if status_filter == "ACTIVE":
            queryset = queryset.filter(is_active=True)
        elif status_filter == "INACTIVE":
            queryset = queryset.filter(is_active=False)
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
    permission_classes = [HasDiaconiaStockPermission]

    def get_object(self, pk):
        return get_object_or_404(get_stock_items_with_balance(), pk=pk)

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


class StockItemDeactivateView(APIView):
    permission_classes = [HasDiaconiaStockPermission]
    permission_required = DIACONIA_STOCK_MANAGE

    def post(self, request, pk):
        try:
            item = deactivate_stock_item(get_object_or_404(StockItem.objects.select_related("category"), pk=pk))
        except DiaconiaError as exc:
            return business_error_response(exc)
        return Response(StockItemSerializer(item).data)


class StockItemReactivateView(APIView):
    permission_classes = [HasDiaconiaStockPermission]
    permission_required = DIACONIA_STOCK_MANAGE

    def post(self, request, pk):
        try:
            item = reactivate_stock_item(get_object_or_404(StockItem.objects.select_related("category"), pk=pk))
        except DiaconiaError as exc:
            return business_error_response(exc)
        return Response(StockItemSerializer(item).data)


class StockMovementListCreateView(APIView):
    permission_classes = [HasDiaconiaStockPermission]

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
    permission_classes = [HasDiaconiaStockPermission]
    permission_required = DIACONIA_VIEW

    def get(self, request, pk):
        movement = get_object_or_404(
            StockMovement.objects.select_related("item", "created_by"),
            pk=pk,
        )
        return Response(StockMovementSerializer(movement).data)
