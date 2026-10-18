from rest_framework.permissions import BasePermission, SAFE_METHODS


class InventoryAccessPermission(BasePermission):
    """
    Authenticated users can read inventory.
    Staff users with Django model permissions can manage catalog data.
    Stock movements are handled by dedicated service actions.
    """

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if request.method in SAFE_METHODS:
            return True

        if view.action in {"issue", "adjust_in", "adjust_out"}:
            return (
                user.is_staff
                and user.has_perm("inventory.add_stockmovement")
            )

        return user.has_perm(
            f"inventory.{self._permission_verb(request.method)}_"
            f"{view.queryset.model._meta.model_name}"
        )

    @staticmethod
    def _permission_verb(method):
        return {
            "POST": "add",
            "PUT": "change",
            "PATCH": "change",
            "DELETE": "delete",
        }.get(method, "view")