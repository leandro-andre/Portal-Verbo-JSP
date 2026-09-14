from django.urls import path

from . import api_views


urlpatterns = [
    path("stock/units/", api_views.StockUnitListView.as_view(), name="diaconia-stock-unit-list"),
    path("stock/categories/", api_views.StockCategoryListCreateView.as_view(), name="diaconia-stock-category-list"),
    path("stock/categories/<int:pk>/", api_views.StockCategoryDetailView.as_view(), name="diaconia-stock-category-detail"),
    path(
        "stock/categories/<int:pk>/deactivate/",
        api_views.StockCategoryDeactivateView.as_view(),
        name="diaconia-stock-category-deactivate",
    ),
    path(
        "stock/categories/<int:pk>/reactivate/",
        api_views.StockCategoryReactivateView.as_view(),
        name="diaconia-stock-category-reactivate",
    ),
    path("stock/items/", api_views.StockItemListCreateView.as_view(), name="diaconia-stock-item-list"),
    path("stock/items/<int:pk>/", api_views.StockItemDetailView.as_view(), name="diaconia-stock-item-detail"),
    path(
        "stock/items/<int:pk>/deactivate/",
        api_views.StockItemDeactivateView.as_view(),
        name="diaconia-stock-item-deactivate",
    ),
    path(
        "stock/items/<int:pk>/reactivate/",
        api_views.StockItemReactivateView.as_view(),
        name="diaconia-stock-item-reactivate",
    ),
    path("stock/movements/", api_views.StockMovementListCreateView.as_view(), name="diaconia-stock-movement-list"),
    path(
        "stock/movements/<int:pk>/",
        api_views.StockMovementDetailView.as_view(),
        name="diaconia-stock-movement-detail",
    ),
]
