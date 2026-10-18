
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from inventory.models import (
    Category,
    InventoryBalance,
    Product,
    StockMovement,
    Warehouse,
)
from inventory.services import change_stock


class InventoryStockTests(TestCase):
    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="inventory_test_user",
            password="test-password-123",
            is_staff=True,
        )

        self.category = Category.objects.create(
            name="Test Electronics",
            description="Products for inventory tests",
        )

        self.product = Product.objects.create(
            sku="TEST-LAP-001",
            name="Test Laptop",
            category=self.category,
            cost_price="45000.00",
            selling_price="50000.00",
            reorder_level=5,
        )

        self.warehouse = Warehouse.objects.create(
            code="TEST-WH-001",
            name="Test Warehouse",
        )

    def test_receipt_increases_stock(self):
        movement = change_stock(
            product_id=self.product.pk,
            warehouse_id=self.warehouse.pk,
            quantity=5,
            movement_type=StockMovement.MovementType.RECEIPT,
            actor=self.user,
            reason="Test stock receipt",
        )

        balance = InventoryBalance.objects.get(
            product=self.product,
            warehouse=self.warehouse,
        )

        self.assertEqual(balance.quantity, 5)
        self.assertEqual(movement.quantity, 5)
        self.assertEqual(movement.balance_after, 5)

    def test_issue_decreases_stock(self):
        change_stock(
            product_id=self.product.pk,
            warehouse_id=self.warehouse.pk,
            quantity=5,
            movement_type=StockMovement.MovementType.RECEIPT,
            actor=self.user,
            reason="Initial test stock",
        )

        movement = change_stock(
            product_id=self.product.pk,
            warehouse_id=self.warehouse.pk,
            quantity=2,
            movement_type=StockMovement.MovementType.ISSUE,
            actor=self.user,
            reason="Test stock issue",
        )

        balance = InventoryBalance.objects.get(
            product=self.product,
            warehouse=self.warehouse,
        )

        self.assertEqual(balance.quantity, 3)
        self.assertEqual(movement.balance_after, 3)

    def test_insufficient_stock_is_rejected(self):
        with self.assertRaises(ValidationError):
            change_stock(
                product_id=self.product.pk,
                warehouse_id=self.warehouse.pk,
                quantity=1,
                movement_type=StockMovement.MovementType.ISSUE,
                actor=self.user,
                reason="Issue without stock",
            )

        self.assertFalse(
            InventoryBalance.objects.filter(
                product=self.product,
                warehouse=self.warehouse,
            ).exists()
        )

        self.assertFalse(StockMovement.objects.exists())

    def test_zero_quantity_is_rejected(self):
        with self.assertRaises(ValidationError):
            change_stock(
                product_id=self.product.pk,
                warehouse_id=self.warehouse.pk,
                quantity=0,
                movement_type=StockMovement.MovementType.RECEIPT,
                actor=self.user,
                reason="Invalid zero receipt",
            )

        self.assertFalse(StockMovement.objects.exists())

    def test_negative_quantity_is_rejected(self):
        with self.assertRaises(ValidationError):
            change_stock(
                product_id=self.product.pk,
                warehouse_id=self.warehouse.pk,
                quantity=-1,
                movement_type=StockMovement.MovementType.RECEIPT,
                actor=self.user,
                reason="Invalid negative receipt",
            )

        self.assertFalse(StockMovement.objects.exists())
