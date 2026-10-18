
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from auditlog.models import AuditEvent
from inventory.models import (
    Category,
    Product,
    Warehouse,
    InventoryBalance,
    StockMovement,
)
from inventory.services import change_stock
from purchasing.models import PurchaseOrder, PurchaseOrderItem
from purchasing.services import receive_purchase_order_item
from suppliers.models import Supplier


User = get_user_model()


class InventoryAuditServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="audit_service_user",
            password="TestPassword123!",
        )

        self.category = Category.objects.create(
            name="Audit Test Category"
        )

        self.product = Product.objects.create(
            sku="AUDIT-001",
            name="Audit Test Product",
            category=self.category,
            cost_price="10.00",
            selling_price="15.00",
        )

        self.warehouse = Warehouse.objects.create(
            code="AUDIT-WH",
            name="Audit Test Warehouse",
        )

        self.balance = InventoryBalance.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            quantity=10,
        )

    def test_successful_stock_change_creates_audit_event(self):
        movement = change_stock(
            product_id=self.product.pk,
            warehouse_id=self.warehouse.pk,
            quantity=2,
            movement_type=StockMovement.MovementType.ISSUE,
            actor=self.user,
            reason="Test stock issue",
        )

        self.balance.refresh_from_db()

        self.assertEqual(self.balance.quantity, 8)

        event = AuditEvent.objects.get(
            action="STOCK_MOVEMENT",
            entity_id=str(movement.reference),
        )

        self.assertEqual(event.actor, self.user)
        self.assertEqual(event.entity_type, "StockMovement")
        self.assertEqual(event.details["quantity"], 2)
        self.assertEqual(event.details["previous_quantity"], 10)
        self.assertEqual(event.details["balance_after"], 8)
        self.assertEqual(event.details["reason"], "Test stock issue")

    def test_failed_stock_issue_leaves_no_partial_changes(self):
        with self.assertRaises(ValidationError):
            change_stock(
                product_id=self.product.pk,
                warehouse_id=self.warehouse.pk,
                quantity=11,
                movement_type=StockMovement.MovementType.ISSUE,
                actor=self.user,
                reason="Insufficient stock test",
            )

        self.balance.refresh_from_db()

        self.assertEqual(self.balance.quantity, 10)
        self.assertEqual(StockMovement.objects.count(), 0)
        self.assertEqual(AuditEvent.objects.count(), 0)


class PurchaseReceiptAuditTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="receipt_audit_user",
            password="TestPassword123!",
        )

        self.category = Category.objects.create(
            name="Receipt Audit Category"
        )

        self.product = Product.objects.create(
            sku="RECEIPT-AUDIT-001",
            name="Receipt Audit Product",
            category=self.category,
            cost_price="20.00",
            selling_price="30.00",
        )

        self.warehouse = Warehouse.objects.create(
            code="RECEIPT-WH",
            name="Receipt Warehouse",
        )

        self.supplier = Supplier.objects.create(
            name="Receipt Audit Supplier",
            code="RECEIPT-SUP",
        )

        self.order = PurchaseOrder.objects.create(
            order_number="PO-AUDIT-001",
            supplier=self.supplier,
            warehouse=self.warehouse,
            status=PurchaseOrder.Status.ORDERED,
            created_by=self.user,
        )

        self.item = PurchaseOrderItem.objects.create(
            purchase_order=self.order,
            product=self.product,
            quantity_ordered=5,
            unit_cost="20.00",
        )

        self.balance = InventoryBalance.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            quantity=0,
        )

    def test_receipt_creates_stock_and_purchase_audit_events(self):
        movement = receive_purchase_order_item(
            order_item_id=self.item.pk,
            quantity=2,
            actor=self.user,
        )

        self.balance.refresh_from_db()
        self.item.refresh_from_db()
        self.order.refresh_from_db()

        self.assertEqual(self.balance.quantity, 2)
        self.assertEqual(self.item.quantity_received, 2)
        self.assertEqual(self.order.status, PurchaseOrder.Status.PARTIAL)

        stock_event = AuditEvent.objects.get(
            action="STOCK_MOVEMENT",
            entity_id=str(movement.reference),
        )

        purchase_event = AuditEvent.objects.get(
            action="PURCHASE_ORDER_RECEIVED",
            entity_id=str(self.order.pk),
        )

        self.assertEqual(stock_event.actor, self.user)
        self.assertEqual(purchase_event.actor, self.user)

        self.assertEqual(
            purchase_event.details["order_number"],
            self.order.order_number,
        )
        self.assertEqual(
            purchase_event.details["quantity_received"],
            2,
        )
        self.assertEqual(
            purchase_event.details["movement_reference"],
            str(movement.reference),
        )

    def test_over_receipt_does_not_change_stock_or_audit(self):
        with self.assertRaises(ValidationError):
            receive_purchase_order_item(
                order_item_id=self.item.pk,
                quantity=6,
                actor=self.user,
            )

        self.balance.refresh_from_db()
        self.item.refresh_from_db()
        self.order.refresh_from_db()

        self.assertEqual(self.balance.quantity, 0)
        self.assertEqual(self.item.quantity_received, 0)
        self.assertEqual(self.order.status, PurchaseOrder.Status.ORDERED)
        self.assertEqual(StockMovement.objects.count(), 0)
        self.assertEqual(AuditEvent.objects.count(), 0)
