
from django.contrib import admin
from .models import PurchaseOrder, PurchaseOrderItem


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "supplier",
        "warehouse",
        "status",
        "created_by",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("order_number", "supplier__name")
    readonly_fields = ("created_by",)
    inlines = [PurchaseOrderItemInline]

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "purchase_order",
        "product",
        "quantity_ordered",
        "quantity_received",
        "unit_cost",
    )
    list_filter = ("purchase_order__status",)
    search_fields = ("purchase_order__order_number", "product__name")
