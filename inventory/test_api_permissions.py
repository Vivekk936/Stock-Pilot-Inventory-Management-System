
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


User = get_user_model()


class StockMovementAPIPermissionTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Test Category"
        )

        self.product = Product.objects.create(
            sku="TEST-001",
            name="Test Product",
            category=self.category,
            cost_price="100.00",
            selling_price="150.00",
            reorder_level=5,
        )

        self.warehouse = Warehouse.objects.create(
            code="WH-TEST",
            name="Test Warehouse",
        )

        self.balance = InventoryBalance.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            quantity=10,
        )

        self.issue_url = reverse("stockmovement-issue")

        self.payload = {
            "product_id": self.product.pk,
            "warehouse_id": self.warehouse.pk,
            "quantity": 2,
            "reason": "API permission test",
        }

        self.stock_permission = Permission.objects.get(
            codename="add_stockmovement",
            content_type__app_label="inventory",
        )

    def create_user(self, *, is_staff=False, with_permission=False):
        user = User.objects.create_user(
            username=f"user_{User.objects.count()}",
            password="TestPassword123!",
            is_staff=is_staff,
        )

        if with_permission:
            user.user_permissions.add(self.stock_permission)

        return user

    def test_unauthenticated_user_cannot_issue_stock(self):
        response = self.client.post(
            self.issue_url,
            self.payload,
            format="json",
        )

        self.assertIn(response.status_code, (401, 403))
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.quantity, 10)
        self.assertEqual(StockMovement.objects.count(), 0)

    def test_non_staff_user_cannot_issue_stock(self):
        user = self.create_user(with_permission=True)
        self.client.force_authenticate(user=user)

        response = self.client.post(
            self.issue_url,
            self.payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.quantity, 10)
        self.assertEqual(StockMovement.objects.count(), 0)

    def test_staff_without_permission_cannot_issue_stock(self):
        user = self.create_user(is_staff=True)
        self.client.force_authenticate(user=user)

        response = self.client.post(
            self.issue_url,
            self.payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.quantity, 10)
        self.assertEqual(StockMovement.objects.count(), 0)

    def test_authorized_staff_can_issue_stock(self):
        user = self.create_user(
            is_staff=True,
            with_permission=True,
        )
        self.client.force_authenticate(user=user)

        response = self.client.post(
            self.issue_url,
            self.payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.balance.refresh_from_db()
        self.assertEqual(self.balance.quantity, 8)

        movement = StockMovement.objects.get()
        self.assertEqual(movement.movement_type, "ISSUE")
        self.assertEqual(movement.quantity, 2)
        self.assertEqual(movement.actor, user)
        self.assertEqual(movement.balance_after, 8)
