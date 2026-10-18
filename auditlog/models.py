
from django.conf import settings
from django.db import models


class AuditEvent(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="audit_events",
    )

    action = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=100)

    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["entity_type", "entity_id"]
            ),
            models.Index(
                fields=["actor", "created_at"]
            ),
        ]

    def __str__(self):
        return (
            f"{self.action} - {self.entity_type} "
            f"{self.entity_id}"
        )

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValueError(
                "Audit events cannot be edited."
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError(
            "Audit events cannot be deleted."
        )
