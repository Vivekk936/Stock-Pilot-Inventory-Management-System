from rest_framework.routers import DefaultRouter
from django.urls import path
from .reports import LowStockReportView, InventoryValuationView
from .views import (
    CategoryViewSet,
    ProductViewSet,
    WarehouseViewSet,
    InventoryBalanceViewSet,
    StockMovementViewSet,
)

router = DefaultRouter()
router.register("categories", CategoryViewSet)
router.register("products", ProductViewSet)
router.register("warehouses", WarehouseViewSet)
router.register("balances", InventoryBalanceViewSet)
router.register("movements", StockMovementViewSet)

urlpatterns = router.urls
urlpatterns += [
    path("reports/low-stock/", LowStockReportView.as_view()),
    path("reports/valuation/", InventoryValuationView.as_view()),
]