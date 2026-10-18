import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Product(TimeStampedModel):
    sku = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    description = models.TextField(blank=True)

    cost_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    selling_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    reorder_level = models.PositiveIntegerField(default=10)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(
                condition=Q(cost_price__gte=0),
                name="product_cost_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(selling_price__gte=0),
                name="product_selling_nonnegative",
            ),
        ]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["is_active", "sku"]),
        ]

    def __str__(self):
        return f"{self.sku} - {self.name}"


class Warehouse(TimeStampedModel):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=150)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class InventoryBalance(TimeStampedModel):
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="balances",
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="balances",
    )
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product", "warehouse"],
                name="unique_product_warehouse_balance",
            ),
            models.CheckConstraint(
                condition=Q(quantity__gte=0),
                name="inventory_quantity_nonnegative",
            ),
        ]

    def __str__(self):
        return (
            f"{self.product.sku} @ "
            f"{self.warehouse.code}: {self.quantity}"
        )


class StockMovement(models.Model):
    class MovementType(models.TextChoices):
        RECEIPT = "RECEIPT", "Receipt"
        ISSUE = "ISSUE", "Issue"
        ADJUSTMENT_IN = "ADJUSTMENT_IN", "Adjustment In"
        ADJUSTMENT_OUT = "ADJUSTMENT_OUT", "Adjustment Out"
        TRANSFER_IN = "TRANSFER_IN", "Transfer In"
        TRANSFER_OUT = "TRANSFER_OUT", "Transfer Out"

    reference = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="stock_movements",
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="stock_movements",
    )
    movement_type = models.CharField(
        max_length=20,
        choices=MovementType.choices,
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    balance_after = models.PositiveIntegerField()

    reason = models.CharField(max_length=255)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="stock_movements",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["product", "created_at"]),
            models.Index(fields=["warehouse", "created_at"]),
        ]

    def __str__(self):
        return (
            f"{self.movement_type}: {self.product.sku} "
            f"x {self.quantity}"
        )

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValueError(
                "Stock movements cannot be edited. "
                "Create a correcting movement instead."
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError(
            "Stock movements cannot be deleted."
        )

# Create your models here.
