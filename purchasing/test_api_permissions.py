
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from inventory.models import (
    Category,
    Product,
    Warehouse,
    InventoryBalance,
    StockMovement,
)
from suppliers.models import Supplier
from purchasing.models import PurchaseOrder, PurchaseOrderItem


User = get_user_model()


class PurchaseOrderReceiveAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="creator",
            password="TestPassword123!",
        )

        self.category = Category.objects.create(name="Test Category")

        self.product = Product.objects.create(
            sku="PO-TEST-001",
            name="Purchase Test Product",
            category=self.category,
            cost_price="10.00",
            selling_price="15.00",
        )

        self.warehouse = Warehouse.objects.create(
            code="PO-WH-01",
            name="Purchase Test Warehouse",
        )

        self.supplier = Supplier.objects.create(
            name="Test Supplier",
            code="SUP-TEST-01",
        )

        self.order = PurchaseOrder.objects.create(
            order_number="PO-TEST-001",
            supplier=self.supplier,
            warehouse=self.warehouse,
            status=PurchaseOrder.Status.ORDERED,
            created_by=self.user,
        )

        self.item = PurchaseOrderItem.objects.create(
            purchase_order=self.order,
            product=self.product,
            quantity_ordered=10,
            unit_cost="10.00",
        )

        self.balance = InventoryBalance.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            quantity=0,
        )

        self.receive_url = reverse(
            "purchaseorder-receive",
            kwargs={
                "pk": self.order.pk,
                "item_id": self.item.pk,
            },
        )

        self.payload = {"quantity": 4}

        self.stock_permission = Permission.objects.get(
            codename="add_stockmovement",
            content_type__app_label="inventory",
        )

    def make_staff(self, *, with_permission=False):
        user = User.objects.create_user(
            username=f"staff_{User.objects.count()}",
            password="TestPassword123!",
            is_staff=True,
        )

        if with_permission:
            user.user_permissions.add(self.stock_permission)

        return user

    def test_unauthenticated_user_cannot_receive_stock(self):
        response = self.client.post(
            self.receive_url,
            self.payload,
            format="json",
        )

        self.assertIn(response.status_code, (401, 403))
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.quantity, 0)
        self.assertEqual(self.item.quantity_received, 0)

    def test_regular_user_cannot_receive_stock(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.receive_url,
            self.payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.quantity, 0)

    def test_staff_without_permission_cannot_receive_stock(self):
        staff = self.make_staff()
        self.client.force_authenticate(user=staff)

        response = self.client.post(
            self.receive_url,
            self.payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.quantity, 0)

    def test_authorized_staff_can_receive_stock(self):
        staff = self.make_staff(with_permission=True)
        self.client.force_authenticate(user=staff)

        response = self.client.post(
            self.receive_url,
            self.payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            response.data,
        )

        self.balance.refresh_from_db()
        self.item.refresh_from_db()

        self.assertEqual(self.balance.quantity, 4)
        self.assertEqual(self.item.quantity_received, 4)
        self.assertEqual(
            StockMovement.objects.filter(
                movement_type=StockMovement.MovementType.RECEIPT,
                actor=staff,
            ).count(),
            1,
        )

    def test_item_from_another_order_is_rejected(self):
        another_order = PurchaseOrder.objects.create(
            order_number="PO-TEST-002",
            supplier=self.supplier,
            warehouse=self.warehouse,
            status=PurchaseOrder.Status.ORDERED,
            created_by=self.user,
        )

        staff = self.make_staff(with_permission=True)
        self.client.force_authenticate(user=staff)

        wrong_url = reverse(
            "purchaseorder-receive",
            kwargs={
                "pk": another_order.pk,
                "item_id": self.item.pk,
            },
        )

        response = self.client.post(
            wrong_url,
            self.payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.balance.refresh_from_db()
        self.item.refresh_from_db()

        self.assertEqual(self.balance.quantity, 0)
        self.assertEqual(self.item.quantity_received, 0)
        self.assertEqual(StockMovement.objects.count(), 0)
