from rest_framework import serializers

from .models import (
    Category,
    Product,
    Warehouse,
    InventoryBalance,
    StockMovement,
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "description"]


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source="category.name",
        read_only=True,
    )

    class Meta:
        model = Product
        fields = [
            "id", "sku", "name", "category", "category_name",
            "description", "cost_price", "selling_price",
            "reorder_level", "is_active",
        ]


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ["id", "code", "name", "address", "is_active"]


class InventoryBalanceSerializer(serializers.ModelSerializer):
    sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.CharField(
        source="product.name", read_only=True
    )
    warehouse_code = serializers.CharField(
        source="warehouse.code", read_only=True
    )

    class Meta:
        model = InventoryBalance
        fields = [
            "id", "product", "sku", "product_name",
            "warehouse", "warehouse_code", "quantity",
        ]


class StockMovementSerializer(serializers.ModelSerializer):
    sku = serializers.CharField(source="product.sku", read_only=True)
    actor_username = serializers.CharField(
        source="actor.username", read_only=True
    )

    class Meta:
        model = StockMovement
        fields = [
            "reference", "product", "sku", "warehouse",
            "movement_type", "quantity", "balance_after",
            "reason", "actor_username", "created_at",
        ]
        read_only_fields = fields


class StockChangeInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    warehouse_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=255)