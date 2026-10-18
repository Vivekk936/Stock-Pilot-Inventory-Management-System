
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from inventory.models import StockMovement
from inventory.serializers import StockMovementSerializer

from .models import PurchaseOrder, PurchaseOrderItem
from .serializers import PurchaseOrderSerializer, ReceiveItemSerializer
from .services import receive_purchase_order_item


class PurchaseOrderViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        PurchaseOrder.objects
        .select_related("supplier", "warehouse", "created_by")
        .prefetch_related("items__product")
    )

    serializer_class = PurchaseOrderSerializer
    permission_classes = [IsAuthenticated]

    filterset_fields = ["status", "supplier", "warehouse"]
    search_fields = ["order_number", "supplier__name"]
    ordering_fields = ["created_at", "order_number"]

    @action(
        detail=True,
        methods=["post"],
        url_path=r"receive/(?P<item_id>[^/.]+)",
    )
    def receive(self, request, pk=None, item_id=None):
        order = self.get_object()

        # Check staff status and permission
        if not request.user.is_staff or not request.user.has_perm(
            "inventory.add_stockmovement"
        ):
            raise PermissionDenied(
                "You are not authorized to receive stock."
            )

        # Validate that the item belongs to this purchase order
        try:
            item = PurchaseOrderItem.objects.get(
                pk=item_id,
                purchase_order=order,
            )
        except PurchaseOrderItem.DoesNotExist:
            raise ValidationError({
                "item_id": "This item does not belong to this purchase order."
            })

        # Validate the requested receiving quantity
        serializer = ReceiveItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            movement = receive_purchase_order_item(
                order_item_id=item.pk,
                quantity=serializer.validated_data["quantity"],
                actor=request.user,
            )
        except DjangoValidationError as exc:
            raise ValidationError({
                "detail": exc.messages
            }) from exc

        return Response(
            StockMovementSerializer(movement).data,
            status=status.HTTP_201_CREATED,
        )
