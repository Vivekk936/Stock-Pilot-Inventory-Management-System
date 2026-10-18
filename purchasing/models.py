from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q


class PurchaseOrder(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ORDERED = "ORDERED", "Ordered"
        PARTIAL = "PARTIAL", "Partially Received"
        RECEIVED = "RECEIVED", "Received"
        CANCELLED = "CANCELLED", "Cancelled"

    order_number = models.CharField(max_length=40, unique=True)

    supplier = models.ForeignKey(
        "suppliers.Supplier",
        on_delete=models.PROTECT,
        related_name="purchase_orders",
    )
    warehouse = models.ForeignKey(
        "inventory.Warehouse",
        on_delete=models.PROTECT,
        related_name="purchase_orders",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    notes = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_purchase_orders",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.order_number

    @property
    def total_cost(self):
        return sum(
            (
                item.quantity_ordered * item.unit_cost
                for item in self.items.all()
            ),
            Decimal("0.00"),
        )


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.PROTECT,
        related_name="items",
    )
    product = models.ForeignKey(
        "inventory.Product",
        on_delete=models.PROTECT,
        related_name="purchase_order_items",
    )

    quantity_ordered = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    quantity_received = models.PositiveIntegerField(default=0)

    unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["purchase_order", "product"],
                name="unique_product_per_purchase_order",
            ),
            models.CheckConstraint(
                condition=Q(quantity_ordered__gte=1),
                name="po_ordered_quantity_positive",
            ),
            models.CheckConstraint(
                condition=Q(quantity_received__gte=0),
                name="po_received_quantity_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(quantity_received__lte=F("quantity_ordered")),
                name="po_received_not_over_ordered",
            ),
            models.CheckConstraint(
                condition=Q(unit_cost__gte=0),
                name="po_unit_cost_nonnegative",
            ),
        ]

    @property
    def quantity_remaining(self):
        return self.quantity_ordered - self.quantity_received

    def __str__(self):
        return (
            f"{self.purchase_order.order_number}: "
            f"{self.product.sku}"
        )