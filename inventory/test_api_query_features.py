
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from inventory.models import Category, Product


User = get_user_model()


class ProductAPIQueryTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="query_test_user",
            password="TestPassword123!",
        )
        self.client.force_authenticate(user=self.user)

        self.category = Category.objects.create(
            name="Query Test Category",
        )

        self.other_category = Category.objects.create(
            name="Other Query Category",
        )

        self.product_url = reverse("product-list")

        self.alpha_product = Product.objects.create(
            sku="QUERY-ALPHA",
            name="Alpha Laptop",
            category=self.category,
            cost_price="100.00",
            selling_price="150.00",
            is_active=True,
        )

        self.beta_product = Product.objects.create(
            sku="QUERY-BETA",
            name="Beta Keyboard",
            category=self.category,
            cost_price="20.00",
            selling_price="35.00",
            is_active=True,
        )

        self.inactive_product = Product.objects.create(
            sku="QUERY-INACTIVE",
            name="Inactive Mouse",
            category=self.other_category,
            cost_price="10.00",
            selling_price="15.00",
            is_active=False,
        )

    def test_search_products_by_name(self):
        response = self.client.get(
            self.product_url,
            {"search": "Alpha Laptop"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["sku"],
            "QUERY-ALPHA",
        )

    def test_filter_products_by_category(self):
        response = self.client.get(
            self.product_url,
            {"category": self.category.pk},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        returned_skus = {
            product["sku"]
            for product in response.data["results"]
        }

        self.assertEqual(
            returned_skus,
            {"QUERY-ALPHA", "QUERY-BETA"},
        )

    def test_filter_products_by_active_status(self):
        response = self.client.get(
            self.product_url,
            {"is_active": "false"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        returned_skus = {
            product["sku"]
            for product in response.data["results"]
        }

        self.assertEqual(returned_skus, {"QUERY-INACTIVE"})

    def test_order_products_by_name(self):
        response = self.client.get(
            self.product_url,
            {"ordering": "name"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        names = [
            product["name"]
            for product in response.data["results"]
        ]

        self.assertEqual(names, sorted(names))

    def test_product_list_is_paginated(self):
        for number in range(30):
            Product.objects.create(
                sku=f"PAGE-{number:03}",
                name=f"Pagination Product {number:03}",
                category=self.category,
                cost_price="5.00",
                selling_price="8.00",
            )

        response = self.client.get(self.product_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 33)
        self.assertEqual(len(response.data["results"]), 25)
        self.assertIsNotNone(response.data["next"])
