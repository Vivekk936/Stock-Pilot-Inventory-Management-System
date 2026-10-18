
from django.contrib.auth import get_user_model
from django.test import TestCase

from auditlog.models import AuditEvent


class AuditEventTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="audit_test_user",
            password="test-password-123",
        )

    def test_audit_event_is_created(self):
        event = AuditEvent.objects.create(
            actor=self.user,
            action="TEST_ACTION",
            entity_type="Product",
            entity_id="TEST-001",
            details={"name": "Test Laptop"},
        )

        self.assertEqual(event.actor, self.user)
        self.assertEqual(event.action, "TEST_ACTION")
        self.assertEqual(event.entity_type, "Product")
        self.assertEqual(event.entity_id, "TEST-001")
        self.assertEqual(event.details["name"], "Test Laptop")

    def test_audit_event_cannot_be_updated(self):
        event = AuditEvent.objects.create(
            actor=self.user,
            action="TEST_ACTION",
            entity_type="Product",
            entity_id="TEST-002",
            details={},
        )

        event.action = "UPDATED_ACTION"

        with self.assertRaises(Exception):
            event.save()

    def test_audit_event_cannot_be_deleted(self):
        event = AuditEvent.objects.create(
            actor=self.user,
            action="TEST_ACTION",
            entity_type="Product",
            entity_id="TEST-003",
            details={},
        )

        with self.assertRaises(Exception):
            event.delete()
