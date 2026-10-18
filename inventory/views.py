from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    Category,
    Product,
    Warehouse,
    InventoryBalance,
    StockMovement,
)
from .permissions import InventoryAccessPermission
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    WarehouseSerializer,
    InventoryBalanceSerializer,
    StockMovementSerializer,
)
from .services import change_stock


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [InventoryAccessPermission]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category").all()
    serializer_class = ProductSerializer
    permission_classes = [InventoryAccessPermission]
    filterset_fields = ["category", "is_active"]
    search_fields = ["sku", "name"]
    ordering_fields = ["name", "cost_price", "selling_price"]


class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [InventoryAccessPermission]
    search_fields = ["code", "name"]


class InventoryBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InventoryBalance.objects.select_related(
        "product", "warehouse"
    ).all()
    serializer_class = InventoryBalanceSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["product", "warehouse"]
    search_fields = ["product__sku", "product__name", "warehouse__code"]


class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockMovement.objects.select_related(
        "product", "warehouse", "actor"
    ).all()
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["product", "warehouse", "movement_type"]
    search_fields = ["product__sku", "reason", "reference"]
    ordering_fields = ["created_at", "quantity"]

    @action(detail=False, methods=["post"])
    def issue(self, request):
        return self._change(request, StockMovement.MovementType.ISSUE)

    @action(detail=False, methods=["post"])
    def adjust_in(self, request):
        return self._change(
            request, StockMovement.MovementType.ADJUSTMENT_IN
        )

    @action(detail=False, methods=["post"])
    def adjust_out(self, request):
        return self._change(
            request, StockMovement.MovementType.ADJUSTMENT_OUT
        )

    def _change(self, request, movement_type):
        if not request.user.is_staff or not request.user.has_perm(
            "inventory.add_stockmovement"
        ):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(
                "You are not authorized to change stock."
            )

        serializer = StockChangeInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            movement = change_stock(
                **serializer.validated_data,
                movement_type=movement_type,
                actor=request.user,
            )
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages) from exc

        return Response(
            StockMovementSerializer(movement).data,
            status=status.HTTP_201_CREATED,
        )


class StockChangeInputSerializer(
    __import__("rest_framework").serializers.Serializer
):
    product_id = __import__("rest_framework").serializers.IntegerField(
        min_value=1
    )
    warehouse_id = __import__("rest_framework").serializers.IntegerField(
        min_value=1
    )
    quantity = __import__("rest_framework").serializers.IntegerField(
        min_value=1
    )
    reason = __import__("rest_framework").serializers.CharField(
        max_length=255
    )