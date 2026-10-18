from django.core.exceptions import ValidationError
from django.db import transaction

from .models import (
    InventoryBalance,
    Product,
    StockMovement,
    Warehouse,
)
from auditlog.models import AuditEvent


@transaction.atomic
def change_stock(
    *,
    product_id,
    warehouse_id,
    quantity,
    movement_type,
    actor,
    reason,
):
    if not actor or not actor.is_authenticated:
        raise ValidationError("An authenticated actor is required.")

    if not isinstance(quantity, int) or isinstance(quantity, bool):
        raise ValidationError("Quantity must be an integer.")

    if quantity <= 0:
        raise ValidationError("Quantity must be greater than zero.")

    if not reason or not reason.strip():
        raise ValidationError("A reason is required.")

    incoming_types = {
        StockMovement.MovementType.RECEIPT,
        StockMovement.MovementType.ADJUSTMENT_IN,
        StockMovement.MovementType.TRANSFER_IN,
    }

    outgoing_types = {
        StockMovement.MovementType.ISSUE,
        StockMovement.MovementType.ADJUSTMENT_OUT,
        StockMovement.MovementType.TRANSFER_OUT,
    }

    if movement_type not in incoming_types | outgoing_types:
        raise ValidationError("Unsupported movement type.")

    # Lock the product row to serialize concurrent stock operations
    # for this product, including first-time balance creation.
    product = Product.objects.select_for_update().get(
        pk=product_id,
        is_active=True,
    )

    warehouse = Warehouse.objects.get(
        pk=warehouse_id,
        is_active=True,
    )

    balance, _ = InventoryBalance.objects.get_or_create(
        product=product,
        warehouse=warehouse,
        defaults={"quantity": 0},
    )

    balance = InventoryBalance.objects.select_for_update().get(
        pk=balance.pk
    )

    old_quantity = balance.quantity

    if movement_type in outgoing_types:
        if old_quantity < quantity:
            raise ValidationError(
                f"Insufficient stock. Available: {old_quantity}."
            )
        new_quantity = old_quantity - quantity
    else:
        new_quantity = old_quantity + quantity

    balance.quantity = new_quantity
    balance.save(update_fields=["quantity", "updated_at"])

    movement = StockMovement.objects.create(
        product=product,
        warehouse=warehouse,
        movement_type=movement_type,
        quantity=quantity,
        balance_after=new_quantity,
        actor=actor,
        reason=reason.strip(),
    )

    AuditEvent.objects.create(
        actor=actor,
        action="STOCK_MOVEMENT",
        entity_type="StockMovement",
        entity_id=str(movement.reference),
        details={
            "product_sku": product.sku,
            "warehouse_code": warehouse.code,
            "movement_type": movement_type,
            "quantity": quantity,
            "previous_quantity": old_quantity,
            "balance_after": new_quantity,
            "reason": reason.strip(),
        },
    )

    return movement