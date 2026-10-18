
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from auditlog.models import AuditEvent
from inventory.models import (
    Category,
    InventoryBalance,
    Product,
    StockMovement,
    Warehouse,
)
from purchasing.models import PurchaseOrder, PurchaseOrderItem
from purchasing.services import receive_purchase_order_item


class PurchaseOrderReceivingTests(TestCase):
    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="purchasing_test_user",
            password="test-password-123",
            is_staff=True,
        )

        self.category = Category.objects.create(
            name="Purchasing Test Category",
        )

        self.product = Product.objects.create(
            sku="PUR-TEST-001",
            name="Purchasing Test Laptop",
            category=self.category,
            cost_price="45000.00",
            selling_price="50000.00",
            reorder_level=2,
        )

        self.warehouse = Warehouse.objects.create(
            code="PUR-TEST-WH",
            name="Purchasing Test Warehouse",
        )

        self.supplier = self._create_supplier()

        self.order = PurchaseOrder.objects.create(
            order_number="PO-TEST-001",
            supplier=self.supplier,
            warehouse=self.warehouse,
            created_by=self.user,
            status=PurchaseOrder.Status.ORDERED,
        )

        self.item = PurchaseOrderItem.objects.create(
            purchase_order=self.order,
            product=self.product,
            quantity_ordered=5,
            quantity_received=0,
            unit_cost="45000.00",
        )

    def _create_supplier(self):
        from suppliers.models import Supplier

        return Supplier.objects.create(
            code="PUR-TEST-SUP",
            name="Purchasing Test Supplier",
        )

    def test_partial_receipt_updates_inventory_and_audit(self):
        movement = receive_purchase_order_item(
            order_item_id=self.item.pk,
            quantity=2,
            actor=self.user,
        )

        self.item.refresh_from_db()
        self.order.refresh_from_db()

        balance = InventoryBalance.objects.get(
            product=self.product,
            warehouse=self.warehouse,
        )

        self.assertEqual(self.item.quantity_received, 2)
        self.assertEqual(self.order.status, PurchaseOrder.Status.PARTIAL)
        self.assertEqual(balance.quantity, 2)
        self.assertEqual(movement.quantity, 2)
        self.assertEqual(
            movement.movement_type,
            StockMovement.MovementType.RECEIPT,
        )

        self.assertTrue(
            AuditEvent.objects.filter(
                action="PURCHASE_ORDER_RECEIVED",
                entity_id=str(self.order.pk),
            ).exists()
        )

    def test_full_receipt_marks_order_received(self):
        receive_purchase_order_item(
            order_item_id=self.item.pk,
            quantity=5,
            actor=self.user,
        )

        self.item.refresh_from_db()
        self.order.refresh_from_db()

        self.assertEqual(self.item.quantity_received, 5)
        self.assertEqual(self.order.status, PurchaseOrder.Status.RECEIVED)

        balance = InventoryBalance.objects.get(
            product=self.product,
            warehouse=self.warehouse,
        )
        self.assertEqual(balance.quantity, 5)

    def test_receiving_more_than_remaining_is_rejected(self):
        with self.assertRaises(ValidationError):
            receive_purchase_order_item(
                order_item_id=self.item.pk,
                quantity=6,
                actor=self.user,
            )

        self.item.refresh_from_db()

        self.assertEqual(self.item.quantity_received, 0)
        self.assertFalse(InventoryBalance.objects.exists())
        self.assertFalse(StockMovement.objects.exists())
