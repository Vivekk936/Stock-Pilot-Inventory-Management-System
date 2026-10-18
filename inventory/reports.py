from decimal import Decimal

from django.db.models import F, Sum, ExpressionWrapper, DecimalField
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import InventoryBalance


class LowStockReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        balances = (
            InventoryBalance.objects
            .select_related("product", "warehouse")
            .filter(
                product__is_active=True,
                warehouse__is_active=True,
                quantity__lte=F("product__reorder_level"),
            )
            .order_by("quantity")
        )

        data = [
            {
                "sku": balance.product.sku,
                "product": balance.product.name,
                "warehouse": balance.warehouse.code,
                "quantity": balance.quantity,
                "reorder_level": balance.product.reorder_level,
            }
            for balance in balances
        ]

        return Response({"count": len(data), "results": data})


class InventoryValuationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        balances = InventoryBalance.objects.filter(
            product__is_active=True,
            warehouse__is_active=True,
        )

        value_expression = ExpressionWrapper(
            F("quantity") * F("product__cost_price"),
            output_field=DecimalField(
                max_digits=24, decimal_places=2
            ),
        )

        totals = balances.aggregate(
            total_units=Sum("quantity"),
            inventory_value=Sum(value_expression),
        )

        return Response({
            "total_units": totals["total_units"] or 0,
            "inventory_value": str(
                totals["inventory_value"] or Decimal("0.00")
            ),
            "valuation_basis": "product cost price",
        })