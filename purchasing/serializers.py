from rest_framework import serializers

from .models import PurchaseOrder, PurchaseOrderItem


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(
        source="product.sku", read_only=True
    )
    quantity_remaining = serializers.IntegerField(read_only=True)

    class Meta:
        model = PurchaseOrderItem
        fields = [
            "id", "product", "product_sku",
            "quantity_ordered", "quantity_received",
            "quantity_remaining", "unit_cost",
        ]


class PurchaseOrderSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(
        source="supplier.name", read_only=True
    )
    warehouse_code = serializers.CharField(
        source="warehouse.code", read_only=True
    )
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    total_cost = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )

    class Meta:
        model = PurchaseOrder
        fields = [
            "id", "order_number", "supplier", "supplier_name",
            "warehouse", "warehouse_code", "status", "notes",
            "created_by", "created_at", "items", "total_cost",
        ]
        read_only_fields = fields


class ReceiveItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)