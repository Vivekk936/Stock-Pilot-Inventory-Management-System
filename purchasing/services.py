from django.core.exceptions import ValidationError
from django.db import transaction

from auditlog.models import AuditEvent
from inventory.models import StockMovement
from inventory.services import change_stock

from .models import PurchaseOrder, PurchaseOrderItem


@transaction.atomic
def receive_purchase_order_item(
    *,
    order_item_id,
    quantity,
    actor,
):
    if not actor or not actor.is_authenticated:
        raise ValidationError("An authenticated actor is required.")

    item = (
        PurchaseOrderItem.objects
        .select_for_update()
        .select_related(
            "purchase_order",
            "purchase_order__supplier",
            "purchase_order__warehouse",
            "product",
        )
        .get(pk=order_item_id)
    )

    order = (
        PurchaseOrder.objects
        .select_for_update()
        .get(pk=item.purchase_order_id)
    )

    if order.status not in {
        PurchaseOrder.Status.ORDERED,
        PurchaseOrder.Status.PARTIAL,
    }:
        raise ValidationError(
            "Only ordered or partially received orders can be received."
        )

    if not isinstance(quantity, int) or isinstance(quantity, bool):
        raise ValidationError("Quantity must be an integer.")

    if quantity <= 0:
        raise ValidationError("Quantity must be positive.")

    if quantity > item.quantity_remaining:
        raise ValidationError(
            f"Only {item.quantity_remaining} units remain to be received."
        )

    movement = change_stock(
        product_id=item.product_id,
        warehouse_id=order.warehouse_id,
        quantity=quantity,
        movement_type=StockMovement.MovementType.RECEIPT,
        actor=actor,
        reason=f"Purchase order {order.order_number}",
    )

    item.quantity_received += quantity
    item.save(update_fields=["quantity_received"])

    remaining_items = list(
        order.items.select_for_update()
    )

    if all(
        row.quantity_received == row.quantity_ordered
        for row in remaining_items
    ):
        order.status = PurchaseOrder.Status.RECEIVED
    else:
        order.status = PurchaseOrder.Status.PARTIAL

    order.save(update_fields=["status", "updated_at"])

    AuditEvent.objects.create(
        actor=actor,
        action="PURCHASE_ORDER_RECEIVED",
        entity_type="PurchaseOrder",
        entity_id=str(order.pk),
        details={
            "order_number": order.order_number,
            "item_id": item.pk,
            "product_sku": item.product.sku,
            "quantity_received": quantity,
            "movement_reference": str(movement.reference),
            "status": order.status,
        },
    )

    return movement